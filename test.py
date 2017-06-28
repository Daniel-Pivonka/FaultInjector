#!/usr/bin/python

import argparse
import datetime
# import threading
# import time

class Fault:
    def stateless(self):
        raise NotImplementedError

    def stateful(self):
        raise NotImplementedError

    def deterministic(self):
        raise NotImplementedError


class Ceph(Fault):
    def stateless(self):
        print "ceph stateless"

    def stateful(self):
        print "ceph stateful"

    def deterministic(self):
        print "ceph deterministic"



# global var for log file
log = open('FaultInjector.log', 'a')

def main():
    # signal handler to restore everything to normal
    signal.signal(signal.SIGINT, signal_handler)

    # start injector
    log.write('{:%Y-%m-%d %H:%M:%S} Fault Injector Started\n'.format(datetime.datetime.now()))

    # create argument parser
    parser = argparse.ArgumentParser(description='Fault Injector')
    parser.add_argument('-d','--deterministic', help='injector will follow the list of tasks in the file specified', action='store', nargs=1, dest='filepath')
    parser.add_argument('-sf','--stateful', help='injector will run in stateful random mode', required=False, action='store_true')
    parser.add_argument('-sl','--stateless', help='injector will run in statelss random mode', required=False, action='store_true')
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
    log.write('{:%Y-%m-%d %H:%M:%S} Deterministic Mode Started\n'.format(datetime.datetime.now()))
    print "deterministic"

def stateful_start(timelimit):
    if timelimit is None:
        log.write('{:%Y-%m-%d %H:%M:%S} Indefinite Timelimit\n'.format(datetime.datetime.now()))
        print "indefinite timelimit"
    else:
        log.write('{:%Y-%m-%d %H:%M:%S} {} Minute Timelimit\n'.format(datetime.datetime.now(), timelimit))
        print "{} Minute Timelimit".format(timelimit)

    log.write('{:%Y-%m-%d %H:%M:%S} Stateful Mode Started\n'.format(datetime.datetime.now()))
    print "stateful"

def stateless_start(timelimit):
    if timelimit is None:
        log.write('{:%Y-%m-%d %H:%M:%S} Indefinite Timelimit\n'.format(datetime.datetime.now()))
        print "indefinite timelimit"
    else:
        log.write('{:%Y-%m-%d %H:%M:%S} {} Minute Timelimit\n'.format(datetime.datetime.now(), timelimit))
        print "{} Minute Timelimit".format(timelimit)

    log.write('{:%Y-%m-%d %H:%M:%S} Stateless Mode Started\n'.format(datetime.datetime.now()))
    print "stateless"

def signal_handler(signal, frame):
        print('\nYou exited! Your environment will be restored to its original state.')

        log.write('{:%Y-%m-%d %H:%M:%S} Signal handler\n'.format(datetime.datetime.now()))

        subprocess.call('ansible-playbook restart-nodes.yml', shell=True)

        log.write('{:%Y-%m-%d %H:%M:%S} Fault Injector Stopped\n'.format(datetime.datetime.now()))
        log.close()

        sys.exit(0)




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


if __name__ == "__main__":
    main()
