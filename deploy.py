from paramiko import SSHClient
import shutil
import subprocess
import json
import sys
import os, zipfile

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
def init():
    useCurrentSavedSetting = input("Use current saved settings?: ")

    if useCurrentSavedSetting == "y":
        if os.path.isfile('deploy-config.json') == False:
            print('There is no saved configuration')
            return
        else:
            return startDeploy()

    projectDir = input("Enter the path of your project: ")
    projectBuildCommand = input("Enter the project build command: ")
    serverHost = input("Enter the server SSH host: ")
    serverPort = input("Enter the server SSH port: ")
    serverUser = input("Enter the server SSH user: ")
    serverPassword = input("Enter the server SSH password: ")
    serverOptionalParameters = input("Enter optional parameters raw: ")
    serverDeployLocation = input("Enter the deploy location dir: ")
    
    if validateDirectoryDir(projectDir) == False:
        print("Invalid project directory")
        return

    data = {
        'project_local_dir': projectDir,
        'project_build_command': projectBuildCommand,
        'serverHost': serverHost,
        'serverPort': serverPort,
        'serverUser': serverUser,
        'serverPassword': serverPassword,
        'serverOptionalParameters': serverOptionalParameters,
        'serverDeployLocation': serverDeployLocation
    }

    with open('deploy-config.json', 'w') as outfile:
        json.dump(data, outfile)

    startDeploy()

    

def startDeploy():
    with open('deploy-config.json') as json_file:
        data = json.load(json_file)
        proc = subprocess.check_call("cd " + data['project_local_dir'] + " && " + data['project_build_command'], shell=True)
        dir_path = os.path.dirname(os.path.realpath(__file__))

        print(bcolors.OKGREEN +' ------ Build done successfully. Initiating connection to remote server. ---------' +  bcolors.ENDC)

        client = SSHClient()
        client.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        client.connect(data['serverHost'], username=data['serverUser'], password=data['serverPassword'], look_for_keys=False)

        print(bcolors.OKBLUE +' ------ Connection to remote server established. Starting file compression. ---------' +  bcolors.ENDC)

        shutil.make_archive(dir_path+'/deploy', 'zip', data['project_local_dir']+'/dist')

        print(bcolors.OKBLUE +' ------ Transferring deploy.zip to ' + data['serverDeployLocation'] + ' ---------' +  bcolors.ENDC)

        ftp_client = client.open_sftp()

        ftp_client.put(dir_path+'/deploy.zip', data['serverDeployLocation']+'/deploy.zip')

        print(bcolors.OKBLUE +'Decompressing deploy.zip....' +  bcolors.ENDC)
        stdin, stdout, stderr = client.exec_command('cd '+data['serverDeployLocation']+' && unzip deploy.zip')

        print(bcolors.OKBLUE +'Successfully decompressed, removing deploy.zip.....' +  bcolors.ENDC)
        stdin, stdout, stderr = client.exec_command('cd '+data['serverDeployLocation']+' && rm deploy.zip')

        print(bcolors.OKGREEN +'DEPLOY SUCCESSFULLY MADE. CLOSING CONNECTION.' +  bcolors.ENDC)

        ftp_client.close()
        client.close()


def validateDirectoryDir(dir):
    return os.path.isdir(dir)

init()