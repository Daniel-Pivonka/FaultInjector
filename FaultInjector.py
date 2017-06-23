#!/usr/bin/python

import datetime
import yaml
import subprocess
import argparse
import random
import time
import signal
import sys

#extra messages printed if true
debug = False

#global var for log file
log = open('FaultInjector.log', 'a')

# Node dictionary holds the node type as a key and
# the node ip and if it's faultable as its value
nodes = {
    
    'controller': [],
    'osd-compute': []

}

def main():
    #signal handler to restore everything to normal
    signal.signal(signal.SIGINT, signal_handler)

    #open log file
    log.write('{:%Y-%m-%d %H:%M:%S} Fault Injector Started\n'.format(datetime.datetime.now()))

    #create argument parser
    parser = argparse.ArgumentParser(description='Fault Injector')
    parser.add_argument('-p','--process', help='run process faults', required=False, action='store_true')
    parser.add_argument('-s','--system', help='run system faults', required=False, action='store_true')
    parser.add_argument('-hw','--hardware', help='run hardware faults', required=False, action='store_true')
    parser.add_argument('-t','--timelimit', help='timelimit for injector to run (mins) default 30 mins', required=False, type=int, default=30, metavar='\b')
    parser.add_argument('-d','--deterministic', help='injector will follow list of tasks in deterministic.yaml', required=False, action='store_true')
    args = parser.parse_args()

    #open config and parse
    with open('config.yaml', 'r') as f:
        config = yaml.load(f)
    log.write('{:%Y-%m-%d %H:%M:%S} Config file opened\n'.format(datetime.datetime.now()))
    parse_config(config)

    #check deterministic mode
    if args.deterministic:
        log.write('{:%Y-%m-%d %H:%M:%S} Deterministic mode started\n'.format(datetime.datetime.now()))
        deterministic_mode()
    else:
        log.write('{:%Y-%m-%d %H:%M:%S} Random mode started\n'.format(datetime.datetime.now()))
        random_mode(args)


    log.write('{:%Y-%m-%d %H:%M:%S} Fault Injector Stopped\n'.format(datetime.datetime.now()))
    log.close()
    

def random_mode(args):
    #list to hold active modes to be randomly chosen
    active_modes = []

    #check mode args
    if args.process:
        if debug:
            print 'Process faults enabled'
        active_modes.append('process')
        log.write('{:%Y-%m-%d %H:%M:%S} Process faults enabled\n'.format(datetime.datetime.now()))
    if args.system:
        if debug:
            print 'System faults enabled'
        active_modes.append('system')
        log.write('{:%Y-%m-%d %H:%M:%S} System faults enabled\n'.format(datetime.datetime.now()))
    if args.hardware:
        if debug:
            print 'Hardware faults enabled'
        active_modes.append('hardware')
        log.write('{:%Y-%m-%d %H:%M:%S} Hardware faults enabled\n'.format(datetime.datetime.now()))

    #test compatiblity
    while not check_config_mode_compatiblity(active_modes):
        #ask for new set of modes
        new_flags = raw_input("You must enable at least one mode (-p, -s, -hw)\n")

        if new_flags.find('-p') != -1:
            if debug:
                print 'Process faults enabled'
            active_modes.append('process')
            log.write('{:%Y-%m-%d %H:%M:%S} process faults enabled\n'.format(datetime.datetime.now()))
        if new_flags.find('-s') != -1:
            if debug:
                print 'System faults enabled'
            active_modes.append('system')
            log.write('{:%Y-%m-%d %H:%M:%S} system faults enabled\n'.format(datetime.datetime.now()))
        if new_flags.find('-hw') != -1:
            if debug:
                print 'Hardware faults enabled'
            active_modes.append('hardware')
            log.write('{:%Y-%m-%d %H:%M:%S} hardware faults enabled\n'.format(datetime.datetime.now()))

    # compatibiliy is safe we got out of the loop above

    #set timelimit from cmd arg/default value
    timelimit = args.timelimit

    while True:
        #runtime info
        if debug:
            print 'Fault Injector will run for {} minute(s)' .format(timelimit)
        log.write('{:%Y-%m-%d %H:%M:%S} Fault Injector will run for {} minute(s)\n'.format(datetime.datetime.now(), timelimit))    

        run_injector(timelimit, active_modes)

        # time limit reached ask if user wants more time 
        while True:

            response = raw_input('Do you want to keep running the injector? if yes, enter how many minutes else, enter "no"\n')
            if is_int(response):
                timelimit = int(response)
                # new time limit will be used in loop
                break
            else:
                response = response.lower().strip(" ")
                if response == "no":
                    # leave prompt loop
                    break 
                else:
                    # not a number or some form of "no"
                    print "Please enter a valid response."

        # response was no break out of everything 
        if response == "no":
            break


def deterministic_mode():

    #open file
    with open("deterministic.yaml") as f:
        
        #read line by line
        for line in f:

            #filter out commented and blank lines
            if line.startswith('#'):
                print "commented line"
            elif line == "\n":
                print "blank line"
            else:

                #break up words
                words = line.split(" ")
                if words[0] == "service":

                    #services
                    if words[1].strip("\n") == "ceph-osd":
                        service_fault('osd-compute', 'osd', 5)
                    elif words[1].strip("\n") == "ceph-mon":
                        service_fault('controller', 'mon', 5)
                    else:
                        print words[1].strip("\n") + " not setup"

                elif words[0] == "system":

                    #system
                    if words[1].strip("\n") == "crash":
                        node_fault('osd-compute', 1)
                    else:
                        print words[1].strip("\n") + " not setup"

                elif words[0] == "hardware":

                    #hardware
                    print words[1].strip("\n") + " not setup"

                else:

                    print "invalid input"


def check_config_mode_compatiblity(active_modes):

    #TODO: actually check compatibility

    if len(active_modes) > 0:
        return True
    else:
        return False


def run_injector(timelimit, active_modes):
    # runtime loop
    timeout = time.time() + 60 * timelimit
    while time.time() < timeout:
        
        # pick mode
        mode = random.choice(active_modes)
        log.write('{:%Y-%m-%d %H:%M:%S} {} Mode Chosen\n'.format(datetime.datetime.now(), mode))

        if mode == 'process':
            service_fault('osd-compute', 'osd', 5)
        elif mode == 'system':
            node_fault('osd-compute', 1)
        elif mode == 'hardware':
            hardware_fault()     
        
    

def service_fault(node_type, service, downtime):
    """ Kills the service specified on a random node of type 'node_type' 
        for 'downtime' seconds.
    """
    target_node = random.choice(nodes[node_type])
    while target_node[1] == False:
        target_node = random.choice(nodes[node_type])
        time.sleep(5) # Wait 5 seconds to give nodes time to recover 

    with open('ceph-' + service + '-fault.yml') as f:
        config = yaml.load(f)
        config[0]['hosts'] = target_node[0]
        for task in config[0]['tasks']:
            if task['name'] == 'Disabling auto restart of ceph-' + service + 'service':
                task['shell'] = 'systemctl disable ceph-' + service + '@' + target_node[0]
            elif task['name'] == 'Restoring ceph-' + service + ' regular behavior':
                task['shell'] = 'systemctl enable ceph-' + service + '@' + target_node[0]
            elif task['name'] == 'Waiting set amount of time before restart':
                task['shell'] = 'sleep ' + str(downtime)

    with open('ceph-' + service + '-fault.yml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    if check_health():    
        subprocess.call('ansible-playbook ceph-' + service + '-fault.yml', shell=True)
    else:
        print "Health is bad"


def node_fault(node_type, downtime):

    #pick random node
    target_node = random.choice(nodes[node_type])

    #modify crash playbook
    with open('system-crash.yml') as f:
        crash_config = yaml.load(f)
        crash_config[0]['hosts'] = target_node[0]
        for task in crash_config[0]['tasks']:
            if task['name'] == 'Power off server':
                task['local_action'] = 'shell . ../stackrc && nova stop ' + target_node[1]

    with open('system-crash.yml', 'w') as f:
        yaml.dump(crash_config, f, default_flow_style=False)

    #modify restore playbook
    with open('system-restore.yml') as f:
        restore_config = yaml.load(f)
        restore_config[0]['hosts'] = target_node[0]
        for task in restore_config[0]['tasks']:
            if task['name'] == 'Power on server':
                task['local_action'] = 'shell . ../stackrc && nova start ' + target_node[1]

    with open('system-restore.yml', 'w') as f:
        yaml.dump(restore_config, f, default_flow_style=False)


    #crash system
    subprocess.call("ansible-playbook system-crash.yml", shell=True)
    log.write('{:%Y-%m-%d %H:%M:%S} Node killed\n'.format(datetime.datetime.now()))

    #wait
    time.sleep(60*downtime)

    #restore system
    subprocess.call("ansible-playbook system-restore.yml", shell=True)
    log.write('{:%Y-%m-%d %H:%M:%S} Node restored\n'.format(datetime.datetime.now()))

def hardware_fault():
    pass

def parse_config(config):
    """ Iterates through the config.yaml object, placing
        each node and corresponding ip in the appropiate
        place in the node dictionary.
    """

    hosts = open('hosts', 'w')

    for node_index in range(config['numnodes']):
        current_node = config['node' + str(node_index)]
        node_type = current_node['type']
        nodes[node_type].append(((current_node['ip']), (current_node['id']), True))
        hosts.write((current_node['ip'])+"\n")

    hosts.close()


    if debug:
        print "Nodes from config:"
        for node in nodes:
            print node, nodes[node]

def is_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False


def signal_handler(signal, frame):
        print('\nYou exited! Your environment will be restored to its original state.')

        log.write('{:%Y-%m-%d %H:%M:%S} Signal handler\n'.format(datetime.datetime.now()))

        subprocess.call('ansible-playbook restart-nodes.yml', shell=True)

        log.write('{:%Y-%m-%d %H:%M:%S} Fault Injector Stopped at\n'.format(datetime.datetime.now()))
        log.close()

        sys.exit(0)

def check_health():
    """ Looks at a random functioning controller node
        and checks the status of the ceph cluster returning
        True if it's healthy
    """
    target_node = random.choice(nodes['controller'])
    while target_node[1] == False:
        target_node = random.choice(nodes['controller'])
        time.sleep(5) # Wait 5 seconds to give nodes time to recover 

    host = 'heat-admin@' + target_node['ip']
    command = "sudo ceph -s"

    ssh = subprocess.Popen(["ssh", "%s" % host, command], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    response = ssh.stdout.readlines()
    if result == []:
        error = ssh.stderr.readlines()
        print >>sys.stderr, "ERROR: %s" % error
    else:
        print result
    return False

    
if __name__ == "__main__":
    main()
