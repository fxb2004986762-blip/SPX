import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import re


topo2bdp = {
    # "leaf_spine_128_100G_OS2": 104000,  # 2-tier
    "fattree": 306000, # 3-tier -> core 400G
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
                        cc_mode = parsed_line[0].split('_')[1].lower() #cc_modes[int(parsed_line[2])]
                    else:
                        lb_mode = parsed_line[0].split('_')[0].lower() #lb_modes[int(parsed_line[3])]
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
                    config.append([topo, netload, cc_mode])
    return new_data_dir, fct_files, LBs, config

def parse_file(filename):
    # """读取文件并返回小流、大流 slowdown 列表"""
    flows = []
    small_flows = []
    large_flows = []
    with open(filename, "r") as f:
        for line in f:
            if not line.strip():
                continue
            parts = line.split()
            size = int(parts[4])          # 第5列 (0-based index 4)
            fct = float(parts[6])         # 第7列 (index 6)
            standalone = float(parts[7])  # 第8列 (index 7)
            slowdown = fct / standalone if standalone >= 0 else None
            if slowdown is None:
                continue
            # if size <= 100*1024:  # 小流
            #     small_flows.append(slowdown)
            # else:  # 大流
            #     large_flows.append(slowdown)
            flows.append(slowdown)
            
    # return np.mean(small_flows) if small_flows else 0, \
    #        np.mean(large_flows) if large_flows else 0, \
    #        np.percentile(small_flows, 99) if small_flows else 0, \
    #        np.percentile(large_flows, 99) if large_flows else 0
    return np.mean(flows) if flows else 0, \
           np.percentile(flows, 99) if flows else 0
            


def plot_results(data_files, LBs, fig_filenames):
    strategies = LBs
    # small = []
    # large = []
    # small_avg = []
    # large_avg = []
    # small_p99 = []
    # large_p99 = []
    flow_avg = []
    flow_p99 = []
    flow = []

    for f in data_files:
        # s_avg, l_avg, s_p99, l_p99 = parse_file(f)
        avg, p99 = parse_file(f)
        # small_avg.append(s_avg)
        # large_avg.append(l_avg)
        # small_p99.append(s_p99)
        # large_p99.append(l_p99)
        flow_avg.append(avg)
        flow_p99.append(p99)
    flow.append(flow_avg)
    flow.append(flow_p99)
    # small.append(small_avg)
    # small.append(small_p99)
    # large.append(large_avg)
    # large.append(large_p99)
    type = 0 # 0: avg, 1: p99
    flow_size = get_flow_size(data_files[0])

    type_name = ["Average", "P99"]
    for fig_filename in fig_filenames:
        n_strategies = len(strategies)
        # x = np.arange(2)  # 两类流量：小流、大流
        width = 0.15      # 每个柱子宽度
        group_gap = 0.1   # 组间间距（调小/调大效果不同）
        x = np.arange(1) * (n_strategies * width + group_gap)


        fig, ax = plt.subplots(figsize=(8, 6))
        ax.grid(which='minor', alpha=0.2, zorder=0)
        ax.grid(which='major', alpha=0.5, zorder=0)

        print(strategies)
        print(flow[type])
        # print(large[type])
        
        for i, strategy in enumerate(strategies):
            offsets = x + i * width
            values = [flow[type][i]]
            bars = ax.bar(offsets, values, width, label=strategy, 
              zorder=3, hatch=hatches[i % len(hatches)])

            # === 在柱状图顶部添加数值，保留两位小数 ===
            for bar in bars:
                height = bar.get_height()
                color = bar.get_facecolor()
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height,
                    f"{height:.2f}",
                    ha='center', va='bottom',
                    fontsize=10,
                    fontweight='bold',
                    color=color
                )
        
        xticklablename = "Ring-All-Reduce ({}MB per flow)".format(flow_size)
        ax.set_xticks(x + width*(len(strategies)-1)/2)
        ax.set_xticklabels([xticklablename])
        plot_name = type_name[type] + " FCT Slowdown"
        ax.set_ylabel(plot_name, fontsize=15)
        ax.set_xlabel("Flow Size", fontsize=15)

        # ax.set_title("Average FCT Slowdown by Flow Size and Strategy")
        ax.legend()


        plt.tight_layout()

        print(fig_filename)
        plt.savefig(fig_filename, transparent=False, bbox_inches='tight')
        plt.close()
        type = type + 1

if __name__ == "__main__":

    data_files = []
    LBs = []
    config = []
    file_dir = getFilePath()
    fig_dir = file_dir + "/../output/1all_figures"
    if not os.path.exists(fig_dir):
        os.makedirs(fig_dir)
    data_dir = file_dir + "/../output"
    # data_dir = file_dir + "/../output"
    history_filename = file_dir + "/../output/lb_compare.history"

    data_dir, data_files, LBs, config = get_config_from_history(history_filename, data_dir)
    if len(config) == 0:
        print("No matched result")
        sys.exit(0)
    fig_filename_avg = fig_dir + "/{}.pdf".format("AVG_FCT:[{}]+[{}]+[CC:{}]".format(config[0][0], config[0][1], config[0][2]))
    fig_filename_p99 = fig_dir + "/{}.pdf".format("P99_FCT:[{}]+[{}]+[CC:{}]".format(config[0][0], config[0][1], config[0][2]))
    fig_filename = [fig_filename_avg, fig_filename_p99]

    plot_results(data_files, LBs, fig_filename)

    
