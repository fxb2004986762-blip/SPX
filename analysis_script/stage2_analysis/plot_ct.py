import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import re

# plt.rcParams.update({
#     "font.family": "serif",
#     "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
#     "font.size": 10,
#     "axes.labelsize": 11,
#     "axes.titlesize": 11,
#     "xtick.labelsize": 9,
#     "ytick.labelsize": 9,
#     "legend.fontsize": 9,
#     "axes.linewidth": 1.2,
#     "pdf.fonttype": 42,
#     "ps.fonttype": 42,
# })

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ["Times New Roman", "Times", "DejaVu Serif"]
plt.rcParams['font.size'] = 14
plt.rcParams['axes.labelsize'] = 16
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['xtick.labelsize'] = 13  # 调整x轴刻度字体大小
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['legend.fontsize'] = 13
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['axes.linewidth'] = 1.2
plt.rcParams['grid.linewidth'] = 0.8
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['pdf.fonttype'] = 42  # 确保字体可编辑
plt.rcParams['ps.fonttype'] = 42

topo2bdp = {
    # "leaf_spine_128_100G_OS2": 104000,  # 2-tier
    "fattree": 306000, # 3-tier -> core 400G
}

hatches = ['/', '\\', '-', '+', 'x', '*', 'o', '.']

# 论文风格配色方案 - 使用更专业的颜色
paper_colors = [
    '#4472C4',  # 蓝色
    '#ED7D31',  # 橙色
    '#A5A5A5',  # 灰色
    '#FFC000',  # 黄色
    '#5B9BD5',  # 浅蓝
    '#70AD47',  # 绿色
    '#264478',  # 深蓝
    '#9E480E',  # 深橙
]

def getFilePath():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    print("File directory: {}".format(dir_path))
    return dir_path

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
           np.percentile(flows, 99) if flows else 0, \
           np.percentile(flows, 95) if flows else 0

def get_jct(filename):
    with open(filename, "r") as f:
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
    # 默认单位纳秒，转换为毫秒
    return (job_end_time - job_start_time) / 1e6

def get_flow_size(filename):
    with open(filename, "r") as f:
        line = f.readline()
        flow_size = float(line.split()[4])
    # 默认B，转换为MB，保留1位小数
    return round(flow_size / (1024 * 1024), 1)

def plot_results(data_files, LBs, fig_filename, type_name):
    strategies = LBs
    flow_avg = []
    flow_p95 = []
    flow_p99 = []
    flow = []
    if type_name == "avg":
        type = 0
    elif type_name == "p99":
        type = 1
    elif type_name == "p95":
        type = 2

    for f in data_files:
        avg, p99, p95 = parse_file(f)
        flow_avg.append(avg)
        flow_p99.append(p99)
        flow_p95.append(p95)
    flow.append(flow_avg)
    flow.append(flow_p99)
    flow.append(flow_p95)
    
    flow_size = get_flow_size(data_files[0])

    n_strategies = len(strategies)
    width = 0.6  # 增加柱子宽度使其更醒目
    
    # 计算每个柱子的x位置
    x = np.arange(n_strategies)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.4, zorder=0)

    print(strategies)
    print(flow[type])
    
    # 绘制柱状图
    bars = ax.bar(x, flow[type], width, 
                  color=[paper_colors[i % len(paper_colors)] for i in range(n_strategies)],
                  edgecolor='black',
                  linewidth=1.2,
                  zorder=3, 
                  hatch=[hatches[i % len(hatches)] for i in range(n_strategies)])

    # 在柱状图顶部添加数值
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{height:.2f}",
            ha='center', va='bottom',
            fontsize=11,
            fontweight='bold'
        )
    
    # 设置x轴刻度和标签（将算法名称作为x轴刻度标签）
    ax.set_xticks(x)
    ax.set_xticklabels(strategies, rotation=15, ha='center')
    
    # 设置y轴标签
    if type == 0:
        plot_name = "Average "
    elif type == 1:
        plot_name = "P99th "
    elif type == 2:
        plot_name = "P95th "
    plot_name = plot_name + "FCT Slowdown"
    ax.set_ylabel(plot_name, fontsize=16, fontweight='bold')
    
    # 不需要图例了，因为算法名称已经在x轴上
    # ax.legend() # 移除图例

    plt.tight_layout()

    print(fig_filename)
    plt.savefig(fig_filename, dpi=300, transparent=False, bbox_inches='tight')
    plt.close()

def plot_results_jct(data_files, LBs, fig_filename):
    strategies = LBs
    jct_values = []

    for f in data_files:
        jct = get_jct(f)
        jct_values.append(jct)
    flow_size = str(get_flow_size(data_files[0]))

    n_strategies = len(strategies)
    width = 0.6  # 增加柱子宽度
    
    # 计算每个柱子的x位置
    x = np.arange(n_strategies)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.grid(which='minor', alpha=0.2, zorder=0, linestyle='--')
    ax.grid(which='major', alpha=0.4, zorder=0, linestyle='--')

    print(strategies)

    # 绘制柱状图
    bars = ax.bar(x, jct_values, width,
                  color=[paper_colors[i % len(paper_colors)] for i in range(n_strategies)],
                  edgecolor='black',
                  linewidth=1.2,
                  zorder=3, 
                  hatch=[hatches[i % len(hatches)] for i in range(n_strategies)])

    # 在柱状图顶部添加数值
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{height:.2f}",
            ha='center', va='bottom',
            fontsize=11,
            # fontweight='bold'
        )
    
    # 设置x轴刻度和标签
    ax.set_xticks(x)
    ax.set_xticklabels(strategies, ha='center')
    
    plot_name = "Collective Runtime (ms)"
    ax.set_xlabel("All-to-All Workload", 
                fontsize=16, 
                # fontweight='bold'
                )
    ax.set_ylabel(plot_name, 
                fontsize=16, 
                # fontweight='bold'
                )
    
    # 移除图例
    # ax.legend()

    plt.tight_layout()

    print(fig_filename)
    plt.savefig(fig_filename, dpi=300, transparent=False, bbox_inches='tight')
    plt.close()


if __name__ == "__main__":

    # 非对称拓扑对比
    # algo_files = {
    #     "aps": "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All/aps-b64-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
    #     "aps-v2": "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All/aps-v2-b64-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
    #     "rps": "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All/rps-b64-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
    #     "reps": "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All/reps-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
    #     "ecmp": "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All/ecmp-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
    #     "flowbender": "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All/flowbender-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
    #     "letflow": "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All/letflow-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
    # }

    # 对称拓扑对比
    algo_files = {
        "aps": "/home/dell/sjw/lb/simulator/output/3lb-class/aps/All-to-All/aps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
        "aps-v2": "/home/dell/sjw/lb/simulator/output/3lb-class/aps-v2/All-to-All/aps-v2_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
        "rps": "/home/dell/sjw/lb/simulator/output/3lb-class/rps/All-to-All/rps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
        # "reps": "/home/dell/sjw/lb/simulator/output/3lb-class/reps/All-to-All/reps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
        "ecmp": "/home/dell/sjw/lb/simulator/output/3lb-class/ecmp/All-to-All/ecmp_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
        "flowbender": "/home/dell/sjw/lb/simulator/output/3lb-class/flowbender/All-to-All/flowbender_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
        "letflow": "/home/dell/sjw/lb/simulator/output/3lb-class/letflow/All-to-All/letflow_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
    }

    out_dir = "/home/dell/sjw/lb/simulator/output/1all_figures/aps-v2_vs._baseline/jct"

    algos = []
    data_files_fct = []
    for algo, data_file in algo_files.items():
        algos.append(algo)
        data_files_fct.append(data_file + "/fct.txt")

    plot_type = ["jct"]
    # plot_type = ["jct", "fct_avg", "fct_p99"]
    # plot_type = ["fct_avg", "fct_p99", "fct_p95"]
    out_pdf_jct_file = out_dir + "/jct_baseline_all2all_2MBpf_without_reps.pdf"
    out_pdf_fct_avg_file = out_dir + "/fct_avg_baseline_all2all_1MBpf.pdf"
    out_pdf_fct_p99_file = out_dir + "/fct_p99_baseline_all2all_1MBpf.pdf"
    out_pdf_fct_p95_file = out_dir + "/fct_p95_baseline_all2all_1MBpf.pdf"
    # out_pdf_jct_file = "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-jct.pdf"
    # out_pdf_fct_avg_file = "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-fct_avg.pdf"
    # out_pdf_fct_p99_file = "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-fct_p99.pdf"
    # out_pdf_jct_file = "/home/dell/sjw/lb/simulator/output/6int-class/freq_compare/jct/f1-jct.pdf"
    # out_pdf_fct_avg_file = "/home/dell/sjw/lb/simulator/output/6int-class/freq_compare/fct_avg/f1-fct_avg.pdf"
    # out_pdf_fct_p99_file = "/home/dell/sjw/lb/simulator/output/6int-class/freq_compare/fct_p99/f1-fct_p99.pdf"

    if "jct" in plot_type:
        plot_results_jct(data_files_fct, algos, out_pdf_jct_file)
    if "fct_avg" in plot_type:
        plot_results(data_files_fct, algos, out_pdf_fct_avg_file, "avg")
    if "fct_p99" in plot_type:
        plot_results(data_files_fct, algos, out_pdf_fct_p99_file, "p99")
    if "fct_p95" in plot_type:
        plot_results(data_files_fct, algos, out_pdf_fct_p95_file, "p95")
    