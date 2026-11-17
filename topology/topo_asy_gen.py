import random
import re
import math
import shutil
from collections import defaultdict


def parse_lines(lines):
    """
    解析所有行，返回结构列表：
    每个元素为 dict:
        - index: 在 lines 中的原始下标
        - leading: 行首空白
        - content: 去除空白后的内容
        - group: 第一列组号（int），空行为 None
    """
    parsed = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        leading = line[:len(line) - len(line.lstrip())]
        if not stripped:
            parsed.append({"index": i, "leading": leading,
                           "content": stripped, "group": None})
        else:
            parts = stripped.split()
            group = int(parts[0]) if parts[0].lstrip('-').isdigit() else None
            parsed.append({"index": i, "leading": leading,
                           "content": stripped, "group": group})
    return parsed


def modify_fourth_column(filename, start, end, min_val, max_val,
                         ratio=1.0):
    """
    修改数据文件中指定行数往后的第四列数值为随机数，
    以组号（第一列）为单位，每组内只修改 ratio 比例的行。

    :param filename:   数据文件路径
    :param start_line: 从第几行开始修改（从1开始计数，空行也计入）
    :param min_val:    随机数最小值
    :param max_val:    随机数最大值
    :param ratio:      每组内被修改的行比例，0.0~1.0，默认1.0（全部修改）
    """
    with open(filename, 'r') as f:
        lines = f.readlines()

    parsed = parse_lines(lines)

    # ── 1. 找出需要处理的非空行（行号 >= start_line） ──────────────────────
    candidates = [
        p for p in parsed
        # if (p["index"] + 1 >= start_line and p["index"] + 1 <= end_line) and p["group"] is not None
        if (p["group"] >= start and p["group"] <= end) and p["group"] is not None
    ]

    # ── 2. 按组号分组，确定每组内要修改的行下标集合 ───────────────────────
    group_map = defaultdict(list)
    for p in candidates:
        group_map[p["group"]].append(p["index"])

    modify_set = set()
    for group_id, indices in group_map.items():
        k = math.ceil(len(indices) * ratio)   # 向上取整，至少保证比例
        chosen = random.sample(indices, k)
        modify_set.update(chosen)

    # ── 3. 逐行输出，命中 modify_set 的行替换第四列 ───────────────────────
    result_lines = []
    current_line = 0
    for p in parsed:
        current_line += 1
        new_content = ""
        if p["index"] in modify_set and BW_FAILURE:
            new_val = random.randint(min_val, max_val)
            new_content = re.sub(
                r'(\S+\s+\S+\s+)\d+Gbps',
                f'\\g<1>{new_val}Gbps',
                p["content"]
            )
        else:
            # 没有修改的行复原（包括空行）
            new_content = re.sub(
                r'(\S+\s+\S+\s+\S+\s+)(\d)+Gbps',
                f'\\g<1>\\g<2>Gbps',
                p["content"]
            )
            # result_lines.append(lines[p["index"]])
        parts = p["content"].split()
        if LINK_FAILURE and current_line > 2 and (int(parts[0]), int(parts[1])) in link_failure:
            result_lines.append(p["leading"] + new_content + ' ' + link_failure[(int(parts[0]), int(parts[1]))] + '\n')
        else:
            result_lines.append(p["leading"] + new_content + '\n')



    with open(filename, 'w') as f:
        f.writelines(result_lines)

    # ── 4. 统计报告 ────────────────────────────────────────────────────────
    print(f"上行链路修改完成！")
    print(f"  起始组    : 第 {start} 组")
    print(f"  结束组    : 第 {end} 组")
    print(f"  修改范围  : 第三列替换为 {min_val}~{max_val}Gbps 的随机值")
    print(f"  组内比例  : {ratio:.0%}")
    print(f"  涉及组数  : {len(group_map)} 组")
    print(f"  实际修改行: {len(modify_set)} / {len(candidates)} 行")
    print()
    print("  各组详情：")
    for group_id in sorted(group_map.keys()):
        total = len(group_map[group_id])
        modified = sum(1 for idx in group_map[group_id] if idx in modify_set)
        print(f"    组 {group_id:>6}：共 {total} 行，修改 {modified} 行")


# ═══════════════════════════════════════════════════════════════
#  在此处修改参数
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    PRIME_FILE_PATH  = "/home/dcn1/fxb/simulator/topology/SpectrumX_1024g_8gps_400Gbps_A100"   # 原始拓扑文件路径
    FILE_PATH = PRIME_FILE_PATH + "_asy"  # 修改后文件路径 _failure _asy
    shutil.copy(PRIME_FILE_PATH, FILE_PATH)

    START_LINE = 1152 #  1027   192       # 从ToR交换机哪个编号开始修改，以ToR编号为组
    END_LINE   = 1167 #    4098    223    # 从ToR交换机哪个编号结束，以ToR编号为组

    ## 修改链路带宽
    BW_FAILURE = True # True, False
    MIN     = 200            # 随机数最小值，基准值
    MAX     = 200           # 随机数最大值
    RATIO      = 0.03          # link pair左侧节点相同的为一个组，每组内被修改的行比例（0.0 ~ 1.0）

    ## 修改链路故障
    LINK_FAILURE = False
    link_failure = {
        (192, 224): "100 200",
        (192, 226): "500 700",
        # (1152, 1280): "100 200",
        # (1152, 1286): "500 700",
    }

    modify_fourth_column(FILE_PATH, START_LINE, END_LINE, MIN, MAX, RATIO)