# Fault Injector

A fault insertion mechanism that can run concurrently with any deployed cloud environment
with the purpose of helping to test and validate the fault resilience built into deployments

### Presentation 

Download a PDF of the presentation made on July 21, 2017 [HERE](PresentationRev1.pdf "Fault Injector Presentation Rev 01 PDF")

### setup.py
Collects all the necessary information for FaultInjector.py to run fully by filling out the config.yaml file.

  -c, --ceph  setup will look for ceph fields in the deployment


### FaultInjector.py

  -sf, --stateful Injector will run in stateful random mode

  -sl NUMFAULTS, --stateless NUMFAULTS
                        Injector will run in stateless mode with the specified number of faults

  -ex EXCLUDE, --exclude EXCLUDE
                        Exclude a node by name in stateless mode (ex.for the purpose of monitoring)

  -tg TARGET, --target TARGET
                        Specify a node type that will be the target of stateless faults

  -d FILEPATH, --deterministic FILEPATH
                        Injector will execute the list of tasks in the file specified

  -t TIMELIMIT, --timelimit TIMELIMIT
                        Time limit for the injector to run (mins)
                        
  -ft FAULT_TIME, --fault_time FAULT_TIME
                        The amount of time faults are active (mins)
                        
  -rt RECOVERY_TIME, --recovery_time RECOVERY_TIME
                        The amount of time faults are given to recover (mins)
                        
  -v VARIABILITY, --variability VARIABILITY
                        A range of time that may be added to fault time (mins)

### Classes:

---

#### Node Fault:

##### Node Kill
- Connects to a node and executes `echo c > /proc/sysrq-trigger` followed by `nova stop [node id]`
	- These commands cause the kernel to crash and then ensures the node won’t restart on its own.
	- Note that these have only been tested on VM deployments
- After the desired amount of time passes, the node is recovered with `nova start [node id]`

---

#### Ceph Fault:

##### OSD Fault
- Connects to the Ceph cluster via a Controller, Ceph, or in the case of an HCI deployment, an OSD-Compute node
- Executes `systemctl stop ceph-osd@[target osd number]` to stop the OSD
- Similarly, the OSD is brought back up with `systemctl start ceph-osd@[target osd number]`

##### Monitor Fault
- Connects to a Controller node and executes `systemctl stop ceph-mon@target` to stop the monitor
- Similarly, the monitor is brought back up with `systemctl start ceph-mon@target`

---

### Modes

##### Stateless:

- Spawns a number of threads equal to the number of faults specified in the flag passed in at runtime
- Each thread runs the *Node Kill Fault* function from within the Node Fault class
- Downtime scales according to *fault time + variability* where variability is an integer from 0 to the given 
  variability value
- The time it takes for a fault to recover is equal to *recovery time*
- Writes to a deterministic file

##### Stateful:

- Spawns a number of threads equal to the following:  
  *number of threads = ceiling(number of monitors / 2) + minimum replication size across all ceph pools*
- Each thread selects from the available stateful fault functions (so far, OSD and monitor faults)
- Each fault function is set to return None if it cannot execute meaning it will not be recorded to the deterministic file
- If that happens 3 times in a row, the thread is killed and a new one is spawned
  which has a chance to run an alternative fault function
- Downtime scales according to *fault time + variability* where variability is an integer from 0 to the given 
  variability value
- The time it takes for a fault to recover is equal to *recovery time*
- Writes to a deterministic file

##### Deterministic:

- Spawns a number of threads equal to the number of faults/lines in the deterministic file
- Each thread waits until its start time to begin which emulates the previous run as accurately as possible

### Usage:

---

##### Setup

- Run setup.py (with the -c flag if Ceph is part of the deployment)
- Review the config.yaml file generated and look for anything missing
    - There is a reference file under the name config_reference.yaml which contains both Ceph  
      and standard deployment attributes

---

##### Running the Tool:

##### Stateful Mode

- If a time limit is desired, run `./FaultInjector.py -sf -t [Time Limit] -ft [Fault Time] -rt [Recovery Time]`  
  (all parameters in minutes)
- Otherwise, run `./FaultInjector.py -sf -ft [Fault time] -rt [Recovery time]`

	##### Explanation of Parameters
	
	- **Fault Time** `-ft [Fault Time]`
	    - The amount of time faults are active (mins)
	
	- **Recovery Time** `-rt [Recovery Time]`
	    - The amount of time given to faults to recover (mins)
	
	- **Variability** `-v [Variability]`
	    - A range of time that can be added to fault time (mins)

##### Stateless Mode

- Stateless mode requires a parameter for the number faults desired to be active at once
- Run it with the following syntax `./FaultInjector.py -sl [Number of Faults] -ft [Fault Time] -rt [Recovery Time]`

	##### Explanation of Parameters

 	- **Time Limit** `-t [Time Limit (in minutes)]`

 	- **Target Node** (the target node type for faults) `-tg [node name]`
		- The script looks for `[node name]` in the stored types of all the nodes in the config.yaml file
		- Example: an input of `[control]` will flag all controller nodes

 	- **Exclusions** (exclude node(s) from faults): `-ex [node name]`
		- The script looks for the exact `[node name]` in the stored names of all the nodes in the config.yaml file

		- Specify multiple nodes with `-ex [node1 node2 node3...]`

		- Example: In a deployment with a single compute node named *novacompute-0*, an input of `[novacompute-0]` will
		           exclude that node, but an input of `[compute]` or `[novacompute]` will **not** exclude any nodes.
        
    - **Fault Time** `-ft [Fault Time]`
	    - The amount of time faults are active (mins)
	
	- **Recovery Time** `-rt [Recovery Time]`
	    - The amount of time given to faults to recover (mins)
	
	- **Variability** `-v [Variability]`
	    - A range of time that can be added to fault time (mins)

##### Deterministic Mode
- Deterministic mode requires the file path of the desired deterministic run to be passed in as a parameter
- Run it with the following syntax: `./FaultInjector.py -d [Filepath]`

---

### Development:

Adding additional fault types involves adhering to the following paradigm:
 
 **Node Class:**  
 The node class contains all of the data for node-based deployments including:
 - Node IP
 - Node ID
 - Node Name
 - Node Type
 
 **Deployment Class:**  
 The deployment class takes in the config.yaml file generated by setup.py  
 It's meant to contain all of the properties of the deployment like:
 - HCI?
 - Containerized?
 - Number of Ceph-OSDs
 - Number of Ceph Monitors
 - Number of Nodes  
 
 In addition, the deployment class contains a list of Node instances which make up the deployment  
 
 **Fault Class:**  
 All fault types inherit from the main fault class which has three methods:
 - Stateless Mode
 - Stateful Mode 
 - Deterministic Mode   
 
 Not all fault modes need to be utilized. For example, there is no stateful mode in  
 the built in Node Fault class, and there is no stateless mode in the Ceph Fault class.  
 If it is possible, it is strongly encouraged to create a deterministic method for a fault  
 class since from a design perspective, it's helpful to be able to rule out random chance  
 when testing and have the ability to recreate a given run.
 
 
 
