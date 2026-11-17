#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cached plotter for out-of-order buffer occupancy logs.

Input format, whitespace separated, no header:
    time_ns src_id dst_id src_port dst_port occupancy

Key design:
1) Heavy raw-log parsing/statistics are cached once.
2) Plot-mode changes reuse cached summary / selected time-series.
3) Heatmap is rendered from a state-like uniform time grid instead of sparse event points.
"""

import os
import json
import math
import hashlib
from typing import Dict, Optional, Tuple

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42

# =========================
# User Config
# =========================
CONFIG_LIST = {
    # "default": {
    #     "single": ".",
    # },
    # "rps": {
    #     "o4": "/home/dcn1/fxb/simulator/output/rps-o4-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "o8": "/home/dcn1/fxb/simulator/output/rps-o8-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "o16": "/home/dcn1/fxb/simulator/output/rps-o16-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "o32": "/home/dcn1/fxb/simulator/output/rps-o32-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "o64": "/home/dcn1/fxb/simulator/output/rps-o64-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "o128": "/home/dcn1/fxb/simulator/output/rps-o128-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "o306": "/home/dcn1/fxb/simulator/output/rps-o306-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    # },
    # "aps-v2": {
    #     "o4": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o4-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "o8": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o8-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "o16": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o16-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "o32": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o32-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "o64": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o64-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "o128": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o128-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "o306": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o306-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    # },
    # "reps": {
    #     "o4": "/home/dcn1/fxb/simulator/output/reps-o4-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "o8": "/home/dcn1/fxb/simulator/output/reps-o8-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "o16": "/home/dcn1/fxb/simulator/output/reps-o16-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "o32": "/home/dcn1/fxb/simulator/output/reps-o32-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "o64": "/home/dcn1/fxb/simulator/output/reps-o64-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "o128": "/home/dcn1/fxb/simulator/output/reps-o128-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "o306": "/home/dcn1/fxb/simulator/output/reps-o306-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    # },
    # "algo_files" : {
    #     "0": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_noWin_RP10/aps-v2/aps-v2-o32-noWin-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "1": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_noWin_RP10/aps-v2/aps-v2-o306-noWin-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "2": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_noWin_RP10/reps/reps-o32-noWin-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "3": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_noWin_RP10/reps/reps-o306-noWin-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "4": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_noWin_RP10/rps/rps-o306-noWin-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    #     "5": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_noWin_RP10/rps/rps-o32-noWin-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
    # },

    # "algo_files_1024GPU_noWin" : {
    #     "0": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/1024GPU/dcqcn_noWin_RP10/aps-v2/aps-v2-o32-noWin-100_300KB_10RP_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
    #     "1": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/1024GPU/dcqcn_noWin_RP10/aps-v2/aps-v2-o306-noWin-100_300KB_10RP_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
    #     "2": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/1024GPU/dcqcn_noWin_RP10/reps/reps-o32-noWin-100_300KB_10RP_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
    #     "3": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/1024GPU/dcqcn_noWin_RP10/reps/reps-o306-noWin-100_300KB_10RP_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
    #     "4": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/1024GPU/dcqcn_noWin_RP10/rps/rps-o306-noWin-100_300KB_10RP_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
    #     "5": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/1024GPU/dcqcn_noWin_RP10/rps/rps-o32-noWin-100_300KB_10RP_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
    # },

    "algo_files_1024GPU" : {
        # "0": "/home/dcn1/fxb/simulator/output/reps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
        "1": "/home/dcn1/fxb/simulator/output/aps-v2_mprdma-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
    }          


}

BASE_DIR = "."
OOO_FILE = os.path.join(BASE_DIR, "ooo.txt")
OUT_DIR = BASE_DIR
OUT_NAME = "ooo_buffer_occupancy"
OUT_CNT = 0

# Target connection for single-connection plot. None means no restriction.
TARGET_SRC_IDS = [0]
TARGET_DST_IDS = [15]
TARGET_SRC_PORTS = [10000]
TARGET_DST_PORTS = [100]

# Time range in us. None means no restriction.
TIME_START_US = None
TIME_END_US = None

TIME_UNIT_IN_FILE = "ns"          # "ns" or "us"
INPUT_FORMAT = "whitespace"       # "whitespace" or "mixed"

# Plot mode: "single", "heatmap", "summary", "all"
PLOT_MODE = "all"

# Top-K selection.
TOP_K_CONNECTIONS = 8
TOPK_SORT_BY = "mean"              # "max", "p99", "mean", "nonzero_ratio"
COMPUTE_P99 = True
P99_QUANTILE = 0.99

# Heatmap rendering.
# Critical: heatmap should use a uniform time grid. If None, SAMPLE_INTERVAL_US is used.
HEATMAP_BIN_US = None              # e.g., 0.1, 1, 10. None -> SAMPLE_INTERVAL_US
SAMPLE_INTERVAL_US = 0.1

# For occupancy state, "last" is usually semantically correct: the value after the latest event in a bin.
# For emphasizing burst peak pressure, use "max".
HEATMAP_AGG_METHOD = "last"        # "last", "max", "mean"

# Whether missing bins should inherit the previous occupancy value.
# For buffer occupancy logs that record state updates, keep True.
# If your log is already periodic sampling, this can also be True and is usually harmless.
HEATMAP_FORWARD_FILL = True

# Optional state-grid completion for single plot. Usually False keeps raw event transitions.
COMPLETE_SINGLE_TIMESERIES = False

BUFFER_CAPACITY = None
SHOW_TITLE = False
SAVE_PDF = False
SAVE_PNG = True
SKIP_IF_EXISTS = True

CACHE_ENABLED = True
CACHE_MODE = "auto"                # "auto", "reuse", "rebuild", "off"
CACHE_SUBDIR = ".ooo_cache"

READ_IN_CHUNKS = True
CHUNK_SIZE = 2_000_000

# =========================
# Style
# =========================
LINE_COLORS = [
    "#1b9e77", "#d95f02", "#7570b3", "#e7298a",
    "#66a61e", "#e6ab02", "#a6761d", "#666666",
]

plt.rcParams.update({
    "axes.titlesize": 16,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 11,
    "figure.titlesize": 18,
})

COLUMNS = ["time", "src_id", "dst_id", "src_port", "dst_port", "occupancy"]
GROUP_COLS = ["src_id", "dst_id", "src_port", "dst_port"]
ID_COLS = ["src_id", "dst_id", "src_port", "dst_port"]


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def time_to_us(series: pd.Series) -> pd.Series:
    if TIME_UNIT_IN_FILE == "ns":
        return series / 1000.0
    if TIME_UNIT_IN_FILE == "us":
        return series
    raise ValueError("TIME_UNIT_IN_FILE must be 'ns' or 'us'.")


def connection_label(row_or_tuple) -> str:
    if isinstance(row_or_tuple, tuple):
        src, dst, sport, dport = row_or_tuple
    else:
        src = row_or_tuple["src_id"]
        dst = row_or_tuple["dst_id"]
        sport = row_or_tuple["src_port"]
        dport = row_or_tuple["dst_port"]
    return f"{int(src)}:{int(sport)}->{int(dst)}:{int(dport)}"


def add_label_column(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        df = df.copy()
        df["label"] = []
        return df
    df = df.copy()
    df["label"] = (
        df["src_id"].astype(int).astype(str)
        + ":" + df["src_port"].astype(int).astype(str)
        + "->" + df["dst_id"].astype(int).astype(str)
        + ":" + df["dst_port"].astype(int).astype(str)
    )
    return df


def filter_time(df: pd.DataFrame) -> pd.DataFrame:
    if TIME_START_US is not None:
        df = df[df["time"] >= TIME_START_US]
    if TIME_END_US is not None:
        df = df[df["time"] <= TIME_END_US]
    return df


def filter_target_connection(df: pd.DataFrame) -> pd.DataFrame:
    if TARGET_SRC_IDS is not None:
        df = df[df["src_id"].isin(TARGET_SRC_IDS)]
    if TARGET_DST_IDS is not None:
        df = df[df["dst_id"].isin(TARGET_DST_IDS)]
    if TARGET_SRC_PORTS is not None:
        df = df[df["src_port"].isin(TARGET_SRC_PORTS)]
    if TARGET_DST_PORTS is not None:
        df = df[df["dst_port"].isin(TARGET_DST_PORTS)]
    return df


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    for c in COLUMNS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=COLUMNS)
    if df.empty:
        return pd.DataFrame(columns=COLUMNS)
    df["time"] = time_to_us(df["time"])
    for c in ID_COLS:
        df[c] = df[c].astype("int32")
    df["occupancy"] = df["occupancy"].astype("float32")
    return filter_time(df)


def read_ooo_buffer_iter(path: str):
    if INPUT_FORMAT == "whitespace":
        sep = r"\s+"
        engine = "c"
    elif INPUT_FORMAT == "mixed":
        sep = r"[\s,]+"
        engine = "python"
    else:
        raise ValueError("INPUT_FORMAT must be 'whitespace' or 'mixed'.")

    kwargs = dict(
        sep=sep,
        header=None,
        names=COLUMNS,
        comment="#",
        engine=engine,
    )

    if READ_IN_CHUNKS:
        for chunk in pd.read_csv(path, chunksize=CHUNK_SIZE, **kwargs):
            yield normalize_df(chunk)
    else:
        yield normalize_df(pd.read_csv(path, **kwargs))


def read_full_ooo_buffer(path: str) -> pd.DataFrame:
    chunks = list(read_ooo_buffer_iter(path))
    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=COLUMNS)


def target_config_dict() -> Dict:
    """Only include options that affect cached data content, not final plot cosmetics."""
    return {
        "target_src_ids": TARGET_SRC_IDS,
        "target_dst_ids": TARGET_DST_IDS,
        "target_src_ports": TARGET_SRC_PORTS,
        "target_dst_ports": TARGET_DST_PORTS,
        "time_start_us": TIME_START_US,
        "time_end_us": TIME_END_US,
        "time_unit_in_file": TIME_UNIT_IN_FILE,
        "input_format": INPUT_FORMAT,
        "top_k_connections": TOP_K_CONNECTIONS,
        "topk_sort_by": TOPK_SORT_BY,
        "compute_p99": COMPUTE_P99,
        "p99_quantile": P99_QUANTILE,
    }


def cache_prefix(raw_path: str) -> str:
    st = os.stat(raw_path)
    signature = {
        "path": os.path.abspath(raw_path),
        "size": st.st_size,
        "mtime_ns": st.st_mtime_ns,
        "config": target_config_dict(),
    }
    h = hashlib.md5(json.dumps(signature, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    return f"{OUT_NAME}_{h}"


def cache_paths(raw_path: str) -> Dict[str, str]:
    cache_dir = os.path.join(OUT_DIR, CACHE_SUBDIR)
    prefix = cache_prefix(raw_path)
    return {
        "dir": cache_dir,
        "meta": os.path.join(cache_dir, f"{prefix}_meta.json"),
        "summary": os.path.join(cache_dir, f"{prefix}_summary.csv"),
        "target_ts": os.path.join(cache_dir, f"{prefix}_target_timeseries.csv"),
        "topk_ts": os.path.join(cache_dir, f"{prefix}_topk_timeseries.csv"),
    }


def cache_is_complete(paths: Dict[str, str]) -> bool:
    return all(os.path.exists(paths[k]) for k in ["meta", "summary", "target_ts", "topk_ts"])


def write_meta(paths: Dict[str, str], raw_path: str):
    st = os.stat(raw_path)
    meta = {
        "raw_file": os.path.abspath(raw_path),
        "raw_size": st.st_size,
        "raw_mtime_ns": st.st_mtime_ns,
        "config": target_config_dict(),
    }
    with open(paths["meta"], "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def compute_summary_fast(path: str) -> pd.DataFrame:
    partials = []
    for chunk in read_ooo_buffer_iter(path):
        if chunk.empty:
            continue
        part = chunk.groupby(GROUP_COLS, sort=False).agg(
            count=("occupancy", "count"),
            sum=("occupancy", "sum"),
            max=("occupancy", "max"),
            nonzero_count=("occupancy", lambda s: int((s > 0).sum())),
            min_time=("time", "min"),
            max_time=("time", "max"),
        ).reset_index()
        partials.append(part)

    if not partials:
        return pd.DataFrame(columns=GROUP_COLS + ["label", "mean", "p99", "max", "nonzero_ratio", "duration_us"])

    p = pd.concat(partials, ignore_index=True)
    merged = p.groupby(GROUP_COLS, sort=False, as_index=False).agg(
        count=("count", "sum"),
        sum=("sum", "sum"),
        max=("max", "max"),
        nonzero_count=("nonzero_count", "sum"),
        min_time=("min_time", "min"),
        max_time=("max_time", "max"),
    )
    merged["mean"] = merged["sum"] / merged["count"].clip(lower=1)
    merged["nonzero_ratio"] = merged["nonzero_count"] / merged["count"].clip(lower=1)
    merged["duration_us"] = (merged["max_time"] - merged["min_time"]).clip(lower=0)

    if COMPUTE_P99:
        full = read_full_ooo_buffer(path)
        p99 = full.groupby(GROUP_COLS, sort=False)["occupancy"].quantile(P99_QUANTILE).reset_index(name="p99")
        merged = merged.merge(p99, on=GROUP_COLS, how="left")
    else:
        merged["p99"] = float("nan")

    merged = add_label_column(merged)
    if TOPK_SORT_BY not in merged.columns:
        raise ValueError(f"TOPK_SORT_BY={TOPK_SORT_BY!r} is not a summary column.")
    return merged.sort_values(TOPK_SORT_BY, ascending=False, kind="mergesort")


def select_topk_keys(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame(columns=GROUP_COLS)
    return summary.head(TOP_K_CONNECTIONS)[GROUP_COLS].copy()


def build_selected_timeseries(path: str, topk_keys: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    target_parts = []
    topk_parts = []
    has_topk = topk_keys is not None and not topk_keys.empty
    if has_topk:
        topk_keys = topk_keys.drop_duplicates(GROUP_COLS)

    for chunk in read_ooo_buffer_iter(path):
        if chunk.empty:
            continue
        t = filter_target_connection(chunk)
        if not t.empty:
            target_parts.append(t)
        if has_topk:
            k = chunk.merge(topk_keys, on=GROUP_COLS, how="inner")
            if not k.empty:
                topk_parts.append(k)

    target_ts = pd.concat(target_parts, ignore_index=True) if target_parts else pd.DataFrame(columns=COLUMNS)
    topk_ts = pd.concat(topk_parts, ignore_index=True) if topk_parts else pd.DataFrame(columns=COLUMNS)
    return target_ts, topk_ts


def build_or_load_cache(path: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, str]]:
    paths = cache_paths(path)
    ensure_dir(paths["dir"])

    if not CACHE_ENABLED or CACHE_MODE == "off":
        print("Cache disabled: building data from raw log.")
        summary = compute_summary_fast(path)
        target_ts, topk_ts = build_selected_timeseries(path, select_topk_keys(summary))
        return summary, target_ts, topk_ts, paths

    if CACHE_MODE in ["auto", "reuse"] and cache_is_complete(paths):
        print(f"Using cache: {paths['dir']}")
        return (
            pd.read_csv(paths["summary"]),
            pd.read_csv(paths["target_ts"]),
            pd.read_csv(paths["topk_ts"]),
            paths,
        )

    if CACHE_MODE == "reuse" and not cache_is_complete(paths):
        raise FileNotFoundError("CACHE_MODE='reuse' but complete cache files were not found.")

    print("Building cache from raw log...")
    summary = compute_summary_fast(path)
    target_ts, topk_ts = build_selected_timeseries(path, select_topk_keys(summary))

    summary.to_csv(paths["summary"], index=False)
    target_ts.to_csv(paths["target_ts"], index=False)
    topk_ts.to_csv(paths["topk_ts"], index=False)
    write_meta(paths, path)

    print(f"Saved cache summary: {paths['summary']}")
    print(f"Saved cache target time-series: {paths['target_ts']}")
    print(f"Saved cache Top-K time-series: {paths['topk_ts']}")
    return summary, target_ts, topk_ts, paths


def make_uniform_state_grid(df: pd.DataFrame, labels_order, bin_us: Optional[float] = None) -> pd.DataFrame:
    """
    Convert sparse occupancy update events into a dense label x time matrix.

    This is the main heatmap fix:
    - Do not pivot sparse events and fill missing columns with 0 directly.
    - First bin events onto a uniform time grid.
    - Then forward-fill within each connection if the log represents state updates.
    """
    if df.empty:
        return pd.DataFrame()

    bin_us = SAMPLE_INTERVAL_US if bin_us is None else bin_us
    if bin_us <= 0:
        raise ValueError("HEATMAP_BIN_US/SAMPLE_INTERVAL_US must be positive.")

    x = add_label_column(df)
    t_start = TIME_START_US if TIME_START_US is not None else math.floor(x["time"].min() / bin_us) * bin_us
    t_end = TIME_END_US if TIME_END_US is not None else math.ceil(x["time"].max() / bin_us) * bin_us
    if t_end < t_start:
        return pd.DataFrame()

    x = x.copy()
    x["time_bin"] = ((x["time"] - t_start) // bin_us).astype("int64")

    group_cols = GROUP_COLS + ["label", "time_bin"]
    if HEATMAP_AGG_METHOD == "max":
        binned = x.groupby(group_cols, sort=False, as_index=False)["occupancy"].max()
    elif HEATMAP_AGG_METHOD == "mean":
        binned = x.groupby(group_cols, sort=False, as_index=False)["occupancy"].mean()
    elif HEATMAP_AGG_METHOD == "last":
        # Only selected Top-K data are sorted here, not the full raw log.
        x = x.sort_values(GROUP_COLS + ["time"], kind="mergesort")
        binned = x.groupby(group_cols, sort=False, as_index=False)["occupancy"].last()
    else:
        raise ValueError("HEATMAP_AGG_METHOD must be 'last', 'max', or 'mean'.")

    n_bins = int(round((t_end - t_start) / bin_us)) + 1
    all_bins = pd.Index(range(n_bins), name="time_bin")
    label_to_series = []

    for label in labels_order:
        g = binned[binned["label"] == label][["time_bin", "occupancy"]]
        if g.empty:
            s = pd.Series(0.0, index=all_bins, name=label)
        else:
            g = g.drop_duplicates("time_bin", keep="last").set_index("time_bin").reindex(all_bins)
            if HEATMAP_FORWARD_FILL:
                s = g["occupancy"].ffill().fillna(0.0)
            else:
                s = g["occupancy"].fillna(0.0)
            s.name = label
        label_to_series.append(s)

    matrix = pd.DataFrame(label_to_series)
    matrix.columns = [t_start + i * bin_us for i in range(n_bins)]
    return matrix


def complete_single_timeseries(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or not COMPLETE_SINGLE_TIMESERIES:
        return df
    labels = add_label_column(df)["label"].drop_duplicates().tolist()
    grid = make_uniform_state_grid(df, labels, bin_us=SAMPLE_INTERVAL_US)
    rows = []
    label_to_keys = add_label_column(df).drop_duplicates("label").set_index("label")[GROUP_COLS]
    for label, row in grid.iterrows():
        keys = label_to_keys.loc[label]
        tmp = pd.DataFrame({"time": grid.columns.astype(float), "occupancy": row.values})
        for c in GROUP_COLS:
            tmp[c] = int(keys[c])
        rows.append(tmp[COLUMNS])
    return pd.concat(rows, ignore_index=True) if rows else df


def save_figure(fig, name: str):
    paths = []
    if SAVE_PNG:
        png_path = os.path.join(OUT_DIR, f"{name}.png")
        fig.savefig(png_path, bbox_inches="tight", dpi=300)
        paths.append(png_path)
    if SAVE_PDF:
        pdf_path = os.path.join(OUT_DIR, f"{name}.pdf")
        fig.savefig(pdf_path, bbox_inches="tight")
        paths.append(pdf_path)
    for p in paths:
        print(f"Saved: {p}")


def plot_single_connection(target_ts: pd.DataFrame, suffix: str = ""):
    if target_ts.empty:
        print("Warning: no target connection data for single plot.")
        return

    target_ts = complete_single_timeseries(target_ts)
    fig, ax = plt.subplots(figsize=(7.2, 4.2))

    for idx, (keys, g) in enumerate(target_ts.groupby(GROUP_COLS, sort=False)):
        g = g.sort_values("time", kind="mergesort")
        color = LINE_COLORS[idx % len(LINE_COLORS)]
        ax.step(g["time"], g["occupancy"], where="post", linewidth=2.2, color=color, label=connection_label(keys))
        ax.fill_between(g["time"], 0, g["occupancy"], where=(g["occupancy"] > 0), step="post", alpha=0.18, color=color)

    if BUFFER_CAPACITY is not None:
        ax.axhline(BUFFER_CAPACITY, linestyle="--", linewidth=1.5, color="black", alpha=0.75, label="Buffer capacity")

    ax.set_xlabel("Time (us)")
    ax.set_ylabel("Out-of-order Buffer Occupancy (pkts)")
    ax.set_ylim(bottom=0)
    ax.grid(True, which="both", linestyle=":", linewidth=0.75, alpha=0.75)
    if SHOW_TITLE:
        ax.set_title("Out-of-order Buffer Occupancy")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.20), ncol=2, frameon=False)
    plt.tight_layout(rect=[0, 0, 1, 0.92])
    save_figure(fig, f"{OUT_NAME}_single{suffix}")
    plt.close(fig)


def plot_topk_heatmap(topk_ts: pd.DataFrame, summary: pd.DataFrame, suffix: str = ""):
    if topk_ts.empty or summary.empty:
        print("Warning: no Top-K data for heatmap.")
        return

    top = summary.head(TOP_K_CONNECTIONS).copy()
    top = add_label_column(top) if "label" not in top.columns else top
    ordered_labels = top["label"].tolist()

    matrix = make_uniform_state_grid(topk_ts, ordered_labels, bin_us=HEATMAP_BIN_US)
    matrix = matrix.loc[[x for x in ordered_labels if x in matrix.index]]
    if matrix.empty:
        print("Warning: empty heatmap matrix after state-grid conversion.")
        return

    fig_height = max(3.2, 0.30 * len(matrix) + 1.8)
    fig, ax = plt.subplots(figsize=(7.8, fig_height))
    im = ax.imshow(matrix.values, aspect="auto", interpolation="nearest", origin="upper")

    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index)
    ax.set_xlabel("Time (us)")
    ax.set_ylabel("Connection")

    times = matrix.columns.to_numpy(dtype=float)
    n_ticks = min(6, len(times))
    if n_ticks > 0:
        if n_ticks > 1:
            tick_pos = [int(round(i)) for i in pd.Series(range(len(times))).quantile([x / (n_ticks - 1) for x in range(n_ticks)]).tolist()]
        else:
            tick_pos = [0]
        tick_pos = sorted(set(max(0, min(len(times) - 1, p)) for p in tick_pos))
        ax.set_xticks(tick_pos)
        ax.set_xticklabels([f"{times[i]:.1f}" for i in tick_pos])

    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("Occupancy (pkts)")
    if SHOW_TITLE:
        ax.set_title(f"Top-{TOP_K_CONNECTIONS} Out-of-order Buffer Occupancy")
    plt.tight_layout()
    save_figure(fig, f"{OUT_NAME}_heatmap{suffix}")
    plt.close(fig)


def plot_summary(summary: pd.DataFrame, suffix: str = ""):
    if summary.empty:
        print("Warning: no data for summary.")
        return

    top = summary.head(TOP_K_CONNECTIONS).copy()
    top = add_label_column(top) if "label" not in top.columns else top
    top = top.iloc[::-1]
    y = range(len(top))

    fig_height = max(3.2, 0.32 * len(top) + 1.8)
    fig, ax = plt.subplots(figsize=(7.2, fig_height))
    ax.barh(y, top["max"], height=0.62, label="Max")
    if "p99" in top.columns and top["p99"].notna().any():
        ax.scatter(top["p99"], y, marker="o", s=34, label="P99")
    ax.scatter(top["mean"], y, marker="x", s=38, label="Mean")

    ax.set_yticks(list(y))
    ax.set_yticklabels(top["label"])
    ax.set_xlabel("Out-of-order Buffer Occupancy (pkts)")
    ax.set_ylabel("Connection")
    ax.set_xlim(left=0)
    ax.grid(True, axis="x", linestyle=":", linewidth=0.75, alpha=0.75)
    if SHOW_TITLE:
        ax.set_title("Out-of-order Occupancy Summary")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.16), ncol=3, frameon=False)
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    save_figure(fig, f"{OUT_NAME}_summary{suffix}")
    plt.close(fig)


def collect_results(config):
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
            data[algo][sz] = config[algo].get(sz, float("nan"))
    return algorithms, sizes, data


def main(suffix: str = ""):
    ensure_dir(OUT_DIR)
    summary, target_ts, topk_ts, _ = build_or_load_cache(OOO_FILE)

    summary_path = os.path.join(OUT_DIR, f"{OUT_NAME}_summary_stats{suffix}.csv")
    summary.to_csv(summary_path, index=False)
    print(f"Saved summary copy: {summary_path}")

    if PLOT_MODE in ["single", "all"]:
        plot_single_connection(target_ts, suffix)
    if PLOT_MODE in ["heatmap", "all"]:
        plot_topk_heatmap(topk_ts, summary, suffix)
    if PLOT_MODE in ["summary", "all"]:
        plot_summary(summary, suffix)


if __name__ == "__main__":
    algo_name, size, data = collect_results(CONFIG_LIST)

    for i, sz in enumerate(size):
        for j, algo in enumerate(algo_name):
            BASE_DIR = data[algo_name[j]][sz]
            if not isinstance(BASE_DIR, str):
                continue

            OOO_FILE = os.path.join(BASE_DIR, "ooo_buffer.txt")
            OUT_DIR = BASE_DIR
            OUT_CNT += 1

            if not os.path.exists(OOO_FILE):
                print(f"[{OUT_CNT}] Warning: required file does not exist, skipping: {OOO_FILE}")
                continue

            suffix = f"_{algo}".replace("/", "-").replace(" ", "")
            first_png = os.path.join(OUT_DIR, f"{OUT_NAME}_single{suffix}.png")
            if SKIP_IF_EXISTS and os.path.exists(first_png):
                print(f"[{OUT_CNT}] Info: image already exists, skipping: {first_png}")
                continue

            print(f"[{OUT_CNT}] Processing [{algo}][{sz}]: {OOO_FILE}")
            main(suffix=suffix)
