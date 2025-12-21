import time
import os
import re
import sys
import numpy as np
import shutil
import tempfile
from eppy.modeleditor import IDF
from eppy.runner.run_functions import (
    install_paths,
    parse_error,
    CalledProcessError,
    check_call,
    StringIO
)
from multiprocessing.pool import Pool
from typing import List, Optional, Dict, Union, Any
from subprocess import Popen
import win32process
from utils import *


def run_with_cpu(
        idf: Union[str, IDF],
        weather: str,
        output_directory: str = "",
        annual: bool = False,
        design_day: bool = False,
        idd: Optional[str] = None,
        epmacro: bool = False,
        expandobjects: bool = False,
        readvars: bool = False,
        output_prefix: Optional[str] = None,
        output_suffix: Optional[str] = None,
        version: bool = False,
        verbose: str = "v",
        ep_version: Optional[str] = None,
        cpu_index: Optional[int] = None
) -> str:
    """
    Function for single task simulation
    Wrapper around the EnergyPlus command line interface with CPU affinity support.
    This is a more robust method from eppy.runner.run_functions.


    Parameters
    ----------
    idf : Union[str, IDF]
        Full/relative path to the IDF file, or an IDF object.
    weather : str
        Full/relative path to the weather file.
    output_directory : str, optional
        Full/relative path to the output directory (default: "").
    annual : bool, optional
        Force annual simulation (default: False).
    design_day : bool, optional
        Force design-day-only simulation (default: False).
    idd : Optional[str], optional
        Path to Input Data Dictionary file (default: Energy+.idd in EnergyPlus directory).
    epmacro : bool, optional
        Run EPMacro prior to simulation (default: False).
    expandobjects : bool, optional
        Run ExpandObjects prior to simulation (default: False).
    readvars : bool, optional
        Run ReadVarsESO after simulation (default: False).
    output_prefix : Optional[str], optional
        Prefix for output file names (default: None, uses "eplus").
    output_suffix : Optional[str], optional
        Suffix style for output files (default: None, uses "L"):
            L: Legacy (e.g., eplustbl.csv)
            C: Capital (e.g., eplusTable.csv)
            D: Dash (e.g., eplus-table.csv)
    version : bool, optional
        Display EnergyPlus version information (default: False).
    verbose : str, optional
        Verbosity level of runtime messages (default: "v"):
            v: verbose
            q: quiet
            s: silent
    ep_version : Optional[str], optional
        EnergyPlus version for locating install directory. Required if passing IDF file path.
    cpu_index : Optional[int], optional
        Index of CPU core to allocate (default: None, uses all cores).

    Returns
    -------
    str
        Status message ("OK" if successful).

    Raises
    ------
    CalledProcessError
        If EnergyPlus execution fails.
    AttributeError
        If ep_version is not provided when passing an IDF file path.
    RuntimeError
        If IDF file is not found or execution error occurs.
    FileNotFoundError
        If EnergyPlus executable is not found.
    """
    args = locals().copy()
    verbose = args.pop("verbose").lower()
    idf = args.pop("idf")
    iddname = args.get("idd")

    if not isinstance(iddname, str):
        args.pop("idd")

    # Resolve IDF path
    try:
        idf_path = os.path.abspath(idf.idfname)
    except AttributeError:
        idf_path = os.path.abspath(idf)

    if not os.path.isfile(idf_path):
        raise RuntimeError(f"ERROR: Could not find input data file: {idf_path}")

    # Auto-enable expandobjects if HVACTEMPLATE exists
    if not expandobjects:
        with open(idf_path, "r") as f:
            args["expandobjects"] = "HVACTEMPLATE:" in f.read().upper()

    ep_version = args.pop("ep_version")

    # Get EnergyPlus version from IDF or raise error
    if not ep_version:
        try:
            ep_version = "-".join(str(x) for x in idf.idd_version[:3])
        except AttributeError:
            raise AttributeError(
                "The ep_version must be set when passing an IDF path. "
                "Alternatively, use IDF.run()"
            )

    # Get EnergyPlus executable and weather directory paths
    eplus_exe_path, eplus_weather_path = install_paths(ep_version, iddname)

    if version:
        cmd = [eplus_exe_path, "--version"]
        check_call(cmd)
        return "OK"

    if not os.path.exists(eplus_exe_path):
        raise FileNotFoundError(f"Could not find eplus executable: {eplus_exe_path}")

    # Resolve weather file path
    if os.path.isfile(args["weather"]):
        args["weather"] = os.path.abspath(args["weather"])
    else:
        args["weather"] = os.path.join(eplus_weather_path, args["weather"])

    # Resolve output directory and IDD path
    args["output_directory"] = os.path.abspath(args["output_directory"])
    if iddname is not None:
        args["idd"] = os.path.abspath(iddname)

    # Prepare runtime environment
    cwd = os.getcwd()
    run_dir = os.path.abspath(tempfile.mkdtemp())
    os.chdir(run_dir)

    # Build command line arguments
    cmd = [eplus_exe_path]
    args.pop("cpu_index")

    for arg in args:
        if args[arg]:
            if isinstance(args[arg], bool):
                args[arg] = ""
            cmd.extend([f"--{arg.replace('_', '-')}"])
            if args[arg] != "":
                if os.path.isfile(args[arg]):
                    args[arg] = f'"{args[arg]}"'
                cmd.extend([args[arg]])

    cmd.extend([f'"{idf_path}"'])

    # Redirect stderr for error parsing
    tmp_err = StringIO()
    old_err = sys.stderr
    sys.stderr = tmp_err

    try:
        # Execute EnergyPlus with appropriate verbosity
        if verbose == "v":
            print(f"\r\n{' '.join(cmd)}\r\n")
            proc = Popen(" ".join(cmd))
        elif verbose == "q":
            proc = Popen(" ".join(cmd), stdout=open(os.devnull, "w"))
        elif verbose == "s":
            with open(os.devnull, "w") as null:
                proc = Popen(" ".join(cmd), stdout=null, stderr=null)
        else:
            raise ValueError(f"Unknown verbose mode: {verbose}")

        # Set CPU affinity if specified
        if cpu_index is not None:
            mask = 1 << cpu_index
            print(f'allocate to {mask}:{cpu_index}->{idf_path}')
            win32process.SetProcessAffinityMask(proc._handle, mask)

        # Wait for process completion
        proc.wait()
        return "OK"

    except CalledProcessError:
        # Parse and raise execution error
        if output_prefix:
            err_file = os.path.join(args["output_directory"], f"{output_prefix}.err")
        else:
            err_file = os.path.join(args["output_directory"], "eplusout.err")
        message = parse_error(tmp_err, err_file)
        raise RuntimeError(message)

    finally:
        # Restore original environment
        sys.stderr = old_err
        os.chdir(cwd)


def occupy(idf_path: str) -> bool:
    """
    Check if IDF simulation is already in progress using a lock file.

    Parameters
    ----------
    idf_path : str
        Path to the IDF file.

    Returns
    -------
    bool
        True if simulation is in progress (lock file exists), False otherwise.
    """
    lock_file = f"{idf_path}start"
    if os.path.exists(lock_file):
        return True
    with open(lock_file, "w") as f:
        f.write("1")
    return False


def make_eplaunch_options(idf: IDF, **kwargs: Any) -> Dict[str, Any]:
    """
    Create simulation options matching EPLaunch behavior on Windows.

    Parameters
    ----------
    idf : IDF
        IDF object for simulation.
    **kwargs : Any
        Additional options to override default values.

    Returns
    -------
    Dict[str, Any]
        Dictionary of simulation options.
    """
    # Parse IDF version
    idfversion = idf.idfobjects['version'][0].Version_Identifier.split('.')
    idfversion.extend([0] * (3 - len(idfversion)))

    # Default EPLaunch-compatible options
    options = {
        'output_prefix': os.path.basename(idf.idfname).split('.')[0],
        'output_suffix': 'C',
        'output_directory': os.path.dirname(idf.idfname),
        'readvars': True,
        'expandobjects': True
    }

    # Override with user-provided kwargs
    options.update(kwargs)
    return options


def error_callback(error: Exception) -> None:
    """
    Callback function for handling multiprocessing errors.

    Parameters
    ----------
    error : Exception
        Exception raised by the multiprocessing task.
    """
    print(f'****Process Error: {error}')


def return_callback(msg: str) -> None:
    """
    Callback function for handling successful multiprocessing task results.

    Parameters
    ----------
    msg : str
        Result message from the multiprocessing task.
    """
    print(msg)


def simulate_file(
        idf_path: str,
        epw: str,
        idd: Optional[str] = None,
        overwrite: bool = False,
        verbose: str = 'q',
        cpu_index: Optional[int] = None,
        long_dir: bool = False,
        **kwargs: Any
) -> str:
    """
    Simulate a single IDF file with specified weather file and options.
    allow stick a simualtion process to defined CPU.
    A packup function to the run_with_cpu for better parallelization.

    Parameters
    ----------
    idf_path : str
        Path to the IDF file.
    epw : str
        Path to the weather (EPW) file.
    idd : Optional[str], optional
        Path to the IDD file (default: None, auto-detected).
    overwrite : bool, optional
        Overwrite existing results if True (default: False).
    verbose : str, optional
        Verbosity level (default: 'q'):
            v: verbose
            q: quiet
            s: silent
    cpu_index : Optional[int], optional
        CPU core index to allocate (default: None).
    long_dir : bool, optional
        Use extended directory name (IDF + EPW name) if True (default: False).
    **kwargs : Any
        Additional options passed to run_with_cpu.

    Returns
    -------
    str
        Status message indicating simulation result.
    """

    def _processing(
            idf_path: str,
            epw: str,
            idd: Optional[str] = None,
            overwrite: bool = False,
            long_dir: bool = False,
            **kwargs: Any
    ) -> str:
        # Check EnergyPlus installation
        if not check_installation(idf_path):
            return f'Energyplus Ver.{get_version(idf_path)} is not yet installed.'

        # Auto-detect IDD if not provided
        if idd is None:
            idd = get_idd(idf_path)
        IDF.setiddname(idd)

        # Create output directory
        if long_dir:
            target_dir = f"{idf_path[:-4]}+{os.path.basename(epw)[:-4]}"
        else:
            target_dir = idf_path[:-4]

        new_idf_path = os.path.join(target_dir, f"{os.path.basename(epw)}.idf")

        # Handle existing results
        if os.path.exists(target_dir):
            if os.path.exists(f"{new_idf_path}.start"):
                return ""
            if overwrite:
                shutil.rmtree(target_dir)
                os.mkdir(target_dir)
            elif os.path.exists(f"{new_idf_path[:-4]}.sql"):
                return f'**********Result Already Exist. Skip:{new_idf_path}'
        else:
            os.mkdir(target_dir)

        print(f'Case Start:{idf_path}')
        shutil.copy(idf_path, new_idf_path)

        # Load IDF and add SQLite output if missing
        idf = IDF(new_idf_path, epw=epw)
        if len(idf.idfobjects['Output:SQLite']) == 0:
            sql = idf.newidfobject('Output:SQLite')
            sql.Option_Type = 'Simple'
            idf.save()
            print(f'add SQL to:{new_idf_path}')

        # Prepare simulation options
        theoptions = make_eplaunch_options(idf, **kwargs)
        if cpu_index is not None:
            theoptions['cpu_index'] = cpu_index

        # Extract additional kwargs
        idd = kwargs.pop("idd", idf.iddname)
        epw = kwargs.pop("weather", idf.epw)

        # Run simulation
        try:
            run_with_cpu(idf, weather=epw, idd=idd, **theoptions)
        finally:
            pass

        return f'Case Done:{new_idf_path}'

    # Set verbosity and execute
    kwargs['verbose'] = verbose
    if os.path.isfile(idf_path) and os.path.exists(idf_path):
        if verbose == 's':
            with hiddenPrint() as log:
                result = _processing(idf_path, epw, idd, overwrite, long_dir, **kwargs)
                log.dump(f"{new_idf_path[:-4]}.log")
                return ""
        else:
            return _processing(idf_path, epw, idd, overwrite, long_dir, **kwargs)
    else:
        return f'IDF not found: {idf_path}'


def simulate_sequence(
        idfs: List[Union[str, IDF]],
        epw: str,
        idd: Optional[str] = None,
        overwrite: bool = False,
        verbose: str = 'q',
        cpu_index: Optional[int] = None,
        long_dir: bool = False,
        **kwargs: Any
) -> None:
    """
    Simulate a sequence of IDF files sequentially on a specific CPU core.

    Parameters
    ----------
    idfs : List[Union[str, IDF]]
        List of IDF file paths or IDF objects.
    epw : str
        Path to the weather (EPW) file.
    idd : Optional[str], optional
        Path to the IDD file (default: None).
    overwrite : bool, optional
        Overwrite existing results if True (default: False).
    verbose : str, optional
        Verbosity level (default: 'q').
    cpu_index : Optional[int], optional
        CPU core index to allocate (default: None).
    long_dir : bool, optional
        Use extended directory name if True (default: False).
    **kwargs : Any
        Additional options passed to simulate_file.
    """
    t1 = time.time()
    for idf_item in idfs:
        if isinstance(idf_item, str):
            if os.path.isfile(idf_item):
                if occupy(idf_item):
                    continue
                simulate_file(idf_item, epw, idd, overwrite, verbose, cpu_index, long_dir, **kwargs)
        elif isinstance(idf_item, IDF):
            simulate_file(idf_item.idfabsname, epw, idd, overwrite, verbose, cpu_index, long_dir, **kwargs)

    print(f'**********Sequence on CPU:{cpu_index} Done**********')
    print("duration:", time.time() - t1)


def simulate_local(
        idf_path: Union[str, IDF],
        epw: Union[str, List[str]],
        idd: Optional[str] = None,
        overwrite: bool = False,
        stdout: Any = sys.stdout,
        verbose: str = 'q',
        prs_count: int = 7,
        forceCPU: bool = False,
        **kwargs: Any
) -> int:
    """
    Simulate IDF files locally with multiprocessing support.

    Parameters
    ----------
    idf_path : Union[str, IDF]
        Path to single IDF file, IDF object, or directory of IDF files.
    epw : Union[str, List[str]]
        Path to single EPW file or list of EPW files.
    idd : Optional[str], optional
        Path to the IDD file (default: None).
    overwrite : bool, optional
        Overwrite existing results if True (default: False).
    stdout : Any, optional
        Standard output stream (default: sys.stdout).
    verbose : str, optional
        Verbosity level (default: 'q').
    prs_count : int, optional
        Number of processes to use (default: 7).
    forceCPU : bool, optional
        Force CPU core allocation if True (default: False).
    **kwargs : Any
        Additional options passed to simulate_file.

    Returns
    -------
    int
        1 if simulation completes successfully.
    """
    sys.stdout = stdout

    # Resolve IDF path if it's an IDF object
    if isinstance(idf_path, IDF):
        idf_path = idf_path.idfabsname

    # Handle single IDF file
    if os.path.isfile(idf_path):
        if isinstance(epw, list):
            for epwi in epw:
                return simulate_file(idf_path, epwi, idd, overwrite, verbose, long_dir=True)
        else:
            return simulate_file(idf_path, epw, idd, overwrite, verbose, long_dir=True)

    # Handle directory of IDF files
    elif os.path.isdir(idf_path):
        prs_pool = Pool(prs_count)

        # Normalize EPW input
        if isinstance(epw, list):
            long_dir = True
        else:
            epw = [epw]
            long_dir = False

        for epwi in epw:
            if prs_count <= os.cpu_count() and forceCPU:
                # Get all IDF files in directory
                idfs = [os.path.join(idf_path, file) for file in os.listdir(idf_path) if file.endswith('.idf')]

                # Allocate IDF files to specific CPU cores
                for cpu_index in range(1, prs_count + 1):
                    prs_pool.apply_async(
                        func=simulate_sequence,
                        args=(idfs[cpu_index - 1:], epwi, idd, overwrite, verbose, cpu_index, long_dir),
                        callback=return_callback,
                        error_callback=error_callback
                    )
            else:
                # No CPU core allocation - use all available cores
                for file in os.listdir(idf_path):
                    file_path = os.path.join(idf_path, file)
                    if file_path.endswith('.idf'):
                        prs_pool.apply_async(
                            func=simulate_file,
                            args=(file_path, epwi, idd, overwrite, verbose, None, long_dir),
                            callback=return_callback,
                            error_callback=error_callback
                        )

        # Wait for all processes to complete
        prs_pool.close()
        prs_pool.join()

        # Clean up lock files
        idf_start_files = [os.path.join(idf_path, file) for file in os.listdir(idf_path) if file.endswith('.idfstart')]
        for f in idf_start_files:
            os.remove(f)

        print('**********ALL DONE**********')
        return 1

    return 0


def simulate_cloud(
        idfs: Union[str, List[str]],
        epw: str,
        project_name: Optional[str] = None,
        overwrite: bool = True,
        remote_folder: str = r"\\166.111.40.8\temp\epeditor\project",
        timeouts: int = 1800
) -> int:
    """
    Simulate IDF files on a remote cloud server by uploading and downloading.

    Parameters
    ----------
    idfs : Union[str, List[str]]
        Path to directory of IDF files or list of IDF file paths.
    epw : str
        Path to the weather (EPW) file.
    project_name : Optional[str], optional
        Name of the remote project folder (default: None, auto-generated).
    overwrite : bool, optional
        Overwrite existing remote project if True (default: True).
    remote_folder : str, optional
        Path to remote storage folder (default: r"\\166.111.40.8\temp\epeditor\project").
    timeouts : int, optional
        Average timeout per task in seconds. It will be automatically adjusted during simulation (default: 1800).

    Returns
    -------
    int
        1 if simulation completes successfully, 0 if remote access fails.

    Raises
    ------
    FileNotFoundError
        If IDF or EPW file is not found.
    """
    t1 = time.time()

    # Normalize IDF input
    if isinstance(idfs, str):
        if os.path.isdir(idfs):
            idfs = [os.path.join(idfs, file) for file in os.listdir(idfs)]
    idfs = [file for file in idfs if file.endswith('.idf')]

    # Generate project name if not provided
    if project_name is None:
        project_name = generate_code(4)

    # Validate input files
    for idf_path in idfs:
        if not os.path.exists(idf_path):
            raise FileNotFoundError(f'IDF not found: {idf_path}')
    if not os.path.exists(epw):
        raise FileNotFoundError(f'EPW not found: {epw}')

    # Prepare remote project directory
    epeditor_dir = rf'{remote_folder}\{project_name}'
    try:
        if not os.path.exists(epeditor_dir):
            os.mkdir(epeditor_dir)
    except Exception as e:
        print(f"Lost access to remote folder: {e}")
        return 0

    # Upload files to remote server
    tasks = []
    for idx, idf_path in enumerate(idfs):
        # Get EnergyPlus version and IDD
        version = get_version(idf_path)
        idd = get_idd(idf_path)
        IDF.setiddname(idd)

        # Load IDF and add SQLite output if missing
        idf_obj = IDF(idf_path, epw=epw)
        if len(idf_obj.idfobjects['Output:SQLite']) == 0:
            sql = idf_obj.newidfobject('Output:SQLite')
            sql.Option_Type = 'Simple'
            idf_obj.save()

        # Create remote IDF directory
        idf_dir = os.path.join(epeditor_dir, os.path.basename(idf_path)[:-4])
        if not overwrite and os.path.exists(idf_dir):
            tasks.append(idf_dir)
            continue

        os.mkdir(idf_dir)

        # Copy files to remote directory
        shutil.copy(idf_path, os.path.join(idf_dir, os.path.basename(idf_path)))
        shutil.copy(epw, os.path.join(idf_dir, os.path.basename(epw)))

        # Create version and run marker files
        with open(os.path.join(idf_dir, f'{version}.vrs'), 'w') as f:
            f.write(version)
        with open(os.path.join(idf_dir, 'runit.runit'), 'w') as f:
            f.write("0")

        tasks.append(idf_dir)
        bar(idx, len(idfs), 2, "Uploading")

    print(f"\n********Upload duration: {time.time() - t1:.2f}s********")

    # Monitor simulation progress
    check_tasks = tasks.copy()
    check_idfs = idfs.copy()

    simulation_control = {
        "remainTask": 0,
        "checkPoint": 0,
        "averageTimeout": timeouts,
        "startTime": time.time()
    }

    while len(check_tasks) > 0:
        finished_indices = []
        remain_task = 0

        # Check each task for completion
        for idx, idf_dir in enumerate(check_tasks):
            finished_files = [f for f in os.listdir(idf_dir) if f.endswith(('.eso', '.err'))]
            if len(finished_files) == 0:
                remain_task += 1
            else:
                finished_indices.append(idx)

        # Copy completed results back
        for idx in finished_indices:
            print(f"\rDownloading: {check_tasks[idx]}", end="")
            shutil.copytree(check_tasks[idx], check_idfs[idx][:-4])

        # Update task lists
        check_tasks = np.delete(check_tasks, finished_indices).tolist()
        check_idfs = np.delete(check_idfs, finished_indices).tolist()

        # Update progress bar
        bar(len(tasks) - remain_task, len(tasks), 2, f'Remain:{remain_task}')

        # Update simulation control metrics
        if remain_task != simulation_control['remainTask']:
            simulation_control['remainTask'] = remain_task
            simulation_control['checkPoint'] = time.time()
            if len(tasks) - remain_task > 0:
                simulation_control['averageTimeout'] = (time.time() - simulation_control['startTime']) / (
                        len(tasks) - remain_task
                )
        else:
            # Timeout check
            if time.time() - simulation_control['checkPoint'] > 1.5 * simulation_control['averageTimeout']:
                break

        time.sleep(1)

    # Print final statistics
    success_count = len(tasks) - remain_task
    print(
        f"\nSuccess: {success_count}, Failed: {remain_task}, "
        f"Average time: {simulation_control['averageTimeout']:.2f}s"
    )
    print('**********ALL DONE**********')

    return 1

def find_sql(idf_dir: str) -> Dict[str, str]:
    """
    Recursively find all SQLite result files in a directory.

    Parameters
    ----------
    idf_dir : str
        Directory to search for SQL files.

    Returns
    -------
    Dict[str, str]
        Dictionary mapping case names to SQL file paths.
    """
    sql_files = {}
    for dirpath, _, filenames in os.walk(idf_dir):
        for file in filenames:
            if re.search(r'\.sql', file, re.IGNORECASE):
                case_name = os.path.normpath(dirpath).split(os.sep)[-1]
                sql_files[case_name] = os.path.join(dirpath, file)
    return sql_files

if __name__ == '__main__':
    msg = simulate_file(
        r'test\baseline_0.idf',
        epw=r'C:\EnergyPlusV22-2-0\WeatherData\CHN_Beijing.Beijing.545110_SWERA.epw'
    )
    print(msg)