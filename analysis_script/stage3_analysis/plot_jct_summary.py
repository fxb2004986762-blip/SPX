#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bubble heatmap for JCT speedup comparison.

Input file:
    tmp_data.csv by default.

Supported input formats:

1) Recommended standard CSV:
    scenario,algorithm,workload,jct_ms
    fattree-alltoall,aps-v2,1MB,0.187102
    fattree-alltoall,aps-v2,4MB,0.715562
    ...

2) Block-style format:
    fattree-alltoall
    algorithm,workload,jct_ms
    aps-v2,1MB,0.187102
    aps-v2,4MB,0.715562

    fattree-allreduce
    algorithm,workload,jct_ms
    ...
"""

import argparse
import io
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm


# =========================
# Default configuration
# =========================

DEFAULT_INPUT_CSV = "/home/dell/sjw/lb/simulator/output/1all_figures/stage3/sym/sym_speedup_data.csv"
DEFAULT_BASELINE_ALG = "ecmp"

DEFAULT_OUTPUT_PNG = "bubble_speedup_heatmap_paper.png"
DEFAULT_OUTPUT_PDF = "bubble_speedup_heatmap_paper.pdf"

SCENARIO_ORDER = [
    "fattree-alltoall",
    "fattree-allreduce",
    "hpn-alltoall",
    "hpn-allreduce",
    "spectrumx-alltoall",
    "spectrumx-allreduce",
]

ALGORITHM_ORDER = [
    "ecmp",
    "aps-v2",
    "reps",
    "rps",
    "rps-sw",
    "flowbender",
    "letflow",
]


# =========================
# Bubble style configuration
# =========================
# matplotlib scatter's `s` is area, not radius.
TIE_BUBBLE_SIZE = 840       # baseline / near-tie values around 1.00x
MIN_BUBBLE_SIZE = 840       # minimum bubble area for non-tie points
MAX_BUBBLE_EXTRA = 2200     # additional bubble area for the largest performance gap
TIE_THRESHOLD = 0.005       # |speedup - 1.0| below this threshold is treated as near-tie


# =========================
# Paper-style figure configuration
# =========================
# Tuned for SIGCOMM/NSDI-like paper figures:
# compact layout, serif fonts, restrained colors, high contrast, embedded PDF fonts.
TEXT_COLOR = "#222222"
AXIS_COLOR = "#333333"
GRID_COLOR = "#B8B8B8"
EDGE_COLOR = "#303030"

FONT_FAMILY = "serif"
SERIF_FONTS = ["Times New Roman", "Times", "DejaVu Serif"]

TITLE_FONT_SIZE = 10.5
AXIS_LABEL_FONT_SIZE = 9.5
TICK_FONT_SIZE = 8.8
BUBBLE_LABEL_FONT_SIZE = 8.2
COLORBAR_FONT_SIZE = 8.6
BUBBLE_EDGE_WIDTH = 0.65


def apply_paper_style() -> None:
    """Apply SIGCOMM/NSDI-like Matplotlib style."""
    plt.rcParams.update({
        "font.family": FONT_FAMILY,
        "font.serif": SERIF_FONTS,
        "font.size": TICK_FONT_SIZE,
        "text.color": TEXT_COLOR,
        "axes.labelcolor": TEXT_COLOR,
        "axes.edgecolor": AXIS_COLOR,
        "axes.linewidth": 0.8,
        "xtick.color": TEXT_COLOR,
        "ytick.color": TEXT_COLOR,
        "xtick.major.width": 0.75,
        "ytick.major.width": 0.75,
        "xtick.major.size": 3.0,
        "ytick.major.size": 3.0,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "savefig.dpi": 300,
        "figure.dpi": 120,
    })


def read_data(input_csv: str) -> pd.DataFrame:
    """
    Read tmp_data.csv.

    The function first tries to parse the file as a standard CSV with columns:
        scenario, algorithm, workload, jct_ms

    If that fails, it falls back to the block-style format:
        scenario_name
        algorithm,workload,jct_ms
        ...
    """
    path = Path(input_csv)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    raw_text = path.read_text(encoding="utf-8-sig").strip()
    if not raw_text:
        raise ValueError(f"Input file is empty: {path}")

    # Try standard CSV first.
    try:
        df = pd.read_csv(io.StringIO(raw_text))
        df.columns = [c.strip() for c in df.columns]

        required = {"scenario", "algorithm", "workload", "jct_ms"}
        if required.issubset(set(df.columns)):
            df = df[["scenario", "algorithm", "workload", "jct_ms"]].copy()
            df["scenario"] = df["scenario"].astype(str).str.strip()
            df["algorithm"] = df["algorithm"].astype(str).str.strip()
            df["workload"] = df["workload"].astype(str).str.strip()
            df["jct_ms"] = pd.to_numeric(df["jct_ms"], errors="coerce")
            df = df.dropna(subset=["jct_ms"])
            if df.empty:
                raise ValueError("No valid jct_ms values found in standard CSV.")
            return df
    except Exception:
        pass

    # Fallback: parse block-style format.
    return parse_block_style_data(raw_text)


def parse_block_style_data(raw_text: str) -> pd.DataFrame:
    """Parse repeated blocks: scenario name + CSV header + CSV rows."""
    blocks = []
    lines = [line.strip() for line in raw_text.splitlines()]
    i = 0

    while i < len(lines):
        if not lines[i]:
            i += 1
            continue

        scenario = lines[i]
        i += 1

        if i >= len(lines):
            break

        header = lines[i]
        i += 1

        rows = []
        while i < len(lines) and lines[i]:
            rows.append(lines[i])
            i += 1

        if rows:
            df = pd.read_csv(io.StringIO(header + "\n" + "\n".join(rows)))
            df.columns = [c.strip() for c in df.columns]

            required = {"algorithm", "workload", "jct_ms"}
            if not required.issubset(set(df.columns)):
                raise ValueError(
                    f"Invalid block under scenario {scenario!r}. "
                    f"Required columns: algorithm, workload, jct_ms"
                )

            df = df[["algorithm", "workload", "jct_ms"]].copy()
            df["scenario"] = scenario
            blocks.append(df)

    if not blocks:
        raise ValueError(
            "No valid data blocks found. Use either standard CSV format or block-style format."
        )

    data = pd.concat(blocks, ignore_index=True)
    data["scenario"] = data["scenario"].astype(str).str.strip()
    data["algorithm"] = data["algorithm"].astype(str).str.strip()
    data["workload"] = data["workload"].astype(str).str.strip()
    data["jct_ms"] = pd.to_numeric(data["jct_ms"], errors="coerce")
    data = data.dropna(subset=["jct_ms"])

    if data.empty:
        raise ValueError("No valid jct_ms values found after parsing block-style data.")

    return data


def build_speedup_table(data: pd.DataFrame, baseline_alg: str) -> pd.DataFrame:
    """
    Average JCT over all workload sizes, then compute speedup against baseline.

    speedup = JCT_baseline / JCT_algorithm

    For JCT:
        speedup > 1: faster than baseline
        speedup = 1: equal to baseline
        speedup < 1: slower than baseline
    """
    avg = (
        data.groupby(["scenario", "algorithm"], as_index=False)["jct_ms"]
        .mean()
        .rename(columns={"jct_ms": "avg_jct_ms"})
    )

    baseline = (
        avg[avg["algorithm"] == baseline_alg][["scenario", "avg_jct_ms"]]
        .rename(columns={"avg_jct_ms": "baseline_jct_ms"})
    )

    if baseline.empty:
        available = sorted(avg["algorithm"].unique())
        raise ValueError(
            f"Baseline algorithm {baseline_alg!r} not found. "
            f"Available algorithms: {available}"
        )

    merged = avg.merge(baseline, on="scenario", how="left")

    missing_baseline = merged[merged["baseline_jct_ms"].isna()]["scenario"].unique()
    if len(missing_baseline) > 0:
        raise ValueError(
            f"Baseline algorithm {baseline_alg!r} is missing in scenarios: "
            f"{list(missing_baseline)}"
        )

    merged["speedup"] = merged["baseline_jct_ms"] / merged["avg_jct_ms"]

    return merged.pivot(index="scenario", columns="algorithm", values="speedup")


def draw_bubble_heatmap(
    speedup_table: pd.DataFrame,
    baseline_alg: str,
    output_png: str,
    output_pdf: str,
) -> None:
    apply_paper_style()

    scenarios = [s for s in SCENARIO_ORDER if s in speedup_table.index]
    scenarios += [s for s in speedup_table.index if s not in scenarios]

    algorithms = [a for a in ALGORITHM_ORDER if a in speedup_table.columns]
    algorithms += [a for a in speedup_table.columns if a not in algorithms]

    mat = speedup_table.reindex(index=scenarios, columns=algorithms)
    valid_vals = mat.values[np.isfinite(mat.values)]

    if len(valid_vals) == 0:
        raise ValueError("No valid speedup values to plot.")

    # Use log2 distance so that 2x better and 0.5x worse have comparable visual magnitude.
    max_log_delta = max(float(np.max(np.abs(np.log2(valid_vals)))), 1e-9)

    xs, ys, vals, sizes, labels = [], [], [], [], []
    for y, scenario in enumerate(scenarios):
        for x, alg in enumerate(algorithms):
            val = mat.loc[scenario, alg]
            if pd.isna(val):
                continue

            log_delta = abs(np.log2(val))
            size = MIN_BUBBLE_SIZE + MAX_BUBBLE_EXTRA * (log_delta / max_log_delta)
            if abs(val - 1.0) < TIE_THRESHOLD:
                size = TIE_BUBBLE_SIZE

            xs.append(x)
            ys.append(y)
            vals.append(float(val))
            sizes.append(size)
            labels.append(f"{val:.2f}×")

    # User-requested semantics:
    # green = worse than baseline, red = better than baseline.
    cmap = LinearSegmentedColormap.from_list(
        "green_gray_red",
        ["#4B8B5A", "#F7F7F7", "#B04A4A"],
    )

    vmin = min(0.80, float(np.nanmin(valid_vals)))
    vmax = max(1.25, float(np.nanmax(valid_vals)))
    norm = TwoSlopeNorm(vmin=vmin, vcenter=1.0, vmax=vmax)

    fig, ax = plt.subplots(figsize=(7.8, 3.9))

    sc = ax.scatter(
        xs,
        ys,
        s=sizes,
        c=vals,
        cmap=cmap,
        norm=norm,
        edgecolors=EDGE_COLOR,
        linewidths=BUBBLE_EDGE_WIDTH,
        alpha=0.96,
    )

    for x, y, val, label in zip(xs, ys, vals, labels):
        text_color = "white" if (val >= 1.35 or val <= 0.88) else TEXT_COLOR
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=BUBBLE_LABEL_FONT_SIZE,
            color=text_color,
            # fontweight="bold" if abs(val - 1.0) > 0.1 else "normal",
            fontweight="normal",
        )

    ax.set_xticks(range(len(algorithms)))
    ax.set_xticklabels(algorithms, rotation=32, ha="right", fontsize=TICK_FONT_SIZE)

    ax.set_yticks(range(len(scenarios)))
    ax.set_yticklabels(scenarios, fontsize=TICK_FONT_SIZE)
    ax.invert_yaxis()

    ax.set_xlabel("Load Balancing Algorithm", fontsize=AXIS_LABEL_FONT_SIZE, color=TEXT_COLOR)
    ax.set_ylabel("Scenario", fontsize=AXIS_LABEL_FONT_SIZE, color=TEXT_COLOR)
    ax.set_title(
        f"JCT Speedup over {baseline_alg} ",
        # r"($speedup = JCT_{baseline} / JCT_{algorithm}$)",
        fontsize=TITLE_FONT_SIZE,
        color=TEXT_COLOR,
        pad=10,
    )

    ax.set_xlim(-0.6, len(algorithms) - 0.4)
    ax.set_ylim(len(scenarios) - 0.4, -0.6)

    ax.tick_params(axis="both", labelsize=TICK_FONT_SIZE, colors=TEXT_COLOR)
    ax.grid(True, axis="both", linestyle=":", linewidth=0.45, color=GRID_COLOR, alpha=0.70)
    ax.set_axisbelow(True)

    for spine in ax.spines.values():
        spine.set_color(AXIS_COLOR)
        spine.set_linewidth(0.8)

    cbar = fig.colorbar(sc, ax=ax, pad=0.018)
    cbar.ax.tick_params(labelsize=COLORBAR_FONT_SIZE, colors=TEXT_COLOR, width=0.7, length=2.5)
    cbar.outline.set_edgecolor(AXIS_COLOR)
    cbar.outline.set_linewidth(0.7)
    cbar.set_label(
        "Speedup vs. baseline\nred: faster, green: slower",
        fontsize=COLORBAR_FONT_SIZE,
        color=TEXT_COLOR,
    )

    fig.tight_layout()
    fig.savefig(output_png, dpi=300, bbox_inches="tight")
    fig.savefig(output_pdf, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Draw a bubble heatmap for JCT speedup over a baseline algorithm."
    )
    parser.add_argument(
        "-i",
        "--input",
        default=DEFAULT_INPUT_CSV,
        help=f"Input CSV file. Default: {DEFAULT_INPUT_CSV}",
    )
    parser.add_argument(
        "-b",
        "--baseline",
        default=DEFAULT_BASELINE_ALG,
        help=f"Baseline algorithm. Default: {DEFAULT_BASELINE_ALG}",
    )
    parser.add_argument(
        "--output-png",
        default=DEFAULT_OUTPUT_PNG,
        help=f"Output PNG file. Default: {DEFAULT_OUTPUT_PNG}",
    )
    parser.add_argument(
        "--output-pdf",
        default=DEFAULT_OUTPUT_PDF,
        help=f"Output PDF file. Default: {DEFAULT_OUTPUT_PDF}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    data = read_data(args.input)
    speedup_table = build_speedup_table(data, args.baseline)
    draw_bubble_heatmap(
        speedup_table=speedup_table,
        baseline_alg=args.baseline,
        output_png=args.output_png,
        output_pdf=args.output_pdf,
    )

    print("Saved figures:")
    print(f"  {args.output_png}")
    print(f"  {args.output_pdf}")
    print("\nSpeedup table:")
    print(speedup_table.round(3).to_string())


if __name__ == "__main__":
    main()
