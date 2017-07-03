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

# General deployment fields:

config['deployment'] = {}

# Discover nodes
node_response = subprocess.check_output('. ../stackrc && nova list | grep ctlplane || true', shell=True, stderr=subprocess.STDOUT).split('\n')[:-1]
for line in node_response:
	node_fields = line[1:-1].split('|')
	node_id = node_fields[0].strip()
	print node_id 
	node_type = node_fields[1].partition('-')[-1].rpartition('-')[0]
	print node_type
	node_ip = node_fields[5].partition('=')[-1].strip()
	print node_ip
	#print "\n", line
	#node_ip_addresses = line.rpartition('=')[-1].replace('|', '').replace(' ', '').replace('\n', '') # Isolate the ip in the string 
	#print node_ip_addresses
#if controller_ip == '':
#	print "error: could not find a controller ip address"
#else:
#	config['deployment']['controller ip'] = controller_ip

# Ceph specific fields -----------------------------------------------------

config['ceph'] = {}

# Find deployment pools' replica sizes
replica_size_command = 'sudo ceph osd pool ls detail -f json'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.24.13', username='heat-admin')
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(replica_size_command)
replica_response = ssh_stdout.read()
ssh_stdout.channel.close()
json_response = json.loads(replica_response)
config['ceph']['pools_replication_size'] = {}
pool_sizes = [] # List of sizes used to find the min
for pool in json_response:
	config['ceph']['pools_replication_size'][pool['pool_name']] = pool['size']
	pool_sizes.append(pool['size'])
config['ceph']['min_replication_size'] = min(pool_sizes)

# --------------------------------------------------------------------------

# Dump changes to file and close it
yaml.safe_dump(config, f, default_flow_style=False)
f.close()