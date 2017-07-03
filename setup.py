#!/usr/bin/python

import json
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
f = open('custom_config.yaml', 'w+')
config = yaml.load(f)
if config is None:
	config = {}

# Find controller ip address
controller_response = subprocess.check_output('. ../stackrc && nova list | grep control || true', shell=True, stderr=subprocess.STDOUT)
controller_ip = controller_response.rpartition('=')[-1].replace('|', '').replace(' ', '')

if controller_ip == '':
	print "error: could not find controller ip address"
else:
	print type(config)
	config['controller ip'] = controller_ip

# Find deployment pools' replica sizes
replica_size_command = 'sudo ceph osd pool ls detail -f json'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.24.13', username='heat-admin')
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(replica_size_command)
replica_response = ssh_stdout.read()
ssh_stdout.channel.close()
json_response = json.loads(replica_response)
for pool in json_response:
	print pool['pool_name']
	print pool['size']


# Dump changes to file and close it
yaml.dump(config, f, default_flow_style=False)
f.close()