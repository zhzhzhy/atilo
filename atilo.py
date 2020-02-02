#! /usr/bin/env python3

import os
import tarfile
import requests
import json
from tqdm import tqdm
import hashlib
import io
import sys


home = os.getenv('HOME')
atilo_home = home + '/.atilo/'
atilo_tmp  = atilo_home + 'tmp/'
atilo_config = atilo_home + 'local.json'
atilo_version = "2.0-Alpha"

def check_dir():
    if not os.path.isdir(atilo_home):
        os.mkdir(atilo_home)
    if not os.path.isdir(atilo_tmp):
        os.mkdir(atilo_tmp)

def check_arch():
    arch = os.uname().machine
    if arch == 'aarch64':
        pass
    elif arch == 'x86_64':
        arch = 'amd64'
    elif arch.__contains__('86'):
        arch = 'i386'
    elif arch.__contains__('arm'):
        arch = 'armhf'
    else:
        print('Your device''s arch are not in supoport')
        exit(1)
    return arch

def load_local():
    if not os.path.isfile(atilo_config):
        with open(atilo_config,'w') as f:
            arch = check_arch()
            data = {
                'config': {
                    'arch': arch,
                    'version': atilo_version
                }
            }
            json.dump(data,f)
    with open(atilo_config,'r') as f:
        config = json.load(f)
    return config

def get_list():
    r = requests.get('https://github.com/YadominJinta/atilo/raw/dev/src/list.json')
    if not r.status_code == 200:
        print('Can''t get images lists.')
        exit(1)
    return r.json()

def pull_image(distro):
    arch = check_arch
    lists = get_list()
    config = load_local()
    if distro in config.keys():
        print('You have installed ' + distro)
        exit(1)
    if not distro in lists.keys():
        print(distro + ' not found')
        exit(1)
    infos = lists.get(distro)
    url = infos.get(arch)
    print('Pulling image')
    r = requests.get(url,stream=True)
    if not r.status_code == 200:
        print('Can''t pull the image')
        print('Network Error')
        exit(1)
    total_size = r.headers.get('Content-Length')
    block_size = io.DEFAULT_BUFFER_SIZE
    t = tqdm(total=total_size,unit='iB',unit_scale=True)
    with open(atilo_tmp.join(distro),'wb') as f:
        for chunk in r.iter_content(block_size):
            t.update(len(chunk))
            f.write(chunk)
    r.close()
    t.close()
    if infos.get('check') == 'ubuntu':
        check_url = 'https://partner-images.canonical.com/core/' + infos.get('version') + '/current/MD5SUMS'
        check_sum_ubuntu(url,distro)
    elif infos.get('check') == 'no':
        print(distro + ' has no check method')
        print('skiping')
    else:
        check_url = url + '.' + infos.get('check')
        check_sum(distro=distro,url=check_url,check=infos.get('check'))
    
    if not infos.get('zip') == 'fedora':
        extract_file(distro,infos.get('zip'))
    else:
        extract_fedora()

def config_image(distro,infos):
    distro_path = atilo_home + distro
    resolv_conf = distro_path + '/etc/resolv.conf'
    with open(resolv_conf,'w') as f:
        f.write('nameserver 1.1.1.1\n')
        f.write('nameserver 8.8.8.8\n')
    with open(atilo_config,'r') as f:
        config_list = json.load(f)
    config_list
    
def extract_file(distro,zip_m):
    distro_path = atilo_home + distro
    file_path = atilo_tmp + distro
    zip_f = tarfile.open(file_path,'r:'+zip_m)
    if not os.path.isdir(distro_path):
        os.mkdir(distro_path)
    print('Extracting image')
    zip_f.extractall(distro_path,numeric_owner=True)

def extract_fedora():
    file_path = atilo_tmp+ 'fedora'
    distro_path = atilo_home + 'fedora'
    print('Extracting image')
    zip_f = tarfile.open(file_path)
    for i in zip_f.list():
        if i.__contains__('layer.tar'):
            zip_name = i
    zip_f.close()
    zip_f = tarfile.open(atilo_tmp + zip_name,'r')
    if not os.path.isdir(distro_path):
        os.mkdir(distro_path)
    zip_f.extractall(distro_path,numeric_owner=True)
    

def check_sum(distro,url,check):
    r = requests.get('url')
    file_path = atilo_tmp + distro
    if not r.status_code == 200:
        print('Can''t get checksum file,are you sure to continue? [y/N]',end=' ')
        a = ''
        input(a)
        if not a == 'y':
            print('Exiting')
            os.remove(file_path)
            exit(1)

    sum_calc = hashlib.md5() if check == 'md5' else  hashlib.sha256()
    total_size = os.path.getsize(file_path)
    block_size = io.DEFAULT_BUFFER_SIZE
    t = tqdm(total=total_size,unit='iB',unit_scale=True)
    with open(file_path,'rb') as f:
        for chunk in iter(lambda: f.read(block_size ), b''):
            t.update(len(chunk))
            sum_calc.update(chunk)
    t.close()
    f.close()

    if r.text.__contains__(sum_calc.hexdigest()):
        return 0
    else:
        print('Checksum error')
        print('Exiting')
        os.remove(file_path)
        exit(1)

def check_sum_ubuntu(distro,url):
    r = requests(url)
    file_path = atilo_tmp + distro
    if not r.status_code == 200:
        print('Can''t get checksum file,are you sure to continue? [y/n]',end=' ')
        a = ''
        input(a)
        if not a == 'y':
            print('Exiting')
            os.remove(file_path)
            exit(1)
    sum_calc = hashlib.md5()
    total_size = os.path.getsize(file_path)
    block_size = io.DEFAULT_BUFFER_SIZE
    t = tqdm(total=total_size,unit='iB',unit_scale=True)
    with open(file_path,'rb') as f:
        for chunk in iter(lambda: f.read(block_size),b''):
            t.update(len(chunk))
            sum_calc.update(chunk)
    t.close()
    f.close()

    if r.text.__contains__(sum_calc.hexdigest()):
        return 0
    else:
        print('Checksum error')
        print('Exiting')
        os.remove(file_path)
        exit(1)

    

def show_help():
    print('Atilo\t\t' + atilo_version )
    print('Usage: atilo [Command] [Argument]\n')
    print('Atilo is a bash script to help you install some GNU/Linux distributions on Termux.\n')
    print('Commands:')
    print('images\t\t list available images')
    print('rm\t\t remove installed images')
    print('pull\t\t pulling an image')
    print('run\t\t running a command in a new container.')
    print('help\t\t show this help.\n')
    

if __name__ == "__main__":
    if len(sys.argv) == 1:
        show_help()
        print('A command is needed.')
        exit(1)
    if sys.argv[1] == 'help':
        show_help()
    elif sys.argv[1] == 'pull':
        if len(sys.argv) < 3:
            print('You need to specific a image from list.')
            exit(1)
        elif len(sys.argv) >3:
            print('Too many arguments.')
            exit(1)
        else:
            pull_image(sys.argv[2])
    elif sys.argv[1] == 'list'


    