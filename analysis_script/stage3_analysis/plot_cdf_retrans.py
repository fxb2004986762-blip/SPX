import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42


# =========================
# User Config
# =========================
CONFIG_LIST = {


}

# 如果本文件的 CONFIG_LIST 为空，则使用共享配置文件中的 CONFIG_LIST
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
if not CONFIG_LIST:
    from configs.result_path import CONFIG_LIST

BASE_DIR = ""
FCT_FILE = os.path.join(BASE_DIR, "fct.txt")

OUT_DIR = BASE_DIR
OUT_CNT = 0

# 是否覆盖已经存在的图片
OVERWRITE_EXISTING = False


# =========================
# FCT Column Config
# =========================
# 注意：这里是 Python 0-based 列索引。
#
# fct.txt 数据列含义示例：
# 599 87 10000 100 1048576 3015 174221 28182 2 0 0 0 1049 0 2
#
# 第 5 列：flow size bytes，索引为 4
# 第 10 列：timeout retransmitted packet count，索引为 9
# 第 12 列：total retransmitted packet count，索引为 11
FLOW_SIZE_COL = 4
RTO_RETRANS_PKT_COL = 9
TOTAL_RETRANS_PKT_COL = 11

# 单个数据包负载大小，单位 Bytes
# 注意：这里表示 payload size，不包含不同算法可能额外引入的包头开销
PACKET_PAYLOAD_BYTES = 1000.0

# 是否把比例绘制成百分比。
# True:  横轴单位为 %
# False: 横轴为原始比例，例如 0.01 表示 1%
PLOT_AS_PERCENT = True

# 是否过滤异常数据
DROP_NON_POSITIVE_FLOW_SIZE = True
DROP_NEGATIVE_RETRANS = True


# =========================
# Output Figure Names
# =========================
RTO_OUT_NAME = "cdf_rto.png"
TOTAL_RETRANS_OUT_NAME = "cdf_retrans.png"


# =========================
# Figure Style
# =========================
plt.rcParams.update({
    "axes.titlesize": 16,
    "axes.labelsize": 16,
    "xtick.labelsize": 13,
    "ytick.labelsize": 13,
    "legend.fontsize": 12,
    "figure.titlesize": 18,
})

FIG_WIDTH = 7.2
FIG_HEIGHT = 4.8

CDF_COLOR = "#1b9e77"
AVG_COLOR = "#d95f02"
P95_COLOR = "#7570b3"
P99_COLOR = "#e7298a"


def collect_results(config):
    """
    Returns:
      algorithms – ordered list of algorithm names
      sizes      – ordered list of traffic size labels
      data       – dict[algo][size] = experiment directory
    """
    algorithms = list(config.keys())

    sizes_seen = {}
    for algo in algorithms:
        for sz in config[algo]:
            sizes_seen[sz] = True
    sizes = list(sizes_seen.keys())

    data = {}
    for algo in algorithms:
        data[algo] = {}
        for sz in sizes:
            fp = config[algo].get(sz, None)
            if fp is None:
                data[algo][sz] = None
            else:
                print(f"  Parsing [{algo}][{sz}]: {fp}")
                data[algo][sz] = fp

    return algorithms, sizes, data


def read_retrans_ratio_file(path, retrans_col):
    """
    读取 fct.txt，并计算每条流量的重传数据包数量占总数据包数量的比例。

    计算方式：
      total_pkts = ceil(flow_size_bytes / PACKET_PAYLOAD_BYTES)
      retrans_ratio = retrans_pkts / total_pkts

    如果 PLOT_AS_PERCENT=True，则返回值乘以 100，单位为 %。

    这样计算只基于数据包数量，不把重传包数量换算成字节数，
    可以避免不同算法包头大小不同带来的统计偏差。

    Args:
      path: fct.txt 路径
      retrans_col: 重传包数量所在列，Python 0-based 索引

    Returns:
      ratio_values: numpy array
    """
    df = pd.read_csv(
        path,
        sep=r"\s+",
        header=None,
        comment="#",
        engine="python",
    )

    if df.empty:
        raise ValueError(f"Empty fct file: {path}")

    n_cols = df.shape[1]
    required_cols = [FLOW_SIZE_COL, retrans_col]
    for col in required_cols:
        if col >= n_cols:
            raise ValueError(
                f"Column index out of range in {path}: "
                f"n_cols={n_cols}, required_col={col}"
            )

    flow_size_bytes = pd.to_numeric(df.iloc[:, FLOW_SIZE_COL], errors="coerce")
    retrans_pkts = pd.to_numeric(df.iloc[:, retrans_col], errors="coerce")

    valid = flow_size_bytes.notna() & retrans_pkts.notna()

    if DROP_NON_POSITIVE_FLOW_SIZE:
        valid &= flow_size_bytes > 0

    if DROP_NEGATIVE_RETRANS:
        valid &= retrans_pkts >= 0

    n_total = len(df)
    n_valid = int(valid.sum())
    n_invalid = n_total - n_valid

    if n_valid == 0:
        raise ValueError(
            f"No valid records in {path}. "
            f"Please check FLOW_SIZE_COL={FLOW_SIZE_COL}, "
            f"retrans_col={retrans_col}."
        )

    if n_invalid > 0:
        print(f"[Warning] {path}: dropped {n_invalid}/{n_total} invalid records.")

    flow_size_bytes = flow_size_bytes[valid].astype(float).to_numpy()
    retrans_pkts = retrans_pkts[valid].astype(float).to_numpy()

    # 总数据包数量：流量总字节数 / 单包 payload，向上取整
    total_pkts = np.ceil(flow_size_bytes / PACKET_PAYLOAD_BYTES)

    # 理论上 total_pkts 不会为 0，因为已经过滤 flow_size_bytes > 0
    ratio = retrans_pkts / total_pkts

    if PLOT_AS_PERCENT:
        ratio = ratio * 100.0

    ratio_values = np.asarray(ratio, dtype=float)
    ratio_values = ratio_values[np.isfinite(ratio_values)]

    if len(ratio_values) == 0:
        raise ValueError(f"No finite retransmission ratio values in {path}.")

    return ratio_values


def compute_cdf(values):
    """
    计算 CDF 曲线。
    """
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]

    if len(values) == 0:
        raise ValueError("No finite values for CDF.")

    values_sorted = np.sort(values)
    cdf = np.arange(1, len(values_sorted) + 1) / len(values_sorted)

    return values_sorted, cdf


def get_cdf_y_at_x(values_sorted, x):
    """
    给定 x，返回经验 CDF 中 value <= x 的比例。
    """
    idx = np.searchsorted(values_sorted, x, side="right")
    return idx / len(values_sorted)


def fmt_ratio(x):
    """
    格式化比例，避免标注过长。
    """
    if PLOT_AS_PERCENT:
        if x >= 100:
            return f"{x:.1f}%"
        if x >= 10:
            return f"{x:.2f}%"
        if x >= 1:
            return f"{x:.3f}%"
        if x >= 0.01:
            return f"{x:.4f}%"
        return f"{x:.6f}%"
    else:
        if x >= 1:
            return f"{x:.3f}"
        if x >= 0.01:
            return f"{x:.5f}"
        return f"{x:.7f}"


def annotate_point_inside(
    ax,
    x,
    y,
    text,
    color,
    text_xy_axes,
    ha="right",
    va="center",
):
    """
    在 CDF 图中标注特征点。

    核心设计：
      - xy 使用 data 坐标，箭头指向真实数据点；
      - xytext 使用 axes fraction 坐标，保证文字框固定在图表内部；
      - ha='right' 时，文字从锚点向左展开，避免超出右边界。
    """
    ax.scatter(
        [x],
        [y],
        s=42,
        color=color,
        zorder=5,
    )

    ax.axvline(
        x=x,
        ymin=0,
        ymax=y,
        color=color,
        linestyle=":",
        linewidth=1.6,
        alpha=0.9,
    )

    ax.axhline(
        y=y,
        xmin=0,
        xmax=1,
        color=color,
        linestyle=":",
        linewidth=1.2,
        alpha=0.45,
    )

    ax.annotate(
        text,
        xy=(x, y),
        xycoords="data",
        xytext=text_xy_axes,
        textcoords="axes fraction",
        ha=ha,
        va=va,
        fontsize=11,
        color=color,
        annotation_clip=False,
        arrowprops=dict(
            arrowstyle="->",
            color=color,
            linewidth=1.1,
            shrinkA=0,
            shrinkB=4,
        ),
        bbox=dict(
            boxstyle="round,pad=0.25",
            fc="white",
            ec=color,
            lw=0.8,
            alpha=0.88,
        ),
    )


def plot_retrans_ratio_cdf(
    ratio_values,
    out_path,
    curve_label,
    x_label,
    title=None,
):
    """
    绘制重传数据包比例 CDF，并标记 Avg、P95、P99。
    """
    values_sorted, cdf = compute_cdf(ratio_values)

    avg = float(np.mean(values_sorted))
    p95 = float(np.percentile(values_sorted, 95))
    p99 = float(np.percentile(values_sorted, 99))

    avg_y = get_cdf_y_at_x(values_sorted, avg)
    p95_y = get_cdf_y_at_x(values_sorted, p95)
    p99_y = get_cdf_y_at_x(values_sorted, p99)

    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))

    ax.plot(
        values_sorted,
        cdf,
        color=CDF_COLOR,
        linewidth=2.4,
        label=curve_label,
    )

    annotate_point_inside(
        ax,
        avg,
        avg_y,
        f"Avg = {fmt_ratio(avg)}\nCDF = {avg_y:.3f}",
        AVG_COLOR,
        text_xy_axes=(0.55, 0.32),
        ha="center",
    )

    annotate_point_inside(
        ax,
        p95,
        p95_y,
        f"P95 = {fmt_ratio(p95)}",
        P95_COLOR,
        text_xy_axes=(0.98, 0.78),
        ha="right",
    )

    annotate_point_inside(
        ax,
        p99,
        p99_y,
        f"P99 = {fmt_ratio(p99)}",
        P99_COLOR,
        text_xy_axes=(0.98, 0.90),
        ha="right",
    )

    ax.set_xlabel(x_label)
    ax.set_ylabel("CDF")

    if title is not None:
        ax.set_title(title, pad=10)

    ax.set_ylim(0, 1.005)
    ax.set_xlim(left=0)

    # 避免所有值都为 0 时，x 轴范围异常
    xmax = float(np.max(values_sorted))
    if xmax <= 0:
        ax.set_xlim(0, 1.0 if PLOT_AS_PERCENT else 0.01)

    ax.grid(
        True,
        which="both",
        linestyle=":",
        linewidth=0.75,
        alpha=0.75,
    )

    ax.legend(
        loc="lower right",
        frameon=False,
        handlelength=2.0,
    )

    fig.subplots_adjust(
        left=0.13,
        right=0.97,
        bottom=0.15,
        top=0.92,
    )

    plt.savefig(
        out_path,
        bbox_inches="tight",
        pad_inches=0.025,
        dpi=300,
    )

    plt.close(fig)

    unit = "%" if PLOT_AS_PERCENT else ""
    print(f"Saved: {out_path}")
    print(
        f"  #flows={len(values_sorted)}, "
        f"Avg={avg:.8f}{unit}, "
        f"P95={p95:.8f}{unit}, "
        f"P99={p99:.8f}{unit}, "
        f"Max={float(np.max(values_sorted)):.8f}{unit}"
    )


def plot_one_metric(
    fct_file,
    out_path,
    retrans_col,
    curve_label,
    x_label,
    title,
):
    """
    读取一个重传指标并绘制 CDF。
    """
    if os.path.exists(out_path) and not OVERWRITE_EXISTING:
        print(f"Info: Image already exists, skipping: {out_path}")
        return

    ratio_values = read_retrans_ratio_file(
        path=fct_file,
        retrans_col=retrans_col,
    )

    plot_retrans_ratio_cdf(
        ratio_values=ratio_values,
        out_path=out_path,
        curve_label=curve_label,
        x_label=x_label,
        title=title,
    )


def main():
    global BASE_DIR, FCT_FILE, OUT_DIR, OUT_CNT

    algo_name, size, data = collect_results(CONFIG_LIST)

    for sz in size:
        for algo in algo_name:
            BASE_DIR = data[algo].get(sz, None)

            if BASE_DIR is None:
                continue

            FCT_FILE = os.path.join(BASE_DIR, "fct.txt")
            OUT_DIR = BASE_DIR
            OUT_CNT += 1

            print(f"\n[{OUT_CNT}] Processing: algo={algo}, size={sz}")
            print(f"  FCT_FILE: {FCT_FILE}")

            if not os.path.exists(FCT_FILE):
                print(f"[{OUT_CNT}] Warning: fct.txt does not exist, skipping: {FCT_FILE}")
                continue

            rto_out_path = os.path.join(OUT_DIR, RTO_OUT_NAME)
            total_retrans_out_path = os.path.join(OUT_DIR, TOTAL_RETRANS_OUT_NAME)

            # 图 1：第 10 列，超时重传数据包占比
            try:
                plot_one_metric(
                    fct_file=FCT_FILE,
                    out_path=rto_out_path,
                    retrans_col=RTO_RETRANS_PKT_COL,
                    curve_label="RTO Retransmission Ratio CDF",
                    x_label=(
                        "RTO Retransmitted Packets / Total Packets (%)"
                        if PLOT_AS_PERCENT
                        else "RTO Retransmitted Packets / Total Packets"
                    ),
                    title=f"{algo}",
                )
            except Exception as e:
                print(f"[{OUT_CNT}] Error while plotting RTO ratio for {FCT_FILE}: {e}")

            # 图 2：第 12 列，总重传数据包占比
            try:
                plot_one_metric(
                    fct_file=FCT_FILE,
                    out_path=total_retrans_out_path,
                    retrans_col=TOTAL_RETRANS_PKT_COL,
                    curve_label="Total Retransmission Ratio CDF",
                    x_label=(
                        "Total Retransmitted Packets / Total Packets (%)"
                        if PLOT_AS_PERCENT
                        else "Total Retransmitted Packets / Total Packets"
                    ),
                    title=f"{algo}",
                )
            except Exception as e:
                print(f"[{OUT_CNT}] Error while plotting total retransmission ratio for {FCT_FILE}: {e}")


if __name__ == "__main__":
    main()