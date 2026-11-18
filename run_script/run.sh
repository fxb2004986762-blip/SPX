#!/bin/bash

function build {
    cd "${simdir:?}" || exit 1
    ./scripts/build.sh -c ns3
}

function clean {
    cd "${simdir:?}" || exit 1
    ./scripts/build.sh -l ns3
}

function run {
    configpath || exit 1
    cd "${simdir:?}" || exit 1

    # 启动模拟器，使用复制后的 conf、workload、network
    nohup $execfile \
    -t $threads \
    -w "$outdir/$workload" \
    -n "$outdir/$network" \
    -c "$outdir/SimAI.conf" \
    > $logfile 2>&1 && 
    notify &
}

function debug {
    configpath || exit 1
    cd "${simdir:?}" || exit 1

    # lunch gdb
    gdb --args $execfile \
     -w "$outdir/$workload" \
     -n "$outdir/$network" \
     -c "$outdir/SimAI.conf" \
     -t $threads
}

function configpath {
    # 1. 获取目录
    if [ ! -d "$simdir" ]; then
        echo "Error: $simdir does not exist."
        exit 1
    fi

    ## 原始 workload 和 network 文件目录
    workload_file="$simdir/workload/$workload"

    if [ ! -f "$workload_file" ]; then
    workload_file="$simdir/custom_trace/${workload}.txt"
    fi

    network_file="$simdir/topology/$network"
    if [ -e $workload_file ]; then 
        echo "find workload: $workload_file"
    else 
        echo "Error: workload not found: $workload_file"
        exit 1
    fi
    if [ -e $network_file ]; then 
        echo "find network topology: $network_file"
    else 
        echo "Error: network topology not found: $network_file"
        exit 1
    fi    
    history   
    ## 获取完整tag
    tag="${tag}-${network}-${workload}"
    ## 输出文件
    outdir="$simdir/output/$tag"
    logfile="$outdir/output.log"
    rm -rf $outdir
    mkdir -p $outdir    
    ## 执行文件目录
    execfile="$simdir/bin/SimAI_simulator"

    # 2. 生成配置文件
    python3 $simdir/run_script/getConfig.py --tag $tag --config $simdir/run_script/simai_config.cfg --base_dir $simdir/output

    # 3. 复制配置文件到 tag 目录下，命名为 SimAI.conf
    cp $simdir/run_script/simai_config.cfg $outdir/SimAI.conf

    ## 复制 workload 和 network 文件到 tag 目录
    cp "$workload_file" "$outdir/$workload"
    cp $network_file $outdir/

    return 0
}

function history {
    # record history
    run_time=`date`
    command="[$run_time]\t$tag\t$workload\t$network\t${tag}-${network}-${workload}"
    echo -e $command >> $simdir/output/.history
    return 0
}

function notify {
    echo "============ Simulation finished ============="
    if [ $notice -eq 1 ]; then
        echo "Sending email notification..."
        python3 $simdir/run_script/notify.py --path $tag &&
        return 0
    fi
    return 0
}

function ready {
    # scripts
    # check
    for arg in "$@"; do
        case "$arg" in
        -r|--run)
            ;;
        -b|--build)
            ;;
        -l|--clean)
            ;;
        -br|--build-run)
            ;;
        -d|--debug)
            ;;
        -w|--workload)
            ;;
        -n|--network)
            ;;        
        -t|--thread)
            ;;  
        -tg|--tag)
            ;;                                                 
        -e|--email)
            ;;
        -h|--help|*)
            usage &&
            exit 0;;
        esac
    done

    return 0
}

function usage {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -r, --run           Run the simulation"
    echo "  -b, --build         Build the simulator"
    echo "  -l, --clean         Clean the build files"
    echo "  -br, --build-run    Build and then run the simulation"
    echo "  -d, --debug         Debug the simulator with gdb"
    echo "  -t, --thread        multi-thread numbers"
    echo "  -w, --workload      workload"
    echo "  -n, --network       network topology"
    echo "  -tg, --tag          output tag"
    # echo "  -e, --email        Send email notification upon completion"
    echo "  -h, --help          Display this help message"
}

########## Main Script ##########
### Default Config ###
# SimAI path
simdir="/home/dcn1/fxb/simulator"

# Tag {lb_mode}_{cc_mode} ecmp_dcqcn aps-v2_dcqcn rps_dcqcn reps_dcqcn
# tag="reps_crc32_dcqcn"
# tag="reps_murmur32_dcqcn"
# tag="reps_jenkins_dcqcn"
# tag="aletflow_mprdma"
# tag="aps-v2-murmur32_dcqcn"
# tag="aps-v2_mprdma"
# tag="aps-v2-o306_dcqcn"
# tag="aps-v2-o306_mprdma"
tag="psn_path_dcqcn"
# tag="rps_dcqcn"
# tag="reps_mprdma"
# tag="reps-symhash_mprdma"
# tag="reps-o306_dcqcn"
# tag="reps-o306_mprdma"
# tag="flowbender_dcqcn"
# tag="letflow_dcqcn"
# tag="ecmp_dcqcn"


# threads
threads=16
# Workload and Network
# microAllReduce_128g_TP2 microAllReduce_128g_TP2_256M
# microAllReduce_128g microAllReduce_1024g microAllReduce_1024g_512M
# microReduceScatter_1024g
# microAllReduce_1024g_6layer

# microAll2All_128g_EP8_8M microAll2All_128g_EP8_32M microAll2All_128g_EP8_64M microAll2All_128g_EP8_128M
# microAll2All_1024g_EP8_32M
workload="trace_test"

# Spectrum-X_32g_8gps_400Gbps_A100  
# AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100
# fattree_k8_128g_2gps_400Gbps_A100 fattree_k8_128g_2gps_400Gbps_A100_failure fattree_k8_128g_2gps_400Gbps_A100_asy
# fattree_k16_1024g_8gps_400Gbps_A100 fattree_k16_1024g_8gps_400Gbps_A100_failure fattree_k16_1024g_8gps_400Gbps_A100_asy
network="fattree_k8_128g_2gps_400Gbps_A100"

### Run ###

# detect switch arg
notice=0 # whether send email
for arg in "$@"; do
    case "$arg" in
    -e|--email)
        notice=1;;
    *)
        continue;;
    esac
done

# config
i=1
while [ $i -le $# ]; do
    # 获取当前索引对应的参数（${!i} 等价于 $i，但i是变量）
    current_arg="${!i}"

    case "$current_arg" in
        -r|--run)
            i=$((i + 1))  # 跳过值，移动到下一个参数
            ;;
        -b|--build)
            i=$((i + 1))  # 跳过值，移动到下一个参数
            ;;
        -l|--clean)
            i=$((i + 1))  # 跳过值，移动到下一个参数
            ;;
        -br|--build-run)
            i=$((i + 1))  # 跳过值，移动到下一个参数
            ;;
        -d|--debug)
            i=$((i + 1))  # 跳过值，移动到下一个参数
            ;;    
        -t|--thread)
            # 下一个参数是值（i+1）
            i=$((i + 1))  # 移动到值的位置
            threads="${!i}"   # 获取值
            i=$((i + 1))  # 跳过值，移动到下一个参数
            ;;
        -w|--workload)
            # 下一个参数是值
            i=$((i + 1))
            workload="${!i}"
            i=$((i + 1))
            ;;
        -n|--network)
            # 下一个参数是值
            i=$((i + 1))
            network="${!i}"
            i=$((i + 1))
            ;;  
        -tg|--tag)
            # 下一个参数是值
            i=$((i + 1))
            tag="${!i}"
            i=$((i + 1))
            ;;     
        -e|--email)
            notice=1
            i=$((i + 1))
            ;;
        -h|--help|*) 
            # 未知参数
            usage &&
            exit 0
            ;;                                       
            # 
    esac
done

# default env var AS_SEND_LAT=3 AS_NVLS_ENABLE=1
if [ -z "$AS_SEND_LAT" ]; then
    export AS_SEND_LAT=3
fi
# if [ -z "$AS_NVLS_ENABLE" ]; then
#     export AS_NVLS_ENABLE=1
# fi

# run
for arg in "$@"; do
    case "$arg" in
    -r|--run)
        run && exit 0;;
    -b|--build)
        build && exit 0;;
    -l|--clean)
        clean && exit 0;;
    -br|--build-run)
        build && run && exit 0;;
    -d|--debug)
        debug;;
    *)
        continue;;
    esac
done
