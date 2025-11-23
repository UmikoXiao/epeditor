cloudServiceAvailable = False

ipAddress = ['']
target_share = ''
username = ''
password = ''

import socket
import subprocess
import os
from .utils import epPath
import json

with open(os.path.join(epPath, 'cloudServices.json'), 'r') as f:
    param = json.load(f)
    cloudServiceAvailable = param['available'] == '1'
    ipAddress = param['ip']
    target_share = str(param['target_share'])
    username = str(param['username'])
    password = str(param['password'])


def host_up(ip: str, timeout=2) -> bool:
    """ping test on the host server"""
    cmd = f'ping -n 1 -w {timeout * 1000} {ip}'
    return subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL).returncode == 0


def smb_port_open(ip: str, port=445, timeout=2) -> bool:
    """test if smb port can be opened"""
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except (socket.timeout, socket.error):
        return False


def share_exists(ip: str) -> bool:
    """
    test connectivity to smb server
    """
    cmd = f'net view \\\\{ip}'

    completed = subprocess.run(cmd, capture_output=True, shell=True)

    return completed.returncode == 0


def test_connect(target_ip: str, timeout=2) -> bool:
    if not host_up(target_ip):
        print('loss connection to', target_ip)
        return False
    elif not smb_port_open(target_ip):
        print('SMB port 445 not open')
        return False
    else:
        if not share_exists(target_ip):
            cmd = rf'net use \\{target_ip}\{target_share} /user:{username} {password}'
            completed = subprocess.run(cmd, capture_output=True, shell=True)
            if completed.returncode != 0:
                print('Do not have access to', target_ip, target_share, 'please check the username and password')

    return True

