#!/bin/bash

# baseDir="/home/dcn1/fxb/simulator/output/aps-v2-mix-c10_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAllReduce_128g_TP2"
# baseDir_rps="/home/dcn1/fxb/simulator/output/rps-mix-b306_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAllReduce_128g_TP2"
if [ -z "$baseDir" ]; then
    echo "baseDir is not set"
    baseDir="/home/dcn1/fxb/simulator/output/aps-v2-mix-c10_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAllReduce_128g_TP2"
fi

cd $baseDir && 
# 提取 <src,dst> 路径信息 -> pathID2Switch
if [ -e "pathID2Switch" ]; then
    echo "pathID2Switch exists"
else
    grep "APS_PATH_SWITCHID" output.log | awk -F ':| |,' '{print $9,$10,$11,$12,$13,$14,$6}' > pathID2Switch 
fi

cd /home/dcn1/fxb/simulator/analysis_script &&
sed -i "s|case_file = .*|case_file = \"$baseDir\"|" topo_parser.py &&
# 解析 <src,dst> 路径交换机出端口 -> pathID2Switch_with_ports.txt
python3 topo_parser.py &&

sed -i "s|basePath = .*|basePath = \"$baseDir\"|" plot_pathQlen.py &&
# 1. 获取路径队列长度 -> pathQlen.txt; 2. 获取路径队列长度随时间变化 -> pathQlen.pdf
python3 plot_pathQlen.py




# cd $baseDir_rps && 
# # 提取 <src,dst> 路径信息 -> pathID2Switch
# cp "$baseDir_aps/pathID2Switch" "$baseDir_rps/pathID2Switch" &&

# cd /home/dcn1/fxb/simulator/analysis_script &&
# sed -i "s|case_file = .*|case_file = \"$baseDir_rps\"|" topo_parser.py &&
# # 解析 <src,dst> 路径交换机出端口 -> pathID2Switch_with_ports.txt
# python3 topo_parser.py &&

# sed -i "s|basePath = .*|basePath = \"$baseDir_rps\"|" plot_pathQlen.py &&
# # (1) 获取路径队列长度 -> pathQlen.txt; (2) 获取路径队列长度随时间变化 -> pathQlen.pdf
# python3 plot_pathQlen.py







