#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plotter for sampled out-of-order buffer occupancy logs.

New input format for ooo.txt:
    time src dst sport dport ooo_buffer_size

Semantics:
1) The monitor samples every SAMPLE_PERIOD_US, e.g., 10 us.
2) For each QP, the logged value is the peak out-of-order buffer occupancy
   within that sampling interval.
3) If a QP's sampled value is unchanged from the previous sampling instant,
   the monitor suppresses this line.
4) Therefore, missing samples between two records of the same QP are treated
   as state continuation / forward-fill.
5) If a QP never appears again after its last record, the default policy assumes
   that the QP ends after that last sampling interval, and inserts a zero state
   for plotting after one sampling period.

Cache design:
- Base cache stores normalized sparse events and interval-weighted per-QP summary.
- Base cache is independent of TOPK_SORT_BY and TOP_K_CONNECTIONS.
- Changing TOPK_SORT_BY among max/mean/p99/nonzero_ratio reuses the base cache.
"""

import os
import json
import math
import hashlib
from typing import Dict, List, Optional, Tuple

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
    # "default": {
    #     "single": ".",
    # },

    # "algo_files_1024GPU": {
    #     "1": "/home/dcn1/fxb/simulator/output/aps-v2_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAll2All_1024g_EP8_128M",
    # }
}

# 如果本文件的 CONFIG_LIST 为空，则使用共享配置文件中的 CONFIG_LIST
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
if not CONFIG_LIST:
    from configs.result_path import CONFIG_LIST

BASE_DIR = "."
OOO_FILE = os.path.join(BASE_DIR, "ooo.txt")
OUT_DIR = BASE_DIR
OUT_NAME = "ooo_buffer_occupancy"
OUT_CNT = 0

# Target connection for single-connection plot. None means no restriction.
# alltoall
TARGET_SRC_IDS = [0]
TARGET_DST_IDS = [128]
TARGET_SRC_PORTS = [10000]
TARGET_DST_PORTS = [100]

# allreduce
# TARGET_SRC_IDS = [504]
# TARGET_DST_IDS = [512]
# TARGET_SRC_PORTS = [10000]
# TARGET_DST_PORTS = [100]

# Time range in us. None means no restriction.
# Note: for sparse sampled logs, intervals are clipped after state reconstruction.
TIME_START_US = None
TIME_END_US = None

# Input and sampling semantics.
TIME_UNIT_IN_FILE = "ns"          # "ns" or "us"
INPUT_FORMAT = "mixed"           # "whitespace" or "mixed"; mixed supports comma/space header
SAMPLE_PERIOD_US = 10.0           # monitor sampling period, e.g., 10 us
SAMPLE_INDEX_BASE_US = 0.0        # usually 0.0; used to map timestamps to sample indexes
SAME_SAMPLE_AGG = "max"           # duplicate same-QP same-sample records: "max" or "last"

# How to handle the last record of each QP.
# "zero_after_last": value is valid for one sample interval; then QP is considered ended. Recommended.
# "global_end":       value is forward-filled to the global trace end. Use only if QPs remain active silently.
# "no_tail_zero":     same statistics as zero_after_last, but plotting does not append the explicit zero point.
QP_END_POLICY = "zero_after_last"

# Plot mode: "single", "heatmap", "summary", "all"
PLOT_MODE = "all"

# Top-K selection.
TOP_K_CONNECTIONS = 8
TOPK_SORT_BY = "max"             # "max", "p99", "mean", "nonzero_ratio", "duration_us"
P99_QUANTILE = 0.99

# Heatmap rendering.
# For sampled logs, the heatmap grid should normally use SAMPLE_PERIOD_US.
HEATMAP_BIN_US = None             # None -> SAMPLE_PERIOD_US
HEATMAP_MAX_BINS = 5000           # downsample only for rendering if the grid is too wide
HEATMAP_DOWNSAMPLE_METHOD = "max" # "max", "mean", "last"

BUFFER_CAPACITY = None
SHOW_TITLE = False
SAVE_PDF = False
SAVE_PNG = True
SKIP_EXISTING_FIGURE = True

CACHE_ENABLED = True
CACHE_MODE = "auto"               # "auto", "reuse", "rebuild", "off"
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


def sample_index_from_time_us(time_us: pd.Series) -> pd.Series:
    if SAMPLE_PERIOD_US <= 0:
        raise ValueError("SAMPLE_PERIOD_US must be positive.")
    # round avoids 9.999999999 / 10.0 becoming the previous bin.
    return np.rint((time_us - SAMPLE_INDEX_BASE_US) / SAMPLE_PERIOD_US).astype("int64")


def sample_index_to_time_us(idx) -> np.ndarray:
    return SAMPLE_INDEX_BASE_US + np.asarray(idx, dtype="float64") * SAMPLE_PERIOD_US


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
    df = df.copy()
    if df.empty:
        df["label"] = []
        return df
    df["label"] = (
        df["src_id"].astype(int).astype(str)
        + ":" + df["src_port"].astype(int).astype(str)
        + "->" + df["dst_id"].astype(int).astype(str)
        + ":" + df["dst_port"].astype(int).astype(str)
    )
    return df


def normalize_target_list(v):
    if v is None:
        return None
    return [int(x) for x in v]


def filter_target_connection(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df
    if TARGET_SRC_IDS is not None:
        out = out[out["src_id"].isin(TARGET_SRC_IDS)]
    if TARGET_DST_IDS is not None:
        out = out[out["dst_id"].isin(TARGET_DST_IDS)]
    if TARGET_SRC_PORTS is not None:
        out = out[out["src_port"].isin(TARGET_SRC_PORTS)]
    if TARGET_DST_PORTS is not None:
        out = out[out["dst_port"].isin(TARGET_DST_PORTS)]
    return out


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    # Header lines such as "time, src, dst, sport, dport, ooo_buffer_size"
    # are automatically coerced to NaN and dropped.
    for c in COLUMNS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=COLUMNS)
    if df.empty:
        return pd.DataFrame(columns=COLUMNS + ["sample_idx"])

    df["time"] = time_to_us(df["time"])
    df["sample_idx"] = sample_index_from_time_us(df["time"])
    # Re-snap time to the sampling grid to avoid floating-point drift.
    df["time"] = sample_index_to_time_us(df["sample_idx"])

    for c in ID_COLS:
        df[c] = df[c].astype("int32")
    df["occupancy"] = df["occupancy"].astype("float32")
    df["sample_idx"] = df["sample_idx"].astype("int64")
    return df[COLUMNS + ["sample_idx"]]


def read_ooo_iter(path: str):
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
        on_bad_lines="skip",
    )

    if READ_IN_CHUNKS:
        for chunk in pd.read_csv(path, chunksize=CHUNK_SIZE, **kwargs):
            norm = normalize_df(chunk)
            if not norm.empty:
                yield norm
    else:
        norm = normalize_df(pd.read_csv(path, **kwargs))
        if not norm.empty:
            yield norm


def read_all_events(path: str) -> pd.DataFrame:
    chunks = list(read_ooo_iter(path))
    if not chunks:
        return pd.DataFrame(columns=COLUMNS + ["sample_idx"])
    events = pd.concat(chunks, ignore_index=True)
    return deduplicate_events(events)


def deduplicate_events(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return events

    # For a sampled peak log, duplicate records for the same QP and same sample
    # should not normally exist. If they do, max is safer for peak semantics.
    group = GROUP_COLS + ["sample_idx"]
    if SAME_SAMPLE_AGG == "max":
        out = events.groupby(group, sort=False, as_index=False).agg(
            time=("time", "last"),
            occupancy=("occupancy", "max"),
        )
        out = out[COLUMNS + ["sample_idx"]]
    elif SAME_SAMPLE_AGG == "last":
        out = events.drop_duplicates(group, keep="last")
    else:
        raise ValueError("SAME_SAMPLE_AGG must be 'max' or 'last'.")

    return out.sort_values(GROUP_COLS + ["sample_idx"], kind="mergesort").reset_index(drop=True)


def processing_config_for_base_cache() -> Dict:
    """Only include options that affect base reconstructed data, not Top-K sorting or plot cosmetics."""
    return {
        "time_start_us": TIME_START_US,
        "time_end_us": TIME_END_US,
        "time_unit_in_file": TIME_UNIT_IN_FILE,
        "input_format": INPUT_FORMAT,
        "sample_period_us": SAMPLE_PERIOD_US,
        "sample_index_base_us": SAMPLE_INDEX_BASE_US,
        "same_sample_agg": SAME_SAMPLE_AGG,
        "qp_end_policy": QP_END_POLICY,
        "p99_quantile": P99_QUANTILE,
    }


def short_hash(obj: Dict, n: int = 12) -> str:
    return hashlib.md5(json.dumps(obj, sort_keys=True).encode("utf-8")).hexdigest()[:n]


def base_cache_prefix(raw_path: str) -> str:
    st = os.stat(raw_path)
    signature = {
        "path": os.path.abspath(raw_path),
        "size": st.st_size,
        "mtime_ns": st.st_mtime_ns,
        "config": processing_config_for_base_cache(),
    }
    return f"{OUT_NAME}_sampled_base_{short_hash(signature)}"


def cache_paths(raw_path: str) -> Dict[str, str]:
    cache_dir = os.path.join(OUT_DIR, CACHE_SUBDIR)
    prefix = base_cache_prefix(raw_path)
    topk_sig = {
        "base_prefix": prefix,
        "top_k_connections": TOP_K_CONNECTIONS,
        "topk_sort_by": TOPK_SORT_BY,
    }
    target_sig = {
        "base_prefix": prefix,
        "target_src_ids": normalize_target_list(TARGET_SRC_IDS),
        "target_dst_ids": normalize_target_list(TARGET_DST_IDS),
        "target_src_ports": normalize_target_list(TARGET_SRC_PORTS),
        "target_dst_ports": normalize_target_list(TARGET_DST_PORTS),
    }
    topk_prefix = f"{OUT_NAME}_topk_{TOPK_SORT_BY}_k{TOP_K_CONNECTIONS}_{short_hash(topk_sig, 8)}"
    target_prefix = f"{OUT_NAME}_target_{short_hash(target_sig, 8)}"
    return {
        "dir": cache_dir,
        "base_prefix": prefix,
        "meta": os.path.join(cache_dir, f"{prefix}_meta.json"),
        "events": os.path.join(cache_dir, f"{prefix}_events.pkl"),
        "summary": os.path.join(cache_dir, f"{prefix}_summary.csv"),
        "topk_events": os.path.join(cache_dir, f"{topk_prefix}_events.pkl"),
        "target_events": os.path.join(cache_dir, f"{target_prefix}_events.pkl"),
    }


def base_cache_complete(paths: Dict[str, str]) -> bool:
    return all(os.path.exists(paths[k]) for k in ["meta", "events", "summary"])


def write_meta(paths: Dict[str, str], raw_path: str):
    st = os.stat(raw_path)
    meta = {
        "raw_file": os.path.abspath(raw_path),
        "raw_size": st.st_size,
        "raw_mtime_ns": st.st_mtime_ns,
        "base_prefix": paths["base_prefix"],
        "config": processing_config_for_base_cache(),
        "note": "Base cache is independent of TOPK_SORT_BY and TOP_K_CONNECTIONS.",
    }
    with open(paths["meta"], "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def clip_interval_bounds(events: pd.DataFrame) -> Tuple[int, int]:
    if events.empty:
        return 0, 0
    if TIME_START_US is None:
        start_idx = int(events["sample_idx"].min())
    else:
        start_idx = int(math.ceil((TIME_START_US - SAMPLE_INDEX_BASE_US) / SAMPLE_PERIOD_US))

    if TIME_END_US is None:
        # Inclusive last sample index; interval end is exclusive.
        if QP_END_POLICY == "global_end":
            end_idx_excl = int(events["sample_idx"].max()) + 1
        else:
            end_idx_excl = int(events["sample_idx"].max()) + 2
    else:
        end_idx_excl = int(math.floor((TIME_END_US - SAMPLE_INDEX_BASE_US) / SAMPLE_PERIOD_US)) + 1

    return start_idx, max(start_idx, end_idx_excl)


def build_intervals(events: pd.DataFrame) -> pd.DataFrame:
    """
    Convert sparse sampled updates into interval representation.

    Each row means:
        occupancy is valid for sample indexes [start_idx, end_idx_excl).

    Missing samples between two update records of the same QP are forward-filled.
    The tail after the last update is controlled by QP_END_POLICY.
    """
    if events.empty:
        return pd.DataFrame(columns=GROUP_COLS + ["label", "start_idx", "end_idx_excl", "count", "occupancy"])

    e = events.sort_values(GROUP_COLS + ["sample_idx"], kind="mergesort").copy()
    e["next_idx"] = e.groupby(GROUP_COLS, sort=False)["sample_idx"].shift(-1)

    if QP_END_POLICY == "global_end":
        global_last_excl = int(e["sample_idx"].max()) + 1
        e["end_idx_excl"] = e["next_idx"].fillna(global_last_excl).astype("int64")
    elif QP_END_POLICY in ["zero_after_last", "no_tail_zero"]:
        e["end_idx_excl"] = e["next_idx"].fillna(e["sample_idx"] + 1).astype("int64")
    else:
        raise ValueError("QP_END_POLICY must be 'zero_after_last', 'global_end', or 'no_tail_zero'.")

    e["start_idx"] = e["sample_idx"].astype("int64")
    # Guard against malformed duplicate / out-of-order samples.
    e["end_idx_excl"] = np.maximum(e["end_idx_excl"], e["start_idx"] + 1)

    clip_start, clip_end_excl = clip_interval_bounds(e)
    e["start_idx"] = np.maximum(e["start_idx"], clip_start)
    e["end_idx_excl"] = np.minimum(e["end_idx_excl"], clip_end_excl)
    e = e[e["end_idx_excl"] > e["start_idx"]].copy()
    e["count"] = (e["end_idx_excl"] - e["start_idx"]).astype("int64")
    e = add_label_column(e)
    return e[GROUP_COLS + ["label", "start_idx", "end_idx_excl", "count", "occupancy"]]


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    if len(values) == 0:
        return float("nan")
    order = np.argsort(values, kind="mergesort")
    v = values[order].astype("float64")
    w = weights[order].astype("float64")
    total = w.sum()
    if total <= 0:
        return float("nan")
    cutoff = q * total
    cumsum = np.cumsum(w)
    idx = int(np.searchsorted(cumsum, cutoff, side="left"))
    idx = max(0, min(idx, len(v) - 1))
    return float(v[idx])


def compute_summary_from_intervals(intervals: pd.DataFrame) -> pd.DataFrame:
    if intervals.empty:
        return pd.DataFrame(columns=GROUP_COLS + ["label", "count", "mean", "p99", "max", "nonzero_ratio", "duration_us"])

    x = intervals.copy()
    x["weighted_sum"] = x["occupancy"] * x["count"]
    x["nonzero_count"] = np.where(x["occupancy"] > 0, x["count"], 0)

    summary = x.groupby(GROUP_COLS, sort=False, as_index=False).agg(
        label=("label", "last"),
        count=("count", "sum"),
        weighted_sum=("weighted_sum", "sum"),
        max=("occupancy", "max"),
        nonzero_count=("nonzero_count", "sum"),
        first_idx=("start_idx", "min"),
        last_idx_excl=("end_idx_excl", "max"),
    )
    summary["mean"] = summary["weighted_sum"] / summary["count"].clip(lower=1)
    summary["nonzero_ratio"] = summary["nonzero_count"] / summary["count"].clip(lower=1)
    summary["duration_us"] = (summary["last_idx_excl"] - summary["first_idx"]).clip(lower=0) * SAMPLE_PERIOD_US

    p99_parts = []
    for keys, g in x.groupby(GROUP_COLS, sort=False):
        p99_parts.append((*keys, weighted_quantile(g["occupancy"].to_numpy(), g["count"].to_numpy(), P99_QUANTILE)))
    p99 = pd.DataFrame(p99_parts, columns=GROUP_COLS + ["p99"])
    summary = summary.merge(p99, on=GROUP_COLS, how="left")

    keep_cols = GROUP_COLS + ["label", "count", "mean", "p99", "max", "nonzero_ratio", "duration_us"]
    return summary[keep_cols]


def sorted_summary(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return summary
    if TOPK_SORT_BY not in summary.columns:
        raise ValueError(f"TOPK_SORT_BY={TOPK_SORT_BY!r} is not available. Valid columns: {list(summary.columns)}")
    return summary.sort_values(TOPK_SORT_BY, ascending=False, kind="mergesort").reset_index(drop=True)


def build_base_cache(raw_path: str, paths: Dict[str, str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    print("Building reusable base cache from raw ooo.txt ...")
    events = read_all_events(raw_path)
    if events.empty:
        summary = compute_summary_from_intervals(pd.DataFrame())
    else:
        intervals = build_intervals(events)
        summary = compute_summary_from_intervals(intervals)

    events.to_pickle(paths["events"])
    summary.to_csv(paths["summary"], index=False)
    write_meta(paths, raw_path)
    print(f"Saved base events cache: {paths['events']}")
    print(f"Saved base summary cache: {paths['summary']}")
    return events, summary


def load_or_build_base(raw_path: str, paths: Dict[str, str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    ensure_dir(paths["dir"])

    if not CACHE_ENABLED or CACHE_MODE == "off":
        print("Cache disabled: reading raw ooo.txt.")
        events = read_all_events(raw_path)
        intervals = build_intervals(events)
        summary = compute_summary_from_intervals(intervals)
        return events, summary

    if CACHE_MODE in ["auto", "reuse"] and base_cache_complete(paths):
        print(f"Using reusable base cache: {paths['base_prefix']}")
        events = pd.read_pickle(paths["events"])
        summary = pd.read_csv(paths["summary"])
        return events, summary

    if CACHE_MODE == "reuse" and not base_cache_complete(paths):
        raise FileNotFoundError("CACHE_MODE='reuse' but reusable base cache files were not found.")

    return build_base_cache(raw_path, paths)


def get_target_events(events: pd.DataFrame, paths: Dict[str, str]) -> pd.DataFrame:
    if CACHE_ENABLED and CACHE_MODE != "off" and CACHE_MODE != "rebuild" and os.path.exists(paths["target_events"]):
        return pd.read_pickle(paths["target_events"])
    target = filter_target_connection(events)
    if CACHE_ENABLED and CACHE_MODE != "off":
        target.to_pickle(paths["target_events"])
    return target


def topk_keys(summary: pd.DataFrame) -> pd.DataFrame:
    top = sorted_summary(summary).head(TOP_K_CONNECTIONS)
    return top[GROUP_COLS].copy()


def get_topk_events(events: pd.DataFrame, summary: pd.DataFrame, paths: Dict[str, str]) -> pd.DataFrame:
    if CACHE_ENABLED and CACHE_MODE != "off" and CACHE_MODE != "rebuild" and os.path.exists(paths["topk_events"]):
        print(f"Using Top-K cache for sort_by={TOPK_SORT_BY}: {paths['topk_events']}")
        return pd.read_pickle(paths["topk_events"])

    keys = topk_keys(summary)
    if keys.empty or events.empty:
        topk = pd.DataFrame(columns=events.columns)
    else:
        topk = events.merge(keys.drop_duplicates(GROUP_COLS), on=GROUP_COLS, how="inner")
        topk = topk.sort_values(GROUP_COLS + ["sample_idx"], kind="mergesort").reset_index(drop=True)

    if CACHE_ENABLED and CACHE_MODE != "off":
        topk.to_pickle(paths["topk_events"])
        print(f"Saved Top-K cache for sort_by={TOPK_SORT_BY}: {paths['topk_events']}")
    return topk


def load_data(raw_path: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, str]]:
    paths = cache_paths(raw_path)
    events, summary = load_or_build_base(raw_path, paths)
    target_events = get_target_events(events, paths)
    topk_events = get_topk_events(events, summary, paths)
    return summary, target_events, topk_events, paths


def intervals_for_events(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame(columns=GROUP_COLS + ["label", "start_idx", "end_idx_excl", "count", "occupancy"])
    return build_intervals(deduplicate_events(events))


def figure_time_bounds_from_intervals(intervals: pd.DataFrame) -> Tuple[int, int]:
    if intervals.empty:
        return 0, 0
    if TIME_START_US is None:
        start_idx = int(intervals["start_idx"].min())
    else:
        start_idx = int(math.ceil((TIME_START_US - SAMPLE_INDEX_BASE_US) / SAMPLE_PERIOD_US))

    if TIME_END_US is None:
        end_idx_excl = int(intervals["end_idx_excl"].max())
    else:
        end_idx_excl = int(math.floor((TIME_END_US - SAMPLE_INDEX_BASE_US) / SAMPLE_PERIOD_US)) + 1
    return start_idx, max(start_idx, end_idx_excl)


def downsample_matrix_for_display(matrix: pd.DataFrame, max_bins: int) -> pd.DataFrame:
    if matrix.empty or matrix.shape[1] <= max_bins or max_bins <= 0:
        return matrix

    factor = int(math.ceil(matrix.shape[1] / max_bins))
    arr = matrix.to_numpy()
    n_rows, n_cols = arr.shape
    pad = (-n_cols) % factor
    if pad > 0:
        arr = np.pad(arr, ((0, 0), (0, pad)), mode="edge")
    arr3 = arr.reshape(n_rows, -1, factor)

    if HEATMAP_DOWNSAMPLE_METHOD == "max":
        ds = arr3.max(axis=2)
    elif HEATMAP_DOWNSAMPLE_METHOD == "mean":
        ds = arr3.mean(axis=2)
    elif HEATMAP_DOWNSAMPLE_METHOD == "last":
        ds = arr3[:, :, -1]
    else:
        raise ValueError("HEATMAP_DOWNSAMPLE_METHOD must be 'max', 'mean', or 'last'.")

    old_cols = matrix.columns.to_numpy(dtype="float64")
    new_cols = []
    for i in range(ds.shape[1]):
        src_idx = min(i * factor, len(old_cols) - 1)
        new_cols.append(old_cols[src_idx])
    return pd.DataFrame(ds, index=matrix.index, columns=new_cols)


def make_state_matrix(events: pd.DataFrame, labels_order: List[str]) -> pd.DataFrame:
    intervals = intervals_for_events(events)
    if intervals.empty:
        return pd.DataFrame()

    # Use sample-period state grid first; optionally downsample only for display.
    start_idx, end_idx_excl = figure_time_bounds_from_intervals(intervals)
    if end_idx_excl <= start_idx:
        return pd.DataFrame()

    sample_indexes = np.arange(start_idx, end_idx_excl, dtype="int64")
    columns = sample_index_to_time_us(sample_indexes)
    label_to_series = []

    for label in labels_order:
        g = intervals[intervals["label"] == label]
        values = np.zeros(len(sample_indexes), dtype="float32")
        for row in g.itertuples(index=False):
            s = max(int(row.start_idx), start_idx) - start_idx
            e = min(int(row.end_idx_excl), end_idx_excl) - start_idx
            if e > s:
                values[s:e] = float(row.occupancy)
        label_to_series.append(pd.Series(values, index=columns, name=label))

    matrix = pd.DataFrame(label_to_series)
    matrix = downsample_matrix_for_display(matrix, HEATMAP_MAX_BINS)

    # If the user explicitly requests a coarser HEATMAP_BIN_US, apply an additional aggregation.
    bin_us = SAMPLE_PERIOD_US if HEATMAP_BIN_US is None else HEATMAP_BIN_US
    if bin_us > SAMPLE_PERIOD_US and not matrix.empty:
        factor = max(1, int(round(bin_us / SAMPLE_PERIOD_US)))
        old_max = HEATMAP_MAX_BINS
        try:
            # Temporarily downsample by the requested factor; then respect HEATMAP_MAX_BINS.
            arr = pd.DataFrame(matrix.to_numpy(), index=matrix.index, columns=matrix.columns)
            n_cols = arr.shape[1]
            pad = (-n_cols) % factor
            raw = arr.to_numpy()
            if pad > 0:
                raw = np.pad(raw, ((0, 0), (0, pad)), mode="edge")
            raw3 = raw.reshape(raw.shape[0], -1, factor)
            if HEATMAP_DOWNSAMPLE_METHOD == "max":
                ds = raw3.max(axis=2)
            elif HEATMAP_DOWNSAMPLE_METHOD == "mean":
                ds = raw3.mean(axis=2)
            else:
                ds = raw3[:, :, -1]
            cols = [matrix.columns[min(i * factor, len(matrix.columns) - 1)] for i in range(ds.shape[1])]
            matrix = pd.DataFrame(ds, index=matrix.index, columns=cols)
            matrix = downsample_matrix_for_display(matrix, old_max)
        except Exception:
            pass

    return matrix


def save_figure(fig, name: str):
    paths = []
    if SAVE_PNG:
        png_path = os.path.join(OUT_DIR, f"{name}.png")
        if SKIP_EXISTING_FIGURE and os.path.exists(png_path):
            print(f"Info: figure already exists, skip saving: {png_path}")
        else:
            fig.savefig(png_path, bbox_inches="tight", dpi=300)
            paths.append(png_path)
    if SAVE_PDF:
        pdf_path = os.path.join(OUT_DIR, f"{name}.pdf")
        if SKIP_EXISTING_FIGURE and os.path.exists(pdf_path):
            print(f"Info: figure already exists, skip saving: {pdf_path}")
        else:
            fig.savefig(pdf_path, bbox_inches="tight")
            paths.append(pdf_path)
    for p in paths:
        print(f"Saved: {p}")


def plot_single_connection(target_events: pd.DataFrame, suffix: str = ""):
    if target_events.empty:
        print("Warning: no target connection data for single plot.")
        return

    intervals = intervals_for_events(target_events)
    if intervals.empty:
        print("Warning: no target intervals for single plot.")
        return

    fig, ax = plt.subplots(figsize=(7.2, 4.2))

    for idx, (keys, g) in enumerate(intervals.groupby(GROUP_COLS, sort=False)):
        g = g.sort_values("start_idx", kind="mergesort")
        color = LINE_COLORS[idx % len(LINE_COLORS)]
        xs = []
        ys = []
        for row in g.itertuples(index=False):
            xs.append(float(sample_index_to_time_us([row.start_idx])[0]))
            ys.append(float(row.occupancy))
        if QP_END_POLICY != "no_tail_zero":
            last_end = int(g["end_idx_excl"].max())
            xs.append(float(sample_index_to_time_us([last_end])[0]))
            ys.append(0.0)

        ax.step(xs, ys, where="post", linewidth=2.2, color=color, label=connection_label(keys))
        ax.fill_between(xs, 0, ys, step="post", alpha=0.18, color=color)

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


def plot_topk_heatmap(topk_events: pd.DataFrame, summary: pd.DataFrame, suffix: str = ""):
    if topk_events.empty or summary.empty:
        print("Warning: no Top-K data for heatmap.")
        return

    top = sorted_summary(summary).head(TOP_K_CONNECTIONS).copy()
    if "label" not in top.columns:
        top = add_label_column(top)
    ordered_labels = top["label"].tolist()

    matrix = make_state_matrix(topk_events, ordered_labels)
    matrix = matrix.loc[[x for x in ordered_labels if x in matrix.index]]
    if matrix.empty:
        print("Warning: empty heatmap matrix.")
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
            tick_pos = np.linspace(0, len(times) - 1, n_ticks).round().astype(int)
        else:
            tick_pos = np.array([0], dtype=int)
        tick_pos = sorted(set(int(max(0, min(len(times) - 1, p))) for p in tick_pos))
        ax.set_xticks(tick_pos)
        ax.set_xticklabels([f"{times[i]:.1f}" for i in tick_pos])

    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("Peak Occupancy per Sample (pkts)")
    if SHOW_TITLE:
        ax.set_title(f"Top-{TOP_K_CONNECTIONS} Out-of-order Buffer Occupancy")
    plt.tight_layout()
    save_figure(fig, f"{OUT_NAME}_heatmap_top{TOP_K_CONNECTIONS}_{TOPK_SORT_BY}{suffix}")
    plt.close(fig)


def plot_summary(summary: pd.DataFrame, suffix: str = ""):
    if summary.empty:
        print("Warning: no data for summary.")
        return

    top = sorted_summary(summary).head(TOP_K_CONNECTIONS).copy()
    if "label" not in top.columns:
        top = add_label_column(top)
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
    save_figure(fig, f"{OUT_NAME}_summary_top{TOP_K_CONNECTIONS}_{TOPK_SORT_BY}{suffix}")
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
    summary, target_events, topk_events, _ = load_data(OOO_FILE)

    summary_out = sorted_summary(summary)
    summary_path = os.path.join(OUT_DIR, f"{OUT_NAME}_summary_stats{suffix}.csv")
    summary_out.to_csv(summary_path, index=False)
    print(f"Saved summary copy: {summary_path}")

    if PLOT_MODE in ["single", "all"]:
        plot_single_connection(target_events, suffix)
    if PLOT_MODE in ["heatmap", "all"]:
        plot_topk_heatmap(topk_events, summary, suffix)
    if PLOT_MODE in ["summary", "all"]:
        plot_summary(summary, suffix)


if __name__ == "__main__":
    algo_name, size, data = collect_results(CONFIG_LIST)

    for i, sz in enumerate(size):
        for j, algo in enumerate(algo_name):
            BASE_DIR = data[algo_name[j]][sz]
            if not isinstance(BASE_DIR, str):
                continue

            OOO_FILE = os.path.join(BASE_DIR, "ooo.txt")
            OUT_DIR = BASE_DIR
            OUT_CNT += 1

            if not os.path.exists(OOO_FILE):
                print(f"[{OUT_CNT}] Warning: required file does not exist, skipping: {OOO_FILE}")
                continue

            suffix = f"_{algo}_{sz}".replace("/", "-").replace(" ", "")
            print(f"[{OUT_CNT}] Processing [{algo}][{sz}]: {OOO_FILE}")
            main(suffix=suffix)
