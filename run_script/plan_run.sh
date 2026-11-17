#!/bin/bash

python3 /home/dcn1/fxb/simulator/run_script/generate_confs.py --plan /home/dcn1/fxb/simulator/run_script/experiment_plan.csv &&
nohup python3 /home/dcn1/fxb/simulator/run_script/sim_scheduler.py > /home/dcn1/fxb/simulator/output/scheduler_status.log 2>&1 &