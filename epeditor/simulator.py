import sys
import time

from typing import List

import queue
from eppy.modeleditor import IDF
import os, shutil, re
import numpy as np
from multiprocessing.pool import Pool
from .utils import *
from eppy.runner.run_functions import install_paths, parse_error, CalledProcessError, check_call, StringIO
import sys
import tempfile
def run_with_cpu(
        idf=None,
        weather=None,
        output_directory="",
        annual=False,
        design_day=False,
        idd=None,
        epmacro=False,
        expandobjects=False,
        readvars=False,
        output_prefix=None,
        output_suffix=None,
        version=False,
        verbose="v",
        ep_version=None,
        cpu_index=None
):
    """
    Wrapper around the EnergyPlus command line interface.

    Parameters
    ----------
    idf : str
        Full or relative path to the IDF file to be run, or an IDF object.

    weather : str
        Full or relative path to the weather file.

    output_directory : str, optional
        Full or relative path to an output directory (default: 'run_outputs)

    annual : bool, optional
        If True then force annual simulation (default: False)

    design_day : bool, optional
        Force design-day-only simulation (default: False)

    idd : str, optional
        Input data dictionary (default: Energy+.idd in EnergyPlus directory)

    epmacro : str, optional
        Run EPMacro prior to simulation (default: False).

    expandobjects : bool, optional
        Run ExpandObjects prior to simulation (default: False)

    readvars : bool, optional
        Run ReadVarsESO after simulation (default: False)

    output_prefix : str, optional
        Prefix for output file names (default: eplus)

    output_suffix : str, optional
        Suffix style for output file names (default: L)
            L: Legacy (e.g., eplustbl.csv)
            C: Capital (e.g., eplusTable.csv)
            D: Dash (e.g., eplus-table.csv)

    version : bool, optional
        Display version information (default: False)

    verbose: str
        Set verbosity of runtime messages (default: v)
            v: verbose
            q: quiet
            s: silent

    ep_version: str
        EnergyPlus version, used to find install directory. Required if run() is
        called with an IDF file path rather than an IDF object.

    cpu_index: int
        Index of CPU cores to use (default: None)

    Returns
    -------
    str : status

    Raises
    ------
    CalledProcessError

    AttributeError
        If no ep_version parameter is passed when calling with an IDF file path
        rather than an IDF object.


    """
    args = locals().copy()
    # get unneeded params out of args ready to pass the rest to energyplus.exe
    verbose = args.pop("verbose").lower()
    idf = args.pop("idf")
    iddname = args.get("idd")
    if not isinstance(iddname, str):
        args.pop("idd")
    try:
        idf_path = os.path.abspath(idf.idfname)
    except AttributeError:
        idf_path = os.path.abspath(idf)
    if not os.path.isfile(idf_path):
        raise RuntimeError(
            "ERROR: Could not find input data file: {}".format(idf_path)
        )
    if not expandobjects:
        with open(idf_path, "r") as f:
            args["expandobjects"] = "HVACTEMPLATE:" in f.read().upper()
    ep_version = args.pop("ep_version")
    # get version from IDF object or by parsing the IDF file for it
    if not ep_version:
        try:
            ep_version = "-".join(str(x) for x in idf.idd_version[:3])
        except AttributeError:
            raise AttributeError(
                "The ep_version must be set when passing an IDF path. \
                Alternatively, use IDF.run()"
            )

    eplus_exe_path, eplus_weather_path = install_paths(ep_version, iddname)
    if version:
        # just get EnergyPlus version number and return
        cmd = [eplus_exe_path, "--version"]
        check_call(cmd)
        return
    if not os.path.exists(eplus_exe_path):
        raise FileNotFoundError("Could not find eplus executable: {}".format(eplus_exe_path))
    # convert paths to absolute paths if required
    if os.path.isfile(args["weather"]):
        args["weather"] = os.path.abspath(args["weather"])
    else:
        args["weather"] = os.path.join(eplus_weather_path, args["weather"])
    output_dir = os.path.abspath(args["output_directory"])
    args["output_directory"] = output_dir
    if iddname is not None:
        args["idd"] = os.path.abspath(iddname)

    # store the directory we start in
    cwd = os.getcwd()
    run_dir = os.path.abspath(tempfile.mkdtemp())
    os.chdir(run_dir)

    # store the output prefix, as it influences the error file name
    output_prefix = args.get("output_prefix")

    # build a list of command line arguments
    cmd = [eplus_exe_path]
    args.pop("cpu_index")
    # if cpu_index:
    #     cmd = [f'start /affinity {} {eplus_exe_path}']

    for arg in args:
        if args[arg]:
            if isinstance(args[arg], bool):
                args[arg] = ""
            cmd.extend(["--{}".format(arg.replace("_", "-"))])
            if args[arg] != "":
                cmd.extend([args[arg]])
    cmd.extend([idf_path])

    # allocate CPUs to the process

    # send stdout to tmp filehandle to avoid issue #245
    tmp_err = StringIO()
    old_err = sys.stderr
    sys.stderr = tmp_err
    try:
        # print(" ".join(cmd))
        import win32process
        from subprocess import Popen
        if verbose == "v":
            print("\r\n" + " ".join(cmd) + "\r\n")
            proc = Popen(" ".join(cmd))
        elif verbose == "q":
            proc = Popen(" ".join(cmd), stdout=open(os.devnull, "w"))
        elif verbose == "s":
            with open(os.devnull, "w") as null:
                # Null can be written to, so this is not expected to affect issue #245.
                proc = Popen(" ".join(cmd), stdout=null, stderr=null)
        if cpu_index:
            mask = 1 << cpu_index
            print(f'allocate to {mask}:{cpu_index}->{idf_path}')
            win32process.SetProcessAffinityMask(proc._handle, mask)
        # 3) 阻塞等待结束
        proc.wait()
        return "OK"
        # if verbose == "v":
        #     print("\r\n" + " ".join(cmd) + "\r\n")
        #     check_call(cmd)
        # elif verbose == "q":
        #     check_call(cmd, stdout=open(os.devnull, "w"))
        # elif verbose == "s":
        #     with open(os.devnull, "w") as null:
        #         # Null can be written to, so this is not expected to affect issue #245.
        #         check_call(cmd, stdout=null, stderr=null)
        # else:
        #     raise ValueError("Unknown verbose mode: {}".format(verbose))
    except CalledProcessError:
        if output_prefix:
            err_file = os.path.join(output_dir, output_prefix + ".err")
        else:
            err_file = os.path.join(output_dir, "eplusout.err")
        message = parse_error(tmp_err, err_file)
        raise RuntimeError(message)
    finally:
        sys.stderr = old_err
        os.chdir(cwd)
    return "OK"


def occupy(idf_path):
    if os.path.exists(idf_path + 'start'):
        return True
    with open(idf_path + 'start', "w") as f:
        f.write("1")
    return False


def make_eplaunch_options(idf, **kwargs):
    """Make options for run, so that it runs like EPLaunch on Windows"""
    idfversion = idf.idfobjects['version'][0].Version_Identifier.split('.')
    idfversion.extend([0] * (3 - len(idfversion)))
    idfversionstr = '-'.join([str(item) for item in idfversion])
    fname = idf.idfname
    options = {
        # 'ep_version':idfversionstr, # runIDFs needs the version number
        # idf.run does not need the above arg
        # you can leave it there and it will be fine :-)

        'output_prefix': os.path.basename(fname).split('.')[0],
        'output_suffix': 'C',
        'output_directory': os.path.dirname(fname),
        'readvars': True,
        'expandobjects': True,
        #'verbose': 'v'  # allow all stdout
        #'verbose':'q' # ban the stdout but allow stderr
        #'verbose':'s'  # ban both the stdout and stderr
    }
    for key in kwargs.keys():
        options[key] = kwargs[key]
    return options


def error_callback(error):
    print(f'****Process Error: {error}')


def return_callback(msg):
    print(msg)


def simulate_file(idf_path: str, epw: str, idd: str = None, overwrite=False, verbose='q', cpu_index=None,long_dir=False, **kwargs):
    def _processing(idf_path: str, epw: str, idd: str = None, overwrite=False,long_dir=False, **kwargs):
        if not check_installation(idf_path):
            return f'Energyplus Ver.{get_version(idf_path)} is not yet installed.'
        if idd is None:
            idd = get_idd(idf_path)
        IDF.setiddname(idd)
        if long_dir:
            target_dir = idf_path[:-4] +"+"+ os.path.basename(epw)[:-4]
        else:
            target_dir = idf_path[:-4]
        new_idf_path = os.path.join(target_dir, os.path.basename(epw)[:-4]) + '.idf'
        if os.path.exists(target_dir):
            if os.path.exists(new_idf_path + '.start'):
                return ""

            if overwrite:
                shutil.rmtree(target_dir)
                os.mkdir(target_dir)

            elif os.path.exists(new_idf_path[:-4] + '.sql'):
                return f'**********Result Already Exist. Skip:{new_idf_path}'
        else:
            os.mkdir(target_dir)

        print(f'Case Start:{idf_path}')
        shutil.copy(idf_path, new_idf_path)
        idf = IDF(new_idf_path)
        if len(idf.idfobjects['Output:SQLite']) == 0:
            sql = idf.newidfobject('Output:SQLite')
            sql.Option_Type = 'Simple'
            idf.save()
            print(f'add SQL to:{new_idf_path}')
        theoptions = make_eplaunch_options(idf, **kwargs)

        if cpu_index:
            theoptions['cpu_index'] = cpu_index
        """
        edited from eppy.modeleditor and add the function to allocate cpu.
        """
        #
        # def _makerandomword(length=6):
        #     import uuid
        #
        #     fullword = uuid.uuid4().hex
        #     return fullword[:length]
        #
        # def _maketempname(idfname, randlength=6):
        #     idfname = str(idfname)
        #     t_suffix = _makerandomword(randlength)
        #     randomname = f"{t_suffix}.idf"
        #     if str(idfname[-4:]) == ".idf":
        #         temp_name = f"{idfname[:-4]}_{randomname}"
        #     else:
        #         temp_name = randomname
        #     return temp_name
        #
        # # write the IDF to the current directory
        #
        # idfname = idf.idfname
        # idfabsname = idf.idfabsname
        #
        # temp_name = _maketempname(idfname)
        # idf.saveas(temp_name)
        # print(idfname,temp_name)
        # if `idd` is not passed explicitly, use the IDF.iddname
        idd = kwargs.pop("idd", idf.iddname)
        epw = kwargs.pop("weather", idf.epw)
        try:
            run_with_cpu(idf, weather=epw, idd=idd, **theoptions)
        finally:
            # idf.idfname = idfname
            # idf.idfabsname = idfabsname
            # os.remove(temp_name)
            pass
        # idf.run(**theoptions)
        return f'Case Done:{new_idf_path}'

    kwargs['verbose'] = verbose
    if os.path.isfile(idf_path) and os.path.exists(idf_path):
        if verbose == 's':
            with hiddenPrint() as log:
                new_idf_path = _processing(idf_path, epw, idd, overwrite,long_dir, **kwargs)
                log.dump(new_idf_path[:-4] + '.log')
                msg = ''
        else:
            msg = _processing(idf_path, epw, idd, overwrite,long_dir, **kwargs)
        return msg
    else:
        return f'IDF not found: {idf_path}'


def simulate_sequence(idfs: list, epw: str, idd: str = None, overwrite=False, verbose='q', cpu_index=None,long_dir=False, **kwargs):
    import time
    t1 = time.time()
    for idf_path in idfs:
        if os.path.isfile(idf_path):
            if occupy(idf_path): continue
            simulate_file(idf_path, epw, idd, overwrite, verbose, cpu_index,long_dir, **kwargs)
        elif isinstance(idf_path, IDF):
            simulate_file(idf_path.idfabsname, epw, idd, overwrite, verbose, cpu_index,long_dir, **kwargs)
    print(f'**********Sequence on CPU:{cpu_index} Done**********')
    print("duration:", time.time() - t1)


def simulate_local(idf_path: str, epw: str, idd: str = None, overwrite=False, stdout=sys.stdout, verbose='q',
                   prs_count=7, forceCPU=False, **kwargs):
    sys.stdout = stdout
    if isinstance(idf_path, IDF):
        idf_path = idf_path.idfabsname
    if os.path.isfile(idf_path):
        if isinstance(epw,list):
            for epwi in epw:
                return simulate_file(idf_path, epwi, idd, overwrite, verbose,long_dir=True)
        else:
            return simulate_file(idf_path, epw, idd, overwrite, verbose, long_dir=True)
    elif os.path.isdir(idf_path):
        prs_pool = Pool(prs_count)
        if isinstance(epw,list):
            long_dir = True
        else:
            epw = [epw]
            long_dir = False
        for epwi in epw:
            if prs_count <= os.cpu_count() and forceCPU:
                idfs = [os.path.join(idf_path, file) for file in os.listdir(idf_path)]
                idfs = [idf for idf in idfs if idf.endswith('.idf')]

                for cpu_index in range(1, prs_count + 1):
                    # st = (cpu_index - 1) * np.floor(len(idfs) / prs_count)
                    # ed = cpu_index * np.floor(len(idfs) / prs_count) if cpu_index < prs_count else len(idfs)
                    prs_pool.apply_async(func=simulate_sequence,
                                         args=(idfs[cpu_index - 1:], epwi, idd, overwrite, verbose, cpu_index,long_dir,),
                                         callback=return_callback,
                                         error_callback=error_callback)

            else:
                for file in os.listdir(idf_path):
                    file = os.path.join(idf_path, file)
                    prs_pool.apply_async(func=simulate_file,
                                         args=(file, epwi, idd, overwrite, verbose, None,long_dir,),
                                         callback=return_callback,
                                         error_callback=error_callback)
        prs_pool.close()
        prs_pool.join()
        idfstart = [os.path.join(idf_path, file) for file in os.listdir(idf_path) if file.endswith('.idfstart')]
        for f in idfstart:
            os.remove(f)
        print('**********ALL DONE**********')
        return 1


def simulate_cloud(idfs: list, epw: str, project_name: str = None,overwrite=True, prs_count=8, **kwargs):
    """
    prs_count is invalid currently.
    """
    # test if ssh is valid
    # user_dir = os.path.expanduser('~')
    # if not os.path.exists(user_dir + '/.ssh'):
    #     os.mkdir(user_dir + '/.ssh')
    #     for f in os.listdir(r'\\166.111.40.8\temp\epeditor\.ssh'):
    #         shutil.copy(os.path.join(r'\\166.111.40.8\temp\epeditor\.ssh', f), os.path.join(user_dir + '/.ssh', f))

    # check idf valid
    t1 = time.time()
    if isinstance(idfs, str):
        if os.path.isdir(idfs):
            idfs = [os.path.join(idfs, idf) for idf in os.listdir(idfs)]
    idfs = [idf for idf in idfs if idf.endswith('.idf')]
    if project_name is None:
        project_name = generate_code(4)
    for idf_path in idfs:
        if not os.path.exists(idf_path):
            raise FileNotFoundError(f'EPW not found: {idf_path}')
    if not os.path.exists(epw):
        raise FileNotFoundError(f'EPW not found: {epw}')
    epeditorDir = rf'\\166.111.40.8\temp\epeditor\project\{project_name}'
    if not os.path.exists(epeditorDir):
        os.mkdir(epeditorDir)
    # uploading
    tasks = []
    for idx, idf in enumerate(idfs):
        version = get_version(idf)
        idd = get_idd(idf)
        IDF.setiddname(idd)
        idfObj = IDF(idf, epw=epw)
        if len(idfObj.idfobjects['Output:SQLite']) == 0:
            sql = idfObj.newidfobject('Output:SQLite')
            sql.Option_Type = 'Simple'
            idfObj.save()
            # print(f'add SQL to:{idf}')
        idfDir = os.path.join(epeditorDir, os.path.basename(idf)[:-4])
        if not overwrite:
            if os.path.exists(idfDir):
                tasks.append(idfDir)
                continue
        os.mkdir(idfDir)
        shutil.copy(idf, os.path.join(idfDir, os.path.basename(idf)))
        shutil.copy(epw, os.path.join(idfDir, os.path.basename(epw)))

        with open(os.path.join(idfDir, version + '.vrs'), 'w') as f:
            f.write(version)
        with open(os.path.join(idfDir, 'runit.runit'), 'w') as f:
            f.write("0")
        tasks.append(idfDir)
        bar(idx, len(idfs), 2,"Uploading")

    # pack and upload file
    # task = []
    # epeditorDir = r'\\166.111.40.8\temp\epeditor\project'
    # for cpu_index in range(1, prs_count + 1):
    #     st = int((cpu_index - 1) * np.floor(len(idfs) / prs_count))
    #     ed = int(cpu_index * np.floor(len(idfs) / prs_count)) if cpu_index < prs_count else len(idfs)
    #     prjDir = rf'{epeditorDir}\{project_name}-{cpu_index}'
    #     if os.path.exists(prjDir):
    #         shutil.rmtree(prjDir)
    #     os.mkdir(prjDir)
    #     shutil.copy(epw, rf'{prjDir}\{os.path.basename(epw)}')
    #     version = get_version(idfs[0])
    #     energyplusEXE = f"/usr/local/EnergyPlus-{version}/energyplus-{'.'.join(version.split('-'))}"
    #     with open(rf'{prjDir}\process.run', 'w+', encoding='utf-8', newline='') as f:
    #         args = [energyplusEXE]
    #         args.extend(['-w', f'\"/mnt/remote/project/{project_name}-{cpu_index}/{os.path.basename(epw)}\"'])
    #         f.write('set -x ')
    #         for arg in kwargs:
    #             args.extend([f"--{arg}", kwargs[arg]])
    #         for idf in idfs[st:ed]:
    #             f.write(
    #                 f"{' '.join(args)} -d \"/mnt/remote/project/{project_name}-{cpu_index}/{os.path.basename(idf)[:-4]}\" ")
    #             f.write(
    #                 f"\"/mnt/remote/project/{project_name}-{cpu_index}/{os.path.basename(idf)[:-4]}/{os.path.basename(idf)}\"\n")
    #
    #     for idf in idfs[st:ed]:
    #         task.append([idf, f'{os.path.basename(idf)}', rf'{prjDir}\{os.path.basename(idf)[:-4]}'])

    # uploading
    # for idx, idfInfo in enumerate(task):
    #     os.mkdir(idfInfo[2])
    #     shutil.copy(idfInfo[0], os.path.join(idfInfo[2], idfInfo[1]))
    #     print('\ruploading: [', '*' * int(20 * idx / len(task)),
    #           '-' * int(20 * (1 - idx / len(task))), ']', end='')

    # call
    # prs_pool = Pool(prs_count)
    # address = [
    #     "192.168.1.157",
    #     "192.168.1.246",
    #     "192.168.1.185",
    #     "192.168.1.240",
    #     "192.168.1.115",
    #     "192.168.1.229",
    #     "192.168.1.136",
    #     "192.168.1.149",
    # ]
    # for cpu_index in range(prs_count):
    #     prs_pool.apply_async(sshRunCmd, args=(address[cpu_index], f"{project_name}-{cpu_index + 1}",))

    print(time.time() - t1)

    # check Finished:
    checkTasks = [ts for ts in tasks]
    checkIdfs = [idf for idf in idfs]
    while len(checkTasks)>0:
        finishedNew = []
        remainTask = 0
        for idx, idfDir in enumerate(checkTasks):
            fs = [file for file in os.listdir(idfDir) if file.endswith('.eso')]
            fs += [file for file in os.listdir(idfDir) if file.endswith('.err')]
            if len(fs) == 0:
                remainTask += 1
            else:
                finishedNew.append(idx)
        for idx in finishedNew:
            shutil.copytree(checkTasks[idx], checkIdfs[idx][:-4])
        checkTasks = np.delete(checkTasks, finishedNew)
        checkIdfs = np.delete(checkIdfs, finishedNew)
        bar(len(tasks)-remainTask,len(tasks),2,f'Remain:{remainTask}')
        time.sleep(1)

    print('**********ALL DONE**********')

    return 1


def sshRunCmd(address, simDir):
    for i in range(10):
        if not os.path.exists(rf'\\166.111.40.8\temp\epeditor\project/{simDir}/process.run'):
            time.sleep(1)
    os.system(f'ssh epeditor0@{address} /mnt/remote/project/{simDir}/process.run')
    return


def find_sql(idf_dir: str):
    file_package = os.walk(idf_dir)
    sql = {}
    for dirpath, dirnames, filenames in file_package:
        for file in filenames:
            if re.search('\.sql', file, re.IGNORECASE) != None:
                case = os.path.normpath(dirpath).split(os.sep)[-1]
                sql[case] = os.path.join(dirpath, file)
    return sql


if __name__ == '__main__':
    msg = simulate_file(
        r'test\baseline_0.idf',
        epw=r'C:\EnergyPlusV22-2-0\WeatherData\CHN_Beijing.Beijing.545110_SWERA.epw'
    )
    print(msg)
