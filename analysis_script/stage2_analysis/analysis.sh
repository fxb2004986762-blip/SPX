#!/bin/bash

baseDir_aps="/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
# export STEP=1
export baseDir=$baseDir_aps
# 获取路径队列长度
function path_qlen {
    ./get_path_qlen.sh
}
# 获取路径平均带宽
function path_bw {
    ./get_path_bw.sh
}

# 获取选路准确率
function select_acc {
    sed -i "s|basePath = .*|basePath = \"$baseDir_aps\"|" acc_path_selected.py &&
    # 获取选路准确率 -> pathAcc.txt
    python3 acc_path_selected.py
}

# 超时重传评估
function timeout_estimate {
    cd $baseDir_aps && 
    timeout_flow_num=$(awk '$10 > 0' fct.txt | wc -l) &&
    timeout_cnt=$(awk '{sum += $10} END {print sum}' ./fct.txt) &&
    echo "########### Timeout Summary ###########"
    echo "Total Timeout Flow Num : $timeout_flow_num"
    echo "Total Timeout Count    : $timeout_cnt"
    echo "#######################################"
    cd -
}

# 检查目录是否存在
if [ ! -d "$baseDir_aps" ]; then
    echo "Error: Directory $baseDir_aps does not exist!"
    exit 1
fi

cd /home/dell/sjw/lb/simulator/analysis_script &&
path_qlen &&
path_bw &&
select_acc 
timeout_estimate