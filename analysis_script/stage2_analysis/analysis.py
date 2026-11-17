import os
from typing import List
import subprocess
from typing import Optional
import re
import numpy as np

def get_child_dir_name(root_dir: str) -> List[str]:
    """
    扫描给定目录，返回其下所有子文件夹名称

    参数:
        root_dir (str): 实验结果的根目录路径

    返回:
        List[str]: 子文件夹名称列表（不包含路径）

    异常:
        FileNotFoundError: 当 root_dir 不存在
        NotADirectoryError: 当 root_dir 不是目录
    """
    # 校验路径是否存在
    if not os.path.exists(root_dir):
        raise FileNotFoundError(f"Directory does not exist: {root_dir}")

    # 校验是否为目录
    if not os.path.isdir(root_dir):
        raise NotADirectoryError(f"Path is not a directory: {root_dir}")

    # 扫描子目录
    case_list = []
    for entry in os.scandir(root_dir):
        if entry.is_dir():
            case_list.append(entry.name)

    # 按名称排序，保证结果可复现
    case_list = sorted(case_list, key=lambda s: tuple(int(x) for x in re.findall(r"\d+", s)))

    return case_list

def run_command_and_log(
    work_dir: str,
    command: str,
    output_file: str,
    shell: bool = True
) -> int:
    """
    在指定目录下执行 Linux 命令，并将标准输出和错误输出
    同时打印到终端和写入文件

    参数:
        work_dir (str): 命令执行的工作目录
        command (str): 要执行的 Linux 命令
        output_file (str): 保存命令输出的文件路径
        shell (bool): 是否通过 shell 执行命令（默认 True）

    返回:
        int: 命令的返回码（return code）

    异常:
        FileNotFoundError: work_dir 不存在
        NotADirectoryError: work_dir 不是目录
    """
    # 目录校验
    if not os.path.exists(work_dir):
        raise FileNotFoundError(f"Working directory does not exist: {work_dir}")

    if not os.path.isdir(work_dir):
        raise NotADirectoryError(f"Path is not a directory: {work_dir}")

    # 确保输出文件所在目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # 打开输出文件
    with open(output_file, "w", encoding="utf-8") as f:
        # 启动子进程
        process = subprocess.Popen(
            command,
            cwd=work_dir,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # 实时读取并输出
        for line in process.stdout:
            print(line, end="")   # 打印到终端
            f.write(line)         # 写入文件

        process.stdout.close()
        return_code = process.wait()

    return return_code

# 在指定目录下执行数据处理逻辑，并记录输出结果
## 获取 JCT
def get_jct(filename):
    """
        获取 JCT 单位 ms
    """

    fct_file = os.path.join(filename, "fct.txt")
    with open(fct_file, "r") as f:
        job_start_time = 0
        job_end_time = 0
        # 读取第一行和最后一行
        for line in f:
            if not line.strip():
                continue
            parts = line.split()
            start_time = float(parts[5])  # 第5列 flow 开始时间
            end_time = float(parts[5]) + float(parts[6])    # 第5列 + 第6列 flow 结束时间
            if job_start_time == 0 or start_time < job_start_time:
                job_start_time = start_time
            if end_time > job_end_time:
                job_end_time = end_time
    # 默认单位纳秒，转换为毫秒，保留3位小数

    return (job_end_time - job_start_time) / 1e6

## 获取 FCT
def get_fct(filename):
    # """读取文件并返回小流、大流 slowdown 列表"""

    fct_file = os.path.join(filename, "fct.txt")
    flows = []
    small_flows = []
    large_flows = []
    with open(fct_file, "r") as f:
        for line in f:
            if not line.strip():
                continue
            parts = line.split()
            size = int(parts[4])          # 第5列 (0-based index 4)
            fct = float(parts[6])         # 第7列 (index 6)
            standalone = float(parts[7])  # 第8列 (index 7)
            flow_type = int(parts[8])
            slowdown = fct / standalone if standalone >= 0 else None
            if slowdown is None:
                continue

            # filter ECMP flow
            if flow_type == 0:
                continue

            flows.append(slowdown)
            
    # return np.mean(small_flows) if small_flows else 0, \
    #        np.mean(large_flows) if large_flows else 0, \
    #        np.percentile(small_flows, 99) if small_flows else 0, \
    #        np.percentile(large_flows, 99) if large_flows else 0
    return np.mean(flows) if flows else 0

def traverse_class_with_handler(test_class_file: str, log_file: str = None, handlers=None) -> None:
    """
    输出指定文件下各个测试用例的 JCT，用于粗略判断
    """
    config_list = get_child_dir_name(test_class_file)
    if log_file is None:
        log_file = "/home/dcn1/fxb/simulator/output/tmp.log"
    with open(log_file, "w") as log_f:
        for config in config_list:
            config_path = os.path.join(test_class_file, config)
            case_list = get_child_dir_name(config_path)
            for case in case_list:
                case_path = os.path.join(config_path, case)
                print(f"\nConfig: {config}, Case: {case}")
                log_f.write(f"\nConfig: {config}, Case: {case}\n")
                for handler in handlers:
                    if handler.__name__ == "get_jct":
                        result = str(round(handler(case_path),3))
                        print(f"{handler.__name__}(ms): " + result + "")
                        log_f.write(f"{handler.__name__}(ms): " + result + "\n")
                    elif handler.__name__ == "get_fct":
                        result = str(round(handler(case_path),3))
                        print(f"{handler.__name__}: " + result)    
                        log_f.write(f"{handler.__name__}: " + result + "\n")    
                log_f.flush()    
        log_f.close()



if __name__ == "__main__":
    
    test_class_file = "/home/dcn1/fxb/simulator/output/7int-mix-class"
    tmp_log_file = "/home/dcn1/fxb/simulator/output/tmp.log"

    handler_list = [get_jct, get_fct]
    traverse_class_with_handler(test_class_file, tmp_log_file, handlers=handler_list)