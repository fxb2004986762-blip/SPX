#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plot average bandwidth / queue length over selected switch range and port range.

Input files under each experiment directory:
  bw.txt   columns: time, node_id, port_id, bandwidth
  qlen.txt columns: time, sw_id, port_id, q_id, q_len, port_len

Typical usage:
  1. Configure CONFIG_LIST or use configs.result_path.CONFIG_LIST.
  2. Configure TARGET_SWITCH_SELECTOR and TARGET_PORT_SELECTOR.
  3. Configure PLOT_MODE and AGGREGATE_MODE.
  4. python3 plot_avg_port_bw_qlen.py
"""

import ast
import math
import os
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42

# =========================================================
# User Config
# =========================================================
CONFIG_LIST = {
    # "test-1024GPU": {
    #     "0": "/home/dell/sjw/lb/simulator/output/12asy_topo/topology_type/hpn/alltoall/ecmp/ecmp_mprdma-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100_asy-microAll2All_1024g_EP8_128M",
    # },
}

# 如果本文件的 CONFIG_LIST 为空，则使用共享配置文件中的 CONFIG_LIST
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
if not CONFIG_LIST:
    from configs.result_path import CONFIG_LIST

BASE_DIR = ""
BW_FILE = os.path.join(BASE_DIR, "bw.txt")
QLEN_FILE = os.path.join(BASE_DIR, "qlen.txt")

OUT_DIR = BASE_DIR
OUT_NAME = "avg_bw_qlen"
OUT_FORMATS = ["png"]       # 可选: ["png"], ["png", "pdf"]
OUT_DPI = 300
SKIP_EXISTING = True
OUT_CNT = 0

# 绘图模式：
#   "both"：同时绘制平均带宽和平均队列，双 y 轴
#   "bw"  ：仅绘制平均带宽
#   "qlen"：仅绘制平均队列
PLOT_MODE = "both"          # "both" or "bw" or "qlen"

# 聚合模式：
#   "port"       ：每个端口一条曲线；对所有目标交换机求平均。推荐默认值。
#   "switch"     ：每个交换机一条曲线；对所有目标端口求平均。
#   "all"        ：所有目标交换机、目标端口整体求平均，只画一条曲线。
#   "switch_port"：每个 switch-port 一条曲线，不做跨 switch/port 平均，曲线可能很多。
AGGREGATE_MODE = "switch"     # "port" or "switch" or "all" or "switch_port"

# -----------------------------
# 交换机范围选择方式
# -----------------------------
# 方式1：列表
# TARGET_SWITCH_SELECTOR = {"type": "list", "values": [1152, 1159, 1160, 1167]}
#
# 方式2：闭区间 range，包含 end
# TARGET_SWITCH_SELECTOR = {"type": "range", "start": 1152, "end": 1160, "step": 1}
#
# 方式3：不等式/表达式。变量名固定为 id。
# 支持: 1152 <= id <= 1160, id >= 1152 and id <= 1160, id % 2 == 0, id in [1152, 1153]
# 注意：表达式会在当前文件实际出现过的交换机 id 集合上求值。
# TARGET_SWITCH_SELECTOR = {"type": "expr", "expr": "1152 <= id <= 1167"}
TARGET_SWITCH_SELECTOR = {"type": "expr", "expr": "1214 <= id <= 1222"}

# -----------------------------
# 端口范围选择方式
# -----------------------------
# TARGET_PORT_SELECTOR = {"type": "list", "values": [65, 73, 81, 89, 96, 105, 113, 121]}
# TARGET_PORT_SELECTOR = {"type": "range", "start": 65, "end": 121, "step": 8}
# TARGET_PORT_SELECTOR = {"type": "expr", "expr": "65 <= id <= 121 and id % 8 == 1"}
TARGET_PORT_SELECTOR = {"type": "list", "values": [5]}
# TARGET_PORT_SELECTOR = {"type": "list", "values": [1, 2, 3, 4]}

# 时间范围。单位由 TIME_CONFIG_UNIT 指定；None 表示不限制。
TIME_START = None
TIME_END = None
TIME_CONFIG_UNIT = "us"     # "ns" or "us" or "ms" or "s"

# 原始文件中 time 字段的单位。你原脚本最后 time / 1000 转成 us，因此通常是 ns。
TIME_IN_FILE_UNIT = "ns"    # "ns" or "us" or "ms" or "s"
PLOT_TIME_UNIT = "us"       # "ns" or "us" or "ms" or "s"

# 补全采样间隔。单位由 SAMPLE_INTERVAL_UNIT 指定。
# 例如原始数据每 10us 采样一次，则填 10 + "us"。
SAMPLE_INTERVAL = 10
SAMPLE_INTERVAL_UNIT = "us"

# 队列长度单位转换
QUEUE_UNIT = "KB"           # "B" or "KB" or "MB"

# 绘制 qlen.txt 中的哪个字段：
#   "port_len"：端口总队列长度，推荐默认值。
#   "q_len"   ：某个/某些优先级队列长度。
QUEUE_FIELD = "port_len"    # "port_len" or "q_len"

# 如果 QUEUE_FIELD == "q_len"，指定优先级队列。
TARGET_Q_IDS = [3]

# 如果 QUEUE_FIELD == "q_len" 且 TARGET_Q_IDS 有多个，先把多个 q_id 聚合成一个 per-port 队列值。
# 可选："mean", "sum", "max"
Q_LEN_AGG = "mean"

# 是否补全每条 switch-port 时间序列。
# 对于 bw/qlen 这类周期采样日志，建议 True；缺失点会使用前值 forward-fill。
FILL_MISSING_TIME = True

# 是否在补全时，对序列开头缺失值使用第一个有效值 bfill。
# 如果你希望开头未知值保持 NaN，可设为 False。
BFILL_SERIES_HEAD = True

# 图大小
FIGSIZE = (7.2, 4.8)

# 曲线颜色。如果目标端口/交换机很多，脚本会自动复用 tab20/tab10 调色板。
BASE_COLORS = [
    "#1b9e77",
    "#d95f02",
    "#7570b3",
    "#e7298a",
    "#66a61e",
    "#e6ab02",
    "#a6761d",
    "#666666",
]

plt.rcParams.update({
    "axes.titlesize": 16,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 11,
    "figure.titlesize": 18,
})


# =========================================================
# Time / Unit Helpers
# =========================================================
_TIME_TO_NS = {
    "ns": 1.0,
    "us": 1000.0,
    "ms": 1000.0 * 1000.0,
    "s": 1000.0 * 1000.0 * 1000.0,
}


def unit_to_ns(unit: str) -> float:
    unit = str(unit).strip().lower()
    if unit not in _TIME_TO_NS:
        raise ValueError(f"Unsupported time unit: {unit}. Use one of {list(_TIME_TO_NS.keys())}.")
    return _TIME_TO_NS[unit]


def convert_time_value(value: Optional[float], from_unit: str, to_unit: str) -> Optional[float]:
    if value is None:
        return None
    return float(value) * unit_to_ns(from_unit) / unit_to_ns(to_unit)


def config_time_to_file_time(value: Optional[float]) -> Optional[float]:
    return convert_time_value(value, TIME_CONFIG_UNIT, TIME_IN_FILE_UNIT)


def file_time_to_plot_time(series: pd.Series) -> pd.Series:
    factor = unit_to_ns(TIME_IN_FILE_UNIT) / unit_to_ns(PLOT_TIME_UNIT)
    return series.astype(float) * factor


def sample_interval_in_file_unit() -> int:
    interval = convert_time_value(SAMPLE_INTERVAL, SAMPLE_INTERVAL_UNIT, TIME_IN_FILE_UNIT)
    if interval is None or interval <= 0:
        raise ValueError("SAMPLE_INTERVAL must be positive.")
    rounded = int(round(interval))
    if rounded <= 0:
        raise ValueError("SAMPLE_INTERVAL is too small after unit conversion.")
    return rounded


# =========================================================
# Data Reading
# =========================================================
def read_csv_clean(path: str, columns: Sequence[str]) -> pd.DataFrame:
    """
    读取 bw.txt / qlen.txt。

    兼容两类格式：
      1. 逗号分隔：time, node_id, port_id, bandwidth
      2. 空格分隔：time node_id port_id bandwidth

    兼容有表头/无表头。
    """
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    sep = r"\s*,\s*|\s+"

    df = pd.read_csv(
        path,
        sep=sep,
        engine="python",
        comment="#",
        skip_blank_lines=True,
    )
    df.columns = [str(c).strip() for c in df.columns]

    # 无标准表头时，按固定列名重新读取。
    if not all(c in df.columns for c in columns):
        df = pd.read_csv(
            path,
            sep=sep,
            engine="python",
            header=None,
            names=columns,
            comment="#",
            skip_blank_lines=True,
        )
        df.columns = [str(c).strip() for c in df.columns]

    # 只保留需要的列，避免文件中存在额外字段影响后续处理。
    df = df[list(columns)].copy()

    for c in columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=columns)

    # id/time 类字段转 int，value 字段保留 float。
    for c in columns:
        if c in ("time", "node_id", "sw_id", "port_id", "q_id"):
            df[c] = df[c].astype(int)

    return df


def queue_unit_convert(series: pd.Series) -> pd.Series:
    unit = str(QUEUE_UNIT).strip().upper()
    if unit == "B":
        return series.astype(float)
    if unit == "KB":
        return series.astype(float) / 1024.0
    if unit == "MB":
        return series.astype(float) / 1024.0 / 1024.0
    raise ValueError('QUEUE_UNIT must be one of: "B", "KB", "MB".')


# =========================================================
# Safe Selector Expression
# =========================================================
_ALLOWED_BIN_OPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
}

_ALLOWED_UNARY_OPS = {
    ast.UAdd: lambda a: +a,
    ast.USub: lambda a: -a,
    ast.Not: lambda a: not a,
}

_ALLOWED_CMP_OPS = {
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
}


def _safe_eval_ast(node: ast.AST, value_id: int) -> Any:
    if isinstance(node, ast.Expression):
        return _safe_eval_ast(node.body, value_id)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, bool)):
            return node.value
        raise ValueError(f"Unsupported constant in selector expression: {node.value!r}")

    if isinstance(node, ast.Name):
        if node.id == "id":
            return value_id
        raise ValueError(f"Unsupported variable in selector expression: {node.id}. Only 'id' is allowed.")

    if isinstance(node, ast.List):
        return [_safe_eval_ast(x, value_id) for x in node.elts]

    if isinstance(node, ast.Tuple):
        return tuple(_safe_eval_ast(x, value_id) for x in node.elts)

    if isinstance(node, ast.Set):
        return set(_safe_eval_ast(x, value_id) for x in node.elts)

    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            return all(bool(_safe_eval_ast(v, value_id)) for v in node.values)
        if isinstance(node.op, ast.Or):
            return any(bool(_safe_eval_ast(v, value_id)) for v in node.values)
        raise ValueError("Unsupported boolean operator in selector expression.")

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_UNARY_OPS:
            raise ValueError("Unsupported unary operator in selector expression.")
        return _ALLOWED_UNARY_OPS[op_type](_safe_eval_ast(node.operand, value_id))

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_BIN_OPS:
            raise ValueError("Unsupported binary operator in selector expression.")
        left = _safe_eval_ast(node.left, value_id)
        right = _safe_eval_ast(node.right, value_id)
        return _ALLOWED_BIN_OPS[op_type](left, right)

    if isinstance(node, ast.Compare):
        left = _safe_eval_ast(node.left, value_id)
        for op, comparator in zip(node.ops, node.comparators):
            op_type = type(op)
            if op_type not in _ALLOWED_CMP_OPS:
                raise ValueError("Unsupported comparison operator in selector expression.")
            right = _safe_eval_ast(comparator, value_id)
            if not _ALLOWED_CMP_OPS[op_type](left, right):
                return False
            left = right
        return True

    raise ValueError(f"Unsupported syntax in selector expression: {ast.dump(node)}")


def eval_selector_expr(expr: str, value_id: int) -> bool:
    tree = ast.parse(expr, mode="eval")
    return bool(_safe_eval_ast(tree, value_id))


Selector = Union[str, Sequence[int], Dict[str, Any], None]


def parse_dash_range(text: str) -> Optional[List[int]]:
    """
    支持简单字符串范围："1152-1160" 或 "65-121:8"。
    """
    text = text.strip()
    m = re.fullmatch(r"(-?\d+)\s*-\s*(-?\d+)(?:\s*:\s*(\d+))?", text)
    if not m:
        return None
    start = int(m.group(1))
    end = int(m.group(2))
    step = int(m.group(3)) if m.group(3) else 1
    if step <= 0:
        raise ValueError("Range step must be positive.")
    if start <= end:
        return list(range(start, end + 1, step))
    return list(range(start, end - 1, -step))


def resolve_selector(selector: Selector, available_ids: Iterable[int], name: str) -> List[int]:
    """
    把 selector 解析成具体 id 列表。

    selector 支持：
      None / "all"                         -> 文件中所有 id
      [1, 2, 3]                            -> 列表
      "1152-1160" / "65-121:8"            -> 简单闭区间字符串
      "1152 <= id <= 1160"                 -> 表达式字符串
      {"type": "list", "values": [...]}  -> 列表
      {"type": "range", "start": a, "end": b, "step": s}
      {"type": "expr", "expr": "..."}   -> 表达式
    """
    available = sorted({int(x) for x in available_ids})
    if not available:
        return []

    if selector is None:
        return available

    if isinstance(selector, str):
        s = selector.strip()
        if s.lower() == "all":
            return available
        dash_range = parse_dash_range(s)
        if dash_range is not None:
            return sorted({int(x) for x in dash_range})
        return [x for x in available if eval_selector_expr(s, x)]

    if isinstance(selector, (list, tuple, set)):
        return sorted({int(x) for x in selector})

    if isinstance(selector, dict):
        typ = str(selector.get("type", "list")).strip().lower()
        if typ == "all":
            return available
        if typ == "list":
            return sorted({int(x) for x in selector.get("values", [])})
        if typ == "range":
            start = int(selector["start"])
            end = int(selector["end"])
            step = int(selector.get("step", 1))
            if step <= 0:
                raise ValueError(f"{name} selector range step must be positive.")
            if start <= end:
                return list(range(start, end + 1, step))
            return list(range(start, end - 1, -step))
        if typ == "expr":
            expr = str(selector["expr"])
            return [x for x in available if eval_selector_expr(expr, x)]
        raise ValueError(f"Unsupported {name} selector type: {typ}")

    raise TypeError(f"Unsupported {name} selector: {selector!r}")


def summarize_id_list(ids: Sequence[int], max_items: int = 6) -> str:
    ids = sorted({int(x) for x in ids})
    if not ids:
        return "none"

    if len(ids) >= 2:
        diffs = [ids[i + 1] - ids[i] for i in range(len(ids) - 1)]
        if len(set(diffs)) == 1:
            step = diffs[0]
            if step == 1:
                return f"{ids[0]}-{ids[-1]}"
            return f"{ids[0]}-{ids[-1]}s{step}"

    if len(ids) <= max_items:
        return "_".join(str(x) for x in ids)
    return f"{ids[0]}-{ids[-1]}n{len(ids)}"


def sanitize_filename(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.()\-]+", "_", s)


# =========================================================
# Time Series Processing
# =========================================================
def filter_time(df: pd.DataFrame) -> pd.DataFrame:
    start = config_time_to_file_time(TIME_START)
    end = config_time_to_file_time(TIME_END)

    if start is not None:
        df = df[df["time"] >= start]
    if end is not None:
        df = df[df["time"] <= end]
    return df


def complete_timeseries(
    df: pd.DataFrame,
    group_cols: Sequence[str],
    value_col: str,
    time_col: str = "time",
) -> pd.DataFrame:
    """
    对每个 group 独立补全时间序列。
    缺失时间戳使用前值 forward-fill。
    """
    if df.empty or not FILL_MISSING_TIME:
        return df

    start_cfg = config_time_to_file_time(TIME_START)
    end_cfg = config_time_to_file_time(TIME_END)

    global_start = int(start_cfg) if start_cfg is not None else int(df[time_col].min())
    global_end = int(end_cfg) if end_cfg is not None else int(df[time_col].max())
    step = sample_interval_in_file_unit()

    if global_end < global_start:
        return df.iloc[0:0].copy()

    full_time_index = pd.Index(
        range(global_start, global_end + 1, step),
        name=time_col,
    )

    completed = []
    for keys, g in df.groupby(list(group_cols)):
        g = g.sort_values(time_col).drop_duplicates(subset=[time_col], keep="last")
        g = g.set_index(time_col).reindex(full_time_index)

        if not isinstance(keys, tuple):
            keys = (keys,)
        for col, key in zip(group_cols, keys):
            g[col] = key

        g[value_col] = g[value_col].ffill()
        if BFILL_SERIES_HEAD:
            g[value_col] = g[value_col].bfill()

        g = g.reset_index()
        completed.append(g)

    if not completed:
        return df.iloc[0:0].copy()

    return pd.concat(completed, ignore_index=True)


def aggregate_values(values: pd.core.groupby.SeriesGroupBy, how: str) -> pd.Series:
    how = str(how).strip().lower()
    if how == "mean":
        return values.mean()
    if how == "sum":
        return values.sum()
    if how == "max":
        return values.max()
    raise ValueError('Aggregation must be one of: "mean", "sum", "max".')


def normalize_plot_mode() -> str:
    mode = str(PLOT_MODE).strip().lower()
    aliases = {
        "both": "both",
        "all": "both",
        "bw_qlen": "both",
        "bandwidth_queue": "both",
        "bw": "bw",
        "bandwidth": "bw",
        "throughput": "bw",
        "qlen": "qlen",
        "queue": "qlen",
    }
    if mode not in aliases:
        raise ValueError('PLOT_MODE must be one of: "both", "bw", "qlen".')
    return aliases[mode]


def normalize_aggregate_mode() -> str:
    mode = str(AGGREGATE_MODE).strip().lower()
    aliases = {
        "port": "port",
        "by_port": "port",
        "avg_by_port": "port",
        "switch": "switch",
        "sw": "switch",
        "by_switch": "switch",
        "all": "all",
        "global": "all",
        "total": "all",
        "switch_port": "switch_port",
        "sw_port": "switch_port",
        "raw": "switch_port",
    }
    if mode not in aliases:
        raise ValueError('AGGREGATE_MODE must be one of: "port", "switch", "all", "switch_port".')
    return aliases[mode]


def need_plot_bw() -> bool:
    return normalize_plot_mode() in ("both", "bw")


def need_plot_qlen() -> bool:
    return normalize_plot_mode() in ("both", "qlen")


# =========================================================
# Load Metric Data
# =========================================================
def load_bw_df(path: str) -> pd.DataFrame:
    df = read_csv_clean(path, ["time", "node_id", "port_id", "bandwidth"])
    return df


def load_qlen_df(path: str) -> pd.DataFrame:
    df = read_csv_clean(path, ["time", "sw_id", "port_id", "q_id", "q_len", "port_len"])
    return df


def prepare_bw_series(
    bw: pd.DataFrame,
    target_switches: Sequence[int],
    target_ports: Sequence[int],
) -> pd.DataFrame:
    bw = bw[
        bw["node_id"].isin(target_switches)
        & bw["port_id"].isin(target_ports)
    ].copy()
    bw = filter_time(bw)

    if bw.empty:
        return pd.DataFrame(columns=["time", "switch_id", "port_id", "value"])

    bw = complete_timeseries(
        bw,
        group_cols=["node_id", "port_id"],
        value_col="bandwidth",
    )

    bw = bw.rename(columns={"node_id": "switch_id", "bandwidth": "value"})
    bw = bw[["time", "switch_id", "port_id", "value"]].copy()
    bw["plot_time"] = file_time_to_plot_time(bw["time"])
    return bw


def prepare_qlen_series(
    qlen: pd.DataFrame,
    target_switches: Sequence[int],
    target_ports: Sequence[int],
) -> pd.DataFrame:
    qlen = qlen[
        qlen["sw_id"].isin(target_switches)
        & qlen["port_id"].isin(target_ports)
    ].copy()

    if QUEUE_FIELD not in ("port_len", "q_len"):
        raise ValueError('QUEUE_FIELD must be one of: "port_len", "q_len".')

    if QUEUE_FIELD == "q_len":
        qlen = qlen[qlen["q_id"].isin(TARGET_Q_IDS)].copy()
        group_cols = ["sw_id", "port_id", "q_id"]
    else:
        # port_len 在同一个 time/sw/port 下会随 q_id 重复出现，只保留一份。
        qlen = qlen.drop_duplicates(
            subset=["time", "sw_id", "port_id"],
            keep="last",
        ).copy()
        group_cols = ["sw_id", "port_id"]

    qlen = filter_time(qlen)

    if qlen.empty:
        return pd.DataFrame(columns=["time", "switch_id", "port_id", "value"])

    qlen["queue_value"] = queue_unit_convert(qlen[QUEUE_FIELD])

    qlen = complete_timeseries(
        qlen,
        group_cols=group_cols,
        value_col="queue_value",
    )

    if QUEUE_FIELD == "q_len":
        # 多个 q_id 先聚合成 per switch-port 的队列值。
        grouped = qlen.groupby(["time", "sw_id", "port_id"])["queue_value"]
        qlen = aggregate_values(grouped, Q_LEN_AGG).reset_index(name="queue_value")

    qlen = qlen.rename(columns={"sw_id": "switch_id", "queue_value": "value"})
    qlen = qlen[["time", "switch_id", "port_id", "value"]].copy()
    qlen["plot_time"] = file_time_to_plot_time(qlen["time"])
    return qlen


def aggregate_for_plot(df: pd.DataFrame) -> pd.DataFrame:
    """
    输入：per switch-port time series
    输出：plot_time, series_key, series_label, value
    """
    mode = normalize_aggregate_mode()
    if df.empty:
        return pd.DataFrame(columns=["plot_time", "series_key", "series_label", "value"])

    if mode == "all":
        out = df.groupby("plot_time")["value"].mean().reset_index()
        out["series_key"] = "AVG"
        out["series_label"] = "Avg"
        return out[["plot_time", "series_key", "series_label", "value"]]

    if mode == "port":
        out = df.groupby(["plot_time", "port_id"])["value"].mean().reset_index()
        out["series_key"] = out["port_id"].astype(int).map(lambda x: f"P{x}")
        out["series_label"] = out["port_id"].astype(int).map(lambda x: f"P{x}")
        return out[["plot_time", "series_key", "series_label", "value"]]

    if mode == "switch":
        out = df.groupby(["plot_time", "switch_id"])["value"].mean().reset_index()
        out["series_key"] = out["switch_id"].astype(int).map(lambda x: f"S{x}")
        out["series_label"] = out["switch_id"].astype(int).map(lambda x: f"S{x}")
        return out[["plot_time", "series_key", "series_label", "value"]]

    if mode == "switch_port":
        out = df.copy()
        out["series_key"] = out.apply(
            lambda r: f"S{int(r['switch_id'])}-P{int(r['port_id'])}", axis=1
        )
        out["series_label"] = out["series_key"]
        return out[["plot_time", "series_key", "series_label", "value"]]

    raise ValueError(f"Unsupported AGGREGATE_MODE: {mode}")


# =========================================================
# Plot Helpers
# =========================================================
def get_colors(series_keys: Sequence[str]) -> Dict[str, Any]:
    keys = list(dict.fromkeys(series_keys))
    colors = []
    colors.extend(BASE_COLORS)

    cmap_names = ["tab20", "tab10"]
    for cmap_name in cmap_names:
        cmap = plt.get_cmap(cmap_name)
        for i in range(cmap.N):
            colors.append(cmap(i))

    if len(keys) > len(colors):
        # 兜底：使用 hsv 按数量生成颜色。
        cmap = plt.get_cmap("hsv")
        for i in range(len(keys) - len(colors)):
            colors.append(cmap(i / max(1, len(keys) - len(colors))))

    return {k: colors[i] for i, k in enumerate(keys)}


def make_metric_handles(plot_bw: bool, plot_qlen: bool) -> List[Line2D]:
    handles = []
    if plot_bw:
        handles.append(
            Line2D(
                [0], [0],
                color="black",
                linewidth=2.2,
                marker="o",
                markersize=4,
                linestyle="-",
                label="BW",
            )
        )
    if plot_qlen:
        handles.append(
            Line2D(
                [0], [0],
                color="black",
                linewidth=2.2,
                linestyle="--",
                label=f"Queue ({QUEUE_UNIT})",
            )
        )
    return handles


def get_output_paths(
    out_dir: str,
    target_switches: Sequence[int],
    target_ports: Sequence[int],
) -> List[str]:
    mode = normalize_plot_mode()
    agg_mode = normalize_aggregate_mode()
    sw_tag = summarize_id_list(target_switches)
    port_tag = summarize_id_list(target_ports)
    q_tag = ""
    if mode in ("both", "qlen") and QUEUE_FIELD == "q_len":
        q_tag = "_q" + summarize_id_list(TARGET_Q_IDS)

    base = sanitize_filename(
        f"{OUT_NAME}_{mode}_{agg_mode}_sw{sw_tag}_p{port_tag}{q_tag}"
    )
    return [os.path.join(out_dir, f"{base}.{fmt}") for fmt in OUT_FORMATS]


def plot_metric_lines(
    ax: plt.Axes,
    data: pd.DataFrame,
    color_map: Dict[str, Any],
    linestyle: str,
    marker: Optional[str],
    alpha: float,
) -> None:
    if data.empty:
        return

    for key, g in data.groupby("series_key", sort=False):
        g = g.sort_values("plot_time")
        ax.plot(
            g["plot_time"],
            g["value"],
            color=color_map[key],
            linewidth=2.0,
            marker=marker,
            markersize=3 if marker else 0,
            linestyle=linestyle,
            alpha=alpha,
            label="_nolegend_",
        )


def plot_one_dir(
    base_dir: str,
    algo_name: str,
    size_label: str,
) -> None:
    global OUT_CNT

    mode = normalize_plot_mode()
    plot_bw = need_plot_bw()
    plot_qlen = need_plot_qlen()

    bw_path = os.path.join(base_dir, "bw.txt")
    qlen_path = os.path.join(base_dir, "qlen.txt")
    out_dir = base_dir
    os.makedirs(out_dir, exist_ok=True)

    required_files = []
    if plot_bw:
        required_files.append(bw_path)
    if plot_qlen:
        required_files.append(qlen_path)

    missing_files = [fp for fp in required_files if not os.path.exists(fp)]
    if missing_files:
        print(f"[{OUT_CNT}] Warning: Required file(s) do not exist, skipping: {missing_files}")
        return

    bw_raw = load_bw_df(bw_path) if plot_bw else None
    qlen_raw = load_qlen_df(qlen_path) if plot_qlen else None

    available_switches = set()
    available_ports = set()
    if bw_raw is not None and not bw_raw.empty:
        available_switches.update(bw_raw["node_id"].astype(int).unique().tolist())
        available_ports.update(bw_raw["port_id"].astype(int).unique().tolist())
    if qlen_raw is not None and not qlen_raw.empty:
        available_switches.update(qlen_raw["sw_id"].astype(int).unique().tolist())
        available_ports.update(qlen_raw["port_id"].astype(int).unique().tolist())

    target_switches = resolve_selector(TARGET_SWITCH_SELECTOR, available_switches, "switch")
    target_ports = resolve_selector(TARGET_PORT_SELECTOR, available_ports, "port")

    if not target_switches:
        print(f"[{OUT_CNT}] Warning: no switch id matched TARGET_SWITCH_SELECTOR, skipping: {base_dir}")
        return
    if not target_ports:
        print(f"[{OUT_CNT}] Warning: no port id matched TARGET_PORT_SELECTOR, skipping: {base_dir}")
        return

    out_paths = get_output_paths(out_dir, target_switches, target_ports)
    if SKIP_EXISTING and all(os.path.exists(p) for p in out_paths):
        print(f"[{OUT_CNT}] Info: image already exists, skipping: {out_paths[0]}")
        return

    print(f"[{OUT_CNT}] Base dir: {base_dir}")
    print(f"[{OUT_CNT}] Selected switches: {summarize_id_list(target_switches)} -> {target_switches}")
    print(f"[{OUT_CNT}] Selected ports   : {summarize_id_list(target_ports)} -> {target_ports}")

    bw_plot = pd.DataFrame(columns=["plot_time", "series_key", "series_label", "value"])
    qlen_plot = pd.DataFrame(columns=["plot_time", "series_key", "series_label", "value"])

    if plot_bw:
        bw_series = prepare_bw_series(bw_raw, target_switches, target_ports)
        bw_plot = aggregate_for_plot(bw_series)
        if bw_plot.empty:
            print(f"[{OUT_CNT}] Warning: no bandwidth data after filtering.")

    if plot_qlen:
        qlen_series = prepare_qlen_series(qlen_raw, target_switches, target_ports)
        qlen_plot = aggregate_for_plot(qlen_series)
        if qlen_plot.empty:
            print(f"[{OUT_CNT}] Warning: no queue data after filtering.")

    if (plot_bw and bw_plot.empty) and (plot_qlen and qlen_plot.empty):
        print(f"[{OUT_CNT}] Warning: no data to plot, skipping.")
        return

    # 统一 series key，保证 bw 和 qlen 相同端口/交换机使用相同颜色。
    series_keys = []
    if not bw_plot.empty:
        series_keys.extend(bw_plot["series_key"].drop_duplicates().tolist())
    if not qlen_plot.empty:
        series_keys.extend(qlen_plot["series_key"].drop_duplicates().tolist())
    series_keys = list(dict.fromkeys(series_keys))
    color_map = get_colors(series_keys)

    fig, ax1 = plt.subplots(figsize=FIGSIZE)
    if mode == "both":
        ax_bw = ax1
        ax_qlen = ax1.twinx()
    elif mode == "bw":
        ax_bw = ax1
        ax_qlen = None
    else:
        ax_bw = None
        ax_qlen = ax1

    if plot_bw and ax_bw is not None:
        plot_metric_lines(
            ax=ax_bw,
            data=bw_plot,
            color_map=color_map,
            linestyle="-",
            marker="o",
            alpha=1.0,
        )

    if plot_qlen and ax_qlen is not None:
        plot_metric_lines(
            ax=ax_qlen,
            data=qlen_plot,
            color_map=color_map,
            linestyle="--",
            marker=None,
            alpha=0.72,
        )

    ax1.set_xlabel(f"Time ({PLOT_TIME_UNIT})")

    if mode == "both":
        ax_bw.set_ylabel("Average Port Throughput (Gbps)")
        ax_qlen.set_ylabel(f"Average Port Queue Length ({QUEUE_UNIT})")
        ax_bw.set_ylim(bottom=0)
        ax_qlen.set_ylim(bottom=0)
    elif mode == "bw":
        ax1.set_ylabel("Average Port Throughput (Gbps)")
        ax1.set_ylim(bottom=0)
    else:
        ax1.set_ylabel(f"Average Port Queue Length ({QUEUE_UNIT})")
        ax1.set_ylim(bottom=0)

    ax1.grid(True, which="both", linestyle=":", linewidth=0.75, alpha=0.75)

    if mode == "both":
        ax_bw.set_zorder(ax_qlen.get_zorder() + 1)
        ax_bw.patch.set_visible(False)

    agg_mode = normalize_aggregate_mode()
    sw_tag = summarize_id_list(target_switches)
    port_tag = summarize_id_list(target_ports)
    # ax1.set_title(f"Average {mode.upper()} | {agg_mode} | sw {sw_tag}, port {port_tag}")

    # Legend：颜色表示聚合后的曲线对象；线型表示指标。
    series_handles = [
        Line2D(
            [0], [0],
            color=color_map[key],
            linewidth=2.2,
            linestyle="-",
            label=key,
        )
        for key in series_keys
    ]
    metric_handles = make_metric_handles(plot_bw, plot_qlen)
    legend_handles = series_handles + metric_handles
    legend_labels = [h.get_label() for h in legend_handles]

    legend_ncol = len(legend_handles)
    if legend_ncol >= 10:
        legend_ncol = max(1, math.ceil(legend_ncol / 2))

    legend = fig.legend(
        legend_handles,
        legend_labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.985),
        ncol=legend_ncol,
        frameon=False,
        fontsize=10,
        handlelength=1.7,
        columnspacing=1.2,
        handletextpad=0.45,
        labelspacing=0.55,
        borderaxespad=0.0,
    )

    # 自适应计算 legend 高度，让绘图区尽量贴近 legend。
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    legend_bbox = legend.get_window_extent(renderer=renderer)
    legend_bbox = legend_bbox.transformed(fig.transFigure.inverted())

    top_pad = 0.018
    adaptive_top = legend_bbox.y0 - top_pad
    adaptive_top = min(adaptive_top, 0.90)
    adaptive_top = max(adaptive_top, 0.68)

    fig.subplots_adjust(
        left=0.095,
        right=0.91 if mode == "both" else 0.97,
        bottom=0.13,
        top=adaptive_top,
    )

    for out_path in out_paths:
        fmt = os.path.splitext(out_path)[1].lower().lstrip(".")
        if fmt == "png":
            plt.savefig(out_path, bbox_inches="tight", pad_inches=0.025, dpi=OUT_DPI)
        else:
            plt.savefig(out_path, bbox_inches="tight", pad_inches=0.025)
        print(f"[{OUT_CNT}] Saved: {out_path}")

    plt.close(fig)


# =========================================================
# Config Collection
# =========================================================
def collect_results(config: Dict[str, Dict[str, str]]) -> Tuple[List[str], List[str], Dict[str, Dict[str, str]]]:
    """
    保留你原脚本的输入组织方式：
      CONFIG_LIST[algo][size] = experiment_output_dir
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
                data[algo][sz] = ""
            else:
                print(f"  Parsing [{algo}][{sz}]: {fp}")
                data[algo][sz] = fp

    return algorithms, sizes, data


def main() -> None:
    global OUT_CNT

    algorithms, sizes, data = collect_results(CONFIG_LIST)

    if not algorithms:
        print("Warning: CONFIG_LIST is empty. Please configure CONFIG_LIST or configs.result_path.CONFIG_LIST.")
        return

    for sz in sizes:
        for algo in algorithms:
            base_dir = data.get(algo, {}).get(sz, "")
            if not base_dir:
                continue
            OUT_CNT += 1
            plot_one_dir(base_dir=base_dir, algo_name=algo, size_label=sz)


if __name__ == "__main__":
    main()
