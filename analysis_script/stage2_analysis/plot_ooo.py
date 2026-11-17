import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import re
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "axes.linewidth": 1.2,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

topo2bdp = {
    # "leaf_spine_128_100G_OS2": 104000,  # 2-tier
    "fattree": 306000, # 3-tier -> core 400G
    "SpectrumX": 204000, # 2-tier -> agg 400G
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
    datafiles = []
    LBs = []
    config = []
    configId = []
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
                        cc_mode = parsed_line[0].split('_')[1].lower() #cc_modes[int(parsed_line[2])]
                    else:
                        lb_mode = parsed_line[0].split('_')[0].lower() #lb_modes[int(parsed_line[3])]
                        cc_mode = "None"

                    netload = parsed_line[1]
                    topo = parsed_line[2]
                    # key = (topo, netload, cc_mode)

                    datafiles.append(data_dir + "/"  + config_id)
                    LBs.append(lb_mode)
                    config.append([topo, netload, cc_mode])
    # print(files, "\n",LBs, "\n", config)
    return datafiles, LBs, config

def read_ooo_buffer(buffer_file):
    """
    读取 ooo_buffer.txt
    返回：list of (time_in_us, buffer)
    """
    time_list = []
    buffer_list = []

    with open(buffer_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 6:
                continue

            time_ns = float(parts[0])
            buffer = int(parts[5])

            if buffer == 0:
                # 忽略为 0 的数据
                continue

            time_us = time_ns / 1000.0
            time_list.append(time_us)
            buffer_list.append(buffer)

    return np.array(time_list), np.array(buffer_list)

def aggregate_peak_by_time(time_array, buf_array, bin_us=5):
    """
    将时间轴分 bin，计算每个时间段内的 buffer 最大值（峰值）
    """
    if len(time_array) == 0:
        return None, None

    min_t, max_t = time_array.min(), time_array.max()
    bins = np.arange(min_t, max_t + bin_us, bin_us)
    digitized = np.digitize(time_array, bins)

    peak_buf = []
    bin_centers = []

    for i in range(1, len(bins)):
        vals = buf_array[digitized == i]
        if len(vals) > 0:
            peak_buf.append(vals.max())  # 峰值（最大值）
            bin_centers.append((bins[i - 1] + bins[i]) / 2)

    return np.array(bin_centers), np.array(peak_buf)

def read_sim_config(simConfig_file):
    config = {}
    with open(simConfig_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                key = parts[0]
                value = parts[1:]
                config[key] = value
    return config

def get_peak_ooo_size(datafile):
    """ 获取测试用例的 Peak OOO size, 并提取配置中指定流量的乱序情况 -> src_ooo_buffer.txt.
        Returns:
            max_ooo_size: peak OOO size in all flows
    """
    sim_config = read_sim_config(datafile + "/SimAI.conf")
    src = sim_config["APS_SELECTED_TRACED_NODE"][0]
    ooo_buffer_file = datafile + "/ooo_buffer.txt"
    select_flow_file = datafile + "/src" + src + "_ooo_buffer.txt"
    summary_file = datafile + "/ooo_summary.txt"
    max_ooo_size = 0
    # 如果summary_file存在，则直接返回 summary_file
    if os.path.exists(summary_file):
        with open(summary_file, 'r') as f:
            for line in f:
                if "MAX_OOO_SIZE" in line:
                    max_ooo_size = int(line.strip().split()[1])
        return max_ooo_size
    else:
        with open(ooo_buffer_file, 'r') as f, open(select_flow_file, 'w') as out_f:
            for line in f:
                parts = line.strip().split()
                if int(parts[-1]) > max_ooo_size:
                    max_ooo_size = int(parts[-1])

                if parts[1] == src and parts[3] == "100" and parts[4] == "10000":
                    dst = parts[2]
                    out_f.write(line)
                else:
                    continue
        with open(summary_file, 'a') as sum_f:
            print("[Max OOO Size:{}][in test case {}]".format(max_ooo_size, datafile + datafile.split("/")[-1]))
            sum_f.write("MAX_OOO_SIZE {}\n".format(max_ooo_size))

    return max_ooo_size


def plot_peak_ooo_results(history_filename, data_dir, fig_filenames, interval):
    # data[algo][config] = peak_ooo_size
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

            netload = parsed_line[1]
            topo = parsed_line[2]

            # files.append(data_dir + "/" + topo + "-" + netload + "/" + config_id + "/fct.txt")
            if os.path.exists(data_dir + "/" + config_id):
                # print("found path {}".format(data_dir + "/" + config_id))
                data_file = data_dir + "/" + config_id
            elif os.path.exists(data_dir + "/" + topo + "-" + netload + "/" + config_id):
                # print("found path {}".format(data_dir + "/" + topo + "-" + netload + "/" + config_id))
                data_file = data_dir + "/" + topo + "-" + netload + "/" + config_id
            else:
                print("config_id {} not found".format(config_id))
                continue

            topo = parsed_line[2].split('_')[0]
            workload = parsed_line[1].split('_')[0] + "_" + str(get_flow_size(data_file + "/fct.txt")) + "M"
            workload = workload.replace("micro", "")
            if "All2All" in workload:
                workload = workload.replace("1.0", "8").replace("4.0", "32")
            elif "AllReduce" in workload:
                workload = workload.replace("1.0", "128").replace("4.0", "512")
            workload = workload.replace("M", "MB")

            if topo == "fattree":
                topo = "FatTree"
            config = "[" + topo + "]\n" + workload  # topo + netload

            peak_ooo_size = get_peak_ooo_size(data_file)
            
            # 获取算法、缓冲区大小、FCT
            algo = lb_mode.rsplit('-', 1)[0]
            data.setdefault(algo, {})[config] = peak_ooo_size

    # 维度整理
    algorithms = sorted(data.keys())
    configurations = sorted({cfg for algo_data in data for cfg in data[algo_data]})
    # 手动指定配置
    # configurations = [
    # '[FatTree]\nAll2All_8MB', 
    # '[FatTree]\nAll2All_32MB', 
    # '[AlibabaHPN]\nAll2All_8MB', 
    # '[AlibabaHPN]\nAll2All_32MB', 
    # '[SpectrumX]\nAll2All_8MB', 
    # '[SpectrumX]\nAll2All_32MB', 
    # ]

    configurations = [
    '[FatTree]\nAllReduce_128MB', 
    '[FatTree]\nAllReduce_512MB', 
    '[AlibabaHPN]\nAllReduce_128MB', 
    '[AlibabaHPN]\nAllReduce_512MB', 
    '[SpectrumX]\nAllReduce_128MB', 
    '[SpectrumX]\nAllReduce_512MB', 
    ]

    # 给每个算法固定一种颜色
    color_map = {
        algo: plt.cm.tab10(i)
        for i, algo in enumerate(algorithms)
    }

    x = np.arange(len(configurations))
    num_algos = len(algorithms)
    bar_width = 0.8 / num_algos

    plt.figure(figsize=(12, 5))
    
    for i, algo in enumerate(algorithms):
        # 按缓存区大小顺序取 FCT
        ooo_size = [
            data[algo].get(b, np.nan)  # 若缺失，用 NaN 占位
            for b in configurations 
        ]

        bars = plt.bar(
        x + i * bar_width,        # 控制并排位置
        ooo_size,
        width=bar_width,
        color=color_map[algo],    # 同一算法同色
        label=algo,                # legend 只显示算法
        edgecolor='black',
        hatch=hatches[i % len(hatches)])

        for bar in bars:
                height = bar.get_height()
                color = bar.get_facecolor()
                plt.text(
                    bar.get_x() + bar.get_width() / 2,
                    height,
                    f"{height}",
                    ha='center', va='bottom',
                    fontsize=10,
                    # fontweight='bold',
                    # color=color
                )

    # 坐标轴
    plt.xticks(
        x + bar_width * (num_algos - 1) / 2,
        configurations,
        # rotation=45,
        # ha="right"
    )
    # plt.xlabel("Topology and Load")
    plt.ylabel("Peak OoO Buffer Size")

    # 图例：只区分算法
    plt.legend(
        loc='upper right',
        frameon=False,
        fontsize=15,          # 比正文略大，论文友好
        handlelength=1.6,
        handletextpad=0.6,
        borderaxespad=0.3
    )

    plt.tight_layout()
    plt.show()
    plt.savefig(fig_filename)

def plot_ooo_results(data_files, LBs, fig_filename, interval):
    strategies = LBs

    plt.figure(figsize=(10, 6))

    for i, strategy in enumerate(strategies):
        buffer_file = data_files[i] + "/ooo_buffer.txt"

        if not os.path.exists(buffer_file):
            print(f"[Warning] {buffer_file} not found, skip.")
            continue

        time_us, buffers = read_ooo_buffer(buffer_file)

        # 聚合：按时间窗口获取峰值
        t, peak = aggregate_peak_by_time(time_us, buffers, bin_us=interval)

        if t is None:
            print(f"[Warning] No valid data for {strategy} with file {data_files[i]}.")
            continue

        plt.plot(t, peak, label=strategy, linewidth=2)
    xlabelname = "Time (µs)" # + str(interval) + "µs"
    plt.xlabel(xlabelname, fontsize=14)
    plt.ylabel("Peak OOO Buffer Occupancy", fontsize=14)
    plt.title("Peak OOO Buffer Occupancy Over Time", fontsize=16)
    plt.legend()

    
    plt.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    
    print(fig_filename)
    plt.savefig(fig_filename, transparent=False, bbox_inches='tight')
    plt.close()


if __name__ == "__main__":

    data_files = []
    LBs = []
    config = []
    file_dir = getFilePath()
    fig_dir = file_dir + "/../output/1all_figures"
    if not os.path.exists(fig_dir):
        os.makedirs(fig_dir)
    # data_dir = file_dir + "/../output"
    data_dir = file_dir + "/../output/5ooo-class"
    history_filename = file_dir + "/../output/ooo_compare.history"

    data_files, LBs, config = get_config_from_history(history_filename, data_dir)
    if len(config) == 0:
        print("No matched result")
        sys.exit(0)
    step = 1 # us

    type = "peak" # "all"
    if type == "peak":
        fig_filename = fig_dir + "/{}.pdf".format("OOO_PEAK:[{}]".format(config[0][1]))
        plot_peak_ooo_results(history_filename, data_dir, fig_filename, step)
    elif type == "all":
        fig_filename = fig_dir + "/{}.pdf".format("OOO_ALL:[{}]+[{}]+[CC:{}]".format(config[0][0], config[0][1], config[0][2]))

        plot_ooo_results(data_files, LBs, fig_filename, step)

    
