import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import re


topo2bdp = {
    # "leaf_spine_128_100G_OS2": 104000,  # 2-tier
    "fattree": 306000, # 3-tier -> core 400G
    "SpectrumX": 204000, # 2-tier -> agg 400G
    "AlibabaHPN": 103000, # 
}

hatches = ['/', '\\', '-', '+', 'x', '*', 'o', '.']

def getFilePath():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    print("File directory: {}".format(dir_path))
    return dir_path

def get_flow_size(filename):
    with open(filename, "r") as f:
        line = f.readline()
        flow_size = float(line.split()[4])
    # 默认B，转换为MB，保留1位小数
    return round(flow_size / (1024 * 1024), 1)

def get_config_from_history(history_filename, data_dir):
    fct_files = []
    LBs = []
    ooo_config = []
    config = []
    configId = []
    new_data_dir = ""
    with open(history_filename, "r") as f:
        for line in f.readlines():
            if line == "\n":
                break
            for topo in topo2bdp.keys():
                if topo in line:
                    parsed_line = re.sub(r'\[.*?\]', '', line).strip() # remove [xxxxxx] in the line
                    parsed_line = parsed_line.split('\t')
                    config_id = parsed_line[-1]

                    if config_id in configId:
                        continue
                    configId.append(config_id)

                    if (len(parsed_line[0].split('_')) >= 2):
                        lb_mode = parsed_line[0].split('_')[0].lower() #lb_modes[int(parsed_line[3])]
                        ooo_buffer_size = parsed_line[0].split('_')[0].split('-')[-1].strip('b')
                        cc_mode = parsed_line[0].split('_')[1].lower() #cc_modes[int(parsed_line[2])]
                    else:
                        lb_mode = parsed_line[0].split('_')[0].lower() #lb_modes[int(parsed_line[3])]
                        ooo_buffer_size = parsed_line[0].split('_')[0].split('-')[-1].strip('b')
                        cc_mode = "None"

                    netload = parsed_line[1]
                    topo = parsed_line[2]
                    # key = (topo, netload, cc_mode)

                    # files.append(data_dir + "/" + topo + "-" + netload + "/" + config_id + "/fct.txt")
                    if os.path.exists(data_dir + "/" + config_id):
                        # print("found path {}".format(data_dir + "/" + config_id))
                        fct_files.append(data_dir + "/" + config_id + "/fct.txt")
                        new_data_dir = data_dir
                    elif os.path.exists(data_dir + "/" + topo + "-" + netload + "/" + config_id):
                        # print("found path {}".format(data_dir + "/" + topo + "-" + netload + "/" + config_id))
                        fct_files.append(data_dir + "/" + topo + "-" + netload + "/" + config_id + "/fct.txt")
                        new_data_dir = data_dir + "/" + topo + "-" + netload
                    else:
                        print("config_id {} not found".format(config_id))
                        continue

                    LBs.append(lb_mode)
                    ooo_config.append(ooo_buffer_size)
                    config.append([topo, netload, cc_mode])
    return new_data_dir, fct_files, LBs, ooo_config, config

def parse_file(filename, type):
    # """读取文件并返回小流、大流 slowdown 列表"""
    flows = []
    with open(filename, "r") as f:
        for line in f:
            if not line.strip():
                continue
            parts = line.split()
            fct = float(parts[6])         # 第7列 (index 6)
            standalone = float(parts[7])  # 第8列 (index 7)
            slowdown = fct / standalone if standalone >= 0 else None
            if slowdown is None:
                continue

            flows.append(slowdown)

    if type == "avg":
        return np.mean(flows) if flows else 0
    elif type == "p99":
        return np.percentile(flows, 99) if flows else 0


def plot_results(history_filename, data_dir, fig_filename, type):
    # data[algo][buffer] = fct
    data = {}

    # 从 history 文件中获取配置
    configId = []
    with open(history_filename, "r") as f:
        for line in f.readlines():
            if line == "\n":
                break
            parsed_line = re.sub(r'\[.*?\]', '', line).strip() # remove [xxxxxx] in the line
            parsed_line = parsed_line.split('\t')
            config_id = parsed_line[-1]

            if config_id in configId:
                continue
            configId.append(config_id)

            lb_mode = parsed_line[0].split('_')[0].lower() #lb_modes[int(parsed_line[3])]
            ooo_buffer_size = parsed_line[0].split('_')[0].split('-')[-1].strip('b')

            fct_file = data_dir + "/" + config_id + "/fct.txt"
            
            # 获取算法、缓冲区大小、FCT
            algo = lb_mode.rsplit('-', 1)[0]
            buffer_size = ooo_buffer_size
            fct_slowdown = parse_file(fct_file, type)

            data.setdefault(algo, {})[int(buffer_size)] = fct_slowdown

    # 维度整理
    algorithms = sorted(data.keys())
    buffers = sorted({c for a in data for c in data[a]})

    # 给每个算法固定一种颜色
    color_map = {
        algo: plt.cm.tab10(i)
        for i, algo in enumerate(algorithms)
    }

    x = np.arange(len(buffers))
    num_algos = len(algorithms)
    bar_width = 0.8 / num_algos

    plt.figure(figsize=(8, 5))

    for i, algo in enumerate(algorithms):
        # 按缓存区大小顺序取 FCT
        fcts = [
            data[algo].get(b, np.nan)  # 若缺失，用 NaN 占位
            for b in buffers
        ]

        bars = plt.bar(
        x + i * bar_width,        # 控制并排位置
        fcts,
        width=bar_width,
        color=color_map[algo],    # 同一算法同色
        label=algo,                # legend 只显示算法
        hatch=hatches[i % len(hatches)])

        for bar in bars:
                height = bar.get_height()
                color = bar.get_facecolor()
                plt.text(
                    bar.get_x() + bar.get_width() / 2,
                    height,
                    f"{height:.2f}",
                    ha='center', va='bottom',
                    fontsize=10,
                    fontweight='bold',
                    color=color
                )

    # 坐标轴
    plt.xticks(
        x + bar_width * (num_algos - 1) / 2,
        buffers
    )
    plt.xlabel("Buffer Window Size")
    if type == "avg":
        plt.ylabel("FCT Slowdown (Avg)")
    elif type == "p99":
        plt.ylabel("FCT Slowdown (P99)")

    # 图例：只区分算法
    plt.legend(title="Algorithm")

    plt.tight_layout()
    plt.show()
    plt.savefig(fig_filename)

if __name__ == "__main__":

    data_files = []
    LBs = []
    config = []
    file_dir = getFilePath()
    fig_dir = file_dir + "/../output/1all_figures"
    if not os.path.exists(fig_dir):
        os.makedirs(fig_dir)
    data_dir = file_dir + "/../output/5ooo-class"
    # data_dir = file_dir + "/../output"
    history_filename = file_dir + "/../output/fct_ooo_compare.history"

    data_dir, fct_files, LBs, ooo_config, config = get_config_from_history(history_filename, data_dir)
    if len(config) == 0:
        print("No matched result")
        sys.exit(0)
    fig_filename_avg = fig_dir + "/{}.pdf".format("AVG_FCT(ooo-fct):[{}]+[{}]+[CC:{}]".format(config[0][0], config[0][1], config[0][2]))
    fig_filename_p99 = fig_dir + "/{}.pdf".format("P99_FCT(ooo-fct):[{}]+[{}]+[CC:{}]".format(config[0][0], config[0][1], config[0][2]))

    plot_results(history_filename, data_dir, fig_filename_avg, "avg")
    plot_results(history_filename, data_dir, fig_filename_p99, "p99")