#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import shlex
import subprocess
from pathlib import Path


TASK_FILE = "/home/dcn1/fxb/simulator/output/work.list"          # 每行一条完整命令
MAX_PARALLEL =  4               # 最大并发数
POLL_INTERVAL = 5                # 轮询间隔（秒）

# check finish
flow_cnt = 0 # alltoall, allreduce
FINISH_TYPE = "flag"  # "flag" or "line_count"
FINISH_FLAG = "Simulator finished"

ALLTOALL_NAME = "all2all"
FINISH_FLOW_ALLTOALL = 896 # 7168 (1024GPU), 896 (128GPU)

ALLREDUCE_NAME = "allreduce"
FINISH_FLOW_ALLREDUCE = 6144
SCHEDULER_LOG = "/home/dcn1/fxb/simulator/output/scheduler_status.log"

def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(SCHEDULER_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_tasks(task_file: str):
    tasks = []
    with open(task_file, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            cmd = line.strip()
            if not cmd or cmd.startswith("#"):
                continue
            tasks.append({
                "task_id": len(tasks) + 1,
                "line_no": line_no,
                "cmd": cmd,
            })
    return tasks


def extract_log_path(cmd: str):
    """
    从命令里提取 > 后面的日志路径
    例如：
      xxx > /path/to/output.log
    返回：
      /path/to/output.log
    """
    m = re.search(r'>\s*(\S+)', cmd)
    if m:
        return m.group(1)
    return None

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

def check_finish(case_path: str):
    if FINISH_TYPE == "line_count":
        fct_path = Path(case_path) / "fct.txt"
        if not fct_path.exists():
            return False, f"fct.txt not found in {case_path}"
        
        if ALLTOALL_NAME in case_path.lower():
            flow_cnt = FINISH_FLOW_ALLTOALL
        elif ALLREDUCE_NAME in case_path.lower():
            flow_cnt = FINISH_FLOW_ALLREDUCE
        else:
            flow_cnt = 0
            return False

        line_count = count_lines_fast(fct_path)
        if line_count < flow_cnt:
            return False

        return True
    else:
        log_path = Path(case_path) / "output.log"
        if not log_path.exists():
            return False, f"output.log not found in {case_path}"

        return check_finish_flag(str(log_path), FINISH_FLAG)


def check_finish_flag(log_path: str, finish_flag: str):
    if not log_path or not os.path.exists(log_path):
        return False
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            return finish_flag in f.read()
    except Exception:
        return False


def start_task(task: dict):
    cmd = task["cmd"]
    log_path = extract_log_path(cmd)

    if log_path is None:
        log(f"[WARN ] task={task['task_id']} 未解析到日志路径，后续无法检查完成标志")

    task["log_path"] = log_path
    task["start_time"] = time.time()

    # 用 shell=True 直接执行整条命令，因为命令中自带 >
    proc = subprocess.Popen(cmd, shell=True)
    task["proc"] = proc

    log(f"[START] task={task['task_id']} line={task['line_no']}")
    log(f"        cmd={cmd}")
    if log_path:
        log(f"        output_log={log_path}")

    return task


def finalize_task(task: dict):
    proc = task["proc"]
    ret = proc.poll()
    if ret is None:
        return None

    elapsed = time.time() - task["start_time"]
    case_path = str(Path(task.get("log_path")).parent)
    finish_ok = check_finish(case_path)
    success = (ret == 0 and finish_ok)

    task["exit_code"] = ret
    task["elapsed"] = elapsed
    task["finish_flag_found"] = finish_ok
    task["success"] = success

    log(
        f"[DONE ] task={task['task_id']} exit_code={ret} "
        f"flag_found={finish_ok} elapsed={elapsed:.1f}s "
        f"result={'SUCCESS' if success else 'FAIL'}"
    )
    if not success:
        if (FINISH_TYPE == "line_count"):
            log(f"FAIL_DETAILS: expected fct.txt lines < {flow_cnt}")
        elif (FINISH_TYPE == "flag"):
            log(f"FAIL_DETAILS: finish_flag={FINISH_FLAG} not found in log")

    return task


def main():
    # 清空旧的调度日志
    Path(SCHEDULER_LOG).write_text("", encoding="utf-8")

    if not os.path.exists(TASK_FILE):
        log(f"[ERROR] 任务文件不存在: {TASK_FILE}")
        return 1

    pending_tasks = load_tasks(TASK_FILE)
    total_tasks = len(pending_tasks)

    if total_tasks == 0:
        log("[INFO ] 任务文件为空，没有可执行任务")
        return 0

    log(f"[INFO ] 从 {TASK_FILE} 加载任务数: {total_tasks}")
    log(f"[INFO ] 最大并发数: {MAX_PARALLEL}")

    running_tasks = []
    finished_tasks = []

    while pending_tasks or running_tasks:
        # 补足空闲槽位
        while pending_tasks and len(running_tasks) < MAX_PARALLEL:
            task = pending_tasks.pop(0)
            start_task(task)
            running_tasks.append(task)

        # 检查运行中的任务
        new_running = []
        for task in running_tasks:
            result = finalize_task(task)
            if result is None:
                new_running.append(task)
            else:
                finished_tasks.append(result)

        running_tasks = new_running

        log(
            f"[STAT ] pending={len(pending_tasks)} "
            f"running={len(running_tasks)} "
            f"finished={len(finished_tasks)}/{total_tasks}"
        )

        if pending_tasks or running_tasks:
            time.sleep(POLL_INTERVAL)

    # 汇总
    success_count = sum(1 for t in finished_tasks if t["success"])
    fail_count = total_tasks - success_count

    log("========== SUMMARY ==========")
    log(f"Total   : {total_tasks}")
    log(f"Success : {success_count}")
    log(f"Fail    : {fail_count}")

    summary_msg = f"All tasks completed: {success_count} success, {fail_count} fail"
    subprocess.run(["python3", "/home/dcn1/fxb/simulator/run_script/notify.py", "--path", summary_msg])

    if fail_count > 0:
        log("Failed tasks:")
        for task in finished_tasks:
            if not task["success"]:
                log(
                    f"  - task={task['task_id']} "
                    f"line={task['line_no']} "
                    f"exit_code={task['exit_code']} "
                    f"flag_found={task['finish_flag_found']} "
                    f"log={task.get('log_path')}"
                )

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())