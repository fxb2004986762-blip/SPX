#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Batch analyze fct.txt files.

fct.txt format assumed:
------------------------------------------------------------
col 1   src
col 2   dst
col 3   sport
col 4   dport
col 5   flow_size (Bytes)
col 6   start_time
col 7   finish_time
col 8   ideal_fct
col 9+  other statistics
------------------------------------------------------------

Core definitions:
    FCT = finish_time - start_time

    JCT = max(finish_time) - min(start_time)

    FCT slowdown = FCT / ideal_fct

Example:
    71 199 10000 100 1048576 5000 38078 26142 3 0 0 0 0 0 166

    start       = 5000
    finish      = 38078
    FCT         = 33078
    ideal FCT   = 26142
    slowdown    = 33078 / 26142 ≈ 1.265
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# User Config
# ============================================================

CONFIG_LIST = {

    # Example 1: two-level dictionary
    #
    # "aps-v2": {
    #     "1MB": "/path/to/aps-v2/1MB",
    #     "4MB": "/path/to/aps-v2/4MB",
    # },
    #
    # "ecmp": {
    #     "1MB": "/path/to/ecmp/1MB",
    #     "4MB": "/path/to/ecmp/4MB",
    # },

    # Example 2: one-level dictionary
    #
    # "1MB": "/path/to/1MB",
    # "4MB": "/path/to/4MB",

}


# 如果本文件的 CONFIG_LIST 为空，
# 使用共享配置文件中的 CONFIG_LIST
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

if not CONFIG_LIST:
    from configs.result_path import CONFIG_LIST


# ============================================================
# Input
# ============================================================

FCT_FILENAME = "fct.txt"


# ============================================================
# Column Definition
# ============================================================
#
# Python index starts from 0.
#
# 用户描述：
# 第5列：flow size
# 第6列：start time
# 第7列：finish time
# 第8列：ideal FCT
#
SRC_COL = 0
FLOW_SIZE_COL = 4
START_TIME_COL = 5
FINISH_TIME_COL = 6
IDEAL_FCT_COL = 7


# ============================================================
# Time Unit
# ============================================================
#
# ns-3 日志中的时间通常为 ns。
#
# 如果你的 fct.txt 中：
#
#   5000 -> 5 us
#
# 那么这里就使用 "ns"。
#
# 可选：
#   "ns"
#   "us"
#   "ms"
#   "s"
#
INPUT_TIME_UNIT = "ns"

# 最终打印 FCT/JCT 时使用什么单位
OUTPUT_TIME_UNIT = "us"


# ============================================================
# Output Configuration
# ============================================================

# 是否保存汇总 CSV
SAVE_CSV = False

# CSV 输出路径
OUTPUT_CSV = "fct_summary.csv"


# 是否保存 Tab 分隔的汇总文件
# 推荐保持开启，可以直接用 Excel / WPS 打开。
SAVE_TSV = True

# TSV 输出路径
OUTPUT_TSV = "fct_summary.tsv"


# 是否打印每个实验的完整详细指标
PRINT_DETAIL = True


# ============================================================
# Metric selection
# ============================================================
#
# 控制最终 summary table 打印哪些指标。
#
SUMMARY_METRICS = [
    "flows",
    "senders",
    "jct",
    "goodput_Gbps",
    "avg_fct",
    "p95_fct",
    "p99_fct",
    "avg_slowdown",
    "p99_slowdown",
]


# ============================================================
# Helper: extract algorithm name from directory
# ============================================================

def get_algorithm_from_directory(directory):
    """
    从实验目录最后一级文件夹名称中提取算法名称。

    Rule
    ----
    1. 获取最后一级目录名称
    2. 使用 "_" 分割
    3. 取第一个字符串

    Examples
    --------
    /path/to/aps-v2_dcqcn-fattree_xxx
        -> aps-v2

    /path/to/reps_mprdma-hpn_xxx
        -> reps

    /path/to/ecmp_dcqcn-spectrumx_xxx
        -> ecmp
    """
    dirname = os.path.basename(
        os.path.normpath(str(directory))
    )

    if not dirname:
        return "unknown"

    return dirname.split("_")[0]


# ============================================================
# Helper: flatten CONFIG_LIST
# ============================================================

def collect_results(config):
    """
    Automatically adapt to different CONFIG_LIST structures.

    Supported
    ---------

    1. Two-level:

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


    2. One-level:

        {
            "1MB": "/path/a",
            "4MB": "/path/b",
        }


    3. Deeper:

        {
            "aps-v2": {
                "sym": {
                    "1MB": "/path/a",
                    "4MB": "/path/b",
                }
            }
        }


    Returns
    -------
    algorithms:
        ordered list of first-level labels

    sizes:
        ordered list of experiment labels

    data:
        data[algo][size] = path
    """

    if not isinstance(config, dict) or not config:
        return [], [], {}

    # --------------------------------------------------------
    # Recursively find all leaf nodes
    # --------------------------------------------------------

    def flatten_dict(d, prefix=()):
        results = []

        for key, value in d.items():
            current_keys = prefix + (str(key),)

            if isinstance(value, dict):
                results.extend(
                    flatten_dict(value, current_keys)
                )
            else:
                results.append(
                    (current_keys, value)
                )

        return results

    flattened = flatten_dict(config)

    if not flattened:
        return [], [], {}

    depths = [
        len(keys)
        for keys, _ in flattened
    ]

    max_depth = max(depths)

    # ========================================================
    # One-level dictionary
    # ========================================================

    if max_depth == 1:
        algorithms = ["default"]

        sizes = []

        data = {
            "default": {}
        }

        for keys, fp in flattened:
            size = keys[0]

            sizes.append(size)

            data["default"][size] = fp

        return algorithms, sizes, data

    # ========================================================
    # Two-level or deeper
    # ========================================================

    algorithms = []

    sizes_seen = {}

    parsed_entries = []

    for keys, fp in flattened:
        algo = keys[0]

        # Merge deeper levels:
        #
        # aps-v2 / sym / 1MB
        #
        # ->
        #
        # algo = aps-v2
        # size = sym/1MB
        #
        size = "/".join(keys[1:])

        if algo not in algorithms:
            algorithms.append(algo)

        if size not in sizes_seen:
            sizes_seen[size] = True

        parsed_entries.append(
            (algo, size, fp)
        )

    sizes = list(sizes_seen.keys())

    data = {}

    for algo in algorithms:
        data[algo] = {
            size: None
            for size in sizes
        }

    for algo, size, fp in parsed_entries:
        data[algo][size] = fp

    return algorithms, sizes, data


# ============================================================
# Time conversion
# ============================================================

def convert_time(value, src_unit, dst_unit):
    """
    Convert time value between ns/us/ms/s.
    """

    unit_to_ns = {
        "ns": 1.0,
        "us": 1e3,
        "ms": 1e6,
        "s": 1e9,
    }

    if src_unit not in unit_to_ns:
        raise ValueError(
            f"Unknown source time unit: {src_unit}"
        )

    if dst_unit not in unit_to_ns:
        raise ValueError(
            f"Unknown destination time unit: {dst_unit}"
        )

    value_ns = value * unit_to_ns[src_unit]

    return value_ns / unit_to_ns[dst_unit]


# ============================================================
# Read fct.txt
# ============================================================

def read_fct_file(fct_path):
    """
    Read fct.txt.

    Lines are separated by whitespace.
    """

    try:
        df = pd.read_csv(
            fct_path,
            sep=r"\s+",
            header=None,
            comment="#",
            engine="python",
        )

    except Exception as e:
        print(
            f"[ERROR] Failed to read {fct_path}: {e}"
        )

        return None

    # --------------------------------------------------------
    # Basic column check
    # --------------------------------------------------------

    required_col = max(
        SRC_COL,
        FLOW_SIZE_COL,
        START_TIME_COL,
        FINISH_TIME_COL,
        IDEAL_FCT_COL,
    )

    if df.shape[1] <= required_col:
        print(
            f"[ERROR] Invalid column number: {fct_path}"
        )

        print(
            f"        Expected at least {required_col + 1} columns, "
            f"but got {df.shape[1]}"
        )

        return None

    # --------------------------------------------------------
    # Convert required columns to numeric
    # --------------------------------------------------------

    target_cols = [
        SRC_COL,
        FLOW_SIZE_COL,
        START_TIME_COL,
        FINISH_TIME_COL,
        IDEAL_FCT_COL,
    ]

    for col in target_cols:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        )

    before = len(df)

    df = df.dropna(
        subset=target_cols
    )

    after = len(df)

    if before != after:
        print(
            f"[WARNING] {fct_path}: "
            f"ignored {before - after} malformed rows"
        )

    return df


# ============================================================
# Analyze one fct.txt
# ============================================================

def analyze_fct_file(fct_path):
    """
    Analyze one fct.txt.

    Returns
    -------
    dict
    """

    df = read_fct_file(fct_path)

    if df is None or df.empty:
        return None

    # ========================================================
    # Extract columns
    # ========================================================

    src = df[SRC_COL].to_numpy(dtype=float)

    flow_size = df[FLOW_SIZE_COL].to_numpy(dtype=float)

    start_time = df[START_TIME_COL].to_numpy(dtype=float)

    finish_time = df[FINISH_TIME_COL].to_numpy(dtype=float)

    ideal_fct = df[IDEAL_FCT_COL].to_numpy(dtype=float)

    # ========================================================
    # FCT
    # ========================================================

    fct = finish_time - start_time

    # Remove invalid records
    valid = (
        np.isfinite(src)
        & np.isfinite(flow_size)
        & np.isfinite(start_time)
        & np.isfinite(finish_time)
        & np.isfinite(fct)
        & np.isfinite(ideal_fct)
        & (fct >= 0)
    )

    src = src[valid]

    flow_size = flow_size[valid]

    start_time = start_time[valid]

    finish_time = finish_time[valid]

    ideal_fct = ideal_fct[valid]

    fct = fct[valid]

    if len(fct) == 0:
        return None

    # ========================================================
    # JCT
    # ========================================================

    job_start = np.min(start_time)

    job_finish = np.max(finish_time)

    jct = job_finish - job_start

    # ========================================================
    # Slowdown
    # ========================================================

    valid_ideal = ideal_fct > 0

    slowdown = (
        fct[valid_ideal]
        / ideal_fct[valid_ideal]
    )

    # ========================================================
    # Flow size
    # ========================================================

    total_bytes = np.sum(flow_size)

    avg_flow_size = np.mean(flow_size)

    # ========================================================
    # Goodput
    # ========================================================
    #
    # Definition used here:
    #
    #                    total application bytes * 8
    #   Goodput = --------------------------------------------------
    #              number of unique senders * global JCT * 1e9
    #
    # Unit: Gbps per sender.
    #
    # total_bytes / JCT is the WHOLE-CLUSTER aggregate goodput.
    # It grows naturally with cluster size and can therefore become
    # tens/hundreds of Tbps in large GPU experiments.
    #
    # Dividing by the number of unique source nodes gives an average
    # task-level effective goodput per sender. This is more intuitive
    # because it can be compared directly with NIC line rate, e.g.
    # 100/200/400 Gbps.
    #
    # We deliberately use the GLOBAL JCT rather than each sender's
    # individual active interval. Therefore waiting time, imbalance,
    # and straggler effects are included in the metric.
    # ========================================================

    num_senders = len(np.unique(src))

    if jct > 0 and num_senders > 0:
        jct_seconds = convert_time(
            jct,
            INPUT_TIME_UNIT,
            "s",
        )

        # Whole-cluster aggregate application goodput.
        aggregate_goodput_gbps = (
            total_bytes
            * 8
            / jct_seconds
            / 1e9
        )

        # Average effective application goodput per sender.
        goodput_gbps = (
            aggregate_goodput_gbps
            / num_senders
        )

    else:
        aggregate_goodput_gbps = np.nan
        goodput_gbps = np.nan

    # ========================================================
    # Convert time units
    # ========================================================

    jct_out = convert_time(
        jct,
        INPUT_TIME_UNIT,
        OUTPUT_TIME_UNIT,
    )

    fct_out = convert_time(
        fct,
        INPUT_TIME_UNIT,
        OUTPUT_TIME_UNIT,
    )

    ideal_out = convert_time(
        ideal_fct,
        INPUT_TIME_UNIT,
        OUTPUT_TIME_UNIT,
    )

    # ========================================================
    # Statistics
    # ========================================================

    result = {
        # Basic
        "flows":
            len(fct),

        "senders":
            num_senders,

        "avg_flow_size_MB":
            avg_flow_size / 1024 / 1024,

        "total_traffic_GB":
            total_bytes / 1024 / 1024 / 1024,

        # Job
        "jct":
            jct_out,

        # FCT
        "avg_fct":
            np.mean(fct_out),

        "median_fct":
            np.median(fct_out),

        "p50_fct":
            np.percentile(fct_out, 50),

        "p90_fct":
            np.percentile(fct_out, 90),

        "p95_fct":
            np.percentile(fct_out, 95),

        "p99_fct":
            np.percentile(fct_out, 99),

        "max_fct":
            np.max(fct_out),

        # Ideal
        "avg_ideal_fct":
            np.mean(ideal_out),

        "p99_ideal_fct":
            np.percentile(ideal_out, 99),

        # Slowdown
        "avg_slowdown":
            np.mean(slowdown)
            if len(slowdown) > 0 else np.nan,

        "median_slowdown":
            np.median(slowdown)
            if len(slowdown) > 0 else np.nan,

        "p50_slowdown":
            np.percentile(slowdown, 50)
            if len(slowdown) > 0 else np.nan,

        "p90_slowdown":
            np.percentile(slowdown, 90)
            if len(slowdown) > 0 else np.nan,

        "p95_slowdown":
            np.percentile(slowdown, 95)
            if len(slowdown) > 0 else np.nan,

        "p99_slowdown":
            np.percentile(slowdown, 99)
            if len(slowdown) > 0 else np.nan,

        "max_slowdown":
            np.max(slowdown)
            if len(slowdown) > 0 else np.nan,

        # Goodput
        # Average task-level effective goodput per sender.
        "goodput_Gbps":
            goodput_gbps,

        # Whole-cluster aggregate value retained for reference.
        "aggregate_goodput_Gbps":
            aggregate_goodput_gbps,
    }

    return result


# ============================================================
# Pretty print one experiment
# ============================================================

def print_detail(
    algo,
    size,
    directory,
    result,
):
    """
    Pretty-print all statistics of one experiment.
    """

    line = "=" * 76

    print()
    print(line)

    print(
        f"Algorithm : {algo}"
    )

    print(
        f"Config    : {size}"
    )

    print(
        f"Directory : {directory}"
    )

    print(line)

    print(
        f"Flows                   : "
        f"{result['flows']}"
    )

    print(
        f"Unique Senders          : "
        f"{result['senders']}"
    )

    print(
        f"Average Flow Size       : "
        f"{result['avg_flow_size_MB']:.3f} MB"
    )

    print(
        f"Total Traffic           : "
        f"{result['total_traffic_GB']:.3f} GB"
    )

    print("-" * 76)

    print(
        f"JCT                     : "
        f"{result['jct']:.6f} {OUTPUT_TIME_UNIT}"
    )

    print("-" * 76)

    print(
        f"Average FCT             : "
        f"{result['avg_fct']:.6f} {OUTPUT_TIME_UNIT}"
    )

    print(
        f"Median FCT              : "
        f"{result['median_fct']:.6f} {OUTPUT_TIME_UNIT}"
    )

    print(
        f"P90 FCT                 : "
        f"{result['p90_fct']:.6f} {OUTPUT_TIME_UNIT}"
    )

    print(
        f"P95 FCT                 : "
        f"{result['p95_fct']:.6f} {OUTPUT_TIME_UNIT}"
    )

    print(
        f"P99 FCT                 : "
        f"{result['p99_fct']:.6f} {OUTPUT_TIME_UNIT}"
    )

    print(
        f"Max FCT                 : "
        f"{result['max_fct']:.6f} {OUTPUT_TIME_UNIT}"
    )

    print("-" * 76)

    print(
        f"Average Ideal FCT       : "
        f"{result['avg_ideal_fct']:.6f} {OUTPUT_TIME_UNIT}"
    )

    print(
        f"P99 Ideal FCT           : "
        f"{result['p99_ideal_fct']:.6f} {OUTPUT_TIME_UNIT}"
    )

    print("-" * 76)

    print(
        f"Average FCT Slowdown    : "
        f"{result['avg_slowdown']:.6f}x"
    )

    print(
        f"Median FCT Slowdown     : "
        f"{result['median_slowdown']:.6f}x"
    )

    print(
        f"P90 FCT Slowdown        : "
        f"{result['p90_slowdown']:.6f}x"
    )

    print(
        f"P95 FCT Slowdown        : "
        f"{result['p95_slowdown']:.6f}x"
    )

    print(
        f"P99 FCT Slowdown        : "
        f"{result['p99_slowdown']:.6f}x"
    )

    print(
        f"Max FCT Slowdown        : "
        f"{result['max_slowdown']:.6f}x"
    )

    print("-" * 76)

    print(
        f"Goodput / Sender        : "
        f"{result['goodput_Gbps']:.3f} Gbps"
    )

    print(
        f"Aggregate Goodput       : "
        f"{result['aggregate_goodput_Gbps']:.3f} Gbps"
    )

    print(line)


# ============================================================
# Compact summary table
# ============================================================

def build_summary_dataframe(results):
    """
    Build the compact summary DataFrame.

    This is shared by:
      1. terminal aligned output
      2. TSV file output
    """

    if not results:
        return pd.DataFrame()

    rows = []

    for item in results:
        row = {
            "algorithm": item["algorithm"],
            "config": item["config"],
        }

        for metric in SUMMARY_METRICS:
            row[metric] = item.get(
                metric,
                np.nan,
            )

        rows.append(row)

    return pd.DataFrame(rows)


def print_summary_table(results):
    """
    Print a human-readable aligned summary table in terminal.

    The spreadsheet-friendly version is written separately to a
    real TSV file, avoiding copy/paste issues in VSCode terminals.
    """

    df = build_summary_dataframe(results)

    if df.empty:
        return

    print()
    print()
    print("=" * 120)
    print("FCT SUMMARY")
    print("=" * 120)

    with pd.option_context(
        "display.max_columns", None,
        "display.width", 260,
        "display.max_colwidth", 80,
    ):
        print(
            df.to_string(
                index=False,
                float_format=lambda x: f"{x:.4f}",
            )
        )

    print("=" * 120)
    print(f"Time unit: {OUTPUT_TIME_UNIT}")
    print()


def save_summary_tsv(results):
    """
    Save summary as a real tab-separated file.

    The file can be:
      - opened directly by Excel / WPS
      - imported as tab-separated text
      - copied from a text editor and pasted into a spreadsheet

    Float values are written with four decimal places.
    """

    if not SAVE_TSV:
        return

    df = build_summary_dataframe(results)

    if df.empty:
        return

    output_path = Path(OUTPUT_TSV)

    # 如果 OUTPUT_TSV 带有目录，自动创建目录。
    if output_path.parent != Path("."):
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    df.to_csv(
        output_path,
        sep="\t",
        index=False,
        float_format="%.4f",
    )

    print(
        f"Saved TSV summary: "
        f"{output_path.resolve()}"
    )


# ============================================================
# Main
# ============================================================

def main():

    algorithms, sizes, data = collect_results(
        CONFIG_LIST
    )

    if not algorithms:
        print(
            "[ERROR] CONFIG_LIST is empty."
        )
        return

    all_results = []

    total = 0
    success = 0
    failed = 0

    # ========================================================
    # Batch traversal
    # ========================================================

    for size in sizes:

        for config_algo in algorithms:

            directory = data[config_algo].get(
                size,
                None,
            )

            # -----------------------------------------------
            # Configuration does not contain this pair
            # -----------------------------------------------

            if directory is None:
                continue

            directory = str(directory)

            total += 1

            fct_path = os.path.join(
                directory,
                FCT_FILENAME,
            )

            # 从实际实验目录名提取算法名称
            display_algo = get_algorithm_from_directory(
                directory
            )

            print(
                f"[{total}] Parsing "
                f"[{display_algo}][{size}]"
            )

            print(
                f"    {fct_path}"
            )

            # -----------------------------------------------
            # File existence
            # -----------------------------------------------

            if not os.path.exists(fct_path):

                print(
                    "    [WARNING] fct.txt does not exist, skip."
                )

                failed += 1
                continue

            # -----------------------------------------------
            # Analyze
            # -----------------------------------------------

            result = analyze_fct_file(
                fct_path
            )

            if result is None:

                print(
                    "    [WARNING] No valid FCT data, skip."
                )

                failed += 1
                continue

            success += 1

            # -----------------------------------------------
            # Metadata
            # -----------------------------------------------

            result["algorithm"] = display_algo

            result["config"] = size

            result["directory"] = directory

            all_results.append(
                result
            )

            # -----------------------------------------------
            # Detailed print
            # -----------------------------------------------

            if PRINT_DETAIL:
                print_detail(
                    display_algo,
                    size,
                    directory,
                    result,
                )

    # ========================================================
    # Summary
    # ========================================================

    print_summary_table(
        all_results
    )

    # ========================================================
    # TSV
    # ========================================================

    save_summary_tsv(
        all_results
    )

    # ========================================================
    # CSV
    # ========================================================

    if SAVE_CSV and all_results:

        df = pd.DataFrame(
            all_results
        )

        # Put metadata first
        first_cols = [
            "algorithm",
            "config",
            "directory",
        ]

        other_cols = [
            c
            for c in df.columns
            if c not in first_cols
        ]

        df = df[
            first_cols + other_cols
        ]

        df.to_csv(
            OUTPUT_CSV,
            index=False,
        )

        print(
            f"\nSaved summary CSV: "
            f"{OUTPUT_CSV}"
        )

    # ========================================================
    # Final status
    # ========================================================

    print()

    print(
        f"Finished: "
        f"total={total}, "
        f"success={success}, "
        f"failed={failed}"
    )


if __name__ == "__main__":
    main()
