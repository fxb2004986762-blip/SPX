"""
Plot Job Completion Time (JCT) of different load-balancing algorithms
under different workload/message sizes.

Data input format is kept consistent with the original script:
  CONFIG = {
      "Algorithm Name": {
          "traffic_size_label": "path/to/experiment_dir_or_fct.txt",
          ...
      },
      ...
  }

For each experiment, this script reads `fct.txt` and computes the collective JCT as:
  JCT = max(start_time + duration) - min(start_time)
where start_time is column 6 and duration is column 7 in each FCT record.
The reported unit is milliseconds.

Usage:
  1. Edit CONFIG / OUTPUT_DIR / OUTPUT_PREFIX.
  2. Run: python plot_jct_workload_scaling.py
"""

import csv
import math
import os
import re
from collections import OrderedDict

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# USER CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────
CONFIG_LIST = {

}

# 如果本文件的CONFIG_LIST为空，则使用共享配置文件中的 CONFIG_LIST
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
if not CONFIG_LIST:
    from configs.result_path import CONFIG_LIST


def field_exists_in_any_path(data_dict, field):
    """
    判断某个字段是否存在于字典中的任意一个目录字符串中。

    参数:
        data_dict: 输出字典，可以是一层字典，也可以是嵌套字典
        field: 要查找的字段字符串

    返回:
        True: 至少有一个路径中包含该字段
        False: 所有路径中都不包含该字段
    """

    for value in data_dict.values():
        if isinstance(value, dict):
            if field_exists_in_any_path(value, field):
                return True
        elif isinstance(value, str):
            if field in value:
                return True
    return False

def get_output_dir(data_dict):
    for value in data_dict.values():
        if isinstance(value, dict):
            result = get_output_dir(value)
            if result != "NONE":
                return str(Path(result).parents[1])
        elif isinstance(value, str):
            return value
    return "NONE"

OUTPUT_DIR = get_output_dir(CONFIG_LIST)

if field_exists_in_any_path(CONFIG_LIST, "dcqcn"):
    CC_ALGOS = "dcqcn"
elif field_exists_in_any_path(CONFIG_LIST, "mprdma"):
    CC_ALGOS = "mprdma"
else:
    print("No valid congestion control algorithm found.")
    exit(1)

if field_exists_in_any_path(CONFIG_LIST, "allreduce"):
    OUTPUT_PREFIX = "jct_fattree_1024g_allreduce" + "_" + CC_ALGOS
    WORKLOAD_NAME = "Ring-AllReduce"
elif field_exists_in_any_path(CONFIG_LIST, "All2All"):
    OUTPUT_PREFIX = "jct_fattree_1024g_alltoall" + "_" + CC_ALGOS
    WORKLOAD_NAME = "AlltoAll"
else:
    print("No valid workload type found.")
    exit(1)


# Set to None if no algorithm should be visually emphasized.
HIGHLIGHT_ALGO = "aps-v2"

# Optional: also dump the parsed JCT values into a CSV file for sanity check.
SAVE_CSV = True

# Use log2 x-axis when workload labels can be parsed as numeric sizes.
# This is suitable for workload-size sweeps such as 1M, 4M, 8M, 16M.
USE_LOG2_X_AXIS = True

# Set to True if you want a second figure showing speedup over NORMALIZE_BASELINE.
# Speedup is computed as: JCT(baseline) / JCT(algorithm).
# Therefore, values larger than 1 mean the algorithm is faster than the baseline.
PLOT_NORMALIZED = True
NORMALIZE_BASELINE = "ecmp"      # ECMP is used as the default baseline.


# ──────────────────────────────────────────────────────────────────────────────
# Data parsing
# ──────────────────────────────────────────────────────────────────────────────

def parse_fct_file(filepath: str) -> float:
    """
    Parse an FCT file and return the collective JCT in milliseconds.

    The input format follows the original script:
      start_time    = column 6, i.e., parts[5], in ns
      duration_time = column 7, i.e., parts[6], in ns

    JCT = last flow end time - first flow start time.
    """
    if not os.path.isfile(filepath):
        print(f"  [WARN] File not found: {filepath!r} -> NaN")
        return float("nan")

    first_start = float("inf")
    last_end = float("-inf")
    found_any = False

    with open(filepath, "r") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 7:
                continue

            try:
                start_ns = float(parts[5])
                duration_ns = float(parts[6])
            except ValueError:
                print(f"  [WARN] Bad numeric record skipped: {filepath}:{line_no}")
                continue

            end_ns = start_ns + duration_ns
            first_start = min(first_start, start_ns)
            last_end = max(last_end, end_ns)
            found_any = True

    if not found_any:
        print(f"  [WARN] No valid FCT records: {filepath!r} -> NaN")
        return float("nan")

    return (last_end - first_start) / 1e6  # ns -> ms


def to_fct_path(path: str) -> str:
    """Accept either an experiment directory or a direct fct.txt path."""
    if path.endswith(".txt"):
        return path
    return os.path.join(path, "fct.txt")



def parse_workload_size_to_mb(label: str):
    """
    Convert labels such as '1 M', '4MB', '8M', '1 G' to MB.
    Returns None if the label is not a simple size label.
    """
    s = label.strip().replace(" ", "")
    m = re.match(r"^([0-9]*\.?[0-9]+)([KkMmGgTt]?)([Bb]?)$", s)
    if not m:
        return None

    value = float(m.group(1))
    unit = m.group(2).upper()

    factor = {
        "": 1.0,       # treat unit-less numeric labels as MB
        "K": 1.0 / 1024.0,
        "M": 1.0,
        "G": 1024.0,
        "T": 1024.0 * 1024.0,
    }[unit]
    return value * factor


def collect_workload_labels(config):
    """Collect unique workload labels and sort them numerically when possible."""
    labels = []
    seen = set()
    for algo in config:
        for label in config[algo]:
            if label not in seen:
                labels.append(label)
                seen.add(label)

    parsed = [parse_workload_size_to_mb(x) for x in labels]
    if all(v is not None for v in parsed):
        labels = [x for _, x in sorted(zip(parsed, labels), key=lambda p: p[0])]

    return labels


def collect_results(config):
    """
    Returns:
      algorithms: ordered list of algorithm names
      workloads:  numerically sorted workload labels when possible
      data:       dict[algo][workload] = JCT_ms
    """
    algorithms = list(config.keys())
    workloads = collect_workload_labels(config)

    data = OrderedDict()
    for algo in algorithms:
        data[algo] = OrderedDict()
        for workload in workloads:
            exp_path = config[algo].get(workload, None)
            if exp_path is None:
                data[algo][workload] = float("nan")
                continue

            fct_path = to_fct_path(exp_path)
            print(f"  Parsing [{algo:>10s}][{workload:>5s}]: {fct_path}")
            data[algo][workload] = parse_fct_file(fct_path)

    return algorithms, workloads, data


def write_results_csv(csv_path, algorithms, workloads, data):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["algorithm", "workload", "jct_ms"])
        for algo in algorithms:
            for workload in workloads:
                value = data[algo].get(workload, float("nan"))
                writer.writerow([algo, workload, value])
    print(f"Parsed results saved to: {csv_path}")


# ──────────────────────────────────────────────────────────────────────────────
# Plot styling
# ──────────────────────────────────────────────────────────────────────────────

# Color-blind friendly palette, suitable for paper figures.
PALETTE = [
    "#D55E00",  # vermillion
    "#0072B2",  # blue
    "#009E73",  # green
    "#CC79A7",  # reddish purple
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#000000",  # black
    "#999999",  # gray
]

MARKERS = ["o", "s", "D", "^", "v", "P", "X", "*"]
LINESTYLES = ["-", "--", "-.", ":", (0, (3, 1, 1, 1)), (0, (5, 2))]


def set_paper_rcparams():
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif", "Georgia"],
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 12,
        "legend.fontsize": 9.5,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "axes.linewidth": 0.8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.dpi": 300,
    })


def style_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)

    ax.tick_params(axis="both", which="major", direction="in", length=4, width=0.8)
    ax.tick_params(axis="both", which="minor", direction="in", length=2, width=0.6)

    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.grid(axis="y", linestyle="--", linewidth=0.55, alpha=0.55)
    ax.set_axisbelow(True)


def compact_number(x, _pos=None):
    if x == 0 or not np.isfinite(x):
        return "0"
    abs_x = abs(x)
    if abs_x >= 1e6:
        return f"{x / 1e6:g}M"
    if abs_x >= 1e3:
        return f"{x / 1e3:g}K"
    if abs_x >= 10:
        return f"{x:g}"
    return f"{x:.2g}"


def build_x_axis(workloads):
    """
    Prefer a numeric workload-size x-axis. Fall back to categorical positions
    when labels cannot be parsed.
    """
    workload_mb = [parse_workload_size_to_mb(w) for w in workloads]
    numeric = all(v is not None and v > 0 for v in workload_mb)

    if numeric:
        x = np.array(workload_mb, dtype=float)
        # Use pure MB values as tick labels because the x-axis title already carries the unit.
        x_labels = [f"{v:g}" for v in workload_mb]
        return x, x_labels, True

    x = np.arange(len(workloads), dtype=float)
    return x, workloads, False


# ──────────────────────────────────────────────────────────────────────────────
# Plotting
# ──────────────────────────────────────────────────────────────────────────────

def plot_jct_scaling(algorithms, workloads, data, output_file):
    """
    Main figure:
      x-axis: workload/message size
      y-axis: JCT
      line:   load-balancing algorithm
    """
    set_paper_rcparams()
    x_values, x_labels, numeric_x = build_x_axis(workloads)

    fig, ax = plt.subplots(figsize=(7.2, 3.6))

    for i, algo in enumerate(algorithms):
        y = np.array([data[algo].get(w, float("nan")) for w in workloads], dtype=float)
        valid = np.isfinite(y)
        if not np.any(valid):
            continue

        is_highlight = (HIGHLIGHT_ALGO is not None and algo == HIGHLIGHT_ALGO)
        color = PALETTE[i % len(PALETTE)]
        marker = MARKERS[i % len(MARKERS)]
        linestyle = LINESTYLES[i % len(LINESTYLES)]

        ax.plot(
            x_values[valid],
            y[valid],
            label=algo,
            color=color,
            linestyle=linestyle,
            linewidth=2.4 if is_highlight else 1.55,
            marker=marker,
            markersize=6.4 if is_highlight else 5.2,
            markerfacecolor="white",
            markeredgewidth=1.15 if is_highlight else 0.9,
            zorder=5 if is_highlight else 3,
        )

    if numeric_x:
        ax.set_xticks(x_values)
        ax.set_xticklabels(x_labels)
        if USE_LOG2_X_AXIS and len(x_values) >= 2:
            ax.set_xscale("log", base=2)
            ax.set_xlim(min(x_values) / 1.18, max(x_values) * 1.18)
    else:
        ax.set_xticks(x_values)
        ax.set_xticklabels(x_labels)
        ax.set_xlim(-0.4, len(x_values) - 0.6)

    ax.set_xlabel(f"{WORKLOAD_NAME} Flow Size (MB)")
    ax.set_ylabel("Job Completion Time (ms)")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(compact_number))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=6))

    # Keep a small top margin for readability.
    ymin, ymax = ax.get_ylim()
    if np.isfinite(ymax):
        ax.set_ylim(bottom=0, top=ymax * 1.08)

    style_axes(ax)

    # Put legend above the plot to avoid covering curves.
    legend = ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=min(6, max(1, len(algorithms))),
        frameon=False,
        columnspacing=1.1,
        handlelength=2.1,
        handletextpad=0.45,
    )

    # Lightweight in-plot hint, useful for paper figures without verbose caption.
    ax.text(
        0.015,
        0.965,
        "Lower is better",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.5,
    )

    fig.tight_layout(pad=0.45)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    fig.savefig(output_file, bbox_inches="tight")
    print(f"Figure saved to: {output_file}")
    plt.close(fig)


def plot_normalized_jct(algorithms, workloads, data, output_file, baseline_algo):
    """
    Optional normalized figure:
      y = JCT(baseline_algo) / JCT(algo)

    This is the speedup over the baseline.
    Values larger than 1 mean the algorithm is faster than the baseline.
    """
    if baseline_algo not in data:
        print(f"[WARN] baseline {baseline_algo!r} not found; skip normalized figure.")
        return

    set_paper_rcparams()
    x_values, x_labels, numeric_x = build_x_axis(workloads)

    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    baseline = np.array([data[baseline_algo].get(w, float("nan")) for w in workloads], dtype=float)

    for i, algo in enumerate(algorithms):
        y_abs = np.array([data[algo].get(w, float("nan")) for w in workloads], dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            y = baseline / y_abs
        valid = np.isfinite(y) & np.isfinite(baseline) & (baseline > 0) & (y_abs > 0)
        if not np.any(valid):
            continue

        is_highlight = (HIGHLIGHT_ALGO is not None and algo == HIGHLIGHT_ALGO)
        ax.plot(
            x_values[valid],
            y[valid],
            label=algo,
            color=PALETTE[i % len(PALETTE)],
            linestyle=LINESTYLES[i % len(LINESTYLES)],
            linewidth=2.4 if is_highlight else 1.55,
            marker=MARKERS[i % len(MARKERS)],
            markersize=6.4 if is_highlight else 5.2,
            markerfacecolor="white",
            markeredgewidth=1.15 if is_highlight else 0.9,
            zorder=5 if is_highlight else 3,
        )

    if numeric_x:
        ax.set_xticks(x_values)
        ax.set_xticklabels(x_labels)
        if USE_LOG2_X_AXIS and len(x_values) >= 2:
            ax.set_xscale("log", base=2)
            ax.set_xlim(min(x_values) / 1.18, max(x_values) * 1.18)
    else:
        ax.set_xticks(x_values)
        ax.set_xticklabels(x_labels)
        ax.set_xlim(-0.4, len(x_values) - 0.6)

    ax.axhline(1.0, color="#777777", linewidth=1.0, linestyle="--", zorder=1)
    ax.set_xlabel(f"{WORKLOAD_NAME} Flow Size (MB)")
    ax.set_ylabel(f"Speedup over {baseline_algo.upper()} (x)")
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=6))

    style_axes(ax)
    ax.text(
        0.015,
        0.965,
        "Higher is better",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.5,
    )
    ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=min(6, max(1, len(algorithms))),
        frameon=False,
        columnspacing=1.1,
        handlelength=2.1,
        handletextpad=0.45,
    )

    fig.tight_layout(pad=0.45)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    fig.savefig(output_file, bbox_inches="tight")
    print(f"Normalized figure saved to: {output_file}")
    plt.close(fig)


def main():
    print("Collecting JCT results ...")
    algorithms, workloads, data = collect_results(CONFIG_LIST)

    output_pdf = os.path.join(OUTPUT_DIR, f"{OUTPUT_PREFIX}.pdf")
    plot_jct_scaling(algorithms, workloads, data, output_pdf)

    if SAVE_CSV:
        output_csv = os.path.join(OUTPUT_DIR, f"{OUTPUT_PREFIX}.csv")
        write_results_csv(output_csv, algorithms, workloads, data)

    if PLOT_NORMALIZED:
        output_norm_pdf = os.path.join(OUTPUT_DIR, f"{OUTPUT_PREFIX}_speedup_over_{NORMALIZE_BASELINE}.pdf")
        plot_normalized_jct(algorithms, workloads, data, output_norm_pdf, NORMALIZE_BASELINE)


if __name__ == "__main__":
    main()
