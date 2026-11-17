#!/bin/bash

python3 /home/dell/sjw/lb/simulator/run_script/generate_confs.py --plan /home/dell/sjw/lb/simulator/run_script/experiment_plan.csv &&
nohup python3 /home/dell/sjw/lb/simulator/run_script/sim_scheduler.py > /home/dell/sjw/lb/simulator/output/scheduler_status.log 2>&1 &