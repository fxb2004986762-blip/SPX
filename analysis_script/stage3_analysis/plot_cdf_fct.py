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
OUT_NAME = "cdf_fct"
OUT_CNT = 0


# =========================
# FCT Column Config
# =========================
# 注意：这里是 Python 0-based 列索引。
# 对于样例：
# 307 179 10000 100 16777216 3015 1869790 ...
# 第 5 列索引 = 5，对应 3015，作为 start_time
# 第 6 列索引 = 6，对应 1869790，作为 end_time
FCT_START_COL = 5
FCT_END_COL = 6

# 输入时间单位与输出绘图单位
# 如果 fct.txt 中时间单位是 ns，绘制成 us，则使用 1000.0
# 如果 fct.txt 中时间单位已经是 us，则改为 1.0
TIME_DIVISOR = 1000.0
TIME_UNIT = "us"

# 是否过滤掉异常 FCT
DROP_NON_POSITIVE_FCT = True


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


def read_fct_file(path):
    """
    读取 fct.txt，并计算 FCT。

    fct = end_time - start_time

    默认使用 Python 0-based 列索引：
      start_time = 第 FCT_START_COL 列
      end_time   = 第 FCT_END_COL 列

    返回：
      fct_values: numpy array，单位为 TIME_UNIT
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
    if FCT_START_COL >= n_cols or FCT_END_COL >= n_cols:
        raise ValueError(
            f"Column index out of range in {path}: "
            f"n_cols={n_cols}, FCT_START_COL={FCT_START_COL}, FCT_END_COL={FCT_END_COL}"
        )

    start_time = pd.to_numeric(df.iloc[:, FCT_START_COL], errors="coerce")
    end_time = pd.to_numeric(df.iloc[:, FCT_END_COL], errors="coerce")

    valid = start_time.notna() & end_time.notna()
    start_time = start_time[valid]
    end_time = end_time[valid]

    fct = end_time - start_time

    n_total = len(fct)
    n_non_positive = int((fct <= 0).sum())

    if n_total == 0:
        raise ValueError(f"No valid start/end time records in {path}")

    if n_non_positive > 0:
        print(
            f"[Warning] {path}: detected {n_non_positive}/{n_total} non-positive FCT records."
        )

    if DROP_NON_POSITIVE_FCT:
        fct = fct[fct > 0]

    if len(fct) == 0:
        raise ValueError(
            f"All FCT records are non-positive in {path}. "
            f"Please check FCT_START_COL and FCT_END_COL."
        )

    fct = fct.to_numpy(dtype=float) / TIME_DIVISOR
    return fct


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
    给定 x，返回经验 CDF 中 FCT <= x 的比例。
    """
    idx = np.searchsorted(values_sorted, x, side="right")
    return idx / len(values_sorted)


def fmt_time(x):
    """
    格式化时间，避免标注过长。
    """
    if x >= 1000:
        return f"{x:.1f}"
    if x >= 100:
        return f"{x:.1f}"
    if x >= 10:
        return f"{x:.2f}"
    return f"{x:.3f}"


def annotate_point(ax, x, y, text, color, xytext):
    """
    标注一个 CDF 特征点。
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
        xytext=xytext,
        textcoords="offset points",
        fontsize=11,
        color=color,
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
            alpha=0.85,
        ),
    )

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

def plot_fct_cdf(fct_values, out_path, title=None):
    """
    绘制 FCT CDF，并标记 Avg、P95、P99。
    """
    values_sorted, cdf = compute_cdf(fct_values)

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
        label="FCT CDF",
    )

    annotate_point_inside(
        ax,
        avg,
        avg_y,
        f"Avg = {fmt_time(avg)} {TIME_UNIT}\nCDF = {avg_y:.3f}",
        AVG_COLOR,
        text_xy_axes=(0.55, 0.32),
        ha="center",
    )

    annotate_point_inside(
        ax,
        p95,
        p95_y,
        f"P95 = {fmt_time(p95)} {TIME_UNIT}",
        P95_COLOR,
        text_xy_axes=(0.98, 0.78),
        ha="right",
    )

    annotate_point_inside(
        ax,
        p99,
        p99_y,
        f"P99 = {fmt_time(p99)} {TIME_UNIT}",
        P99_COLOR,
        text_xy_axes=(0.98, 0.90),
        ha="right",
    )

    ax.set_xlabel(f"Flow Completion Time ({TIME_UNIT})")
    ax.set_ylabel("CDF")

    if title is not None:
        ax.set_title(title, pad=10)

    ax.set_ylim(0, 1.005)
    ax.set_xlim(left=0)

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
        f"Avg={avg:.6f} {TIME_UNIT}, "
        f"P95={p95:.6f} {TIME_UNIT}, "
        f"P99={p99:.6f} {TIME_UNIT}"
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

            if not os.path.exists(FCT_FILE):
                print(f"[{OUT_CNT}] Warning: fct.txt does not exist, skipping: {FCT_FILE}")
                continue

            out_path = os.path.join(
                OUT_DIR,
                f"{OUT_NAME}.png"
            )

            if os.path.exists(out_path):
                print(f"[{OUT_CNT}] Info: Image already exists, skipping: {out_path}")
                continue

            try:
                fct_values = read_fct_file(FCT_FILE)
            except Exception as e:
                print(f"[{OUT_CNT}] Error while reading {FCT_FILE}: {e}")
                continue

            title = f"{algo}"

            try:
                plot_fct_cdf(
                    fct_values=fct_values,
                    out_path=out_path,
                    title=title,
                )
            except Exception as e:
                print(f"[{OUT_CNT}] Error while plotting {FCT_FILE}: {e}")
                continue


if __name__ == "__main__":
    main()