"""This is a very simple and crude way to scan and run idf files in a folder,
avoiding duplicated run a file."""
import os
import time
import random
import shutil
import subprocess


NASFolder = r'/mnt/remote/project/'
epWorkingFolder = r'/epTemp'
mode = 'random'

if not os.path.exists(epWorkingFolder):
    os.mkdir(epWorkingFolder)


def scan(walkMethod):
    """
    Scan.
    
    Parameters
    ----------
    walkMethod : Any
        Input parameter `walkMethod`.
    
    Returns
    -------
    Any
        Return value from `scan`.
    """
    time.sleep(random.randint(0, 10) / 10)
    print('Scanning folder...')
    for dirpath, dirnames, filenames in walkMethod(NASFolder):
        for fname in filenames:
            if fname.endswith('.runit'):
                runFile(dirpath)
                break

def randomWalk(root: str):
    """
    Randomwalk.
    
    Parameters
    ----------
    root : str
        Input parameter `root`.
    
    Returns
    -------
    Any
        Return value from `randomWalk`.
    """
    """
    same function as os.walk(), but for random walking.
    :param root:   wolk folder
    """
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        random.shuffle(dirnames)
        yield dirpath, dirnames, filenames

def timeWalk(root: str, *, reverse: bool = False):
    """
    Timewalk.
    
    Parameters
    ----------
    root : str
        Input parameter `root`.
    
    reverse : bool
        Input parameter `reverse`.
    
    Returns
    -------
    Any
        Return value from `timeWalk`.
    """
    """
    same function as os.walk(), but walk by edit time of the folder
    :param root:   wolk folder
    :param reverse: False old->new, True new->old
    """
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirs_with_time = []
        for d in dirnames:
            try:
                mtime = os.path.getmtime(os.path.join(dirpath, d))
            except (FileNotFoundError, PermissionError):
                mtime = 0
            dirs_with_time.append((d, mtime))

        dirs_with_time.sort(key=lambda t: t[1], reverse=reverse)

        dirnames[:] = [t[0] for t in dirs_with_time]

        yield dirpath, dirnames, filenames

def runFile(folder):
    """
    Runfile.
    
    Parameters
    ----------
    folder : Any
        Input parameter `folder`.
    
    Returns
    -------
    Any
        Return value from `runFile`.
    """
    try:
        if not os.path.exists(os.path.join(folder, 'runit.runit')):
            return -2
        os.remove(os.path.join(folder, 'runit.runit'))
        files = os.listdir(folder)
        epw, idf, version = None, None, None
        for file in files:
            if file.endswith('.epw'):
                epw = file
            if file.endswith('.idf'):
                idf = file
            if file.endswith('.vrs'):
                version = file[:-4]
        print(idf, epw, version)
        if epw and idf and version:
            folder_local = epWorkingFolder+'/' + os.path.basename(folder.rstrip('/'))
            if os.path.exists(folder_local):
                shutil.rmtree(folder_local)
            shutil.copytree(folder, folder_local)
            cwd = f"set -x; /usr/local/EnergyPlus-" + version + "/energyplus-" + '.'.join(version.split('-'))
            cwd += " -w " + "\"" + os.path.join(folder_local, epw) + "\""
            cwd += " -d " + "\"" + folder_local + "\""
            cwd += " " + "\"" + os.path.join(folder_local, idf) + "\""
            print(cwd)
            run_live(cwd)
            for file in os.listdir(folder_local):
                if not os.path.exists(os.path.join(folder, file)):
                    shutil.copy(os.path.join(folder_local, file), os.path.join(folder, file))
            shutil.rmtree(folder_local)
            return 0
        return -1
    except Exception as e:
        return 1


def run_capture(cmd, text=True):
    """
    Run capture.
    
    Parameters
    ----------
    cmd : Any
        Input parameter `cmd`.
    
    text : Any
        Input parameter `text`.
    
    Returns
    -------
    Any
        Return value from `run_capture`.
    """
    cp = subprocess.run(cmd, shell=True, capture_output=True, text=text)
    return cp.stdout, cp.stderr, cp.returncode


def run_live(cmd):
    """
    Run live.
    
    Parameters
    ----------
    cmd : Any
        Input parameter `cmd`.
    
    Returns
    -------
    Any
        Return value from `run_live`.
    """
    return subprocess.run(cmd, shell=True, executable="/bin/bash").returncode


if __name__ == '__main__':
    if mode == 'random':
        walkMethod = randomWalk
    elif mode == 'time':
        walkMethod = timeWalk
    else:
        walkMethod = os.walk
    while True:
        scan(walkMethod)
        time.sleep(random.randint(0, 10) / 10)
