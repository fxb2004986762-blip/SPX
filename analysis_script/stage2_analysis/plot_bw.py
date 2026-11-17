"""
多负载均衡算法下整网 NIC 平均吞吐随时间变化的可视化脚本

功能说明：
- 读取网络仿真生成的 bw.txt 文件，对比多种负载均衡算法的性能。
- 仅统计 NIC 节点（node_id ∈ [0, 1023]），NIC 总数固定为 1024。
- 时间按 10us 粒度离散：
    - 某 NIC 在某时间窗口无数据时，其吞吐记为 0；
    - 同一时间窗口内多条记录取平均。
- 在每个时间窗口上，对所有 NIC 的吞吐求平均，得到整网平均吞吐。

绘图与输出：
- 横轴：时间（ms），主刻度间隔 2 ms；
- 纵轴：平均 NIC 吞吐（Gbps），主刻度间隔 100 Gbps；
- 支持多算法曲线对比，输出论文级 PDF 矢量图。
- 同时输出各算法在全时间范围内的平均吞吐，用于定量对比或表格展示。
"""

import pandas as pd
import numpy as np
from matplotlib.ticker import MultipleLocator
import matplotlib.pyplot as plt
import os

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "axes.linewidth": 1.2,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

NIC_NUM = 1024
TIME_BIN_US = 10   # bucket us
XAXIS_LOCATOR = 5 # x轴刻度间隔 ms
# MAX_TIME_BIN = 30000 # us，截取前 10ms 数据

def load_avg_bw_over_time(bw_file, nic_max_id=NIC_NUM - 1):
    df = pd.read_csv(bw_file, skipinitialspace=True)

    # 仅保留 NIC
    df = df[df["node_id"] <= nic_max_id]

    # time: ns -> us
    df["time_us"] = df["time"] / 1000.0
    df["time_bin"] = (df["time_us"] // TIME_BIN_US).astype(int)

    # 截取前 ms 数据
    # max_time_bin = int(MAX_TIME_BIN / TIME_BIN_US)
    # df = df[df["time_bin"] <= max_time_bin]

    # 每 (time_bin, node_id) 取平均
    per_nic = (
        df.groupby(["time_bin", "node_id"])["bandwidth"]
        .mean()
        .reset_index()
    )

    # 构造截断的 time_bin × NIC
    # all_time_bins = np.arange(
    #     per_nic["time_bin"].min(),
    #     max_time_bin
    # )

    # 构造完整 time_bin × NIC 
    all_time_bins = np.arange( per_nic["time_bin"].min(), per_nic["time_bin"].max() + 1 )

    full_index = pd.MultiIndex.from_product(
        [all_time_bins, range(NIC_NUM)],
        names=["time_bin", "node_id"]
    )

    per_nic = (
        per_nic
        .set_index(["time_bin", "node_id"])
        .reindex(full_index, fill_value=0)
        .reset_index()
    )

    avg_bw = (
        per_nic
        .groupby("time_bin")["bandwidth"]
        .mean()
        .reset_index()
    )

    avg_bw["time_ms"] = avg_bw["time_bin"] * TIME_BIN_US / 1000.0

    return avg_bw[["time_ms", "bandwidth"]]




def evaluate_and_plot(
    algo_files: dict,
    out_pdf: str
):
    """
    algo_files:
        {
            "ECMP": "ecmp/bw.txt",
            "APS":  "aps/bw.txt",
            "XXX":  "xxx/bw.txt"
        }
    """
    plt.figure(figsize=(6.5, 3.5))

    ax = plt.gca()
    results = {}

    # 如果 bw_file 中的目录不存在，直接报错返回
    if not all([os.path.exists(f) for f in algo_files.values()]):
        missing_files = [f for f in algo_files.values() if not os.path.exists(f)]
        raise FileNotFoundError(f"以下 bw.txt 文件不存在：{missing_files}")

    for algo_name, file_dir in algo_files.items():
        bw_file = file_dir + "/bw.txt"
        avg_bw = load_avg_bw_over_time(bw_file)

        # 全时间平均吞吐
        overall_avg = avg_bw["bandwidth"].mean()
        results[algo_name] = overall_avg

        if algo_name in baseline:
            ax.plot(
                avg_bw["time_ms"],
                avg_bw["bandwidth"],
                linewidth=2,
                linestyle="--",
                label=algo_name
            )
        else:
            ax.plot(
                avg_bw["time_ms"],
                avg_bw["bandwidth"],
                linewidth=2,
                label=algo_name
            )

    # 坐标轴格式
    ax.set_xlabel("Time (ms)", fontsize=11)
    ax.set_ylabel("Average NIC Throughput (Gbps)", fontsize=11)

    # 根据数据范围自适应调整x轴刻度间隔
    if avg_bw["time_ms"].max() <= 2:
        x_locator = 0.1
    elif avg_bw["time_ms"].max() <= 5:
        x_locator = 0.5
    elif avg_bw["time_ms"].max() <= 10:
        x_locator = 1
    elif avg_bw["time_ms"].max() <= 50:
        x_locator = 5
    elif avg_bw["time_ms"].max() <= 100:
        x_locator = 10
    elif avg_bw["time_ms"].max() <= 500:
        x_locator = 50
    elif avg_bw["time_ms"].max() <= 1000:
        x_locator = 100
    elif avg_bw["time_ms"].max() <= 5000:
        x_locator = 500
    else:
        x_locator = XAXIS_LOCATOR


    ax.xaxis.set_major_locator(MultipleLocator(x_locator))     # 1 ms
    ax.yaxis.set_major_locator(MultipleLocator(50))   # 100 Gbps

    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
    ax.legend(
    ncol=2,                 # 两列
    frameon=False,
    fontsize=10,
    # loc="upper center",     # 上方居中
    # bbox_to_anchor=(0.5, 1.15)
    )

    plt.tight_layout()
    plt.savefig(out_pdf, format="pdf")
    plt.close()

    return results

if __name__ == "__main__":

    # algo_files = {
    #     # "aps-v2": "/home/dcn1/fxb/simulator/output/aps-v2-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
    #     "aps-v2-c2": "/home/dcn1/fxb/simulator/output/aps-v2-c2-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
    #     "aps-v2-c4": "/home/dcn1/fxb/simulator/output/aps-v2-c4-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
    #     # "aps-v2-c8": "/home/dcn1/fxb/simulator/output/aps-v2-c8-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
    #     # "aps-v2-eq": "/home/dcn1/fxb/simulator/output/aps-v2-eq-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
    #     "aps-v2-eq-c2": "/home/dcn1/fxb/simulator/output/aps-v2-eq-c2-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
    #     "aps-v2-eq-c4": "/home/dcn1/fxb/simulator/output/aps-v2-eq-c4-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
    #     # "aps-v2-eq-c8": "/home/dcn1/fxb/simulator/output/aps-v2-eq-c8-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
    #     "aps-v2-q-c4": "/home/dcn1/fxb/simulator/output/aps-v2-q-c4-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
    #     "rps": "/home/dcn1/fxb/simulator/output/rps-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
    #     "ecmp": "/home/dcn1/fxb/simulator/output/ecmp-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M"
    # }
    # algo_files = {
    #     "aps-v2-f1": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
    #     "aps-v2-f4": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f4_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
    #     "aps": "/home/dcn1/fxb/simulator/output/aps-b64_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
    #     "rps": "/home/dcn1/fxb/simulator/output/6int-class-full/rps/rps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
    #     "ecmp": "/home/dcn1/fxb/simulator/output/6int-class-full/ecmp/ecmp_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
    #     "flowbender": "/home/dcn1/fxb/simulator/output/6int-class-full/flowbender/flowbender_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
    #     "letflow": "/home/dcn1/fxb/simulator/output/6int-class-full/letflow/letflow_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
    # }
    # algo_files = {
    #     "aps-v2-b0": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b0_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    #     "aps-v2-b4": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    #     "aps-v2-b8": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b8_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    #     "aps-v2-b16": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b16_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    #     "aps-v2-b32": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b32_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    #     "aps-v2-b64": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b64_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    #     "rps-b0": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b0_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    # }
    # algo_files = {
    #     "aps-v2-b0": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b0_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    #     "aps-v2-b4": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    #     "aps-v2-b8": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b8_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    #     "aps-v2-b16": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b16_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    #     "aps-v2-b32": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b32_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    #     "aps-v2-b64": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b64_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    #     "aps-v2-b306": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b306_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    #     "rps-b0": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b0_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    #     "rps-b4": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    #     "rps-b8": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b8_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    #     "rps-b16": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b16_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    #     "rps-b32": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b32_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    #     "rps-b64": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b64_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
    #     "rps-b306": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b306_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M"
    # }
    # algo_files = {
    #     "aps-v2-b4-8MB": "/home/dcn1/fxb/simulator/output/aps-v2-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAll2All_1024g_EP8_8M",
    #     "aps-v2-b4-32MB": "/home/dcn1/fxb/simulator/output/aps-v2-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAll2All_1024g_EP8_32M"
    # }
    # algo_files = {
    #     "aps-v2-qu-f1": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
    #     "aps-v2-qu-f4": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f4_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
    #     "aps-v2-qu-f8": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f8_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
    #     "aps-v2-qu-f16": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f16_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
    #     "aps-v2-qu-f32": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f32_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
    #     "aps-v2-qu-f64": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f64_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
    #     "aps-v2-qu-f306": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f306_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
    #     "rps": "/home/dcn1/fxb/simulator/output/6int-class-full/rps/rps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
    #     "ecmp": "/home/dcn1/fxb/simulator/output/6int-class-full/ecmp/ecmp_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
    #     "flowbender": "/home/dcn1/fxb/simulator/output/6int-class-full/flowbender/flowbender_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
    #     "letflow": "/home/dcn1/fxb/simulator/output/6int-class-full/letflow/letflow_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
    # }


    algo_files = {
        "aps-v2": "/home/dcn1/fxb/simulator/output/3lb-class/aps-v2/All-to-All/aps-v2_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_64M",
        "rps": "/home/dcn1/fxb/simulator/output/3lb-class/rps/All-to-All/rps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_64M",
        # "aps": "/home/dcn1/fxb/simulator/output/3lb-class/aps/aps-b64_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
        "reps": "/home/dcn1/fxb/simulator/output/3lb-class/reps/reps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_64M",
        "ecmp": "/home/dcn1/fxb/simulator/output/3lb-class/ecmp/ecmp_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_64M",
        # "flowbender": "/home/dcn1/fxb/simulator/output/6int-class-full/flowbender/flowbender_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
        # "letflow": "/home/dcn1/fxb/simulator/output/6int-class-full/letflow/letflow_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",

    }
    out_dir = "/home/dcn1/fxb/simulator/output/1all_figures"
    out_file = out_dir + "/bw_baseline_all2all_8MBpf.txt"
    out_pdf_file = out_dir + "/bw_baseline_all2all_8MBpf.pdf"


    # out_dir = "/home/dcn1/fxb/simulator/output/1all_figures"
    # out_file = out_dir + "/32MB_nic_bw.txt"
    # out_pdf_file = out_dir + "/32MB_nic_bw.pdf"

    baseline = ["rps", "ecmp", "flowbender", "letflow"]
    baseline = ["rps", "ecmp"]


    avg_results = evaluate_and_plot(
        algo_files,
        out_pdf=out_pdf_file
    )

    with open(out_file, "w") as f:
        f.write("Algorithm\tAverage NIC Throughput (Gbps)\n")
        for algo, bw in avg_results.items():
            f.write(f"{algo}\t{bw:.2f} Gbps\n")
    # 输出全时间平均吞吐（论文可直接引用）
    print("Overall Average NIC Throughput:")
    for algo, bw in avg_results.items():
        print(f"{algo:10s}: {bw:.2f} Gbps")
