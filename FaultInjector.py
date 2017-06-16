#!/usr/bin/python

import datetime
import yaml
import subprocess
import argparse


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
    if args['process'] is True:
        print 'process faults enabled'
        log.write('{:%Y-%m-%d %H:%M:%S} process faults enabled\n'.format(datetime.datetime.now()))

    if args['system'] is True:
        print 'system faults enabled'
        log.write('{:%Y-%m-%d %H:%M:%S} system faults enabled\n'.format(datetime.datetime.now()))

    if args['hardware'] is True:
        print 'hardware faults enabled'
        log.write('{:%Y-%m-%d %H:%M:%S} hardware faults enabled\n'.format(datetime.datetime.now()))



    #open config
    with open('config.yaml', 'r') as f:
        config = yaml.load(f)
    log.write('{:%Y-%m-%d %H:%M:%S} Config file opened\n'.format(datetime.datetime.now()))



    #test compatiblity
    if check_config_mode_compatiblity() is True:
        #pick mode
    else:
        #ask for new set of modes










    #run ansible playbook
    #subprocess.call("ansible-playbook playbook.yml", shell=True)
    #log.write('{:%Y-%m-%d %H:%M:%S} ansible\n'.format(datetime.datetime.now()))

    log.write('{:%Y-%m-%d %H:%M:%S} Fault Injector Stopped\n'.format(datetime.datetime.now()))
    log.close()
    #end


def check_config_mode_compatiblity()

def service_fault()

def node_fault()

def hardware_fault()


    
if __name__ == "__main__":main()
