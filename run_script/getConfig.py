from dataclasses import dataclass, asdict, field
from typing import Dict, Any
import os


@dataclass
class SimAIConfig:
    # 基础功能开关
    ENABLE_QCN: int = 1
    USE_DYNAMIC_PFC_THRESHOLD: int = 1

    # 数据包参数
    PACKET_PAYLOAD_SIZE: int = 1000

    # 输出路径基目录
    base_output: str = ""

    # 文件路径（会根据 tag 自动生成）
    FLOW_FILE: str = ""
    FLOW_FILE: str = "/home/dell/sjw/lb/simulator/custom_trace/trace_test.txt"
    # FLOW_FILE: str = "/home/dell/sjw/lb/simulator/custom_trace/alltoall_128g_1MB.txt"
    TRACE_FILE: str = ""
    TRACE_OUTPUT_FILE: str = ""
    FCT_OUTPUT_FILE: str = ""
    PFC_OUTPUT_FILE: str = ""
    QLEN_MON_FILE: str = ""
    BW_MON_FILE: str = ""
    RATE_MON_FILE: str = ""
    OOO_MON_FILE: str = ""
    CNP_MON_FILE: str = ""
    SWITCH_FORWARD_OUTPUT_FILE: str = ""
    SEND_OUTPUT_FILE: str = ""
    OOO_BUFFER_OUTPUT_FILE: str = ""
    APS_SELECTED_OUTPUT_FILE: str = ""
    HASH_MON_FILE: str = ""

    # 监控参数 Interval 设为 0 表示关闭
    MON_START: int = 0
    MON_END: int = 2000000 # 2s 2000000 1000
    QP_MON_INTERVAL: int = 10 # us
    
    QLEN_MON_INTERVAL: int = 10 # us
    BW_MON_INTERVAL: int = 10 # us
    SWITCH_OUTPORT_MON_INTERVAL: int = 0 # 0: turn-off, other on
    # ns
    APS_SELECTED_MON_INTERVAL: int = 10000
    # traced node ID,  511[fat-tree, Spectrum], 14[fat-tree-128g]
    APS_SELECTED_TRACED_NODE: int = 511

    # 模拟器参数
    SIMULATOR_STOP_TIME: float = 40000000000000.00

    # 可靠传输
    RETRANS_TIME_OUT: int = 0 # ns, 0 means auto setting
    MAX_OOO_SIZE: int = 306
    DROP_RATE: float = 0.000 # 0.0~1.0

    # 负载均衡
    # ECMP APS run in a mix
    MIX_LB_RATIO: float = 0
    ## 0: ECMP, 1: APS, 2: RPS, 3: FlowBender, 4: LetFlow, 5: REPS, 6: PSN-PATH
    LB_MODE: int = 0
    HASH_TYPE: int = 0
    APS_PATH_CREDIT: int = 1 # credit buffer size
    APS_UPDATE_FREQUENCY: int = 1
    ## 3 bit mask for INT indicator, 001:ecn, 010:qlen, 100:util, ..., 111:all
    APS_INDICATOR_MASK: int = 7
    SWITCH_SAMPLE_TIME_INTERVAL: int = 1000
    FLOWBENDER_ECN_T: float = 0.05
    FLOWBENDER_SWITCH_N: int = 1
    LETFLOW_TIMEOUT: int = 500
    LETFLOW_AGING_TIME: int = 2
    REPS_BUFFER_SIZE: int = 8
    IOPS_BUFFER_SIZE: int = 8

    # 拥塞控制
    CC_MODE: int = 1 # dcqcn:1, dctcp:8, mprdma:11
    ALPHA_RESUME_INTERVAL: int = 1
    RATE_DECREASE_INTERVAL: int = 4
    CLAMP_TARGET_RATE: int = 0
    RP_TIMER: int = 900 # HPCC初始状态 900
    EWMA_GAIN: float = 0.00390625
    FAST_RECOVERY_TIMES: int = 1
    RATE_AI: str = "50Mb/s"
    RATE_HAI: str = "100Mb/s"
    MIN_RATE: str = "100Mb/s"
    DCTCP_RATE_AI: str = "1000Mb/s"

    # 链路层
    ERROR_RATE_PER_LINK: float = 0.0
    L2_CHUNK_SIZE: int = 4000
    L2_ACK_INTERVAL: int = 1
    L2_BACK_TO_ZERO: int = 0

    # 窗口控制
    HAS_WIN: int = 1 # 开启拥塞窗口控制（cwnd+inflight），例如mprdma，dcqcn+win，dctcp
    GLOBAL_T: int = 0
    VAR_WIN: int = 1
    OOO_ACK: int = 1 # 默认开启，开启时支持inflight乱序统计ACK，关闭时采用inflight = snd_nxt - snd_una（用于GoBackN）
    ACK_PSN: int = 1 # 默认开启，开启时ACK固定携带PSN，ACK的seq则表示收端的ePSN
    FAST_REACT: int = 1
    U_TARGET: float = 0.95
    MI_THRESH: int = 0
    INT_MULTI: int = 1
    MULTI_RATE: int = 0
    SAMPLE_FEEDBACK: int = 0
    PINT_LOG_BASE: float = 1.05
    PINT_PROB: float = 1.0

    # 限速
    RATE_BOUND: int = 1

    # ACK 优先级
    ACK_HIGH_PRIO: int = 0

    # 链路控制
    LINK_DOWN: str = "0 0 0" # "100 192 224"
    SWITCH_FAILURE: str = "/home/dell/sjw/lb/simulator/run_script/switch_failure.cfg"

    # trace 控制
    ENABLE_TRACE: int = 1
    ENABLE_OOO_TRACE: int = 0 # 需要时单独开启，否则存储占用过高

    # 映射参数
    KMAX_MAP: str = "6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400"
    KMIN_MAP: str = "6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600"
    PMAX_MAP: str = "6 25000000000 0.2 50000000000 0.2 100000000000 0.2 200000000000 0.8 400000000000 0.2 1600000000000 0.2"

    # 缓冲区
    BUFFER_SIZE: int = 32

    def apply_tag(self, tag: str, base_output: str):
        """根据 tag 更新所有输出文件路径"""
        self.base_output = base_output
        outdir = os.path.join(self.base_output, tag)
        os.makedirs(outdir, exist_ok=True)
        # self.FLOW_FILE = f"{outdir}/flow1.txt"
        self.TRACE_FILE = f"{outdir}/trace1.txt"
        self.TRACE_OUTPUT_FILE = f"{outdir}/mix.tr"
        self.FCT_OUTPUT_FILE = f"{outdir}/fct.txt"
        self.PFC_OUTPUT_FILE = f"{outdir}/pfc.txt"
        self.QLEN_MON_FILE = f"{outdir}/qlen.txt"
        self.BW_MON_FILE = f"{outdir}/bw.txt"
        self.RATE_MON_FILE = f"{outdir}/rate.txt"
        self.OOO_MON_FILE = f"{outdir}/ooo.txt"
        self.CNP_MON_FILE = f"{outdir}/cnp.txt"
        self.SWITCH_FORWARD_OUTPUT_FILE = f"{outdir}/switch_forward.txt"
        self.SEND_OUTPUT_FILE = f"{outdir}/send.txt"
        self.OOO_BUFFER_OUTPUT_FILE = f"{outdir}/ooo_buffer.txt"
        self.APS_SELECTED_OUTPUT_FILE = f"{outdir}/aps_selected.txt"
        self.HASH_MON_FILE = f"{outdir}/hash_mon.txt"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，保持 key 顺序"""
        return asdict(self)

    def save(self, filename: str = "simai_config.cfg"):
        """保存为配置文件"""
        with open(filename, "w") as f:
            for k, v in self.to_dict().items():
                if k == "base_output":  # 不写入配置文件
                    continue
                f.write(f"{k} {v}\n")
        print(f"配置文件已保存到 {filename}")


if __name__ == "__main__":
    
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", type=str, default="default", help="输出路径下的 tag 子目录")
    parser.add_argument("--base_dir", type=str, default="default", help="output base 输出路径")
    parser.add_argument("--config", type=str, default="default", help="config 输出路径")
    args = parser.parse_args()

    cfg = SimAIConfig()
    print("Created runing dir:",args.tag)
    cfg.apply_tag(args.tag, args.base_dir)
    cfg.save(args.config)

