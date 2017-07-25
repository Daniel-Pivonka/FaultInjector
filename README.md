# Fault Injector

A tool to inject faults into a deployed cloud environment



## setup.py

Collects all the necessary information for the fault injector to run fully by filling out the config.yaml file

  -c, --ceph  setup will look for ceph fields in the deployment


## FaultInjector.py

  -h, --help            show this help message and exit
  
  -sf, --stateful       injector will run in stateful random mode
  
  -sl NUMFAULTS, --stateless NUMFAULTS
                        injector will run in stateless mode with specified
                        number of faults
                        
  -ex EXCLUDE, --exclude EXCLUDE
                        exclude a node by name in stateless mode (for the
                        purpose of monitoring)
                        
  -tg TARGET, --target TARGET
                        specific a node type that will be the target of
                        stateless faults
                        
  -d FILEPATH, --deterministic FILEPATH
                        injector will follow the list of tasks in the file
                        specified
                        
  -t TIMELIMIT, --timelimit TIMELIMIT
                        timelimit for injector to run (mins)
                        
### Classes

#### Node Fault:

	Node KIll
    Connects to a node and executes echo c > /proc/sysrq-trigger followed by a nova stop [node id] command which crashes the kernel and then ensures the node won’t restart on its own
    After the desired amount of time passes, the node is recovered through the  nova start [node id] command

#### Ceph Fault:
	
	OSD Fault
    Connects to the Ceph cluster via a Controller, Ceph, or in the case of an HCI deployment, an OSD-Compute node and executes systemctl stop ceph-osd.[target osd number] to stop the OSD
    Similarly, the OSD is brought back up with: 
    systemctl start ceph-osd.[target osd number]
#
	Monitor Fault 
    Connects to a Controller node and executes: 
    systemctl stop ceph-mon.target to stop the monitor
    Similarly, the monitor is brought back up with: 
    systemctl start ceph-mon.target

### Modes

	Stateless:
    Spawn a number of threads equal to the number of faults specified in the flag given at runtime

    Each thread runs the Node Kill fault function from within the Node Fault class

    Downtime scales with the amount of time left up to a 45 minute limit (open to suggestions with this time)

    Writes a deterministic file	
#
	Stateful:
    Spawns a number of threads equal to the following:			number of threads= (number of monitors / 2)  + minimum replication size across all ceph volumes 

    Each thread selects from the available stateful functions (so far OSD and monitor faults)

    Each fault function is set to return None if it cannot execute. If that happens 3 times in a row, the thread is killed and a new one is spawned which has a chance to run an alternate fault function

    Downtime scales with the amount of time left up to a 10 minute limit 
    (open to suggestions with this time)

    Writes a deterministic file
#	
    Deterministic: 
    Spawns a number of threads equal to the number of lines in the deterministic file 

    Each thread waits until its start time to begin to emulate the previous run as accurately as possible

