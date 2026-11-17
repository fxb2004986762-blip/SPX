#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import operator
from dataclasses import dataclass
from typing import List, Optional, Any


# ============================================================
# 1. 输入配置：沿用之前脚本的路径配置习惯
# ============================================================

CONFIG_LIST = {
    "test": {
        # 可以直接填文件路径
        "0": "/home/dcn1/fxb/simulator/output/12asy_topo/topology_type/hpn/alltoall/letflow/letflow_mprdma-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100_asy-microAll2All_1024g_EP8_128M",

        # 也可以填目录路径，如果是目录，会自动拼接 INPUT_FILE_NAME
        # "1": "/home/dcn1/fxb/simulator/output",
    },
}

SELECT_GROUP = "test"
SELECT_ID = "0"

# 当 CONFIG_LIST 中填的是目录时，会自动读取该目录下的这个文件
INPUT_FILE_NAME = "qlen.txt"


# ============================================================
# 2. 过滤配置
# ============================================================

# 多个过滤条件之间的关系：
# "and"：所有条件都满足才打印
# "or" ：任意一个条件满足就打印
FILTER_LOGIC = "and"

# 字段列号从 1 开始
#
# 支持的 op:
#   ">"        大于
#   ">="       大于等于
#   "<"        小于
#   "<="       小于等于
#   "=="       等于
#   "!="       不等于
#   "between" 区间过滤，闭区间 [low, high]
#
# 示例数据：
#   790000, 1156, 73, 2.342400
#
# 第1列: 790000
# 第2列: 1156
# 第3列: 73
# 第4列: 2.342400
FILTERS = [
    {
        "column": 2,
        "op": "between",
        # "value": (1152, 1167),
        "value": (1168, 1183),
    },
    {
        "column": 3,
        "op": ">",
        "value": 65,
    },    
    {
        "column": 6,
        "op": ">",
        "value": 300_000,
    },    

    # 示例：第3列大于等于75
    # {
    #     "column": 3,
    #     "op": ">=",
    #     "value": 75,
    # },

    # 示例：第4列在 [3.0, 10.0] 范围内
    # {
    #     "column": 4,
    #     "op": "between",
    #     "value": (3.0, 10.0),
    # },
]


# ============================================================
# 3. 输出控制配置
# ============================================================

# 是否打印行号
PRINT_LINE_NO = True

# 是否打印最终统计信息
PRINT_SUMMARY = True

# 是否跳过无法解析的行
SKIP_BAD_LINES = True

# 是否打印无法解析的行
PRINT_BAD_LINES = False


# ============================================================
# 4. 打印速度控制配置
# ============================================================

# 是否开启限速打印
ENABLE_PRINT_THROTTLE = True

# 每秒大约打印多少行
#
# 推荐：
#   10 ~ 20：适合慢速观察
#   20 ~ 40：适合看整体趋势
#   50 ~ 100：快速扫日志
PRINT_LINES_PER_SECOND = 60

# 每打印多少行后 sleep 一次
#
# 不建议设置成 1，否则会频繁 sleep，脚本效率较低。
# 推荐 5 或 10。
# PRINT_BURST_LINES = 25


# ============================================================
# 5. 终端趋势条形图配置
# ============================================================

# 是否在每行末尾增加条形图
ENABLE_BAR_VIEW = False

# 使用哪一列绘制条形图，列号从1开始
BAR_COLUMN = 4

# 条形图缩放比例
#
# bar_width = value / BAR_SCALE
#
# 例如 value = 13.9, BAR_SCALE = 1.0，则大约打印 13 个 #
# 如果数值很大，例如 qlen 是几千，可以设置成 100 或 1000。
BAR_SCALE = 1.0

# 条形图最大宽度，避免终端太长
BAR_MAX_WIDTH = 60

# 条形图字符
BAR_CHAR = "#"


# ============================================================
# 6. 基础过滤操作符
# ============================================================

OPS = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}


# ============================================================
# 7. 数据结构和过滤规则
# ============================================================

@dataclass
class FilterRule:
    column: int
    op: str
    value: Any

    def match(self, fields: List[float]) -> bool:
        """
        判断一行数据是否满足当前过滤条件。

        参数：
            fields: 当前行解析后的数值列表

        返回：
            True  表示满足条件
            False 表示不满足条件
        """
        idx = self.column - 1

        if idx < 0 or idx >= len(fields):
            return False

        current_value = fields[idx]

        if self.op == "between":
            low, high = self.value
            return low <= current_value <= high

        if self.op not in OPS:
            raise ValueError(f"Unsupported operator: {self.op}")

        return OPS[self.op](current_value, self.value)


class PrintController:
    """
    控制终端打印速度。

    设计思路：
        不对每一行 sleep，而是每打印 burst_lines 行后 sleep 一次。
        这样既能控制终端滚动速度，又不会严重影响脚本执行效率。
    """

    def __init__(
        self,
        enable: bool = True,
        lines_per_second: int = 25,
        burst_lines: int = 5,
    ):
        self.enable = enable
        self.lines_per_second = lines_per_second
        self.burst_lines = max(1, burst_lines)
        self.printed_since_sleep = 0

        if self.lines_per_second <= 0:
            self.sleep_time = 0
        else:
            self.sleep_time = self.burst_lines / self.lines_per_second

    def print_line(self, line: str) -> None:
        print(line, flush=True)

        if not self.enable:
            return

        self.printed_since_sleep += 1

        if self.printed_since_sleep >= self.burst_lines:
            time.sleep(self.sleep_time)
            self.printed_since_sleep = 0


# ============================================================
# 8. 工具函数
# ============================================================

def resolve_input_path() -> str:
    """
    根据 CONFIG_LIST 解析最终输入文件路径。
    """
    path = CONFIG_LIST[SELECT_GROUP][SELECT_ID]

    if os.path.isdir(path):
        return os.path.join(path, INPUT_FILE_NAME)

    return path


def parse_line(line: str) -> Optional[List[float]]:
    """
    解析一行数据。

    兼容两种格式：
        790000, 1156, 73, 2.342400
        790000 1156 73 2.342400
    """
    line = line.strip()

    if not line:
        return None

    if line.startswith("#"):
        return None

    # 统一替换逗号为空格
    parts = line.replace(",", " ").split()

    try:
        return [float(x) for x in parts]
    except ValueError:
        return None


def build_filters(configs: List[dict]) -> List[FilterRule]:
    """
    根据 FILTERS 配置构造过滤规则。
    """
    rules = []

    for cfg in configs:
        rules.append(
            FilterRule(
                column=cfg["column"],
                op=cfg["op"],
                value=cfg["value"],
            )
        )

    return rules


def match_filters(
    fields: List[float],
    rules: List[FilterRule],
    logic: str = "and",
) -> bool:
    """
    判断当前行是否满足所有过滤规则。
    """
    if not rules:
        return True

    results = [rule.match(fields) for rule in rules]

    if logic == "and":
        return all(results)

    if logic == "or":
        return any(results)

    raise ValueError(f"Unsupported filter logic: {logic}")


def make_bar(
    value: float,
    scale: float = 1.0,
    max_width: int = 60,
    char: str = "#",
) -> str:
    """
    根据数值生成终端条形图。
    """
    if scale <= 0:
        scale = 1.0

    width = int(value / scale)
    width = max(0, min(width, max_width))

    return char * width


def format_output_line(
    line_no: int,
    raw_line: str,
    fields: List[float],
) -> str:
    """
    格式化输出内容。
    """
    if PRINT_LINE_NO:
        output = f"[line {line_no}] {raw_line}"
    else:
        output = raw_line

    if ENABLE_BAR_VIEW:
        bar_idx = BAR_COLUMN - 1

        if 0 <= bar_idx < len(fields):
            bar_value = fields[bar_idx]
            bar = make_bar(
                value=bar_value,
                scale=BAR_SCALE,
                max_width=BAR_MAX_WIDTH,
                char=BAR_CHAR,
            )
            output += f" | {bar}"

    return output


def print_filter_config(input_path: str, rules: List[FilterRule]) -> None:
    """
    打印当前过滤配置。
    """
    print("=" * 100)
    print(f"Input file      : {input_path}")
    print(f"Filter logic    : {FILTER_LOGIC}")
    print(f"Print throttle  : {ENABLE_PRINT_THROTTLE}")
    print(f"Lines per second: {PRINT_LINES_PER_SECOND}")
    # print(f"Burst lines     : {PRINT_BURST_LINES}")
    print(f"Bar view        : {ENABLE_BAR_VIEW}")

    if ENABLE_BAR_VIEW:
        print(f"Bar column      : {BAR_COLUMN}")
        print(f"Bar scale       : {BAR_SCALE}")
        print(f"Bar max width   : {BAR_MAX_WIDTH}")

    print("-" * 100)
    print("Filters:")

    if not rules:
        print("  No filters. All valid lines will be printed.")
    else:
        for rule in rules:
            print(f"  column {rule.column} {rule.op} {rule.value}")

    print("=" * 100)


# ============================================================
# 9. 主过滤逻辑
# ============================================================

def filter_file(input_path: str, rules: List[FilterRule]) -> None:
    """
    读取文件，过滤并打印满足条件的行。
    """
    total_lines = 0
    valid_lines = 0
    bad_lines = 0
    matched_lines = 0

    printer = PrintController(
        enable=ENABLE_PRINT_THROTTLE,
        lines_per_second=PRINT_LINES_PER_SECOND,
        # burst_lines=PRINT_BURST_LINES,
    )

    print_filter_config(input_path, rules)

    with open(input_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            total_lines += 1
            raw_line = line.rstrip("\n")

            fields = parse_line(raw_line)

            if fields is None:
                bad_lines += 1

                if not SKIP_BAD_LINES or PRINT_BAD_LINES:
                    printer.print_line(f"[BAD LINE {line_no}] {raw_line}")

                continue

            valid_lines += 1

            if match_filters(fields, rules, FILTER_LOGIC):
                matched_lines += 1
                output = format_output_line(line_no, raw_line, fields)
                printer.print_line(output)

    if PRINT_SUMMARY:
        print("=" * 100)
        print(f"Total lines   : {total_lines}")
        print(f"Valid lines   : {valid_lines}")
        print(f"Bad lines     : {bad_lines}")
        print(f"Matched lines : {matched_lines}")

        if valid_lines > 0:
            ratio = matched_lines / valid_lines * 100
            print(f"Matched ratio : {ratio:.2f}%")

        print("=" * 100)


# ============================================================
# 10. 主函数
# ============================================================

def main() -> None:
    input_path = resolve_input_path()

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    rules = build_filters(FILTERS)

    filter_file(input_path, rules)


if __name__ == "__main__":
    main()