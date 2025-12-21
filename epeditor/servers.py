"""This is a very simple and crude way to scan and run idf files in a folder,
avoiding duplicated run a file."""
import time

import os
import random
import shutil
import subprocess
import traceback

NASFolder = os.getenv('REMOTE_PROJECT_FOLDER',r'/mnt/remote/project/')
epWorkingFolder = os.getenv('EP_WORK_DIR',r'/epTemp')
mode = os.getenv('WALK_MODE','random')

if not os.path.exists(epWorkingFolder):
    os.mkdir(epWorkingFolder)


def scan(walkMethod):
    time.sleep(random.randint(0, 10) / 10)
    print('Scanning folder...')
    for dirpath, dirnames, filenames in walkMethod(NASFolder):
        for fname in filenames:
            if fname.endswith('.runit'):
                runFile(dirpath)
                break


def randomWalk(root: str):
    """
    same function as os.walk(), but for random walking.
    :param root:   wolk folder
    """
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        random.shuffle(dirnames)
        yield dirpath, dirnames, filenames


def timeWalk(root: str, *, reverse: bool = False):
    """
    same function as os.walk(), but walk by edit time of the folder
    :param root:   wolk folder
    :param reverse: False old->new, True new->old
    """
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # 1. 拿到 (dirname, mtime) 列表
        dirs_with_time = []
        for d in dirnames:
            try:
                mtime = os.path.getmtime(os.path.join(dirpath, d))
            except (FileNotFoundError, PermissionError):
                mtime = 0  # 拿不到时间放最后
            dirs_with_time.append((d, mtime))

        # 2. 按时间排序
        dirs_with_time.sort(key=lambda t: t[1], reverse=reverse)

        # 3. 替换原 dirnames 顺序（原地修改，os.walk 会按新顺序递归）
        dirnames[:] = [t[0] for t in dirs_with_time]

        yield dirpath, dirnames, filenames


def runFile(folder):
    "run a idf folder and create runit tag to avoid duplicated run a file."
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
            folder_local = epWorkingFolder + '/' + os.path.basename(folder.rstrip('/'))
            if os.path.exists(folder_local):
                shutil.rmtree(folder_local)
            shutil.copytree(folder, folder_local)
            cwd = f"set -x; /usr/local/EnergyPlus-" + version + "/energyplus-" + '.'.join(version.split('-'))
            cwd += " -w " + "\"" + os.path.join(folder_local, epw) + "\""
            cwd += " -d " + "\"" + folder_local + "\""
            cwd += " " + "\"" + os.path.join(folder_local, idf) + "\""
            print(cwd)
            # out, err, code = run_capture(cwd)
            # print("STDOUT:", out)
            # print("STDERR:", err)
            # print("CODE:", code)
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
    return (stdout, stderr, returncode) but not print anything
    """
    cp = subprocess.run(cmd, shell=True, capture_output=True, text=text)
    return cp.stdout, cp.stderr, cp.returncode


def run_live(cmd):
    """print stdout/stderr live and return a code"""
    return subprocess.run(cmd, shell=True, executable="/bin/bash").returncode


def listing():
    if mode == 'random':
        walkMethod = randomWalk
    elif mode == 'time':
        walkMethod = timeWalk
    else:
        walkMethod = os.walk
    while True:
        try:
            scan(walkMethod)
        except Exception as e:
            traceback.print_exc()
        finally:
            time.sleep(random.randint(0, 10) / 10)


if __name__ == '__main__':
    listing()
