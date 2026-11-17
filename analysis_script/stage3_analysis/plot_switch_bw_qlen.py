import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.lines import Line2D


matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42

# =========================
# User Config
# =========================
CONFIG_LIST = {


# "test-1024GPU": {
#     "0": "/home/dell/sjw/lb/simulator/output/12asy_topo/topology_type/spectrumx/allreduce/flowbender/flowbender_mprdma-SpectrumX_1024g_8gps_400Gbps_A100_asy-microAllReduce_1024g_2048M",
# },


}
# 如果本文件的CONFIG_LIST为空，则使用共享配置文件中的 CONFIG_LIST
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
if not CONFIG_LIST:
    from configs.result_path import CONFIG_LIST

BASE_DIR = ""
BW_FILE = os.path.join(BASE_DIR, "bw.txt")
QLEN_FILE = os.path.join(BASE_DIR, "qlen.txt")

OUT_DIR = BASE_DIR
OUT_NAME = "port_bw_qlen"
OUT_CNT = 0

# 绘图模式：
# "both"：同时绘制 bw 和 qlen，保持原始双 y 轴图像；
# "bw"：仅绘制 bw.txt 中的端口带宽；
# "qlen"：仅绘制 qlen.txt 中的队列长度。
PLOT_MODE = "both"   # "both" or "bw" or "qlen"

# 手动指定节点和端口范围
# leaf-spine_2048_128ToR
TARGET_NODE_IDS = [2304]       # bw.txt, qlen.txt 中的 node_id 1024GPU:1280, 1152 128GPU:192
TARGET_PORT_IDS =  [129,145,161,177,193,209,225,241]     # 需要绘制的端口 id 128GPU: [1,2,3,4] [5,6,7,8] 1024GPU: [9,10,11,12,13,14,15,16]


# fattree-1024
# TARGET_NODE_IDS = [1152, 1408, 1153, 1281, 1280]       # bw.txt, qlen.txt 中的 node_id 1024GPU:1280, 1152 128GPU:192
# TARGET_PORT_IDS =  [9,10,11,12,13,14,15,16]     # 需要绘制的端口 id 128GPU: [1,2,3,4] [5,6,7,8] 1024GPU: [9,10,11,12,13,14,15,16]

# fattree-128
# TARGET_NODE_IDS = [192, 193, 224, 225, 256]       # bw.txt, qlen.txt 中的 node_id 1024GPU:1280, 1152 128GPU:192
# TARGET_PORT_IDS =  [5,6,7,8]     # 需要绘制的端口 id 128GPU: [1,2,3,4] [5,6,7,8] 1024GPU: [9,10,11,12,13,14,15,16]

# hpn-1024
# TARGET_NODE_IDS = [1152, 1153]       # bw.txt, qlen.txt 中的 node_id 1024GPU:1280, 1152 128GPU:192
# TARGET_PORT_IDS =  [65,70,75,80,85,90]     # 需要绘制的端口 id 128GPU: [1,2,3,4] [5,6,7,8] 1024GPU: [9,10,11,12,13,14,15,16]

# spectrum-1024
# TARGET_NODE_IDS = [1152, 1153]       # bw.txt, qlen.txt 中的 node_id 1024GPU:1280, 1152 128GPU:192
# TARGET_PORT_IDS =  [65,73,81,89,96,105,113,121]     # 需要绘制的端口 id 128GPU: [1,2,3,4] [5,6,7,8] 1024GPU: [9,10,11,12,13,14,15,16]

# test
# TARGET_NODE_IDS = [1164, 1180]       # bw.txt, qlen.txt 中的 node_id 1024GPU:1280, 1152 128GPU:192
# TARGET_PORT_IDS =  [62, 65,70,75,80,85,90]     # 需要绘制的端口 id 128GPU: [1,2,3,4] [5,6,7,8] 1024GPU: [9,10,11,12,13,14,15,16]
# TARGET_NODE_IDS = [1156, 1172]       # bw.txt, qlen.txt 中的 node_id 1024GPU:1280, 1152 128GPU:192
# TARGET_PORT_IDS =  [30, 65,70,75,80,85,90]     # 需要绘制的端口 id 128GPU: [1,2,3,4] [5,6,7,8] 1024GPU: [9,10,11,12,13,14,15,16]
# TARGET_NODE_IDS = [1004, 236, 492, 364]       # bw.txt, qlen.txt 中的 node_id 1024GPU:1280, 1152 128GPU:192
# TARGET_NODE_IDS = [236, 492]       # bw.txt, qlen.txt 中的 node_id 1024GPU:1280, 1152 128GPU:192
# TARGET_PORT_IDS =  [2, 3]     # 需要绘制的端口 id 128GPU: [1,2,3,4] [5,6,7,8] 1024GPU: [9,10,11,12,13,14,15,16]

# TARGET_NODE_IDS = [1180]       # bw.txt, qlen.txt 中的 node_id 1024GPU:1280, 1152 128GPU:192
# TARGET_PORT_IDS =  [90]     # 需要绘制的端口 id 128GPU: [1,2,3,4] [5,6,7,8] 1024GPU: [9,10,11,12,13,14,15,16]
# TARGET_PORT_IDS =  [69,74,79,84,89,94]     # 需要绘制的端口 id 128GPU: [1,2,3,4] [5,6,7,8] 1024GPU: [9,10,11,12,13,14,15,16]
# TARGET_NODE_IDS = [1156, 1172]       # bw.txt, qlen.txt 中的 node_id 1024GPU:1280, 1152 128GPU:192
# TARGET_PORT_IDS =  [1]     # 需要绘制的端口 id 128GPU: [1,2,3,4] [5,6,7,8] 1024GPU: [9,10,11,12,13,14,15,16]
# TARGET_NODE_IDS = [1214]       # bw.txt, qlen.txt 中的 node_id 1024GPU:1280, 1152 128GPU:192
# TARGET_PORT_IDS = [5]       # bw.txt, qlen.txt 中的 node_id 1024GPU:1280, 1152 128GPU:192


# 时间范围，单位：us；None 表示不限制
TIME_START_US = None
TIME_END_US = None

# 补全采样间隔，单位：us
# 例如原始数据每 10us 或 100us 采样一次，这里就填对应值
SAMPLE_INTERVAL_US = 10

# 队列长度单位转换
# q_len / port_len 如果原始单位是 Byte，则设置为 "KB" 更直观
QUEUE_UNIT = "KB"   # "B" or "KB" or "MB"

# 绘制 qlen.txt 中的哪个字段
# "port_len" 表示端口总队列长度；"q_len" 表示单优先级队列长度
QUEUE_FIELD = "port_len"

# 如果 QUEUE_FIELD == "q_len"，可指定优先级队列
TARGET_Q_IDS = [3]

# =========================
# Style
# =========================
PORT_COLORS = [
    "#1b9e77",
    "#d95f02",
    "#7570b3",
    "#e7298a",
    "#66a61e",
    "#e6ab02",
    "#a6761d",
    "#666666",
]

plt.rcParams.update({
    "axes.titlesize": 16,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 11,
    "figure.titlesize": 18,
})


def read_csv_clean(path, columns):
    """
    读取带逗号分隔、可能包含空格和表头的数据文件。
    """
    df = pd.read_csv(path, comment="#", skipinitialspace=True)

    # 兼容可能存在的列名前后空格
    df.columns = [c.strip() for c in df.columns]

    # 如果文件没有标准表头，则重新读取
    if not all(c in df.columns for c in columns):
        df = pd.read_csv(
            path,
            header=None,
            names=columns,
            comment="#",
            skipinitialspace=True,
        )

    for c in columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=columns)
    return df


def queue_unit_convert(series):
    if QUEUE_UNIT == "B":
        return series
    if QUEUE_UNIT == "KB":
        return series / 1024.0
    if QUEUE_UNIT == "MB":
        return series / 1024.0 / 1024.0
    raise ValueError("QUEUE_UNIT must be one of: B, KB, MB")


def complete_timeseries(df, group_cols, value_col, time_col="time"):
    """
    对每个 group 独立补全时间序列。
    若某个时间戳缺失，则使用前一个时间戳的数据进行 forward-fill。
    """
    if df.empty:
        return df

    global_start = df[time_col].min() if TIME_START_US is None else TIME_START_US
    global_end = df[time_col].max() if TIME_END_US is None else TIME_END_US

    full_time_index = pd.Index(
        range(int(global_start), int(global_end) + 1, int(SAMPLE_INTERVAL_US)),
        name=time_col,
    )

    completed = []

    for keys, g in df.groupby(group_cols):
        g = g.sort_values(time_col).drop_duplicates(subset=[time_col], keep="last")
        g = g.set_index(time_col).reindex(full_time_index)

        # 恢复 group 列
        if not isinstance(keys, tuple):
            keys = (keys,)
        for col, key in zip(group_cols, keys):
            g[col] = key

        # 核心：缺失值使用前一个时间戳的值补全
        g[value_col] = g[value_col].ffill()

        # 如果序列开头缺失，用第一个有效值补齐，避免开头 NaN
        g[value_col] = g[value_col].bfill()

        g = g.reset_index()
        completed.append(g)

    return pd.concat(completed, ignore_index=True)


def filter_time(df):
    if TIME_START_US is not None:
        df = df[df["time"] >= TIME_START_US]
    if TIME_END_US is not None:
        df = df[df["time"] <= TIME_END_US]
    return df


def normalize_plot_mode():
    """
    规范化绘图模式，支持少量别名，避免手动配置时大小写或命名差异导致错误。
    """
    mode = str(PLOT_MODE).strip().lower()
    aliases = {
        "both": "both",
        "all": "both",
        "bw_qlen": "both",
        "bandwidth_queue": "both",
        "bw": "bw",
        "bandwidth": "bw",
        "qlen": "qlen",
        "queue": "qlen",
    }

    if mode not in aliases:
        raise ValueError(
            'PLOT_MODE must be one of: "both", "bw", "qlen" '
            '(aliases: "all", "bw_qlen", "bandwidth", "queue").'
        )
    return aliases[mode]


def need_plot_bw():
    return normalize_plot_mode() in ("both", "bw")


def need_plot_qlen():
    return normalize_plot_mode() in ("both", "qlen")


def get_output_png_path(sw_node):
    """
    默认 both 模式保持原始输出文件名不变；
    单独绘制 bw / qlen 时增加模式后缀，避免三种模式的图像互相覆盖。
    """
    mode = normalize_plot_mode()
    mode_suffix = "" if mode == "both" else f"_{mode}"
    return os.path.join(
        OUT_DIR,
        f"{OUT_NAME}{mode_suffix}_{sw_node}({TARGET_PORT_IDS[0]}-{TARGET_PORT_IDS[-1]}).png",
    )

# def collect_results(config):
#     """
#     Returns:
#       algorithms  – ordered list of algorithm names
#       sizes       – ordered list of traffic size labels
#       data        – dict[algo][size] = JCT_ms (float or nan)
#     """
#     algorithms = list(config.keys())
#     # Collect all unique sizes preserving insertion order
#     sizes_seen = {}
#     for algo in algorithms:
#         for sz in config[algo]:
#             sizes_seen[sz] = True
#     sizes = list(sizes_seen.keys())

#     data = {}
#     for algo in algorithms:
#         data[algo] = {}
#         for sz in sizes:
#             fp = config[algo].get(sz, None)
#             if fp is None:
#                 data[algo][sz] = float("nan")
#             else:
#                 print(f"  Parsing [{algo}][{sz}]: {fp}")
#                 data[algo][sz] = fp

#     return algorithms, sizes, data
def collect_results(config):
    """
    Automatically adapt to different CONFIG_LIST structures.

    Supported examples
    ------------------

    1. Two-level dictionary:

        {
            "aps-v2": {
                "1MB": "/path/a",
                "4MB": "/path/b",
            },
            "ecmp": {
                "1MB": "/path/c",
                "4MB": "/path/d",
            }
        }

        Returns:
            algorithms = ["aps-v2", "ecmp"]
            sizes      = ["1MB", "4MB"]

    2. One-level dictionary:

        {
            "1MB": "/path/a",
            "4MB": "/path/b",
            "8MB": "/path/c",
        }

        Returns:
            algorithms = ["default"]
            sizes      = ["1MB", "4MB", "8MB"]

    3. Deeper dictionary:

        {
            "aps-v2": {
                "sym": {
                    "1MB": "/path/a",
                    "4MB": "/path/b",
                }
            }
        }

        Returns:
            algorithms = ["aps-v2"]
            sizes      = ["sym/1MB", "sym/4MB"]

    Returns
    -------
    algorithms : ordered list of algorithm names

    sizes : ordered list of configuration/traffic-size labels

    data : dict[algo][size] = path or nan
    """

    if not isinstance(config, dict) or not config:
        return [], [], {}

    # ============================================================
    # Helper: recursively flatten all leaf paths
    # ============================================================
    def flatten_dict(d, prefix=()):
        """
        Convert nested dictionary into:

            [
                (("aps-v2", "1MB"), "/path/a"),
                (("aps-v2", "4MB"), "/path/b"),
                ...
            ]
        """
        results = []

        for key, value in d.items():
            current_keys = prefix + (str(key),)

            if isinstance(value, dict):
                results.extend(flatten_dict(value, current_keys))
            else:
                results.append((current_keys, value))

        return results

    flattened = flatten_dict(config)

    if not flattened:
        return [], [], {}

    # ============================================================
    # Detect dictionary structure
    # ============================================================
    depths = [len(keys) for keys, _ in flattened]
    max_depth = max(depths)

    # ------------------------------------------------------------
    # Case 1:
    # {
    #     "1MB": "/path/a",
    #     "4MB": "/path/b"
    # }
    #
    # No explicit algorithm level.
    # Treat all entries as belonging to one "default" algorithm.
    # ------------------------------------------------------------
    if max_depth == 1:
        algorithms = ["default"]

        sizes = []
        data = {
            "default": {}
        }

        for keys, fp in flattened:
            size = keys[0]

            sizes.append(size)

            print(f"  Parsing [default][{size}]: {fp}")
            data["default"][size] = fp

        return algorithms, sizes, data

    # ------------------------------------------------------------
    # Case 2+:
    #
    # First level is interpreted as algorithm.
    # Remaining levels are merged into one size/config label.
    #
    # Example:
    #
    # aps-v2 -> sym -> 1MB
    #
    # becomes:
    #
    # algorithm = aps-v2
    # size      = sym/1MB
    # ------------------------------------------------------------
    algorithms = []
    sizes_seen = {}

    parsed_entries = []

    for keys, fp in flattened:
        algo = keys[0]

        # Everything below algorithm becomes configuration label
        size = "/".join(keys[1:])

        if algo not in algorithms:
            algorithms.append(algo)

        if size not in sizes_seen:
            sizes_seen[size] = True

        parsed_entries.append((algo, size, fp))

    sizes = list(sizes_seen.keys())

    # ============================================================
    # Initialize matrix with NaN
    # ============================================================
    data = {}

    for algo in algorithms:
        data[algo] = {
            size: float("nan")
            for size in sizes
        }

    # ============================================================
    # Fill available entries
    # ============================================================
    for algo, size, fp in parsed_entries:
        print(f"  Parsing [{algo}][{size}]: {fp}")
        data[algo][size] = fp

    return algorithms, sizes, data


def main(sw_node):
    os.makedirs(OUT_DIR, exist_ok=True)

    mode = normalize_plot_mode()
    plot_bw = need_plot_bw()
    plot_qlen = need_plot_qlen()

    switch_node = [sw_node]
    bw = None
    qlen = None

    # =========================
    # 1. Load bandwidth data
    # =========================
    if plot_bw:
        bw = read_csv_clean(
            BW_FILE,
            ["time", "node_id", "port_id", "bandwidth"],
        )

        bw = bw[
            bw["node_id"].isin(switch_node)
            & bw["port_id"].isin(TARGET_PORT_IDS)
        ]
        bw = filter_time(bw)

        bw = complete_timeseries(
            bw,
            group_cols=["node_id", "port_id"],
            value_col="bandwidth",
        )
        bw["time"] = bw["time"] / 1000.0  # 转换为 us

    # =========================
    # 2. Load queue data
    # =========================
    if plot_qlen:
        qlen = read_csv_clean(
            QLEN_FILE,
            ["time", "sw_id", "port_id", "q_id", "q_len", "port_len"],
        )

        qlen = qlen[
            qlen["sw_id"].isin(switch_node)
            & qlen["port_id"].isin(TARGET_PORT_IDS)
        ]

        if QUEUE_FIELD == "q_len":
            qlen = qlen[qlen["q_id"].isin(TARGET_Q_IDS)]
            group_cols = ["sw_id", "port_id", "q_id"]
        else:
            # port_len 在同一个 time/sw/port 下会随 q_id 重复出现，只保留一份
            qlen = qlen.drop_duplicates(
                subset=["time", "sw_id", "port_id"],
                keep="last",
            )
            group_cols = ["sw_id", "port_id"]

        qlen = filter_time(qlen)

        qlen["queue_value"] = queue_unit_convert(qlen[QUEUE_FIELD])

        qlen = complete_timeseries(
            qlen,
            group_cols=group_cols,
            value_col="queue_value",
        )
        qlen["time"] = qlen["time"] / 1000.0  # 转换为 us

    # =========================
    # 3. Plot
    # =========================
    fig, ax1 = plt.subplots(figsize=(7.2, 4.8))
    # fig, ax1 = plt.subplots(figsize=(8.2, 5.8))

    if mode == "both":
        ax_bw = ax1
        ax_qlen = ax1.twinx()
    elif mode == "bw":
        ax_bw = ax1
        ax_qlen = None
    else:
        ax_bw = None
        ax_qlen = ax1

    port_list = sorted(TARGET_PORT_IDS)
    if len(port_list) > len(PORT_COLORS):
        raise ValueError("Number of target ports exceeds available colors.")

    port_color = {
        port: PORT_COLORS[i]
        for i, port in enumerate(port_list)
    }

    # ---- bandwidth lines ----
    if plot_bw:
        for (node_id, port_id), g in bw.groupby(["node_id", "port_id"]):
            ax_bw.plot(
                g["time"],
                g["bandwidth"],
                color=port_color[int(port_id)],
                linewidth=2,
                marker="o",
                markersize=3,
                # label=f"Port {int(port_id)} (BW)",
                label="_nolegend_",
            )

    # ---- queue lines ----
    if plot_qlen:
        if QUEUE_FIELD == "q_len":
            q_groups = qlen.groupby(["sw_id", "port_id", "q_id"])
            for (sw_id, port_id, q_id), g in q_groups:
                ax_qlen.plot(
                    g["time"],
                    g["queue_value"],
                    color=port_color[int(port_id)],
                    linewidth=2,
                    linestyle="--",
                    alpha=0.65,
                    label=f"Q sw {int(sw_id)} port {int(port_id)} q {int(q_id)}",
                )
        else:
            q_groups = qlen.groupby(["sw_id", "port_id"])
            for (sw_id, port_id), g in q_groups:
                ax_qlen.plot(
                    g["time"],
                    g["queue_value"],
                    color=port_color[int(port_id)],
                    linewidth=2,
                    linestyle="--",
                    alpha=0.65,
                    # label=f"Port {int(port_id)} (Q)",
                    label="_nolegend_",
                )

    ax1.set_xlabel("Time (us)")

    if mode == "both":
        ax_bw.set_ylabel("Port Throughput (Gbps)")
        ax_qlen.set_ylabel(f"Port Queue Length ({QUEUE_UNIT})")
        ax_bw.set_ylim(bottom=0)
        ax_qlen.set_ylim(bottom=0)
    elif mode == "bw":
        ax1.set_ylabel("Port Throughput (Gbps)")
        ax1.set_ylim(bottom=0)
    else:
        ax1.set_ylabel(f"Port Queue Length ({QUEUE_UNIT})")
        ax1.set_ylim(bottom=0)

    ax1.grid(True, which="both", linestyle=":", linewidth=0.75, alpha=0.75)

    # 让左轴曲线显示在右轴背景上方
    if mode == "both":
        ax_bw.set_zorder(ax_qlen.get_zorder() + 1)
        ax_bw.patch.set_visible(False)

    # 合并双 y 轴 legend
    # =========================
    # 4. Compact Legend Layout
    # =========================
    # 不再为每条曲线单独生成 legend。
    # 颜色表示端口，线型表示指标。
    port_handles = [
        Line2D(
            [0], [0],
            color=port_color[int(port_id)],
            linewidth=2.2,
            marker="o",
            markersize=4,
            linestyle="-",
            label=f"P{int(port_id)}",
        )
        for port_id in port_list
    ]

    metric_handles = []
    if plot_bw:
        metric_handles.append(
            Line2D(
                [0], [0],
                color="black",
                linewidth=2.2,
                marker="o",
                markersize=4,
                linestyle="-",
                label="BW",
            )
        )

    if plot_qlen:
        metric_handles.append(
            Line2D(
                [0], [0],
                color="black",
                linewidth=2.2,
                linestyle="--",
                label=f"Queue ({QUEUE_UNIT})",
            )
        )

    legend_handles = port_handles + metric_handles
    legend_labels = [h.get_label() for h in legend_handles]

    # 注意：这里不要使用 mode="expand"
    # mode="expand" 会强行拉伸列宽，在 item 较多时反而容易挤压文字。
    legend_ncol = len(TARGET_PORT_IDS) + len(metric_handles)
    if legend_ncol >= 10:
        legend_ncol = max(1, int((legend_ncol + 1) / 2))

    legend = fig.legend(
        legend_handles,
        legend_labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.985),
        ncol=legend_ncol,
        frameon=False,
        fontsize=10,
        handlelength=1.7,
        columnspacing=1.2,
        handletextpad=0.45,
        labelspacing=0.55,
        borderaxespad=0.0,
    )

    # 自适应计算 legend 高度，让绘图区尽量贴近 legend
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    legend_bbox = legend.get_window_extent(renderer=renderer)
    legend_bbox = legend_bbox.transformed(fig.transFigure.inverted())

    top_pad = 0.018
    adaptive_top = legend_bbox.y0 - top_pad

    adaptive_top = min(adaptive_top, 0.92)
    adaptive_top = max(adaptive_top, 0.70)

    fig.subplots_adjust(
        left=0.085,
        right=0.925,
        bottom=0.13,
        top=adaptive_top,
    )

    # ax1.legend(
    #     h1 + h2,
    #     l1 + l2,
    #     loc="upper center",
    #     bbox_to_anchor=(0.5, 1.22),
    #     ncol=4,
    #     frameon=False,
    # )

    # plt.tight_layout(rect=[0, 0, 1, 0.9])

    png_path = get_output_png_path(switch_node[0])
    # pdf_path = os.path.join(OUT_DIR, f"{OUT_NAME}_{switch_node[0]}({TARGET_PORT_IDS[0]}-{TARGET_PORT_IDS[-1]}).pdf")

    plt.savefig(
        png_path,
        bbox_inches="tight",
        pad_inches=0.025,
        dpi=300,
    )
    # plt.savefig(pdf_path, bbox_inches="tight")
    print(f"[{OUT_CNT}] Saved: {png_path}")
    # print(f"Saved: {pdf_path}")
    plt.close(fig)


if __name__ == "__main__":

    algo_name, size, data = collect_results(CONFIG_LIST)
    for i, sz in enumerate(size):
        for j, algo in enumerate(algo_name):
            BASE_DIR = data[algo_name[j]][sz]
            print(BASE_DIR)
            BW_FILE = os.path.join(BASE_DIR, "bw.txt")
            QLEN_FILE = os.path.join(BASE_DIR, "qlen.txt")
            OUT_DIR = BASE_DIR
            OUT_CNT += 1

            required_files = []
            if need_plot_bw():
                required_files.append(BW_FILE)
            if need_plot_qlen():
                required_files.append(QLEN_FILE)

            # 判断如果目录不存在则跳过
            missing_files = [fp for fp in required_files if not os.path.exists(fp)]
            if missing_files:
                print(f"[{OUT_CNT}] Warning: Required file(s) do not exist, skipping: {missing_files}")
                continue

            for sw_node in TARGET_NODE_IDS:
                # 判断如果图片已经存在也跳过
                png_path = get_output_png_path(sw_node)
                if os.path.exists(png_path):
                    print(f"[{OUT_CNT}] Info: Image already exists, skipping: {png_path}")
                    continue

                main(sw_node)
