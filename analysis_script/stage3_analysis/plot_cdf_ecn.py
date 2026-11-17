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
# 使用方式 1：批量绘图
#   将你原脚本中的 CONFIG_LIST 原样粘贴到这里即可。
#
# 使用方式 2：单目录绘图
#   保持 CONFIG_LIST = {}，并设置 BASE_DIR 为某个实验输出目录。
CONFIG_LIST = {

}
# 如果本文件的CONFIG_LIST为空，则使用共享配置文件中的 CONFIG_LIST
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
if not CONFIG_LIST:
    from configs.result_path import CONFIG_LIST

BASE_DIR = ""
FCT_FILE = os.path.join(BASE_DIR, "fct.txt")

OUT_DIR = BASE_DIR
OUT_NAME = "cdf_ecn"
OUT_CNT = 0


# =========================
# ECN Column Config
# =========================
# 注意：这里是 Python 0-based 列索引。
# -1 表示最后一列。
# 对于样例数据，最后一列为一条流量完成时累计接收的 ECN 数量。
ECN_COUNT_COL = -1

# 是否过滤掉异常 ECN 数量
# ECN 数量允许为 0，但不应为负数。
DROP_NEGATIVE_ECN = True


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

# 是否覆盖已有图片
OVERWRITE = False


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


def read_ecn_file(path):
    """
    读取 fct.txt，并提取最后一列 ECN 累计数量。

    返回：
      ecn_values: numpy array，单位为 count
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

    # 支持负数列索引，例如 -1 表示最后一列。
    col = ECN_COUNT_COL
    if col < 0:
        col = n_cols + col

    if col < 0 or col >= n_cols:
        raise ValueError(
            f"Column index out of range in {path}: "
            f"n_cols={n_cols}, ECN_COUNT_COL={ECN_COUNT_COL}"
        )

    ecn_count = pd.to_numeric(df.iloc[:, col], errors="coerce")

    n_total = len(ecn_count)
    n_nan = int(ecn_count.isna().sum())

    if n_nan > 0:
        print(f"[Warning] {path}: detected {n_nan}/{n_total} NaN ECN records.")

    ecn_count = ecn_count.dropna()

    if len(ecn_count) == 0:
        raise ValueError(f"No valid ECN count records in {path}")

    n_negative = int((ecn_count < 0).sum())
    if n_negative > 0:
        print(
            f"[Warning] {path}: detected {n_negative}/{len(ecn_count)} "
            f"negative ECN count records."
        )

    if DROP_NEGATIVE_ECN:
        ecn_count = ecn_count[ecn_count >= 0]

    if len(ecn_count) == 0:
        raise ValueError(
            f"All ECN count records are negative in {path}. "
            f"Please check ECN_COUNT_COL."
        )

    return ecn_count.to_numpy(dtype=float)


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
    给定 x，返回经验 CDF 中 ECN count <= x 的比例。
    """
    idx = np.searchsorted(values_sorted, x, side="right")
    return idx / len(values_sorted)


def fmt_count(x):
    """
    格式化 ECN 数量。
    percentile 可能因为插值产生小数，因此这里保留必要的小数。
    """
    if abs(x - round(x)) < 1e-9:
        return f"{int(round(x))}"
    if x >= 100:
        return f"{x:.1f}"
    if x >= 10:
        return f"{x:.2f}"
    return f"{x:.3f}"


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


def plot_ecn_cdf(ecn_values, out_path, title=None):
    """
    绘制 ECN 数量分布 CDF，并标记 Avg、P95、P99。
    """
    values_sorted, cdf = compute_cdf(ecn_values)

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
        label="ECN Count CDF",
    )

    annotate_point_inside(
        ax,
        avg,
        avg_y,
        f"Avg = {fmt_count(avg)}\nCDF = {avg_y:.3f}",
        AVG_COLOR,
        text_xy_axes=(0.55, 0.32),
        ha="center",
    )

    annotate_point_inside(
        ax,
        p95,
        p95_y,
        f"P95 = {fmt_count(p95)}",
        P95_COLOR,
        text_xy_axes=(0.98, 0.78),
        ha="right",
    )

    annotate_point_inside(
        ax,
        p99,
        p99_y,
        f"P99 = {fmt_count(p99)}",
        P99_COLOR,
        text_xy_axes=(0.98, 0.90),
        ha="right",
    )

    ax.set_xlabel("Cumulative ECN Count per Flow")
    ax.set_ylabel("CDF")

    if title is not None:
        ax.set_title(title, pad=10)

    ax.set_ylim(0, 1.005)

    x_min = float(np.min(values_sorted))
    x_max = float(np.max(values_sorted))

    if x_min >= 0:
        x_left = 0
    else:
        x_left = x_min * 1.05

    x_right = x_max * 1.05 if x_max > 0 else 1.0
    if x_right <= x_left:
        x_right = x_left + 1.0

    ax.set_xlim(left=x_left, right=x_right)

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

    print(f"Saved: {out_path}")
    print(
        f"  #flows={len(values_sorted)}, "
        f"Avg={avg:.6f}, "
        f"P95={p95:.6f}, "
        f"P99={p99:.6f}"
    )


def plot_one_dir(base_dir, title=None):
    """
    对单个实验目录绘图。
    """
    fct_file = os.path.join(base_dir, "fct.txt")
    out_path = os.path.join(base_dir, f"{OUT_NAME}.png")

    if not os.path.exists(fct_file):
        print(f"Warning: fct.txt does not exist, skipping: {fct_file}")
        return

    if os.path.exists(out_path) and not OVERWRITE:
        print(f"Info: Image already exists, skipping: {out_path}")
        return

    try:
        ecn_values = read_ecn_file(fct_file)
    except Exception as e:
        print(f"Error while reading {fct_file}: {e}")
        return

    try:
        plot_ecn_cdf(
            ecn_values=ecn_values,
            out_path=out_path,
            title=title,
        )
    except Exception as e:
        print(f"Error while plotting {fct_file}: {e}")
        return


def main():
    global BASE_DIR, OUT_CNT

    # 批量模式：使用 CONFIG_LIST
    if len(CONFIG_LIST) > 0:
        algo_name, size, data = collect_results(CONFIG_LIST)

        for sz in size:
            for algo in algo_name:
                BASE_DIR = data[algo].get(sz, None)

                if BASE_DIR is None:
                    continue

                OUT_CNT += 1
                title = f"{algo}"

                print(f"[{OUT_CNT}] Processing: {title}")
                plot_one_dir(BASE_DIR, title=title)

    # 单目录模式：直接读取 BASE_DIR/fct.txt
    else:
        if BASE_DIR == "":
            BASE_DIR = "."
        print(f"Processing single directory: {BASE_DIR}")
        plot_one_dir(BASE_DIR, title=None)


if __name__ == "__main__":
    main()