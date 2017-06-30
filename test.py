#!/usr/bin/python

import argparse
import datetime
import os
import paramiko
import random
import re
import signal
import subprocess
import sys
import threading
import time
import yaml

""" Template class to make your own fault
    add an instance of your fault to the list of plugins in main
"""
class Fault:
    Name = NotImplementedError

    def __init__(self, deployment):
        self.deployment = deployment
        #create a list of fault functions
        self.functions = []

    def stateless(self, deterministic_file, timelimit):
        raise NotImplementedError

    def stateful(self, deterministic_file):
        raise NotImplementedError

    def deterministic(self):
        raise NotImplementedError

class Ceph(Fault):

    def __init__(self, deployment):
        Fault.__init__(self, deployment)
        #create a list of fault functions
        self.functions = [self.fault_type_1]

    def __repr__(self):
        return "Ceph"

    def stateless(self, deterministic_file, timelimit):
        """ func that will be called and run on main thread
            will write a log for deterministic mode
            will take a timelimit or run indefinetly till ctrl-c
            will do things randomly (pick node to fault and timing)
        """

        print "ceph stateless"

        # if fault_domain == "fault_type_1":
        #     result = fault_type_1(target)
        #     deterministic_file.write("Fault Type 1 | " + str(target) + " | " + result[0] + " | Wait Time | " + result[1] + " | " + result[2] + "\n")
        
        if timelimit is None:
            while 1:
                random.choice(self.functions)()
        else: 
            # runtime loop
            timeout = time.time() + 60 * timelimit
            while time.time() < timeout:
                random.choice(self.functions)()
                

    def stateful(self, deterministic_file):
        """ func that will be set up on a thread
            will write to a shared (all stateful threads will share) log for deterministic mode
            will take a timelimit or run indefinetly till ctrl-c
            will do things randomly (pick node to fault and timing)
        """
        print "ceph stateful"

    def deterministic(self):
        """ func that will be set up on a thread
            will take a start time, end time and waiting times (time between fault and restore)
            will take specific node/osd to fault (ip or uuid)
            will run until completion
        """
        print "ceph deterministic"

    def check_health(self):
        """ Looks at a random functioning controller node
            and checks the status of the ceph cluster returning
            True if it's healthy
        """
        controllers = []
        for node in self.deployment.nodes:
            if node.type == "controller":
                controllers.append(node)
        if len(controllers) == 0:
            print "Warning: No controller found in deployment"
            return False

        target_node = random.choice(controllers)
        host = target_node.ip
        response = subprocess.call(['ping', '-c', '5', '-W', '3', host],
                               stdout=open(os.devnull, 'w'),
                               stderr=open(os.devnull, 'w'))
        while response != 0:
            print "Could not connect to node @" + target_node.ip + ". Trying another..."
            target_node = random.choice(controllers)
            host = target_node.ip
            time.sleep(20) # Wait 20 seconds to give nodes time to recover 
            response = subprocess.call(['ping', '-c', '5', '-W', '3', host],
                               stdout=open(os.devnull, 'w'),
                               stderr=open(os.devnull, 'w'))

        command = "sudo ceph -s | grep health"
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username='heat-admin')
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(command)
        response = str(ssh_stdout.readlines())
        return re.search("HEALTH_OK", response, flags=0)

    # Write fault functions below --------------------------------------------- 

    def fault_type_1(self):

        print "sup"

        start_time = datetime.datetime.now() - global_starttime
        # Call to playbook goes here
        # Delay x amount of time
        end_time = datetime.datetime.now() - global_starttime
        # Placeholder fault function
        return [start_time, end_time, "Exit Status"] # Placeholder exit status variable

    def osd_service_fault(downtime):
        """ Kills a random osd service specified on a random ceph node or osd-compute node
            for 'downtime' seconds.
        """
        candidate_nodes = []
        for node in self.deployment.nodes:
            if deployment.hci:
                if node.type == "osd-compute":
                    candidate_nodes.append(node)
            else:
                if node.type == "ceph":
                    candidate_nodes.append(node)

        target_node = random.choice(candidate_nodes)
        host = target_node.ip
        response = subprocess.call(['ping', '-c', '5', '-W', '3', host],
                                   stdout=open(os.devnull, 'w'),
                                   stderr=open(os.devnull, 'w'))
        while response != 0:
            target_node = random.choice(candidate_nodes)
            host = target_node.ip
            time.sleep(20) # Wait 20 seconds to give nodes time to recover 
            response = subprocess.call(['ping', '-c', '5', '-W', '3', host],
                                   stdout=open(os.devnull, 'w'),
                                   stderr=open(os.devnull, 'w'))

        with open('playbooks/ceph-osd-fault-crash.yml') as f:
            config = yaml.load(f)
            config[0]['hosts'] = host
        with open('ceph-osd-fault-crash.yml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        with open('ceph-osd-fault-restore.yml') as f:
            config = yaml.load(f)
            config[0]['hosts'] = host
        with open('ceph-osd-fault-restore.yml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        if check_health():    
            print "Cluster is healthy, executing fault."
            start_time = datetime.datetime.now() - global_start
            subprocess.call('ansible-playbook ceph-osd-fault-crash.yml', shell=True)
            time.sleep(downtime)
            subprocess.call('ansible-playbook ceph-osd-fault-restore.yml', shell=True)
            end_time = datetime.datetime.now() - global_start
            return [start_time, end_time, "Exit Status"] # Placeholder exit status variable

        else:
            print "Cluster is not healthy, waiting 30 seconds before trying another node."
            time.sleep(30)

class Node:
    def __init__(self, node_type, node_ip, node_id):
        self.type = node_type
        self.ip = node_ip
        self.id = node_id 
        self.faulted = False

class Deployment:
    def __init__(self, filename):
        """ Takes in a deployment config file 
        """
        self.nodes = []
        with open(filename, 'r') as f:
            config = yaml.load(f)
        for node_index in range(config['numnodes']):
            current_node = config['node' + str(node_index)]
            self.nodes.append(Node(current_node['type'], current_node['ip'], current_node['id']))

# global var for start time of program
global_starttime = datetime.datetime.now()

# global var for log file
log = open('FaultInjector.log', 'a')

#global list of all plugins
plugins = []

def main():
    deployment = Deployment("config.yaml")

    #create list of all plugins
    plugins.append(Ceph(deployment))

    # signal handler to restore everything to normal
    signal.signal(signal.SIGINT, signal_handler)

    # start injector
    log.write('{:%Y-%m-%d %H:%M:%S} Fault Injector Started\n'.format(datetime.datetime.now()))

    # create argument parser
    parser = argparse.ArgumentParser(description='Fault Injector')
    parser.add_argument('-d','--deterministic', help='injector will follow the list of tasks in the file specified', action='store', nargs=1, dest='filepath')
    parser.add_argument('-sf','--stateful', help='injector will run in stateful random mode', required=False, action='store_true')
    parser.add_argument('-sl','--stateless', help='injector will run in stateless random mode', required=False, action='store_true')
    parser.add_argument('-t','--timelimit', help='timelimit for injector to run (mins)', required=False, type=int, metavar='\b')
    args = parser.parse_args()

    # check mode
    if args.filepath:
        if args.timelimit:
            print "Timelimit not applicable in deterministic mode"
        deterministic_start()
    elif args.stateful:
        stateful_start(args.timelimit)
    elif args.stateless:
        stateless_start(args.timelimit)
    else:
        print "No Mode Chosen"

    # end injector
    log.write('{:%Y-%m-%d %H:%M:%S} Fault Injector Stopped\n'.format(datetime.datetime.now()))
    log.close()


def deterministic_start():
    """ func that will read deterministic log
        will create all threads (one per entry in log) and spawn them
        will wait for all threads to complete
    """
    log.write('{:%Y-%m-%d %H:%M:%S} Deterministic Mode Started\n'.format(datetime.datetime.now()))
    print "deterministic"

def stateful_start(timelimit):
    """ func that will create a thread for every plugin
        will create a deterministci file that will be passed to every thread
        will pass all threads the timelimit (could be infiniety)
        will spawn all threads
        will wait for all threads to compplete or for ctrl-c
    """

    if timelimit is None:
        log.write('{:%Y-%m-%d %H:%M:%S} Indefinite Timelimit\n'.format(datetime.datetime.now()))
        print "indefinite timelimit"
    else:
        log.write('{:%Y-%m-%d %H:%M:%S} {} Minute Timelimit\n'.format(datetime.datetime.now(), timelimit))
        print "{} Minute Timelimit".format(timelimit)



    log.write('{:%Y-%m-%d %H:%M:%S} Stateful Mode Started\n'.format(datetime.datetime.now()))
    print "stateful"

def stateless_start(timelimit):
    """ func that will read from stateless config
        will run one plugin's statless mode on main thread
        ill pass the timelimit (could be infiniety)
    """
    log.write('{:%Y-%m-%d %H:%M:%S} Stateless Mode Started\n'.format(datetime.datetime.now()))

    if timelimit is None:
        log.write('{:%Y-%m-%d %H:%M:%S} Indefinite Timelimit Enabled\n'.format(datetime.datetime.now()))
        print "indefinite timelimit"
    else:
        log.write('{:%Y-%m-%d %H:%M:%S} {} Minute Timelimit\n'.format(datetime.datetime.now(), timelimit))
        print "{} Minute Timelimit".format(timelimit)

    #pick plugin to use
    plugin = random.choice(plugins)

    log.write('{:%Y-%m-%d %H:%M:%S} {} Plugin Chosen\n'.format(datetime.datetime.now(), plugin.__repr__()))

    # writes a file that can feed into a deterministic run
    dir_path = os.path.join(os.path.dirname(__file__), "deterministic-runs/")
    # create directory if it doesn't exist
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    deterministic_filename = dir_path + str(global_starttime) + '-run.txt'
    deterministic_file = open(deterministic_filename, 'w')

    #start plugins stateless mode
    plugin.stateless(deterministic_file, timelimit)


def signal_handler(signal, frame):
        print('\nYou exited! Your environment will be restored to its original state.')

        log.write('{:%Y-%m-%d %H:%M:%S} Signal handler\n'.format(datetime.datetime.now()))

        subprocess.call('ansible-playbook restart-nodes.yml', shell=True)

        log.write('{:%Y-%m-%d %H:%M:%S} Fault Injector Stopped\n'.format(datetime.datetime.now()))
        log.close()

        sys.exit(0)

if __name__ == "__main__":
    main()

#   print "main"
#   t1 = threading.Thread(target=thread1)
#   t2 = threading.Thread(target=thread2)
#   t3 = threading.Thread(target=thread3)
#   t1.start()
#   t2.start()
#   t3.start()

#   t1.join()
#   t2.join()
#   t3.join()

#   print "done"

# def thread1():
#   time.sleep(5)
#   print "im the thread1"
#   time.sleep(5)
#   print "thread1 again"

# def thread2():
#   time.sleep(5)
#   print "im the thread2"
#   time.sleep(5)
#   print "thread2 again"

# def thread3():
#   time.sleep(5)
#   print "im the thread3"
#   time.sleep(5)
#   print "thread3 again"