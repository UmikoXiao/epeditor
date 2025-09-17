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
    返回 (stdout, stderr, returncode)
    text=True 表示自动解码成 str，不用再 .decode()
    """
    cp = subprocess.run(cmd, shell=True, capture_output=True, text=text)
    return cp.stdout, cp.stderr, cp.returncode


def run_live(cmd):
    """实时打印 stdout/stderr，最后返回 returncode"""
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
