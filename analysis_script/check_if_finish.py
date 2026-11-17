#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any, Iterator, Tuple


# DEFAULT_TARGET_LINES = 7168 #alltoall 7168, allreduce 6144
DEFAULT_TARGET_LINES = 0 #alltoall 7168, allreduce 6144
DEFAULT_FCT_FILENAME = "fct.txt"
ALLTOALL_FCT_LINES = 7168
ALLREDUCE_FCT_LINES = 6144

# 默认从configs.result_path导入 CONFIG_LIST
CONFIG_LIST = {}
# 如果本文件的CONFIG_LIST为空，则使用共享配置文件中的 CONFIG_LIST
if not CONFIG_LIST:
    from configs.result_path import CONFIG_LIST

def load_config_list(config_file: str) -> Dict[str, Any]:
    """
    从指定 Python 配置文件中动态导入 CONFIG_LIST。
    例如：
        python check_fct_lines.py --config config_paths.py
    """
    config_path = Path(config_file).resolve()

    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    spec = importlib.util.spec_from_file_location("config_module", config_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载配置文件: {config_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["config_module"] = module
    spec.loader.exec_module(module)

    if not hasattr(module, "CONFIG_LIST"):
        raise AttributeError(f"配置文件中没有找到 CONFIG_LIST: {config_path}")

    config_list = getattr(module, "CONFIG_LIST")

    if not isinstance(config_list, dict):
        raise TypeError("CONFIG_LIST 必须是 dict 类型")

    return config_list


def iter_config_dirs(
    config: Dict[str, Any],
    prefix: Tuple[str, ...] = ()
) -> Iterator[Tuple[Tuple[str, ...], Path]]:
    """
    递归遍历 CONFIG_LIST，找到所有目录字符串。

    支持如下结构：
        CONFIG_LIST = {
            "aps-v2": {
                "0": "/path/to/exp0",
                "1": "/path/to/exp1",
            }
        }

    返回：
        (("aps-v2", "0"), Path("/path/to/exp0"))
    """
    for key, value in config.items():
        cur_prefix = prefix + (str(key),)

        if isinstance(value, str):
            yield cur_prefix, Path(value)
        elif isinstance(value, dict):
            yield from iter_config_dirs(value, cur_prefix)
        else:
            print(f"[WARN] 跳过非法配置项: {'/'.join(cur_prefix)} -> {value}")


def count_lines_fast(file_path: Path) -> int:
    """
    快速统计文件行数，适合较大的 fct.txt。
    注意：
        如果文件最后一行没有换行符，也会正确计为一行。
    """
    line_count = 0
    last_char = b""

    with file_path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            line_count += chunk.count(b"\n")
            last_char = chunk[-1:]

    if file_path.stat().st_size > 0 and last_char != b"\n":
        line_count += 1

    return line_count


def check_fct_files(
    config_list: Dict[str, Any],
    target_lines: int,
    fct_filename: str,
):
    """
    检查所有目录下的 fct.txt 行数是否等于 target_lines。
    返回异常结果列表。
    """
    bad_results = []
    total_count = 0
    ok_count = 0
    workload_type = ""

    for keys, exp_dir in iter_config_dirs(config_list):
        total_count += 1

        fct_path = exp_dir / fct_filename
        label = "/".join(keys)

        if not exp_dir.exists():
            bad_results.append({
                "label": label,
                "dir": str(exp_dir),
                "fct_path": str(fct_path),
                "status": "DIR_NOT_FOUND",
                "lines": None,
            })
            continue

        if not fct_path.exists():
            bad_results.append({
                "label": label,
                "dir": str(exp_dir),
                "fct_path": str(fct_path),
                "status": "FCT_NOT_FOUND",
                "lines": None,
            })
            continue

        try:
            line_count = count_lines_fast(fct_path)
        except Exception as e:
            bad_results.append({
                "label": label,
                "dir": str(exp_dir),
                "fct_path": str(fct_path),
                "status": f"READ_ERROR: {e}",
                "lines": None,
            })
            continue
        if ("allreduce" in str(exp_dir)): 
            target_lines = ALLREDUCE_FCT_LINES
            workload_type = "allreduce"

        elif ("alltoall" in str(exp_dir)): 
            target_lines = ALLTOALL_FCT_LINES
            workload_type = "alltoall"


        if line_count != target_lines:
            bad_results.append({
                "label": label,
                "dir": str(exp_dir),
                "fct_path": str(fct_path),
                "status": "LINE_COUNT_MISMATCH",
                "lines": line_count,
            })
        else:
            ok_count += 1

    return total_count, ok_count, bad_results, workload_type


def print_results(total_count: int, ok_count: int, bad_results: list, target_lines: int):
    print("=" * 100)
    print(f"检查完成")
    print(f"目标行数: {target_lines}")
    print(f"总目录数: {total_count}")
    print(f"正常目录数: {ok_count}")
    print(f"异常目录数: {len(bad_results)}")
    print("=" * 100)

    if not bad_results:
        print("所有目录下的 fct.txt 行数均满足要求。")
        return

    print("\n不满足条件的目录如下：\n")
    cnt = 1
    for item in bad_results:
        print("-" * 100)
        print(f"配置项 {cnt}: {item['label']}")
        print(f"状态:   {item['status']}")
        print(f"行数:   {item['lines']}")
        print(f"目录:   {item['dir']}")
        print(f"文件:   {item['fct_path']}")
        cnt += 1


def save_results(bad_results: list, output_file: str):
    output_path = Path(output_file)
    cnt = 1
    with output_path.open("w", encoding="utf-8") as f:
        for item in bad_results:
            f.write("-" * 100 + "\n")
            f.write(f"配置项 {cnt}: {item['label']}\n")
            f.write(f"状态:   {item['status']}\n")
            f.write(f"行数:   {item['lines']}\n")
            f.write(f"目录:   {item['dir']}\n")
            f.write(f"文件:   {item['fct_path']}\n")
        cnt += 1

    print(f"\n异常结果已写入: {output_path.resolve()}")


def main():
    parser = argparse.ArgumentParser(
        description="扫描 CONFIG_LIST 中所有目录下 fct.txt 的行数是否满足指定值。"
    )

    parser.add_argument(
        "--config",
        type=str,
        default="None",
        help="包含 CONFIG_LIST 的 Python 配置文件路径，例如 config_paths.py",
    )

    # parser.add_argument(
    #     "--target-lines",
    #     type=int,
    #     default=DEFAULT_TARGET_LINES,
    #     help=f"要求的 fct.txt 行数，默认 {DEFAULT_TARGET_LINES}",
    # )

    parser.add_argument(
        "--fct-name",
        type=str,
        default=DEFAULT_FCT_FILENAME,
        help=f"待检查的文件名，默认 {DEFAULT_FCT_FILENAME}",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="可选：将异常目录输出到指定 txt 文件",
    )

    args = parser.parse_args()

    if args.config != "None":
        config_list = load_config_list(args.config)
    else:
        config_list = CONFIG_LIST

    total_count, ok_count, bad_results, workload_type = check_fct_files(
        config_list=config_list,
        target_lines=0,
        fct_filename=args.fct_name,
    )

    workload_fct_line = 0
    if workload_type == "allreduce":
        print(f"检测到工作负载类型: ALLREDUCE，要求的 fct.txt 行数为 {ALLREDUCE_FCT_LINES}")
        workload_fct_line = ALLREDUCE_FCT_LINES

    elif workload_type == "all2all":
        print(f"检测到工作负载类型: ALLTOALL，要求的 fct.txt 行数为 {ALLTOALL_FCT_LINES}")
        workload_fct_line = ALLTOALL_FCT_LINES
    
    print_results(
        total_count=total_count,
        ok_count=ok_count,
        bad_results=bad_results,
        target_lines=workload_fct_line,
    )

    if args.output is not None:
        save_results(bad_results, args.output)


if __name__ == "__main__":
    main()