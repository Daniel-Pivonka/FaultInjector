#!/usr/bin/python

import datetime
import yaml
import subprocess
import argparse
import random
import time


debug = True

# Node dictionary holds the node type as a key and
# the node ip and if it's faultable as its value
nodes = {
    
    'controller': [],
    'osd-compute': []

}

def main():
    #open log file
    log = open('FaultInjector.log', 'a')
    log.write('{:%Y-%m-%d %H:%M:%S} Fault Injector Started\n'.format(datetime.datetime.now()))



    #create argument parser
    parser = argparse.ArgumentParser(description='Fault Injector')
    parser.add_argument('-p','--process', help='run process faults', required=False, action='store_true')
    parser.add_argument('-s','--system', help='run system faults', required=False, action='store_true')
    parser.add_argument('-hw','--hardware', help='run hardware faults', required=False, action='store_true')
    args = vars(parser.parse_args())



    #check mode args
    if args['process']:
        print 'process faults enabled'
        log.write('{:%Y-%m-%d %H:%M:%S} process faults enabled\n'.format(datetime.datetime.now()))

    if args['system']:
        print 'system faults enabled'
        log.write('{:%Y-%m-%d %H:%M:%S} system faults enabled\n'.format(datetime.datetime.now()))

    if args['hardware']:
        print 'hardware faults enabled'
        log.write('{:%Y-%m-%d %H:%M:%S} hardware faults enabled\n'.format(datetime.datetime.now()))



    #open config
    with open('config.yaml', 'r') as f:
        config = yaml.load(f)
    log.write('{:%Y-%m-%d %H:%M:%S} Config file opened\n'.format(datetime.datetime.now()))

    parse_config(config)
    service_fault('osd-compute', 'ceph', 5)

    #test compatiblity
    if check_config_mode_compatiblity():
        #pick mode
        pass
    else:
        pass
        #ask for new set of modes










    #run ansible playbook
    #subprocess.call("ansible-playbook playbook.yml", shell=True)
    #log.write('{:%Y-%m-%d %H:%M:%S} ansible\n'.format(datetime.datetime.now()))

    log.write('{:%Y-%m-%d %H:%M:%S} Fault Injector Stopped\n'.format(datetime.datetime.now()))
    log.close()
    #end


def check_config_mode_compatiblity():
    pass

def service_fault(node_type, service, downtime):
    """ Kills the service specified on a random node of type 'node_type' 
        for 'downtime' seconds.
    """
    target_node = random.choice(nodes[node_type])
    while target_node[1] == False:
        target_node = random.choice(nodes[node_type])
        time.sleep(5) # Wait 5 seconds to give nodes time to recover 
        """
    with open('roles/ceph-service-fault/tasks/ceph-service-stop.yaml') as f:
        config = yaml.load(f)
        for heading in config:
            if heading
        config["shell"] = "systemctl disable ceph-mon@" + target_node[0]
        

    with open('roles/ceph-service-fault/tasks/ceph-service-stop.yaml', 'w') as f:
        yaml.dump(config, f)
        """

def node_fault():
    pass

def hardware_fault():
    pass

def parse_config(config):
    """ Iterates through the config.yaml file, placing
        each node and corresponding ip in the appropiate
        place in the node dictionary.
    """
    for node_index in range(config['numnodes']):
        current_node = config['node' + str(node_index)]
        node_type = current_node['type']
        nodes[node_type].append(((current_node['ip']), True))

    if debug:
        print "Nodes from config:"
        for node in nodes:
            print node, nodes[node]

    
if __name__ == "__main__":
    main()
