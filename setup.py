#!/usr/bin/python

import paramiko
import subprocess
import yaml 

"""
The purpose of this file is to attempt to fill the config file
as thouroughly as possible. Note that some parameters in the config
like "HCI" may not be filled in certain cases, so the config should
be checked before running the main program
"""




# Open config file  
f = open('playbooks/ceph-osd-fault-restore.yml', 'w+')
config = yaml.load(f)

controller_response = subprocess.check_output(['. stackrc && nova list | grep control'], shell=True)

print controller_response 

replica_size_command = 'ceph osd pool ls detail -f json'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.24.13', username='heat-admin')
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(replica_size_command)
replica_response = str(ssh_stdout.readlines())
print replica_response


# Dump changes to file and close it
yaml.dump(config, f, default_flow_style=False)
f.close()