#!/usr/bin/python

import argparse
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

# Manage arguments passed with the script

parser = argparse.ArgumentParser(description='Fault Injector Setup')
parser.add_argument('-c','--ceph', help='setup will look for ceph fields in the deployment', required=False, dest='activate_ceph', action='store_true')
parser.set_defaults(activate_ceph=False)
args = parser.parse_args()

# Open config file  
f = open('config.yaml', 'w+')
config = yaml.load(f)
if config is None:
	config = {}

# General deployment fields:

print "Discovering general deployment information..."

config['deployment'] = {'nodes': {}, 'containerized': False, 'hci': False, 'num_nodes': 0}

# Discover node properties
node_response = subprocess.check_output('. ../stackrc && nova list | grep ctlplane || true', shell=True, stderr=subprocess.STDOUT).split('\n')[:-1]
for line in node_response:
	node_fields = line[1:-1].split('|')
	node_id = node_fields[0].strip()
	node_type = node_fields[1].partition('-')[-1].rpartition('-')[0]
	node_ip = node_fields[5].partition('=')[-1].strip()
	config['deployment']['nodes'][node_id] = {'node_type': node_type, 'node_ip': node_ip}

config['deployment']['num_nodes'] = len(config['deployment']['nodes'])


# Ceph specific fields -----------------------------------------------------

if args.activate_ceph:

	print "Discovering Ceph-specific information..."

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
	config['ceph']['pools_and_replication_size'] = {}
	pool_sizes = [] # List of sizes used to find the min
	for pool in json_response:
		config['ceph']['pools_and_replication_size'][pool['pool_name']] = pool['size']
		pool_sizes.append(pool['size'])
	config['ceph']['minimum_replication_size'] = min(pool_sizes)

# --------------------------------------------------------------------------

# Dump changes to file and close it
yaml.safe_dump(config, f, default_flow_style=False)
f.close()
print "Completed!"
