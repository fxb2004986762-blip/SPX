#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch plot split-cell speedup heatmaps from a dictionary-style input.

This script follows the user's usual "dictionary input" style:
you provide one CONFIG_LIST dictionary whose string values are folder paths.
The script scans all folder paths in the dictionary, reads the data file
(default: tmp_data.csv) inside each folder, and generates one heatmap per folder.

Main features:
1. Dictionary-style input (supports nested dict / list / tuple / set).
2. Batch plotting for multiple folders.
3. Compatible with Python 3.8+.
4. Supports both standard CSV format and block-style format.
5. If the folder path contains:
      - "asy"
      - "failure"
      - "sym"
   then the corresponding field will be appended as a suffix to the output filename.

Output naming:
    split_cell_speedup_heatmap[_suffix].png
    split_cell_speedup_heatmap[_suffix].pdf

Examples:
    split_cell_speedup_heatmap_asy.png
    split_cell_speedup_heatmap_failure.pdf
    split_cell_speedup_heatmap_sym.png
"""

import io
import re
from pathlib import Path
from typing import Optional, Tuple, List, Iterable, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm


# ============================================================
# User input: dictionary-style configuration
# Replace the example paths below with your own directories.
# Any string value inside CONFIG_LIST will be treated as a folder path.
# ============================================================

CONFIG_LIST = {
    "0": "/home/dell/sjw/lb/simulator/output/1all_figures/stage3/jct_summary/asy",
    "1": "/home/dell/sjw/lb/simulator/output/1all_figures/stage3/jct_summary/failure",
    "2": "/home/dell/sjw/lb/simulator/output/1all_figures/stage3/jct_summary/sym",
    # "single_case": "/path/to/dir_c",
}

# Name of the data file inside each directory.
INPUT_FILENAME = "speedup_data.csv"

# Baseline algorithm.
BASELINE_ALG = "rps"

# Output file basename.
OUTPUT_BASENAME = "speedup_heatmap"
OUTPUT_BASENAME = OUTPUT_BASENAME + "_" + BASELINE_ALG


# =========================
# Default plotting order
# =========================

SCENARIO_ORDER = [
    "fattree-alltoall",
    "fattree-allreduce",
    "hpn-alltoall",
    "hpn-allreduce",
    "spectrumx-alltoall",
    "spectrumx-allreduce",
]

ALGORITHM_ORDER = [
    "rps",
    "aps-v2",
    "reps",
    "flowbender",
    "letflow",
    "ecmp",
]

# Each scenario-algorithm cell is split into a 2x2 layout.
# Workload position:
#   1MB | 4MB
#   8MB | 16MB
WORKLOAD_ORDER = ["1MB", "4MB", "8MB", "16MB"]


# =========================
# Split-cell style configuration
# =========================

CELL_WIDTH = 0.86
CELL_HEIGHT = 0.78
SUBCELL_GAP = 0.035

SUBCELL_EDGE_WIDTH = 0.55
MISSING_CELL_EDGE_WIDTH = 0.35

# Text inside each small square.
SUBCELL_LABEL_FONT_SIZE = 6.5


# =========================
# Paper-style figure configuration
# =========================

TEXT_COLOR = "#222222"
AXIS_COLOR = "#333333"
GRID_COLOR = "#B8B8B8"
EDGE_COLOR = "#303030"
MISSING_EDGE_COLOR = "#D0D0D0"

FONT_FAMILY = "serif"
SERIF_FONTS = ["Times New Roman", "Times", "DejaVu Serif"]

TITLE_FONT_SIZE = 10.5
AXIS_LABEL_FONT_SIZE = 9.5
TICK_FONT_SIZE = 8.8
COLORBAR_FONT_SIZE = 8.6
FOOTNOTE_FONT_SIZE = 7.6

# Four-square workload layout legend.
LAYOUT_LEGEND_FONT_SIZE = 7.2
LAYOUT_LEGEND_TITLE_SIZE = 7.5
LAYOUT_LEGEND_EDGE_WIDTH = 0.55
LAYOUT_LEGEND_BG_COLOR = "#FFFFFF"
LAYOUT_LEGEND_BG_ALPHA = 0.92


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


def workload_sort_key(workload: str):
    """Sort strings such as 1MB, 4MB, 16MB numerically when possible."""
    m = re.match(r"^\s*([0-9.]+)\s*([KMGTP]?B)?\s*$", str(workload), re.I)
    if not m:
        return (float("inf"), str(workload))

    value = float(m.group(1))
    unit = (m.group(2) or "").upper()
    scale = {
        "B": 1,
        "KB": 1024,
        "MB": 1024 ** 2,
        "GB": 1024 ** 3,
        "TB": 1024 ** 4,
        "PB": 1024 ** 5,
    }.get(unit, 1)

    return (value * scale, str(workload))


def flatten_paths(obj: Any) -> List[str]:
    """
    Recursively extract all string values from a nested dictionary/list/tuple/set.
    These string values are treated as directory paths.
    """
    paths = []

    if isinstance(obj, str):
        paths.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            paths.extend(flatten_paths(v))
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            paths.extend(flatten_paths(item))

    return paths


def unique_existing_dirs(paths: Iterable[str]) -> List[Path]:
    """
    Remove duplicates while preserving order, and keep only existing directories.
    """
    seen = set()
    result = []
    for p in paths:
        path = Path(str(p)).expanduser()
        try:
            key = str(path.resolve())
        except Exception:
            key = str(path)

        if key in seen:
            continue
        seen.add(key)

        if path.is_dir():
            result.append(path)
        else:
            print("[WARN] Skip non-directory path: {}".format(path))
    return result


def detect_suffix_from_path(path: Path) -> str:
    """
    Detect suffix fields from the directory string:
        asy / failure / sym

    To avoid false positives (e.g., 'asym' mistakenly matching 'sym'),
    a token-like regex is used.

    If multiple fields appear, they are concatenated in a stable order.
    Example:
        _asy
        _failure
        _sym
        _asy_failure
    """
    s = str(path).lower()

    patterns = [
        ("asy", r"(^|[^a-z])asy([^a-z]|$)"),
        ("failure", r"(^|[^a-z])failure([^a-z]|$)"),
        ("sym", r"(^|[^a-z])sym([^a-z]|$)"),
    ]

    matched = []
    for name, pattern in patterns:
        if re.search(pattern, s):
            matched.append(name)

    if not matched:
        return ""

    return "_" + "_".join(matched)


def read_data_from_file(input_file: Path) -> pd.DataFrame:
    """
    Read one speedup_data.csv file.

    The function first tries to parse the file as a standard CSV with columns:
        scenario, algorithm, workload, jct_ms

    If that fails, it falls back to the block-style format:
        scenario_name
        algorithm,workload,jct_ms
        ...
    """
    if not input_file.exists():
        raise FileNotFoundError("Input file not found: {}".format(input_file))

    raw_text = input_file.read_text(encoding="utf-8-sig").strip()
    if not raw_text:
        raise ValueError("Input file is empty: {}".format(input_file))

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
                    "Invalid block under scenario {!r}. Required columns: algorithm, workload, jct_ms".format(
                        scenario
                    )
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


def build_speedup_long(data: pd.DataFrame, baseline_alg: str) -> pd.DataFrame:
    """
    Compute per-workload speedup.

    If there are repeated rows for the same scenario/algorithm/workload,
    the script first averages their JCT.
    """
    avg = (
        data.groupby(["scenario", "algorithm", "workload"], as_index=False)["jct_ms"]
        .mean()
        .rename(columns={"jct_ms": "avg_jct_ms"})
    )

    baseline = (
        avg[avg["algorithm"] == baseline_alg][["scenario", "workload", "avg_jct_ms"]]
        .rename(columns={"avg_jct_ms": "baseline_jct_ms"})
    )

    if baseline.empty:
        available = sorted(avg["algorithm"].unique())
        raise ValueError(
            "Baseline algorithm {!r} not found. Available algorithms: {}".format(
                baseline_alg, available
            )
        )

    merged = avg.merge(baseline, on=["scenario", "workload"], how="left")

    missing_baseline = (
        merged[merged["baseline_jct_ms"].isna()][["scenario", "workload"]]
        .drop_duplicates()
        .values
        .tolist()
    )
    if missing_baseline:
        raise ValueError(
            "Baseline algorithm {!r} is missing in these scenario-workload pairs: {}".format(
                baseline_alg, missing_baseline
            )
        )

    merged["speedup"] = merged["baseline_jct_ms"] / merged["avg_jct_ms"]
    return merged


def resolve_orders(speedup_long: pd.DataFrame) -> Tuple[List[str], List[str], List[str]]:
    """Resolve scenario, algorithm, and workload orders."""
    scenario_set = set(speedup_long["scenario"])
    algorithm_set = set(speedup_long["algorithm"])
    workload_set = set(speedup_long["workload"])

    scenarios = [s for s in SCENARIO_ORDER if s in scenario_set]
    scenarios += [s for s in speedup_long["scenario"].unique() if s not in scenarios]

    algorithms = [a for a in ALGORITHM_ORDER if a in algorithm_set]
    algorithms += [a for a in speedup_long["algorithm"].unique() if a not in algorithms]

    workloads = [w for w in WORKLOAD_ORDER if w in workload_set]
    extra_workloads = [w for w in speedup_long["workload"].unique() if w not in workloads]
    workloads += sorted(extra_workloads, key=workload_sort_key)

    if len(workloads) != 4:
        raise ValueError(
            "This split-cell figure expects exactly 4 workloads. "
            "Resolved workloads: {}. "
            "Please modify WORKLOAD_ORDER or the layout logic if you need a different number.".format(
                workloads
            )
        )

    return scenarios, algorithms, workloads


def draw_workload_layout_legend(fig, workloads):
    """
    Draw a compact 2x2 workload-layout legend at the bottom-right of the figure.

    Layout:
        workloads[0] | workloads[1]
        workloads[2] | workloads[3]
    """
    # [left, bottom, width, height] in figure coordinates.
    legend_ax = fig.add_axes([0.05, 0.052, 0.135, 0.145])
    legend_ax.set_xlim(0.0, 2.0)
    legend_ax.set_ylim(0.0, 2.35)
    legend_ax.axis("off")

    bg = patches.FancyBboxPatch(
        (-0.10, -0.08),
        2.20,
        2.45,
        boxstyle="round,pad=0.045,rounding_size=0.035",
        facecolor=LAYOUT_LEGEND_BG_COLOR,
        edgecolor=MISSING_EDGE_COLOR,
        linewidth=0.45,
        alpha=LAYOUT_LEGEND_BG_ALPHA,
        zorder=0,
    )
    legend_ax.add_patch(bg)

    legend_ax.text(
        1.0,
        2.18,
        "Cell layout",
        ha="center",
        va="center",
        fontsize=LAYOUT_LEGEND_TITLE_SIZE,
        color=TEXT_COLOR,
        fontweight="normal",
    )

    positions = [
        (0.08, 1.08, workloads[0]),
        (1.02, 1.08, workloads[1]),
        (0.08, 0.14, workloads[2]),
        (1.02, 0.14, workloads[3]),
    ]

    for x0, y0, label in positions:
        rect = patches.Rectangle(
            (x0, y0),
            0.88,
            0.82,
            facecolor="#F7F7F7",
            edgecolor=EDGE_COLOR,
            linewidth=LAYOUT_LEGEND_EDGE_WIDTH,
            zorder=1,
        )
        legend_ax.add_patch(rect)
        legend_ax.text(
            x0 + 0.44,
            y0 + 0.41,
            str(label),
            ha="center",
            va="center",
            fontsize=LAYOUT_LEGEND_FONT_SIZE,
            color=TEXT_COLOR,
            zorder=2,
        )


def draw_split_cell_heatmap(
    speedup_long: pd.DataFrame,
    baseline_alg: str,
    output_png: Path,
    output_pdf: Path,
    color_vmin: Optional[float] = None,
    color_vmax: Optional[float] = None,
) -> None:
    apply_paper_style()
    topo_type = detect_suffix_from_path(output_pdf)
    scenarios, algorithms, workloads = resolve_orders(speedup_long)

    speedup_map = {
        (row["scenario"], row["algorithm"], row["workload"]): float(row["speedup"])
        for _, row in speedup_long.iterrows()
    }

    valid_vals = np.array(list(speedup_map.values()), dtype=float)
    valid_vals = valid_vals[np.isfinite(valid_vals)]
    if len(valid_vals) == 0:
        raise ValueError("No valid speedup values to plot.")

    vmin = color_vmin if color_vmin is not None else min(0.80, float(np.nanmin(valid_vals)))
    vmax = color_vmax if color_vmax is not None else max(1.25, float(np.nanmax(valid_vals)))

    if vmin >= 1.0 or vmax <= 1.0:
        raise ValueError(
            "Invalid color range: vmin={}, vmax={}; 1.0 must be inside.".format(vmin, vmax)
        )

    norm = TwoSlopeNorm(vmin=vmin, vcenter=1.0, vmax=vmax)

    # User-requested semantics:
    # green = worse than baseline, red = better than baseline.
    cmap = LinearSegmentedColormap.from_list(
        "green_gray_red",
        ["#4B8B5A", "#F7F7F7", "#B04A4A"],
    )

    # 2x2 subcell geometry.
    sub_w = (CELL_WIDTH - SUBCELL_GAP) / 2.0
    sub_h = (CELL_HEIGHT - SUBCELL_GAP) / 2.0

    workload_offsets = {
        workloads[0]: (-CELL_WIDTH / 2.0, -CELL_HEIGHT / 2.0 + sub_h + SUBCELL_GAP),  # top-left
        workloads[1]: (-CELL_WIDTH / 2.0 + sub_w + SUBCELL_GAP, -CELL_HEIGHT / 2.0 + sub_h + SUBCELL_GAP),  # top-right
        workloads[2]: (-CELL_WIDTH / 2.0, -CELL_HEIGHT / 2.0),  # bottom-left
        workloads[3]: (-CELL_WIDTH / 2.0 + sub_w + SUBCELL_GAP, -CELL_HEIGHT / 2.0),  # bottom-right
    }

    fig, ax = plt.subplots(figsize=(8.4, 4.4))

    for scenario_idx, scenario in enumerate(scenarios):
        y = len(scenarios) - 1 - scenario_idx

        for x, alg in enumerate(algorithms):
            outer = patches.Rectangle(
                (x - CELL_WIDTH / 2.0, y - CELL_HEIGHT / 2.0),
                CELL_WIDTH,
                CELL_HEIGHT,
                facecolor="none",
                edgecolor=MISSING_EDGE_COLOR,
                linewidth=MISSING_CELL_EDGE_WIDTH,
                zorder=1,
            )
            ax.add_patch(outer)

            for workload in workloads:
                val = speedup_map.get((scenario, alg, workload))
                dx, dy = workload_offsets[workload]
                x0 = x + dx
                y0 = y + dy

                if val is None or not np.isfinite(val):
                    facecolor = "#FFFFFF"
                    edgecolor = MISSING_EDGE_COLOR
                    label = ""
                else:
                    facecolor = cmap(norm(val))
                    edgecolor = EDGE_COLOR
                    label = "{:.2f}×".format(val)

                rect = patches.Rectangle(
                    (x0, y0),
                    sub_w,
                    sub_h,
                    facecolor=facecolor,
                    edgecolor=edgecolor,
                    linewidth=SUBCELL_EDGE_WIDTH,
                    zorder=2,
                )
                ax.add_patch(rect)

                if label:
                    text_color = "white" if (val >= 1.35 or val <= 0.88) else TEXT_COLOR
                    ax.text(
                        x0 + sub_w / 2.0,
                        y0 + sub_h / 2.0,
                        label,
                        ha="center",
                        va="center",
                        fontsize=SUBCELL_LABEL_FONT_SIZE,
                        color=text_color,
                        fontweight="normal",
                        zorder=3,
                    )

    ax.set_xticks(range(len(algorithms)))
    ax.set_xticklabels(algorithms, rotation=32, ha="right", fontsize=TICK_FONT_SIZE)

    y_positions = [len(scenarios) - 1 - i for i in range(len(scenarios))]
    ax.set_yticks(y_positions)
    ax.set_yticklabels(scenarios, fontsize=TICK_FONT_SIZE)

    ax.set_xlabel("Load Balancing Algorithm", fontsize=AXIS_LABEL_FONT_SIZE, color=TEXT_COLOR)
    ax.set_ylabel("Scenario", fontsize=AXIS_LABEL_FONT_SIZE, color=TEXT_COLOR)
    ax.set_title(
        "JCT Speedup over {} ({})".format(baseline_alg, topo_type.strip("_")),
        fontsize=TITLE_FONT_SIZE,
        color=TEXT_COLOR,
        pad=10,
    )

    ax.set_xlim(-0.6, len(algorithms) - 0.4)
    ax.set_ylim(-0.6, len(scenarios) - 0.4)

    ax.tick_params(axis="both", labelsize=TICK_FONT_SIZE, colors=TEXT_COLOR)
    ax.grid(True, axis="both", linestyle=":", linewidth=0.45, color=GRID_COLOR, alpha=0.70)
    ax.set_axisbelow(True)

    for spine in ax.spines.values():
        spine.set_color(AXIS_COLOR)
        spine.set_linewidth(0.8)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, pad=0.018)
    cbar.ax.tick_params(labelsize=COLORBAR_FONT_SIZE, colors=TEXT_COLOR, width=0.7, length=2.5)
    cbar.outline.set_edgecolor(AXIS_COLOR)
    cbar.outline.set_linewidth(0.7)
    cbar.set_label(
        # "Speedup vs. baseline\n" \
        "green: slower, red: faster",
        fontsize=COLORBAR_FONT_SIZE,
        color=TEXT_COLOR,
    )

    fig.tight_layout(rect=[0.0, 0.02, 1.0, 1.0])
    draw_workload_layout_legend(fig, workloads)

    fig.savefig(str(output_png), dpi=300, bbox_inches="tight")
    # fig.savefig(str(output_pdf), dpi=300, bbox_inches="tight")
    plt.close(fig)


def build_output_paths(directory: Path) -> Tuple[Path, Path]:
    """
    Build output PNG/PDF paths under the same directory as the input file.
    If the directory path contains asy / failure / sym, append it as suffix.
    """
    suffix = detect_suffix_from_path(directory)
    png_path = directory / "{}{}.png".format(OUTPUT_BASENAME, suffix)
    pdf_path = directory / "{}{}.pdf".format(OUTPUT_BASENAME, suffix)
    return png_path, pdf_path


def process_one_directory(directory: Path) -> None:
    input_file = directory / INPUT_FILENAME
    print("\n[INFO] Processing directory: {}".format(directory))
    print("[INFO] Input data file: {}".format(input_file))

    data = read_data_from_file(input_file)
    speedup_long = build_speedup_long(data, BASELINE_ALG)

    output_png, output_pdf = build_output_paths(directory)
    draw_split_cell_heatmap(
        speedup_long=speedup_long,
        baseline_alg=BASELINE_ALG,
        output_png=output_png,
        output_pdf=output_pdf,
        color_vmin=None,
        color_vmax=None,
    )

    print("[INFO] Saved PNG: {}".format(output_png))
    # print("[INFO] Saved PDF: {}".format(output_pdf))


def main() -> None:
    raw_paths = flatten_paths(CONFIG_LIST)
    directories = unique_existing_dirs(raw_paths)

    if not directories:
        print("[ERROR] No valid directory paths found in CONFIG_LIST.")
        return

    print("[INFO] Found {} valid directories.".format(len(directories)))

    success = 0
    failed = 0

    for directory in directories:
        try:
            process_one_directory(directory)
            success += 1
        except Exception as e:
            failed += 1
            print("[ERROR] Failed to process {}: {}".format(directory, e))

    print("\n[SUMMARY] Success: {}, Failed: {}".format(success, failed))


if __name__ == "__main__":
    main()
