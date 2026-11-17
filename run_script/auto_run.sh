#!/bin/bash

config_file="getConfig.py"
run_file="run.sh"
########################################
# workload + topology 统一配置
########################################
### Workload
# 128g:  
# microAllReduce_128g microAllReduce_128g_TP2 microAllReduce_128g_TP2_256M
# microAll2All_128g_EP8_8M microAll2All_128g_EP8_32M microAll2All_128g_EP8_64M microAll2All_128g_EP8_128M
# 1024g: 
# microReduceScatter_1024g
# microAllReduce_1024g_6layer
# microAllReduce_1024g microAllReduce_1024g_512M microAllReduce_1024g_1024M
# microAll2All_1024g_EP8_8M microAll2All_1024g_EP8_16M microAll2All_1024g_EP8_32M microAll2All_1024g_EP8_64M microAll2All_1024g_EP8_128M
# microAll2All_1024g_EP12_48M
# microAll2All_1024g_EP16_16M 
# microAll2All_1024g_EP32_32M 
# microAll2All_1024g_EP64_64M
# microAll2All_1024g_EP128_128M
sed -i '144,180s/workload=.*/workload="microAll2All_128g_EP8_8M"/' $run_file 

### topology
# SpectrumX_32g_8gps_400Gbps_A100  SpectrumX_1024g_8gps_400Gbps_A100
# AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100
# fattree_k8_128g_2gps_400Gbps_A100 fattree_k8_128g_2gps_400Gbps_A100_asy fattree_k8_128g_2gps_400Gbps_A100_failure
# fattree_k16_1024g_8gps_400Gbps_A100 fattree_k16_1024g_8gps_400Gbps_A100_failure
sed -i '144,180s/network=.*/network="fattree_k8_128g_2gps_400Gbps_A100_failure"/' $run_file

########################################
# 默认参数
########################################
sed -i 's/QP_MON_INTERVAL.*/QP_MON_INTERVAL: int = 10 \# us/' $config_file # all2all 10us; allreduce 100us
sed -i 's/QLEN_MON_INTERVAL.*/QLEN_MON_INTERVAL: int = 10 \# us/' $config_file
sed -i 's/BW_MON_INTERVAL.*/BW_MON_INTERVAL: int = 10 \# us/' $config_file
sed -i 's/APS_SELECTED_TRACED_NODE.*/APS_SELECTED_TRACED_NODE: int = 511/' $config_file
sed -i 's/APS_SELECTED_MON_INTERVAL.*/APS_SELECTED_MON_INTERVAL: int = 10000/' $config_file # 10000 ns
sed -i 's/SWITCH_SAMPLE_TIME_INTERVAL.*/SWITCH_SAMPLE_TIME_INTERVAL: int = 1000/' $config_file # 10000 ns


########################################
# 实验0：ECMP
########################################
function ecmp {

echo "===== 实验 0: ecmp dcqcn buffersize64 ====="

# 修改 getConfig.py
sed -i 's/LB_MODE.*/LB_MODE: int = 0/' $config_file

# 修改 run.sh
# sed -i '144,180s/tag=.*/tag="ecmp-asy_dcqcn"/' $run_file
sed -i '144,180s/tag=.*/tag="ecmp_dcqcn"/' $run_file

# 执行仿真
./run.sh -r -e

}
########################################
# 实验1：APS-v2 动态包喷洒
########################################
# function aps {
# apsTag=64
# echo "===== 实验 1: aps dcqcn $apsTag ====="

# # 修改 getConfig.py
# sed -i 's/LB_MODE.*/LB_MODE: int = 1/' $config_file
# sed -i 's/APS_INDICATOR_MASK.*/APS_INDICATOR_MASK: int = 7/' $config_file # eq:3 eu:5 q:2 qu:3 u:4; 001:ecn, 010:qlen, 100:util, ..., 111:all
# # sed -i 's/APS_PATH_CREDIT.*/APS_PATH_CREDIT: int = '${apsTag}'/' $config_file
# sed -i 's/APS_PATH_CREDIT.*/APS_PATH_CREDIT: int = 4/' $config_file
# # sed -i 's/APS_UPDATE_FREQUENCY.*/APS_UPDATE_FREQUENCY: int = '${apsTag}'/' $config_file
# sed -i 's/APS_UPDATE_FREQUENCY.*/APS_UPDATE_FREQUENCY: int = 1/' $config_file
# # sed -i 's/MAX_OOO_SIZE.*/MAX_OOO_SIZE: int = '${apsTag}'/' $config_file
# sed -i 's/MAX_OOO_SIZE.*/MAX_OOO_SIZE: int = 64/' $config_file
# sed -i 's/APS_SELECTED_MON_INTERVAL.*/APS_SELECTED_MON_INTERVAL: int = 10000/' $config_file
# sed -i 's/MIX_LB_RATIO.*/MIX_LB_RATIO: float = 0/' $config_file

# # 修改 run.sh
# # sed -i '144,180s/tag=.*/tag="aps-v2-f'${apsTag}'_dcqcn"/' $run_file
# # sed -i '144,180s/tag=.*/tag="aps-v2-b64-asy_dcqcn"/' $run_file
# sed -i '144,180s/tag=.*/tag="aps-v2_dcqcn"/' $run_file

# # 执行仿真
# ./run.sh -r -e
# }
########################################
# 实验1：APS 动态包喷洒
########################################
function aps {
apsTag=64
echo "===== 实验 1: aps dcqcn $apsTag ====="

# 修改 getConfig.py
sed -i 's/LB_MODE.*/LB_MODE: int = 1/' $config_file
sed -i 's/APS_INDICATOR_MASK.*/APS_INDICATOR_MASK: int = 7/' $config_file # 001:ecn, 010:qlen, 100:util, ..., 111:all
# sed -i 's/APS_PATH_CREDIT.*/APS_PATH_CREDIT: int = '${apsTag}'/' $config_file
sed -i 's/APS_PATH_CREDIT.*/APS_PATH_CREDIT: int = 1/' $config_file
# sed -i 's/APS_UPDATE_FREQUENCY.*/APS_UPDATE_FREQUENCY: int = '${apsTag}'/' $config_file
sed -i 's/APS_UPDATE_FREQUENCY.*/APS_UPDATE_FREQUENCY: int = 1/' $config_file
# sed -i 's/MAX_OOO_SIZE.*/MAX_OOO_SIZE: int = '${apsTag}'/' $config_file
sed -i 's/MAX_OOO_SIZE.*/MAX_OOO_SIZE: int = 64/' $config_file
sed -i 's/APS_SELECTED_MON_INTERVAL.*/APS_SELECTED_MON_INTERVAL: int = 10000/' $config_file
sed -i 's/MIX_LB_RATIO.*/MIX_LB_RATIO: float = 0/' $config_file

# 修改 run.sh
# sed -i '144,180s/tag=.*/tag="aps-b'${apsTag}'-asy_dcqcn"/' $run_file
sed -i '144,180s/tag=.*/tag="aps_dcqcn"/' $run_file
# sed -i '144,180s/tag=.*/tag="aps-b64-asy_dcqcn"/' $run_file

# 执行仿真
./run.sh -r -e
}
########################################
# 实验2：RPS[INFOCOM'13] 随机包喷洒(交换机)
########################################
function rps {
rpsTag=1
echo "===== 实验 2: rps_dcqcn  ====="

# 修改 getConfig.py
sed -i 's/LB_MODE.*/LB_MODE: int = 2/' $config_file
sed -i 's/MIX_LB_RATIO.*/MIX_LB_RATIO: float = 0/' $config_file
# sed -i 's/MAX_OOO_SIZE.*/MAX_OOO_SIZE: int = '${rpsTag}'/' $config_file
sed -i 's/MAX_OOO_SIZE.*/MAX_OOO_SIZE: int = 64/' $config_file

# 修改 run.sh
# sed -i '144,180s/tag=.*/tag="rps-b64-asy_dcqcn"/' $run_file
sed -i '144,180s/tag=.*/tag="rps_dcqcn"/' $run_file
# sed -i '144,180s/tag=.*/tag="rps-b'${rpsTag}'_dcqcn"/' $run_file

# 执行仿真
./run.sh -r -e
}
########################################
# 实验3：FlowBender[CoNEXT'14]
########################################
function flowbender {
echo "===== 实验 3: flowbender dcqcn ====="

# 修改 getConfig.py
sed -i 's/LB_MODE.*/LB_MODE: int = 3/' $config_file
sed -i 's/FLOWBENDER_ECN_T.*/FLOWBENDER_ECN_T: float = 0.05/' $config_file
sed -i 's/FLOWBENDER_SWITCH_N.*/FLOWBENDER_SWITCH_N: int = 1/' $config_file
sed -i 's/MAX_OOO_SIZE.*/MAX_OOO_SIZE: int = 64/' $config_file


# 修改 run.sh
# sed -i '144,180s/tag=.*/tag="flowbender-asy_dcqcn"/' $run_file
sed -i '144,180s/tag=.*/tag="flowbender_dcqcn"/' $run_file

# 执行仿真
./run.sh -r  -e
}
########################################
# 实验4：LetFlow[NSDI'17]
########################################
function letflow {
echo "===== 实验 4: letflow dcqcn ====="

# 修改 getConfig.py
sed -i 's/LB_MODE.*/LB_MODE: int = 4/' $config_file
sed -i 's/LETFLOW_TIMEOUT.*/LETFLOW_TIMEOUT: int = 500/' $config_file # 500 us
sed -i 's/LETFLOW_AGING_TIME.*/LETFLOW_AGING_TIME: int = 2/' $config_file # 2 ms

# 修改 run.sh
# sed -i '144,180s/tag=.*/tag="letflow-asy_dcqcn"/' $run_file
sed -i '144,180s/tag=.*/tag="letflow_dcqcn"/' $run_file

# 执行仿真
./run.sh -r -e
}
########################################
# 实验5：REPS[arXiv'25]
########################################
function reps {
repsTag=306
echo "===== 实验 5: reps dcqcn buffersize 64 ====="

# 修改 getConfig.py
sed -i 's/LB_MODE.*/LB_MODE: int = 5/' $config_file
sed -i 's/MAX_OOO_SIZE.*/MAX_OOO_SIZE: int = 64/' $config_file
sed -i 's/REPS_BUFFER_SIZE.*/REPS_BUFFER_SIZE: int = 8/' $config_file # EV buffer size for burst ACK

# 修改 run.sh
# sed -i '144,180s/tag=.*/tag="reps-asy_dcqcn"/' $run_file
sed -i '144,180s/tag=.*/tag="reps-b'${repsTag}'_dcqcn"/' $run_file
# sed -i '144,180s/tag=.*/tag="reps_dcqcn"/' $run_file

# 执行仿真
./run.sh -r -e
}
########################################
# 实验6：IOPS
########################################
function iops {
echo "===== 实验 6: iops dcqcn buffersize 64 ====="

# 修改 getConfig.py
sed -i 's/LB_MODE.*/LB_MODE: int = 6/' $config_file
sed -i 's/MAX_OOO_SIZE.*/MAX_OOO_SIZE: int = 64/' $config_file
sed -i 's/IOPS_BUFFER_SIZE.*/IOPS_BUFFER_SIZE: int = 8/' $config_file # EV buffer size for burst ACK

# 修改 run.sh
sed -i '144,180s/tag=.*/tag="iops_dcqcn"/' $run_file

# 执行仿真
./run.sh -r 
}
########################################
# 参数复原
########################################
function restore {
# 修改 getConfig.py
sed -i 's/MIX_LB_RATIO.*/MIX_LB_RATIO: float = 0/' $config_file
sed -i 's/LB_MODE.*/LB_MODE: int = 1/' $config_file
sed -i 's/APS_INDICATOR_MASK.*/APS_INDICATOR_MASK: int = 7/' $config_file
sed -i 's/APS_PATH_CREDIT.*/APS_PATH_CREDIT: int = 1/' $config_file
sed -i 's/APS_UPDATE_FREQUENCY.*/APS_UPDATE_FREQUENCY: int = 1/' $config_file
sed -i 's/MAX_OOO_SIZE.*/MAX_OOO_SIZE: int = 306/' $config_file
sed -i 's/APS_SELECTED_MON_INTERVAL.*/APS_SELECTED_MON_INTERVAL: int = 10000/' $config_file
}


########################################
function help {
    echo "Usage: ./auto_run.sh [lb_mode...]"
    echo "lb_mode options:"
    echo "  0 - ECMP"
    echo "  1 - APS"
    echo "  2 - RPS"
    echo "  3 - FlowBender"
    echo "  4 - LetFlow"
    echo "  5 - REPS"
    echo "  6 - IOPS"
    echo "  a - Run all experiments sequentially"
    echo "e.g., [./auto_run.sh 0 1 2] or [./auto_run.sh a]"
    exit 1
}

if [ $# -eq 0 ]; then
    help
    exit 1
fi

for arg in "$@"; do
    case "$arg" in
    0)
        ecmp ;;
    1)  
        aps ;;
    2)
        rps ;;
    3)
        flowbender ;;
    4)
        letflow ;;
    5)
        reps ;;
    6)
        iops ;;
    a)
        ecmp &&
        aps &&
        rps &&
        flowbender &&
        letflow &&
        reps &&
        iops ;;
    *)
        echo "no such lb_mode"
        help
    ;;
    esac
    shift
done

# restore


