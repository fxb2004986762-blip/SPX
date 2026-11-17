import os
import sys

# =========================
# 输出文件配置
# =========================
WRITE_OUTPUT_FILE = "/home/dell/sjw/lb/simulator/analysis_script/configs/result_path.py"

# 是否直接写入文件
WRITE_DIRECTLY = True
# 写入文件中的变量名
WRITE_OUTPUT_VAR_NAME = "CONFIG_LIST"


def scan_directory_and_generate_dict_mode1(base_dir, separator="dcqcn"):
    """
    扫描指定目录下的子目录,并生成字典格式输出
    
    参数:
        base_dir: 要扫描的基础目录路径
        separator: 用于分割目录名称以提取key的分隔符,默认为"dcqcn"
    
    返回:
        包含目录名称和绝对路径的字典
    """
    algo_files = {}
    
    # 检查目录是否存在
    if not os.path.exists(base_dir):
        print(f"错误: 目录不存在: {base_dir}")
        return algo_files
    
    if not os.path.isdir(base_dir):
        print(f"错误: 路径不是目录: {base_dir}")
        return algo_files
    
    print("遍历所有条目...")
    # 遍历基础目录下的所有项
    try:
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            
            # 只处理子目录
            if os.path.isdir(item_path):
                # 定制key

                ## 以拥塞控制算法作为分隔符，将Tag作为Key
                # if f"_{separator}-" in item:
                #     # 分割目录名称,取分隔符前的部分作为key
                #     key = item.split(f"_{separator}-")[0]
                #     # 获取绝对路径
                #     abs_path = os.path.abspath(item_path)
                #     algo_files[key] = abs_path

                ## 以EP并行度作为分隔符，将流量大小作为key
                print(item)
                if f"_{separator}_" in item:
                    msg_size = item.split(f"_{separator}_")[-1].split("M")[0]  # 取分隔符后的第一部分作为key
                    ep_size = separator.split("EP")[-1]  # 取分隔符中的EP并行度
                    key = str(int(float(msg_size) / float(ep_size))) + " M"
                    abs_path = os.path.abspath(item_path)
                    algo_files[key] = abs_path

                else:
                    print(f"警告: 目录名称格式不符合预期,跳过: {item}")
    
    except PermissionError:
        print(f"错误: 没有权限访问目录: {base_dir}")
    except Exception as e:
        print(f"错误: 扫描目录时发生异常: {e}")
    
    return algo_files


def scan_directory_and_generate_dict_mode0(base_dir, separator="dcqcn"):
    """
    扫描指定目录下的子目录,并生成字典格式输出
    
    参数:
        base_dir: 要扫描的基础目录路径
        separator: 用于分割目录名称以提取key的分隔符,默认为"dcqcn"
    
    返回:
        包含目录名称和绝对路径的字典
    """
    algo_files = {}
    
    # 检查目录是否存在
    if not os.path.exists(base_dir):
        print(f"错误: 目录不存在: {base_dir}")
        return algo_files
    
    if not os.path.isdir(base_dir):
        print(f"错误: 路径不是目录: {base_dir}")
        return algo_files
    
    print("遍历所有条目...")
    # 遍历基础目录下的所有项
    try:
        key = 0
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            
            # 只处理子目录
            if os.path.isdir(item_path):
                print(item)
                abs_path = os.path.abspath(item_path)
                algo_files[str(key)] = abs_path
                key += 1

    
    except PermissionError:
        print(f"错误: 没有权限访问目录: {base_dir}")
    except Exception as e:
        print(f"错误: 扫描目录时发生异常: {e}")
    
    return algo_files

def scan_directory_and_generate_dict_mode2(base_dir):
    """
    扫描指定目录下第一层子目录，并对每个第一层子目录下的用例目录按字母排序后生成字典。

    参数:
        base_dir: 要扫描的基础目录路径

    返回:
        嵌套字典:
        {
            "aps-v2": {
                "0": "...",
                "1": "...",
            },
            "rps": {
                "0": "...",
                "1": "...",
            }
        }
    """
    all_case_files = {}

    # 检查目录是否存在
    if not os.path.exists(base_dir):
        print(f"错误: 目录不存在: {base_dir}")
        return all_case_files

    if not os.path.isdir(base_dir):
        print(f"错误: 路径不是目录: {base_dir}")
        return all_case_files

    print("遍历第一层子目录...")

    try:
        # 第一层子目录也按字母排序，保证输出顺序稳定
        for item in sorted(os.listdir(base_dir)):
            item_path = os.path.join(base_dir, item)

            # 只处理第一层子目录
            if os.path.isdir(item_path):
                print(f"\n正在扫描第一层子目录: {item}")

                sub_result = {}
                key = 0

                print("遍历所有条目...")

                # 对每一个第一层子目录内部的用例目录按字母排序
                for sub_item in sorted(os.listdir(item_path)):
                    sub_item_path = os.path.join(item_path, sub_item)

                    # 只处理子目录
                    if os.path.isdir(sub_item_path):
                        print(sub_item)
                        abs_path = os.path.abspath(sub_item_path)
                        sub_result[str(key)] = abs_path
                        key += 1

                all_case_files[item] = sub_result

    except PermissionError:
        print(f"错误: 没有权限访问目录: {base_dir}")
    except Exception as e:
        print(f"错误: 扫描目录时发生异常: {e}")

    return all_case_files

def scan_directory_and_generate_dict_mode3(base_dir, filter_fields):
    """
    扫描指定目录下第一层子目录，并对每个第一层子目录下的用例目录进行字段筛选。

    功能:
        1. 基础扫描逻辑与 mode2 一致；
        2. 支持多个字段筛选，目录名中同时包含所有字段才会被选中；
        3. 通信量大小从每个测试用例目录下的 fct.txt 第一行第五列读取；
        4. 第五列默认单位为 Byte，除以 1024*1024 后得到 MB；
        5. 筛选后的用例目录按照通信量大小排序；
        6. 每个内部字典的 key 使用通信量大小，并拼接单位 MB。

    参数:
        base_dir: 要扫描的基础目录路径
        filter_fields: 字段列表，例如 ["dcqcn", "EP8"]

    返回:
        嵌套字典:
        {
            "aps-v2": {
                "8MB": "...",
                "32MB": "...",
                "64MB": "...",
            },
            "rps": {
                "8MB": "...",
                "32MB": "...",
                "64MB": "...",
            }
        }
    """
    all_case_files = {}

    # 检查目录是否存在
    if not os.path.exists(base_dir):
        print(f"错误: 目录不存在: {base_dir}")
        return all_case_files

    if not os.path.isdir(base_dir):
        print(f"错误: 路径不是目录: {base_dir}")
        return all_case_files

    print("遍历第一层子目录...")
    print(f"筛选字段: {filter_fields}")

    try:
        # 第一层子目录按照字母排序，保证输出稳定
        for item in sorted(os.listdir(base_dir)):
            item_path = os.path.join(base_dir, item)

            # 只处理第一层子目录
            if os.path.isdir(item_path):
                print(f"\n正在扫描第一层子目录: {item}")

                matched_items = []

                print("遍历所有条目...")

                # 扫描当前第一层子目录下的所有用例目录
                for sub_item in sorted(os.listdir(item_path)):
                    sub_item_path = os.path.join(item_path, sub_item)

                    # 只处理子目录
                    if os.path.isdir(sub_item_path):

                        # 多字段筛选：要求目录名同时包含所有字段
                        if all(field in sub_item for field in filter_fields):
                            msg_size_mb = extract_msg_size_from_fct_file(sub_item_path)

                            if msg_size_mb is None:
                                continue

                            matched_items.append((msg_size_mb, sub_item, sub_item_path))

                # 按 fct.txt 中读取到的通信量大小排序
                matched_items.sort(key=lambda x: x[0])

                sub_result = {}

                for msg_size_mb, sub_item, sub_item_path in matched_items:
                    print(sub_item)
                    abs_path = os.path.abspath(sub_item_path)

                    # key 使用通信量大小 + MB
                    key = format_msg_size_key(msg_size_mb)

                    # 如果同一个第一层子目录下出现相同通信量大小，会覆盖已有 key
                    # 这里保留字典结构不变，只给出提示
                    if key in sub_result:
                        print(f"警告: 当前子目录 {item} 中存在重复通信量大小 {key}, 后者将覆盖前者")

                    sub_result[key] = abs_path

                all_case_files[item] = sub_result

    except PermissionError:
        print(f"错误: 没有权限访问目录: {base_dir}")
    except Exception as e:
        print(f"错误: 扫描目录时发生异常: {e}")

    return all_case_files
def natural_sort_key(key):
    """
    自然排序的key函数,将字符串中的数字部分按数值排序
    
    参数:
        key: 要排序的字符串
    
    返回:
        用于排序的元组
    """
    import re
    # 将字符串分割成文本和数字部分
    parts = re.split(r'(\d+)', key)
    # 将数字部分转换为整数,文本部分保持不变
    return [int(part) if part.isdigit() else part for part in parts]

def extract_msg_size_from_dirname(dirname):
    """
    从目录名中提取通信量大小。

    默认认为目录名按照 "_" 分隔后，最后一个字段为通信量大小，例如:
        xxx_EP8_32M  -> 32
        xxx_EP8_32   -> 32
        xxx_EP8_128M -> 128

    返回:
        int 类型通信量大小；如果解析失败，返回 None
    """
    try:
        last_field = dirname.split("_")[-1]
        last_field = last_field.strip()

        # 去掉常见单位
        if last_field.endswith("M") or last_field.endswith("m"):
            last_field = last_field[:-1]

        return int(float(last_field))

    except Exception:
        return None

def extract_msg_size_from_fct_file(case_dir):
    """
    从测试用例目录下的 fct.txt 文件中读取通信量大小。

    默认格式:
        fct.txt 每一行各列使用空格分隔；
        第一行第 5 列为流量大小，单位为 Byte。

    处理方式:
        msg_size_MB = 第 5 列 / (1024 * 1024)

    参数:
        case_dir: 测试用例目录路径

    返回:
        float 类型通信量大小，单位 MB；如果解析失败，返回 None
    """
    fct_file = os.path.join(case_dir, "fct.txt")

    if not os.path.exists(fct_file):
        print(f"警告: fct.txt 不存在,跳过: {case_dir}")
        return None

    if not os.path.isfile(fct_file):
        print(f"警告: fct.txt 不是普通文件,跳过: {fct_file}")
        return None

    try:
        with open(fct_file, "r") as f:
            first_line = f.readline().strip()

            if not first_line:
                print(f"警告: fct.txt 第一行为空,跳过: {fct_file}")
                return None

            fields = first_line.split()

            if len(fields) < 5:
                print(f"警告: fct.txt 第一行字段数量不足5列,跳过: {fct_file}")
                return None

            msg_size_bytes = float(fields[4])
            msg_size_mb = msg_size_bytes / (1024 * 1024)

            return msg_size_mb

    except Exception as e:
        print(f"警告: 读取 fct.txt 失败,跳过: {fct_file}, 错误: {e}")
        return None

def format_msg_size_key(msg_size_mb):
    """
    将通信量大小格式化为字典 key。

    例如:
        32.0  -> "32MB"
        32.5  -> "32.5MB"
    """
    if msg_size_mb == int(msg_size_mb):
        return f"{int(msg_size_mb)}MB"
    else:
        return f"{msg_size_mb:g}MB"

# def format_output(algo_files):
#     """
#     格式化输出字典为Python代码格式
    
#     参数:
#         algo_files: 包含目录信息的字典
#     """
#     # 按key自然排序(数字部分按数值排序)
#     sorted_items = sorted(algo_files.items(), key=lambda x: natural_sort_key(x[0]))
    
#     print("algo_files = {")
#     for i, (key, path) in enumerate(sorted_items):
#         if i < len(sorted_items) - 1:
#             print(f'    "{key}": "{path}",')
#         else:
#             print(f'    "{key}": "{path}",\n')
#     print("}")

def format_output(algo_files):
    """
    格式化输出字典为Python代码格式
    
    参数:
        algo_files: 包含目录信息的字典
    """
    output_str = build_output_string(algo_files, var_name="algo_files")
    print(output_str)

def format_nested_output(all_case_files):
    """
    格式化输出嵌套字典为Python代码格式

    参数:
        all_case_files: 第一层key为算法/用例目录名称，第二层为mode0生成的目录字典
    """
    sorted_outer_items = sorted(all_case_files.items(), key=lambda x: natural_sort_key(x[0]))

    print("algo_files = {")
    for outer_key, inner_dict in sorted_outer_items:
        print(f'    "{outer_key}": {{')

        sorted_inner_items = sorted(inner_dict.items(), key=lambda x: natural_sort_key(x[0]))

        for key, path in sorted_inner_items:
            print(f'        "{key}": "{path}",')

        print("    },")
    print("}")

def build_output_string(algo_files, var_name="algo_files"):
    """
    将普通字典转换为 Python 代码字符串
    """
    sorted_items = sorted(algo_files.items(), key=lambda x: natural_sort_key(x[0]))

    lines = []
    lines.append(f"{var_name} = {{")

    for key, path in sorted_items:
        lines.append(f'    "{key}": "{path}",')

    lines.append("}")
    lines.append("")

    return "\n".join(lines)


def build_nested_output_string(all_case_files, var_name="algo_files"):
    """
    将嵌套字典转换为 Python 代码字符串
    """
    sorted_outer_items = sorted(
        all_case_files.items(),
        key=lambda x: natural_sort_key(x[0])
    )

    lines = []
    lines.append(f"{var_name} = {{")

    for outer_key, inner_dict in sorted_outer_items:
        lines.append(f'    "{outer_key}": {{')

        sorted_inner_items = sorted(
            inner_dict.items(),
            key=lambda x: natural_sort_key(x[0])
        )

        for key, path in sorted_inner_items:
            lines.append(f'        "{key}": "{path}",')

        lines.append("    },")

    lines.append("}")
    lines.append("")

    return "\n".join(lines)

def write_output_to_file(output_str, output_file=WRITE_OUTPUT_FILE):
    """
    将生成的字典字符串写入指定文件。

    参数:
        output_str: 要写入的字符串内容
        output_file: 输出文件路径
    """
    try:
        output_dir = os.path.dirname(output_file)

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_file, "w") as f:
            f.write(output_str)

        print(f"\n已写入文件: {output_file}")

    except Exception as e:
        print(f"\n错误: 写入文件失败: {output_file}")
        print(f"错误信息: {e}")

def ask_and_write_output(output_str):
    """
    询问用户是否将结果写入文件。
    """
    if WRITE_DIRECTLY:
        write_output_to_file(output_str)
        return
    else:
        write_choice = input(f"\n是否直接写入文件 {WRITE_OUTPUT_FILE}? (y/n): ").strip().lower()

        if write_choice in ["n", "N", "No", "NO", "no"]:
            print("未写入文件")
        else:
            write_output_to_file(output_str)
    

def main():
    # 从命令行参数获取扫描目录的模式
    if len(sys.argv) > 1:
        scan_mode = sys.argv[1]
    else:
        # 如果没有提供命令行参数,提示用户输入
        scan_mode = input("请输入扫描模式(0:扫描目录, 1:扫描算法, 2:扫描目录并获取所有子目录的用例, 3:支持字段筛选的子目录扫描): ").strip()
    
    if (scan_mode == "0"):
        while True:
            # 从命令行参数获取目录路径
            if len(sys.argv) > 1:
                target_dir = sys.argv[1]
            else:
                # 如果没有提供命令行参数,提示用户输入
                target_dir = input("请输入要扫描的目录路径: ").strip()
            
            print(f"\n正在扫描目录: {target_dir}\n")
            # 扫描目录
            result = scan_directory_and_generate_dict_mode0(target_dir)
            
            # 输出结果
            if result:
                print(f"\n找到 {len(result)} 个符合条件的子目录:\n")
                format_output(result)

                output_str = build_output_string(result, var_name=WRITE_OUTPUT_VAR_NAME)
                ask_and_write_output(output_str)
            else:
                print("\n未找到符合条件的子目录")

    elif (scan_mode == "1"):
        while True:
            # 从命令行参数获取目录路径
            if len(sys.argv) > 1:
                target_dir = sys.argv[1]
            else:
                # 如果没有提供命令行参数,提示用户输入
                target_dir = input("请输入要扫描的目录路径: ").strip()
            
            # 可选:自定义分隔符
            # separator = "dcqcn"
            separator = "EP8"
            if len(sys.argv) > 2:
                separator = sys.argv[2]
            
            print(f"\n正在扫描目录: {target_dir}")
            print(f"使用分隔符: {separator}\n")
            
            # 扫描目录
            result = scan_directory_and_generate_dict_mode1(target_dir, separator)
            
            # 输出结果
            if result:
                print(f"\n找到 {len(result)} 个符合条件的子目录:\n")
                format_output(result)

                output_str = build_output_string(result, var_name=WRITE_OUTPUT_VAR_NAME)
                ask_and_write_output(output_str)
            else:
                print("\n未找到符合条件的子目录")

    elif (scan_mode == "2"):
        while True:
            # 从命令行参数获取目录路径
            if len(sys.argv) > 1:
                target_dir = sys.argv[1]
            else:
                # 如果没有提供命令行参数,提示用户输入
                target_dir = input("请输入要扫描的目录路径: ").strip()

            print(f"\n正在扫描目录: {target_dir}")
            print("扫描模式: 2:扫描目录并获取所有子目录的用例\n")

            # 扫描目录
            result = scan_directory_and_generate_dict_mode2(target_dir)

            # 输出结果
            if result:
                total_cases = sum(len(v) for v in result.values())
                print(f"\n找到 {len(result)} 个第一层子目录，共 {total_cases} 个用例子目录:\n")
                format_nested_output(result)

                output_str = build_nested_output_string(result, var_name=WRITE_OUTPUT_VAR_NAME)
                ask_and_write_output(output_str)
            else:
                print("\n未找到符合条件的子目录")

    elif (scan_mode == "3"):
        while True:
            # 从命令行参数获取目录路径
            if len(sys.argv) > 1:
                target_dir = sys.argv[1]
            else:
                # 如果没有提供命令行参数,提示用户输入
                target_dir = input("请输入要扫描的目录路径: ").strip()

            # 输入筛选字段，多个字段用空格分隔
            if len(sys.argv) > 2:
                filter_fields = sys.argv[2:]
            else:
                filter_input = input("请输入筛选字段，多个字段用空格分隔: ").strip()
                filter_fields = filter_input.split()

            print(f"\n正在扫描目录: {target_dir}")
            print("扫描模式: 3:支持字段筛选的子目录扫描")
            print(f"筛选字段: {filter_fields}\n")

            # 扫描目录
            result = scan_directory_and_generate_dict_mode3(target_dir, filter_fields)

            # 输出结果
            if result:
                total_cases = sum(len(v) for v in result.values())
                print(f"\n找到 {len(result)} 个第一层子目录，共 {total_cases} 个符合条件的用例子目录:\n")
                format_nested_output(result)

                output_str = build_nested_output_string(result, var_name=WRITE_OUTPUT_VAR_NAME)
                ask_and_write_output(output_str)
            else:
                print("\n未找到符合条件的子目录")              


if __name__ == "__main__":
    main()