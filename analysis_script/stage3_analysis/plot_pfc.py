#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PFC log analysis script.

Input file: pfc.txt

Each row format:
    time_ns device_id device_type port_id pfc_state

Column meaning:
    time_ns      : time when interface PFC state changes
    device_id    : device id
    device_type  : 0 = NIC, 1 = switch
    port_id      : interface / port id
    pfc_state    : 1 = paused by PFC, 0 = resumed

Output:
    For each experiment directory, generate:
        - overall PFC event timeline
        - active paused-interface count over time
        - top-device PFC heatmap
        - top-device pause statistics
        - per-device PFC state timeline
        - per-device per-port pause duration
        - CSV summary files
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# 1. Input configuration
# ============================================================
CONFIG_LIST = {


}

# 如果本文件的CONFIG_LIST为空，则使用共享配置文件中的 CONFIG_LIST
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
if not CONFIG_LIST:
    from configs.result_path import CONFIG_LIST


# ============================================================
# 2. Analysis configuration
# ============================================================

PFC_FILENAME = "pfc.txt"

# Output directory name under each experiment directory.
OUTPUT_DIRNAME = "pfc_analysis"

# Time bin for global aggregation.
# Example:
#   10_000 ns = 10 us
#   100_000 ns = 100 us
#   1_000_000 ns = 1 ms
TIME_BIN_NS = 10_000

# Number of top devices shown in global heatmap / ranking figures.
TOP_N_DEVICES = 30

# Local device analysis.
# If empty, the script will automatically select top devices by pause-event count.
TARGET_DEVICES: List[int] = [1004, 236, 364, 492]

# If TARGET_DEVICES is empty, analyze top K devices locally.
AUTO_LOCAL_TOP_K = 3

# Restrict local analysis to a device type or analyze all types.
# None = no restriction.
# 0 = NIC only.
# 1 = switch only.
TARGET_DEVICE_TYPE: Optional[int] = None

# Figure formats.
SAVE_PDF = False
SAVE_PNG = True

# Time axis unit.
# Supported: "ns", "us", "ms", "s"
TIME_UNIT = "us"

DEVICE_TYPE_NAME = {
    0: "NIC",
    1: "SW",
}


# ============================================================
# 3. Plot style
# ============================================================

def setup_matplotlib_style() -> None:
    plt.rcParams.update({
        "figure.figsize": (9.0, 4.8),
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "font.size": 11,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "legend.fontsize": 10,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": "--",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })


def get_time_scale(unit: str) -> Tuple[float, str]:
    unit = unit.lower()
    if unit == "ns":
        return 1.0, "Time (ns)"
    if unit == "us":
        return 1e3, "Time (us)"
    if unit == "ms":
        return 1e6, "Time (ms)"
    if unit == "s":
        return 1e9, "Time (s)"
    raise ValueError(f"Unsupported TIME_UNIT: {unit}")


def save_figure(fig: plt.Figure, out_dir: Path, name: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    if SAVE_PDF:
        fig.savefig(out_dir / f"{name}.pdf", bbox_inches="tight")
    if SAVE_PNG:
        fig.savefig(out_dir / f"{name}.png", bbox_inches="tight")

    plt.close(fig)


# ============================================================
# 4. Data loading and preprocessing
# ============================================================

def load_pfc_file(pfc_path: Path) -> pd.DataFrame:
    if not pfc_path.exists():
        raise FileNotFoundError(f"Cannot find {pfc_path}")

    df = pd.read_csv(
        pfc_path,
        sep=r"\s+",
        header=None,
        comment="#",
        names=["time_ns", "device_id", "device_type", "port_id", "pfc_state"],
        dtype={
            "time_ns": np.int64,
            "device_id": np.int64,
            "device_type": np.int64,
            "port_id": np.int64,
            "pfc_state": np.int64,
        },
    )

    if df.empty:
        raise ValueError(f"{pfc_path} is empty")

    df = df.sort_values(["time_ns", "device_type", "device_id", "port_id"]).reset_index(drop=True)

    valid_states = set(df["pfc_state"].unique())
    if not valid_states.issubset({0, 1}):
        raise ValueError(f"Invalid pfc_state found in {pfc_path}: {valid_states}")

    df["device_type_name"] = df["device_type"].map(DEVICE_TYPE_NAME).fillna("UNKNOWN")
    df["device_key"] = df["device_type_name"] + "-" + df["device_id"].astype(str)

    return df


def add_time_bin(df: pd.DataFrame, time_bin_ns: int) -> pd.DataFrame:
    df = df.copy()
    t0 = df["time_ns"].min()
    df["rel_time_ns"] = df["time_ns"] - t0
    df["time_bin"] = (df["rel_time_ns"] // time_bin_ns).astype(np.int64)
    df["bin_start_ns"] = df["time_bin"] * time_bin_ns
    return df


# ============================================================
# 5. Reconstruct PFC pause intervals
# ============================================================

def reconstruct_pause_intervals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reconstruct pause intervals for each (device_type, device_id, port_id).

    If a port receives state=1, it enters PFC pause.
    If it later receives state=0, the pause interval ends.

    If the final state is still pause, the interval is closed at the last timestamp
    of the whole trace.
    """
    max_time = int(df["time_ns"].max())
    records = []

    group_cols = ["device_type", "device_id", "port_id"]

    for (device_type, device_id, port_id), g in df.groupby(group_cols):
        g = g.sort_values("time_ns")

        active = False
        start_time = None

        for row in g.itertuples(index=False):
            t = int(row.time_ns)
            state = int(row.pfc_state)

            if state == 1:
                if not active:
                    active = True
                    start_time = t
                else:
                    # Duplicate pause signal before resume.
                    # Keep the original start time to avoid splitting one pause period.
                    pass

            elif state == 0:
                if active:
                    end_time = t
                    if end_time >= start_time:
                        records.append({
                            "device_type": int(device_type),
                            "device_id": int(device_id),
                            "port_id": int(port_id),
                            "start_ns": int(start_time),
                            "end_ns": int(end_time),
                            "duration_ns": int(end_time - start_time),
                            "closed_by_resume": True,
                        })
                    active = False
                    start_time = None
                else:
                    # Resume without previous pause.
                    # Ignore it, but do not treat it as an error.
                    pass

        if active and start_time is not None:
            records.append({
                "device_type": int(device_type),
                "device_id": int(device_id),
                "port_id": int(port_id),
                "start_ns": int(start_time),
                "end_ns": int(max_time),
                "duration_ns": int(max_time - start_time),
                "closed_by_resume": False,
            })

    interval_df = pd.DataFrame(records)

    if interval_df.empty:
        return pd.DataFrame(columns=[
            "device_type",
            "device_id",
            "port_id",
            "start_ns",
            "end_ns",
            "duration_ns",
            "closed_by_resume",
            "device_type_name",
            "device_key",
        ])

    interval_df["device_type_name"] = interval_df["device_type"].map(DEVICE_TYPE_NAME).fillna("UNKNOWN")
    interval_df["device_key"] = interval_df["device_type_name"] + "-" + interval_df["device_id"].astype(str)

    return interval_df


# ============================================================
# 6. Global statistics
# ============================================================

def compute_device_summary(df: pd.DataFrame, interval_df: pd.DataFrame) -> pd.DataFrame:
    pause_count = (
        df[df["pfc_state"] == 1]
        .groupby(["device_type", "device_id", "device_key"])
        .size()
        .reset_index(name="pause_event_count")
    )

    resume_count = (
        df[df["pfc_state"] == 0]
        .groupby(["device_type", "device_id", "device_key"])
        .size()
        .reset_index(name="resume_event_count")
    )

    if interval_df.empty:
        pause_duration = pd.DataFrame(columns=[
            "device_type",
            "device_id",
            "device_key",
            "total_pause_ns",
            "max_single_pause_ns",
            "pause_interval_count",
            "unclosed_pause_interval_count",
        ])
    else:
        pause_duration = (
            interval_df
            .groupby(["device_type", "device_id", "device_key"])
            .agg(
                total_pause_ns=("duration_ns", "sum"),
                max_single_pause_ns=("duration_ns", "max"),
                pause_interval_count=("duration_ns", "count"),
                unclosed_pause_interval_count=("closed_by_resume", lambda x: int((~x).sum())),
            )
            .reset_index()
        )

    summary = pause_count.merge(
        resume_count,
        on=["device_type", "device_id", "device_key"],
        how="outer",
    ).merge(
        pause_duration,
        on=["device_type", "device_id", "device_key"],
        how="outer",
    )

    fill_cols = [
        "pause_event_count",
        "resume_event_count",
        "total_pause_ns",
        "max_single_pause_ns",
        "pause_interval_count",
        "unclosed_pause_interval_count",
    ]
    for col in fill_cols:
        if col in summary.columns:
            summary[col] = summary[col].fillna(0)

    summary["total_pause_us"] = summary["total_pause_ns"] / 1e3
    summary["max_single_pause_us"] = summary["max_single_pause_ns"] / 1e3

    summary = summary.sort_values(
        ["pause_event_count", "total_pause_ns"],
        ascending=False,
    ).reset_index(drop=True)

    return summary


def compute_active_pause_count(
    interval_df: pd.DataFrame,
    min_time_ns: int,
    max_time_ns: int,
    time_bin_ns: int,
) -> pd.DataFrame:
    if max_time_ns <= min_time_ns:
        max_time_ns = min_time_ns + time_bin_ns

    num_bins = int(np.ceil((max_time_ns - min_time_ns) / time_bin_ns)) + 1
    diff = np.zeros(num_bins + 1, dtype=np.int64)

    if not interval_df.empty:
        for row in interval_df.itertuples(index=False):
            start = max(int(row.start_ns), min_time_ns)
            end = min(int(row.end_ns), max_time_ns)

            if end < start:
                continue

            start_bin = int((start - min_time_ns) // time_bin_ns)
            end_bin = int(np.ceil((end - min_time_ns) / time_bin_ns))

            start_bin = max(0, min(start_bin, num_bins))
            end_bin = max(0, min(end_bin, num_bins))

            diff[start_bin] += 1
            diff[end_bin] -= 1

    active_count = np.cumsum(diff[:-1])
    bin_start_ns = np.arange(num_bins, dtype=np.int64) * time_bin_ns

    return pd.DataFrame({
        "time_bin": np.arange(num_bins, dtype=np.int64),
        "bin_start_ns": bin_start_ns,
        "active_paused_interfaces": active_count,
    })


# ============================================================
# 7. Plot global figures
# ============================================================

def plot_global_event_timeline(df: pd.DataFrame, out_dir: Path, prefix: str) -> None:
    scale, xlabel = get_time_scale(TIME_UNIT)

    pause_df = df[df["pfc_state"] == 1]
    resume_df = df[df["pfc_state"] == 0]

    max_bin = int(df["time_bin"].max())
    bins = np.arange(max_bin + 1, dtype=np.int64)

    pause_counts = pause_df.groupby("time_bin").size().reindex(bins, fill_value=0)
    resume_counts = resume_df.groupby("time_bin").size().reindex(bins, fill_value=0)

    x = bins * TIME_BIN_NS / scale

    fig, ax = plt.subplots()
    ax.plot(x, pause_counts.values, linewidth=1.8, label="PFC pause events")
    ax.plot(x, resume_counts.values, linewidth=1.5, linestyle="--", label="PFC resume events")

    ax.set_xlabel(xlabel)
    ax.set_ylabel(f"Event count per {TIME_BIN_NS / scale:g} {TIME_UNIT}")
    ax.set_title("Global PFC State-Change Events Over Time")
    ax.legend(frameon=False)
    ax.grid(True, axis="y")

    save_figure(fig, out_dir, f"{prefix}_global_pfc_event_timeline")


def plot_active_pause_pressure(
    active_df: pd.DataFrame,
    out_dir: Path,
    prefix: str,
) -> None:
    scale, xlabel = get_time_scale(TIME_UNIT)

    x = active_df["bin_start_ns"].values / scale
    y = active_df["active_paused_interfaces"].values

    fig, ax = plt.subplots()
    ax.plot(x, y, linewidth=1.8)

    if len(y) > 0:
        peak_idx = int(np.argmax(y))
        peak_x = x[peak_idx]
        peak_y = y[peak_idx]
        ax.scatter([peak_x], [peak_y], zorder=3)
        ax.annotate(
            f"Peak = {peak_y}",
            xy=(peak_x, peak_y),
            xytext=(8, 8),
            textcoords="offset points",
            fontsize=10,
            arrowprops=dict(arrowstyle="->", lw=0.8),
        )

    ax.set_xlabel(xlabel)
    ax.set_ylabel("Active PFC-paused interfaces")
    ax.set_title("System-Level PFC Pressure Over Time")
    ax.grid(True, axis="y")

    save_figure(fig, out_dir, f"{prefix}_active_pfc_pressure")


def plot_top_device_heatmap(
    df: pd.DataFrame,
    summary_df: pd.DataFrame,
    out_dir: Path,
    prefix: str,
    top_n: int,
) -> None:
    scale, xlabel = get_time_scale(TIME_UNIT)

    top_devices = summary_df.head(top_n)["device_key"].tolist()
    pause_df = df[(df["pfc_state"] == 1) & (df["device_key"].isin(top_devices))]

    if pause_df.empty:
        return

    max_bin = int(df["time_bin"].max())
    bins = np.arange(max_bin + 1, dtype=np.int64)

    pivot = (
        pause_df
        .groupby(["device_key", "time_bin"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=top_devices, columns=bins, fill_value=0)
    )

    fig_height = max(4.8, 0.28 * len(top_devices) + 1.5)
    fig, ax = plt.subplots(figsize=(10.5, fig_height))

    im = ax.imshow(
        pivot.values,
        aspect="auto",
        interpolation="nearest",
        origin="upper",
    )

    x_tick_count = min(8, len(bins))
    if x_tick_count > 1:
        x_ticks = np.linspace(0, len(bins) - 1, x_tick_count, dtype=int)
    else:
        x_ticks = np.array([0], dtype=int)

    x_labels = [f"{bins[i] * TIME_BIN_NS / scale:g}" for i in x_ticks]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_labels)

    ax.set_yticks(np.arange(len(top_devices)))
    ax.set_yticklabels(top_devices)

    ax.set_xlabel(xlabel)
    ax.set_ylabel("Top PFC devices")
    ax.set_title("PFC Pause Event Heatmap of Top Devices")

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Pause events per time bin")

    save_figure(fig, out_dir, f"{prefix}_top_device_pfc_heatmap")


def plot_top_device_summary(
    summary_df: pd.DataFrame,
    out_dir: Path,
    prefix: str,
    top_n: int,
) -> None:
    if summary_df.empty:
        return

    top_df = summary_df.head(top_n).copy()
    top_df = top_df.iloc[::-1]

    labels = top_df["device_key"].tolist()
    counts = top_df["pause_event_count"].values
    durations_us = top_df["total_pause_us"].values

    fig_height = max(4.8, 0.28 * len(top_df) + 1.5)
    fig, ax = plt.subplots(figsize=(9.5, fig_height))

    y = np.arange(len(top_df))
    ax.barh(y, counts)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)

    ax.set_xlabel("PFC pause event count")
    ax.set_ylabel("Device")
    ax.set_title("Top Devices by PFC Pause Events")

    max_count = max(counts) if len(counts) > 0 else 0
    text_x_offset = max(1, max_count * 0.01)

    for i, (cnt, dur) in enumerate(zip(counts, durations_us)):
        ax.text(
            cnt + text_x_offset,
            i,
            f"{int(cnt)} events, {dur:.2f} us",
            va="center",
            fontsize=9,
        )

    ax.grid(True, axis="x")

    save_figure(fig, out_dir, f"{prefix}_top_device_pfc_summary")


# ============================================================
# 8. Plot local device figures
# ============================================================

def build_device_state_timeline(device_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build step-style state timeline for each port of one device.
    """
    records = []
    min_time = int(device_df["time_ns"].min())
    max_time = int(device_df["time_ns"].max())

    for port_id, g in device_df.groupby("port_id"):
        g = g.sort_values("time_ns")

        current_state = 0
        last_time = min_time

        for row in g.itertuples(index=False):
            t = int(row.time_ns)
            state = int(row.pfc_state)

            if t >= last_time:
                records.append({
                    "port_id": int(port_id),
                    "start_ns": int(last_time),
                    "end_ns": int(t),
                    "state": int(current_state),
                })

            current_state = state
            last_time = t

        records.append({
            "port_id": int(port_id),
            "start_ns": int(last_time),
            "end_ns": int(max_time),
            "state": int(current_state),
        })

    return pd.DataFrame(records)


def plot_device_state_timeline(
    df: pd.DataFrame,
    out_dir: Path,
    prefix: str,
    device_id: int,
    device_type: Optional[int] = None,
) -> None:
    scale, xlabel = get_time_scale(TIME_UNIT)

    device_df = df[df["device_id"] == device_id].copy()

    if device_type is not None:
        device_df = device_df[device_df["device_type"] == device_type]

    if device_df.empty:
        print(f"[WARN] No PFC records for device_id={device_id}, device_type={device_type}")
        return

    device_type_values = sorted(device_df["device_type"].unique().tolist())

    for dtype in device_type_values:
        one_dev_df = device_df[device_df["device_type"] == dtype].copy()
        dtype_name = DEVICE_TYPE_NAME.get(dtype, f"type{dtype}")

        state_df = build_device_state_timeline(one_dev_df)

        ports = sorted(one_dev_df["port_id"].unique().tolist())
        port_to_y = {port: i for i, port in enumerate(ports)}

        fig_height = max(4.5, 0.45 * len(ports) + 1.5)
        fig, ax = plt.subplots(figsize=(10.0, fig_height))

        for port in ports:
            segs = state_df[state_df["port_id"] == port]
            y_base = port_to_y[port]

            for row in segs.itertuples(index=False):
                x0 = row.start_ns / scale
                x1 = row.end_ns / scale
                state = int(row.state)

                if x1 < x0:
                    continue

                # Draw 0/1 state as a small offset above the port baseline.
                y = y_base + 0.35 * state
                ax.hlines(
                    y=y,
                    xmin=x0,
                    xmax=x1,
                    linewidth=2.0 if state == 1 else 1.0,
                )

            # Event markers.
            p_events = one_dev_df[one_dev_df["port_id"] == port]
            pause_events = p_events[p_events["pfc_state"] == 1]
            resume_events = p_events[p_events["pfc_state"] == 0]

            ax.scatter(
                pause_events["time_ns"].values / scale,
                np.full(len(pause_events), y_base + 0.35),
                marker="|",
                s=60,
                label="Pause event" if port == ports[0] else None,
            )
            ax.scatter(
                resume_events["time_ns"].values / scale,
                np.full(len(resume_events), y_base),
                marker="|",
                s=60,
                label="Resume event" if port == ports[0] else None,
            )

        ax.set_yticks(np.arange(len(ports)))
        ax.set_yticklabels([f"port {p}" for p in ports])

        ax.set_xlabel(xlabel)
        ax.set_ylabel("Interface")
        ax.set_title(f"PFC State Timeline: {dtype_name}-{device_id}")
        ax.legend(frameon=False, loc="upper right")
        ax.grid(True, axis="x")

        save_figure(
            fig,
            out_dir,
            f"{prefix}_{dtype_name}_{device_id}_pfc_state_timeline",
        )


def plot_device_port_pause_duration(
    interval_df: pd.DataFrame,
    out_dir: Path,
    prefix: str,
    device_id: int,
    device_type: Optional[int] = None,
) -> None:
    device_interval_df = interval_df[interval_df["device_id"] == device_id].copy()

    if device_type is not None:
        device_interval_df = device_interval_df[device_interval_df["device_type"] == device_type]

    if device_interval_df.empty:
        return

    for dtype in sorted(device_interval_df["device_type"].unique().tolist()):
        one_dev = device_interval_df[device_interval_df["device_type"] == dtype].copy()
        dtype_name = DEVICE_TYPE_NAME.get(dtype, f"type{dtype}")

        port_summary = (
            one_dev
            .groupby("port_id")
            .agg(
                total_pause_us=("duration_ns", lambda x: x.sum() / 1e3),
                pause_interval_count=("duration_ns", "count"),
                max_single_pause_us=("duration_ns", lambda x: x.max() / 1e3),
            )
            .reset_index()
            .sort_values("total_pause_us", ascending=False)
        )

        if port_summary.empty:
            continue

        port_summary.to_csv(
            out_dir / f"{prefix}_{dtype_name}_{device_id}_port_pause_summary.csv",
            index=False,
        )

        plot_df = port_summary.iloc[::-1]

        fig_height = max(4.2, 0.35 * len(plot_df) + 1.2)
        fig, ax = plt.subplots(figsize=(8.8, fig_height))

        y = np.arange(len(plot_df))
        ax.barh(y, plot_df["total_pause_us"].values)
        ax.set_yticks(y)
        ax.set_yticklabels([f"port {p}" for p in plot_df["port_id"].tolist()])

        ax.set_xlabel("Total PFC pause duration (us)")
        ax.set_ylabel("Interface")
        ax.set_title(f"Per-Port PFC Pause Duration: {dtype_name}-{device_id}")

        max_v = plot_df["total_pause_us"].max()
        offset = max(0.01, max_v * 0.01)

        for i, row in enumerate(plot_df.itertuples(index=False)):
            ax.text(
                row.total_pause_us + offset,
                i,
                f"{row.total_pause_us:.2f} us, {int(row.pause_interval_count)} intervals",
                va="center",
                fontsize=9,
            )

        ax.grid(True, axis="x")

        save_figure(
            fig,
            out_dir,
            f"{prefix}_{dtype_name}_{device_id}_port_pause_duration",
        )


# ============================================================
# 9. Main per-experiment analysis
# ============================================================

def analyze_one_experiment(group_name: str, case_name: str, exp_dir: str) -> None:
    exp_path = Path(exp_dir)
    pfc_path = exp_path / PFC_FILENAME
    out_dir = exp_path / OUTPUT_DIRNAME

    prefix = f"{group_name}_{case_name}"

    print("=" * 80)
    print(f"[INFO] Analyze experiment: {group_name}/{case_name}")
    print(f"[INFO] Input : {pfc_path}")
    print(f"[INFO] Output: {out_dir}")

    df = load_pfc_file(pfc_path)
    df = add_time_bin(df, TIME_BIN_NS)

    interval_df = reconstruct_pause_intervals(df)
    summary_df = compute_device_summary(df, interval_df)

    out_dir.mkdir(parents=True, exist_ok=True)

    df.to_csv(out_dir / f"{prefix}_pfc_events_normalized.csv", index=False)
    interval_df.to_csv(out_dir / f"{prefix}_pfc_pause_intervals.csv", index=False)
    summary_df.to_csv(out_dir / f"{prefix}_pfc_device_summary.csv", index=False)

    min_time_ns = int(df["time_ns"].min())
    max_time_ns = int(df["time_ns"].max())

    active_df = compute_active_pause_count(
        interval_df=interval_df,
        min_time_ns=min_time_ns,
        max_time_ns=max_time_ns,
        time_bin_ns=TIME_BIN_NS,
    )
    active_df.to_csv(out_dir / f"{prefix}_active_pfc_pressure.csv", index=False)

    # Global figures.
    plot_global_event_timeline(df, out_dir, prefix)
    plot_active_pause_pressure(active_df, out_dir, prefix)
    plot_top_device_heatmap(df, summary_df, out_dir, prefix, TOP_N_DEVICES)
    plot_top_device_summary(summary_df, out_dir, prefix, TOP_N_DEVICES)

    # Decide local target devices.
    if TARGET_DEVICES:
        local_devices = TARGET_DEVICES
    else:
        local_devices = summary_df.head(AUTO_LOCAL_TOP_K)["device_id"].astype(int).tolist()

    # Local figures.
    for dev_id in local_devices:
        plot_device_state_timeline(
            df=df,
            out_dir=out_dir,
            prefix=prefix,
            device_id=dev_id,
            device_type=TARGET_DEVICE_TYPE,
        )
        plot_device_port_pause_duration(
            interval_df=interval_df,
            out_dir=out_dir,
            prefix=prefix,
            device_id=dev_id,
            device_type=TARGET_DEVICE_TYPE,
        )

    print(f"[INFO] Done: {group_name}/{case_name}")
    print(f"[INFO] Total PFC records: {len(df)}")
    print(f"[INFO] Total pause events: {int((df['pfc_state'] == 1).sum())}")
    print(f"[INFO] Total resume events: {int((df['pfc_state'] == 0).sum())}")
    print(f"[INFO] Device summary saved to: {out_dir / f'{prefix}_pfc_device_summary.csv'}")

    if not summary_df.empty:
        print("[INFO] Top devices:")
        print(summary_df.head(10)[[
            "device_key",
            "pause_event_count",
            "resume_event_count",
            "total_pause_us",
            "max_single_pause_us",
            "unclosed_pause_interval_count",
        ]].to_string(index=False))


def main() -> None:
    setup_matplotlib_style()

    for group_name, cases in CONFIG_LIST.items():
        for case_name, exp_dir in cases.items():
            try:
                analyze_one_experiment(group_name, case_name, exp_dir)
            except Exception as e:
                print("=" * 80)
                print(f"[ERROR] Failed to analyze {group_name}/{case_name}")
                print(f"[ERROR] Directory: {exp_dir}")
                print(f"[ERROR] Reason: {e}")


if __name__ == "__main__":
    main()