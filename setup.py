import platform
import shutil

import requests
import zipfile
import os
import re

epEditor = os.path.abspath('.')


def download(url, dest, chunk_size=1024):
    with requests.get(url) as response:
        if response.status_code == 200:
            if url.endswith('.zip'):
                save_path = 'temp.zip'
            else:
                save_path = dest
            total = int(response.headers.get('content-length', 0))
            done = 0
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        print(f'\rdownload: {done / 1024 / 1024:.1f} / {total / 1024 / 1024:.1f} MB  '
                              f'({done * 100 // total}%)', end='')
            print('\nFinished →', save_path)

            if url.endswith('.zip'):
                print('Success. unzipped:', os.path.abspath(dest))
                zip_path = save_path
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(os.path.abspath(dest))
                os.remove(zip_path)

                with open(zip_path, 'wb') as file:
                    file.write(response.content)
        else:
            raise ConnectionError(url)


print("check venv...")
if not os.path.exists('venv'):
    url = {'AMD64': r'https://www.python.org/ftp/python/3.7.9/python-3.7.9-embed-amd64.zip',
           'i386': r'https://www.python.org/ftp/python/3.7.9/python-3.7.9-embed-win32.zip',
           'aarch64': r'https://www.python.org/ftp/python/3.7.9/python-3.7.9-embed-arm64.zip'}
    try:
        url = url[platform.machine()]
    except:
        url = url['AMD64']

    print('Get embedded python from:', url)
    try:
        download(url, 'venv')

    except Exception as e:
        print('******embedded python failed, remove the files******')
        if os.path.exists('venv'):
            shutil.rmtree('venv')
        raise ConnectionError(f'failed to get embedded python.\n '
                              f'please download your compatible version from https://www.python.org/ftp/python/3.7.9/ \n'
                              f'then unzip the python to {os.path.abspath("venv")}')

print('Deploy python 3.7.9...')
try:
    download(r'https://bootstrap.pypa.io/pip/3.7/get-pip.py',r'venv\get-pip.py')
except Exception as e:
    print('******get-pip.py failed, remove the files******')
    if os.path.exists('venv\get-pip.py'):
        shutil.rmtree('venv\get-pip.py')
    raise ConnectionError('failed to get get-pip.py.\n '
                          'please download it from https://bootstrap.pypa.io/pip/3.7/get-pip.py \n'
                          f'then put it to {os.path.abspath("venv")}/get-pip.py')
shutil.copy(r'.\setup\python37._pth', r'.\venv\python37._pth')

with open(r'venv\setupEnv.bat', 'w+') as f:
    f.write('.\python37.exe get-pip.py\n')
    # f.write('.\python37.exe -m pip install pydot\n')
    # stable packages
    for pack in os.listdir(r'setup\packages'):
        pack = os.path.abspath(os.path.join(r'setup\packages',pack))
        f.write(f'.\python37.exe -m pip install {pack}\n')
    # pyQt5 could not be installed all in the same time.
    with open(os.path.abspath("requirements.txt"), 'r') as req:
        req = req.readlines()
        for req_s in req:
            f.write(f'.\python37.exe -m pip install --only-binary=all {req_s.strip()}\n')

os.chdir('venv')
if os.path.exists('python.exe'):
    os.rename('python.exe', 'python37.exe')
os.system('setupEnv.bat')

print('check EnergyPlus installation...')
cPathFile = [dir for dir in os.listdir(r'C:\\') if re.search('EnergyPlus', dir) is not None]
# print(os.listdir(r'C:\\'))
_ready = []
for _dir in cPathFile:
    if os.path.exists(os.path.join(r'C:\\', _dir, 'energyplus.exe')):
        _ready.append(os.path.join(r'C:\\', _dir))
        print("found:", os.path.join(r'C:\\', _dir, 'energyplus.exe'))

if len(_ready) == 0:
    print('download and install EnergyPlus...')
    url = {
        'AMD64': r'https://github.com/NREL/EnergyPlus/releases/download/v24.1.0/EnergyPlus-24.1.0-9d7789a3ac-Windows-x86_64.zip',
        'i386': r'https://github.com/NREL/EnergyPlus/releases/download/v24.1.0/EnergyPlus-24.1.0-9d7789a3ac-Windows-i386.zip',
        'aarch64': r'https://github.com/NREL/EnergyPlus/releases/download/v24.1.0/EnergyPlus-24.1.0-9d7789a3ac-Windows-x86_64.zip'}
    try:
        url = url[platform.machine()]
    except:
        url = url['AMD64']
    try:
        download(url, 'C:\\EnergyPlusV24-1-0')
        os.rename(r'C:\EnergyPlus-24.1.0-9d7789a3ac-Windows-x86_64', r'C:\EnergyPlusV24-1-0')
        _ready = ['C:\\EnergyPlusV24-1-0']
    except Exception as e:
        raise ConnectionError(f'failed to get EnergyPlus 24.1.0.\n '
                              f'please download your compatible version from https://energyplus.net/downloads \n'
                              )

# print('prepare idd files...')
# if not os.path.exists(os.path.join(epEditor, f'epeditor\idd')):
#     os.mkdir(os.path.join(epEditor, f'epeditor\idd'))
# for _dir in _ready:
#     iddFolder = os.path.join(_dir, 'PreProcess\IDFVersionUpdater')
#     iddFile = [f for f in os.listdir(iddFolder) if f.endswith('.idd')]
#     for file in iddFile:
#         shutil.copy(os.path.join(iddFolder, file), os.path.join(epEditor, f'epeditor\idd', file))

print('preparing documents...')
if not os.path.exists(f'doc\InputOutputReference.pdf'):
    download('https://energyplus.net/assets/nrel_custom/pdfs/pdfs_v25.1.0/InputOutputReference.pdf',
             os.path.join(epEditor, f'doc\InputOutputReference.pdf'))

print('test EpeditorW...')
os.chdir(epEditor)
for file in os.listdir(r'setup\EpeditorW'):
    shutil.copy(os.path.join(r'setup\EpeditorW', file), os.path.join(epEditor, file))
os.system('run.bat')
