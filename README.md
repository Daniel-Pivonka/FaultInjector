#Fault Injector

A tool to inject faults into a deployed cloud environment



#setup.py

  -c, --ceph  setup will look for ceph fields in the deployment


#FaultInjector.py

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
