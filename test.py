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

    def stateful(self, deterministic_file, timelimit):
        raise NotImplementedError

    def deterministic(self, args):
        raise NotImplementedError

    def check_exit_signal(self):
        if stopper.is_set():
                sys.exit(0)

class Node_fault(Fault):
    def __init__(self, deployment):
        Fault.__init__(self, deployment)
        #create a list of fault functions
        self.functions = [self.node_kill_fault]

    def __repr__(self):
        return "Node_fault"

    def stateless(self, deterministic_file, timelimit):
        raise NotImplementedError

    def stateful(self, deterministic_file, timelimit):
        raise NotImplementedError

    def deterministic(self, args):
        raise NotImplementedError

    # Write fault functions below --------------------------------------------- 

    def node_kill_fault(self):
        pass

    def det_node_kill_fault(self, target_node, downtime):
        pass

class Ceph(Fault):

    def __init__(self, deployment):
        Fault.__init__(self, deployment)
        #create a list of fault functions
        self.functions = [self.osd_service_fault]

    def __repr__(self):
        return "Ceph"

    def stateless(self, deterministic_file, timelimit):
        """ func that will be called and run on main thread
            will write a log for deterministic mode
            will take a timelimit or run indefinetly till ctrl-c
            will do things randomly (pick node to fault and timing)
        """
        # eterministic_file = open(deterministic_file, 'w')

        print "Beginning Ceph stateless mode"

        if timelimit is None:
            while 1:
                random.choice(self.functions)()
        else: 
            # runtime loop
            timeout = time.time() + 60 * timelimit
            while time.time() < timeout:
                # Calls a fault function and stores the results
                result = random.choice(self.functions)() 
                if result is None:
                    continue
                deterministic_file.write(self.__repr__() + " | " + str(result[0]) + 
                                        " | " + str(result[1]) + " | " + str(result[2]) + 
                                         " | " + str(result[3]) + " | " + str(result[4]) + 
                                         " | " + str(result[5]) + '\n')
            deterministic_file.close()

    def stateful(self, deterministic_file, timelimit):
        """ func that will be set up on a thread
            will write to a shared (all stateful threads will share) log for deterministic mode
            will take a timelimit or run indefinetly till ctrl-c
            will do things randomly (pick node to fault and timing)
        """
        print "ceph stateful"
        self.check_exit_signal()

    def deterministic(self, args):
        """ func that will be set up on a thread
            will take a start time, end time and waiting times (time between fault and restore)
            will take specific node/osd to fault (ip or uuid)
            will run until completion
        """

        #convert endtime to seconds
        l = args[3].split(':')
        secs = int(l[0]) * 3600 + int(l[1]) * 60 + int(float(l[2]))

        #find target node
        for node in self.deployment.nodes:
            if node.ip == args[2]:
                target = node

        #wait until starttime
        while time.time() < int(global_starttime.strftime('%s')) + secs:
            self.check_exit_signal()
            time.sleep(1)

        #call fault
        if args[1] == 'ceph-osd-fault':
            self.det_osd_service_fault(target, int(args[5]))
        else:
            print "no matching function found"

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
            print "[check_health] warning: no controller found in deployment"
            return False

        target_node = random.choice(controllers)
        host = target_node.ip
        response = subprocess.call(['ping', '-c', '5', '-W', '3', host],
                               stdout=open(os.devnull, 'w'),
                               stderr=open(os.devnull, 'w'))
        while response != 0:
            print "[check_health] could not connect to node @" +  \
                    target_node.ip + ", trying another after 20 seconds..."
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
        return False if re.search("HEALTH_OK", response, flags=0) == None else True

    # Write fault functions below --------------------------------------------- 

    def template_fault(self):

        print "template_fault was called"

        start_time = datetime.datetime.now() - global_starttime
        # Call to playbook goes here
        # Delay x amount of time
        end_time = datetime.datetime.now() - global_starttime
        # Placeholder fault function
        return [start_time, end_time, "Exit Status"] # Placeholder exit status variable

    def osd_service_fault(self):
        """ Kills a random osd service specified on a random ceph node
            or osd-compute node
        """
        candidate_nodes = []
        for node in self.deployment.nodes:
            if self.deployment.hci:
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
        while response != 0 or target_node.occupied:
            target_node = random.choice(candidate_nodes)
            host = target_node.ip
            time.sleep(20) # Wait 20 seconds to give nodes time to recover
            log.write('{:%Y-%m-%d %H:%M:%S} [ceph-osd-fault] Failed to find \
                        acceptable node. Waiting 20 seconds before searching \
                        for a different node to fault.\n'.format(datetime.datetime.now())) 
            response = subprocess.call(['ping', '-c', '5', '-W', '3', host],
                                   stdout=open(os.devnull, 'w'),
                                   stderr=open(os.devnull, 'w'))

            target_node.occupied = True # Mark node as being used 

        with open('playbooks/ceph-osd-fault-crash.yml') as f:
            config = yaml.load(f)
            config[0]['hosts'] = host
        with open('playbooks/ceph-osd-fault-crash.yml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        with open('playbooks/ceph-osd-fault-restore.yml') as f:
            config = yaml.load(f)
            config[0]['hosts'] = host
        with open('playbooks/ceph-osd-fault-restore.yml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        if self.check_health():    
            print "[ceph-osd-fault] cluster is healthy, executing fault."
            start_time = datetime.datetime.now() - global_starttime
            subprocess.call('ansible-playbook playbooks/ceph-osd-fault-crash.yml', shell=True)
            downtime = random.randint(15, 45) # Picks a random integer such that: 15 <= downtime <= 45
            log.write('{:%Y-%m-%d %H:%M:%S} [ceph-osd-fault] waiting ' + 
                      str(downtime) + ' minutes before introducing OSD again \
                      \n'.format(datetime.datetime.now()))
            time.sleep(30) #(downtime * 60)
            subprocess.call('ansible-playbook playbooks/ceph-osd-fault-restore.yml', shell=True)
            end_time = datetime.datetime.now() - global_starttime
            exit_status = self.check_health()
            target_node.occupied = False # Free up the node
            return ['ceph-osd-fault', target_node.ip, start_time, end_time, downtime, exit_status] 

        else:
            print "[ceph-osd-fault] cluster is not healthy, returning to \
                    stateless function to pick another fault type"
            log.write('{:%Y-%m-%d %H:%M:%S} [ceph-osd-fault] cluster is not \
                       healthy, returning to stateless function to pick another \
                       fault type\n'.format(datetime.datetime.now()))
            time.sleep(10)

        # Deterministic fault functions below ---------------------------------------------
        
    def det_osd_service_fault(self, target_node, downtime):
        """ Kills a random osd service specified on a random ceph node or osd-compute node
        """

        #check for exit signal
        self.check_exit_signal()

        host = target_node.ip
        response = subprocess.call(['ping', '-c', '5', '-W', '3', host],
                                   stdout=open(os.devnull, 'w'),
                                   stderr=open(os.devnull, 'w'))

        #check for exit signal
        self.check_exit_signal()

        # Make sure target node is reachable 
        if response != 0:
            print "[det_osd_service_fault] error: target node unreachable, \
                    exiting fault function"
            return None

        target_node.occupied = True # Mark node as being used 

        with open('playbooks/ceph-osd-fault-crash.yml') as f:
            config = yaml.load(f)
            config[0]['hosts'] = host
        with open('playbooks/ceph-osd-fault-crash.yml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        #check for exit signal
        self.check_exit_signal()

        with open('playbooks/ceph-osd-fault-restore.yml') as f:
            config = yaml.load(f)
            config[0]['hosts'] = host
        with open('playbooks/ceph-osd-fault-restore.yml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        #check for exit signal
        self.check_exit_signal()

        if self.check_health():    
            print "[det_ceph-osd-fault] cluster is healthy, executing fault."
            subprocess.call('ansible-playbook playbooks/ceph-osd-fault-crash.yml', shell=True)
            log.write('{:%Y-%m-%d %H:%M:%S} [det_ceph-osd-fault] waiting ' + 
                        str(downtime) + ' minutes before introducing OSD \
                        again\n'.format(datetime.datetime.now()))
            
            while downtime > 0:
                #check for exit signal
                self.check_exit_signal()
                time.sleep(60)
                downtime -= 1

            subprocess.call('ansible-playbook playbooks/ceph-osd-fault-restore.yml', shell=True)
            target_node.occupied = False # Free up the node
            print "[det_osd_service_fault] deterministic step completed"
            return True 

        else:
            print "[ceph-osd-fault] cluster is not healthy, moving onto \
                    next step without faulting"
            log.write('{:%Y-%m-%d %H:%M:%S} [ceph-osd-fault] cluster is not \
                        healthy, moving onto next step without faulting \
                        \n'.format(datetime.datetime.now()))
            time.sleep(10)

class Node:
    def __init__(self, node_type, node_ip, node_id):
        self.type = node_type
        self.ip = node_ip
        self.id = node_id 
        self.occupied = False

class Deployment:
    def __init__(self, filename):
        """ Takes in a deployment config file and parses it for the
            deployment configuration 
        """
        self.nodes = []

        hosts = open('hosts', 'w')

        with open(filename, 'r') as f:
            config = yaml.load(f)

            # Check for a Ceph deployment
            if 'ceph' in config:
                ceph_deployment = True

            for node_id in config['deployment']['nodes']:
                self.nodes.append(Node(config['deployment']['nodes'][node_id]['node_type'], \
                     config['deployment']['nodes'][node_id]['node_ip'], node_id))
                self.hci = config['deployment']['hci']
                self.containerized = config['deployment']['containerized']
                self.num_nodes = config['deployment']['num_nodes']
                # Fill hosts file with IPs
                hosts.write((config['deployment']['nodes'][node_id]['node_ip']) + '\n')
                if ceph_deployment:
                    self.num_osds = config['deployment']['nodes'][node_id]['num_osds']

# global var for start time of program
global_starttime = datetime.datetime.now()

# global var for log file
log = open('FaultInjector.log', 'a')

#global list of all plugins
plugins = []

#global list of threads
threads = []

#global exit signal for threads
stopper = threading.Event()

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
    parser.add_argument('-d','--deterministic', help='injector will follow the \
                         list of tasks in the file specified', action='store', 
                        nargs=1, dest='filepath')
    parser.add_argument('-sf','--stateful', help='injector will run in stateful \
                        random mode', required=False, action='store_true')
    parser.add_argument('-sl','--stateless', help='injector will run in stateless \
                        random mode', required=False, action='store_true')
    parser.add_argument('-t','--timelimit', help='timelimit for injector to run \
                         (mins)', required=False, type=int, metavar='\b')
    args = parser.parse_args()

    # check mode
    if args.filepath:
        if args.timelimit:
            print "Time Limit not applicable in deterministic mode"
        deterministic_start(args.filepath)
    elif args.stateful:
        stateful_start(args.timelimit)
    elif args.stateless:
        stateless_start(args.timelimit)
    else:
        print "No Mode Chosen"

    # end injector
    log.write('{:%Y-%m-%d %H:%M:%S} Fault Injector Stopped\n'.format(datetime.datetime.now()))
    log.close()
    print "fin"

def deterministic_start(filepath):
    """ func that will read deterministic log
        will create all threads (one per entry in log) and spawn them
        will wait for all threads to complete
    """
    log.write('{:%Y-%m-%d %H:%M:%S} Deterministic Mode Started\n'.format(datetime.datetime.now()))

    # open file
    with open(filepath[0]) as f:
        # read line by line
        for line in f:
            #break into list
            words = line.strip("| ").split(" | ")

            #find matching plugin
            for plugin in plugins:
                if plugin.__repr__() == words[0].strip(" "):
                    #create thread
                    threads.append(threading.Thread(target=plugin.deterministic, args=(words,)))

    #start all threads
    for thread in threads:
        thread.start()
      
    #wait for all threads to end  
    not_done = True
    while not_done:
        not_done = False
        for thread in threads:
            if thread.isAlive():
                not_done = True
        time.sleep(1)

def stateful_start(timelimit):
    """ func that will create a thread for every plugin
        will create a deterministci file that will be passed to every thread
        will pass all threads the timelimit (could be infiniety)
        will spawn all threads
        will wait for all threads to compplete or for ctrl-c
    """
    log.write('{:%Y-%m-%d %H:%M:%S} Stateful Mode Started\n'.format(datetime.datetime.now()))
    print "stateful"

    if timelimit is None:
        log.write('{:%Y-%m-%d %H:%M:%S} Indefinite Timelimit\n'.format(datetime.datetime.now()))
        print "Indefinite Time Limit"
    else:
        log.write('{:%Y-%m-%d %H:%M:%S} {} Minute Timelimit\n'.format(datetime.datetime.now(), timelimit))
        print "{} Minute Time Limit".format(timelimit)

     # writes a file that can feed into a deterministic run
    dir_path = os.path.join(os.path.dirname(__file__), "deterministic-runs/")
    # create directory if it doesn't exist
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    deterministic_filename = dir_path + str(global_starttime).replace(" ", "_") + '-run.txt'
    deterministic_file = open(deterministic_filename, 'w')

    #create thread for every plugin
    for plugin in plugins:
        threads.append(threading.Thread(target=plugin.stateful, args=(deterministic_file, timelimit)))

    #start all threads
    for thread in threads:
        thread.start()
      
    #wait for all threads to end  
    not_done = True
    while not_done:
        not_done = False
        for thread in threads:
            if thread.isAlive():
                not_done = True
        time.sleep(1)

def stateless_start(timelimit):
    """ func that will read from stateless config
        will run one plugin's statless mode on main thread
        ill pass the timelimit (could be infiniety)
    """
    log.write('{:%Y-%m-%d %H:%M:%S} Stateless Mode Started\n'.format(datetime.datetime.now()))

    if timelimit is None:
        log.write('{:%Y-%m-%d %H:%M:%S} Indefinite Time Limit Enabled\n'.format(datetime.datetime.now()))
        print "Indefinite Time Limit"
    else:
        log.write('{:%Y-%m-%d %H:%M:%S} {} Minute Time Limit\n'.format(datetime.datetime.now(), timelimit))
        print "{} Minute Time Limit".format(timelimit)

    #pick plugin to use
    plugin = random.choice(plugins)

    log.write('{:%Y-%m-%d %H:%M:%S} {} Plugin Chosen\n'.format(datetime.datetime.now(), plugin.__repr__()))

    # writes a file that can feed into a deterministic run
    dir_path = os.path.join(os.path.dirname(__file__), "deterministic-runs/")
    # create directory if it doesn't exist
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    deterministic_filename = dir_path + str(global_starttime).replace(" ", "_") + '-run.txt'
    deterministic_file = open(deterministic_filename, 'w')

    #start plugins stateless mode
    plugin.stateless(deterministic_file, timelimit)

def signal_handler(signal, frame):
        
        print('\nYou exited!\nPlease wait while your environment is restored.\nThis may take some time.')

        log.write('{:%Y-%m-%d %H:%M:%S} Signal handler\n'.format(datetime.datetime.now()))

        stopper.set()

        for thread in threads:
            thread.join()

        subprocess.call('ansible-playbook playbooks/restart-nodes.yml', shell=True)

        log.write('{:%Y-%m-%d %H:%M:%S} Fault Injector Stopped\n'.format(datetime.datetime.now()))
        log.close()

        sys.exit(0)

if __name__ == "__main__":
    main()
