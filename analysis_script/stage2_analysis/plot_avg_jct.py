#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本脚本绘制针对Ring-AllReduce的平均任务完成时间（JCT）
平均JCT：一次AllReduce通信中，单独求各个节点通信的JCT，再对所有节点的JCT取平均
平均吞吐：根据各个节点的JCT求平均吞吐，再对所有节点求平均，，得到整网平均吞吐
"""

import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import sys

# 设置论文级别的绘图样式
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ["Times New Roman", "Times", "DejaVu Serif"]
plt.rcParams['font.size'] = 14
plt.rcParams['axes.labelsize'] = 16
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['legend.fontsize'] = 13
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['axes.linewidth'] = 1.2
plt.rcParams['grid.linewidth'] = 0.8
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['pdf.fonttype'] = 42  # 确保字体可编辑
plt.rcParams['ps.fonttype'] = 42


def parse_fct_file(filename):
    """
    解析FCT数据文件
    
    返回: 字典，键为(发端ID, 收端ID)，值为流量列表
    每条流量包含: {start_time, end_time, bytes}
    """
    flows = defaultdict(list)
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split()
            if len(parts) < 8:
                continue
            
            src_id = int(parts[0])
            dst_id = int(parts[1])
            src_port = int(parts[2])
            flow_bytes = int(parts[4])
            start_time = int(parts[5])  # 纳秒
            duration = int(parts[6])     # 纳秒
            
            end_time = start_time + duration
            
            flows[(src_id, dst_id)].append({
                'start_time': start_time,
                'end_time': end_time,
                'bytes': flow_bytes,
                'src_port': src_port
            })
    
    return flows


def calculate_jct(flows):
    """
    计算任务完成时间(JCT)
    
    JCT = 最晚结束时间 - 最早开始时间
    
    返回: 所有(发端,收端)对的平均JCT，单位为毫秒
    """
    jct_list = []
    
    for (src, dst), flow_list in flows.items():
        if not flow_list:
            continue
        
        earliest_start = min(f['start_time'] for f in flow_list)
        latest_end = max(f['end_time'] for f in flow_list)
        
        jct_ns = latest_end - earliest_start
        jct_ms = jct_ns / 1e6  # 纳秒转毫秒
        
        jct_list.append(jct_ms)
    
    if not jct_list:
        return 0.0
    
    return np.mean(jct_list)

def calculate_avg_throughput(flows):
    """
    计算平均吞吐量
    
    返回: 所有(发端,收端)对平均吞吐量，单位为 Gbps
    """
    throughput_list = []
    
    for (src, dst), flow_list in flows.items():
        if not flow_list:
            continue
        
        earliest_start = min(f['start_time'] for f in flow_list)
        latest_end = max(f['end_time'] for f in flow_list)
        total_bytes = sum(f['bytes'] for f in flow_list)
        
        jct_ns = latest_end - earliest_start
        jct_ms = jct_ns / 1e6  # 纳秒转毫秒
        throughput = total_bytes * 8 / jct_ns # Gbps
        
        throughput_list.append(throughput)
    
    if not throughput_list:
        return 0.0
    
    return np.mean(throughput_list)
    


def plot_jct_comparison(jct_data, output_file='jct_comparison.pdf', legend_position='bottom'):
    """
    绘制不同负载均衡算法的JCT对比柱状图
    
    参数:
        jct_data: 字典，键为算法名称，值为平均JCT(ms)
        output_file: 输出文件名
        legend_position: 图例位置，可选值：
            'top' - 图表上方（适合3-6个算法）
            'bottom' - 图表下方（推荐，适合任意数量）
            'right' - 图表右侧（适合较少算法）
            'left' - 图表左侧
    """
    algorithms = list(jct_data.keys())
    jct_values = list(jct_data.values())
    num_algos = len(algorithms)
    
    # 顶会论文常用配色方案 (专业且对比明显)
    colors = ['#4472C4', '#ED7D31', '#A5A5A5', '#FFC000', '#5B9BD5', '#70AD47', 
              '#C5504B', '#548DD4', '#95B3D7', '#D99694', '#8E7CC3', '#C65911']
    colors = colors[:num_algos]
    
    # 不同的填充纹理（hatch patterns）
    hatches = ['', '//', '\\\\', '||', '--', '++', 'xx', '**', 'oo', '..', '///', '|||']
    hatches = hatches[:num_algos]
    
    # 调整图表尺寸，增加宽度
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 绘制柱状图：调宽柱子(width=0.75)，减小间隔
    x_pos = np.arange(num_algos)
    bars = []
    for i, (x, y, color, hatch) in enumerate(zip(x_pos, jct_values, colors, hatches)):
        bar = ax.bar(x, y, width=0.75, color=color, 
                     edgecolor='black', linewidth=1.5, alpha=0.85,
                     hatch=hatch)
        bars.append(bar)
    
    # 在柱状图上方标注数值
    for i, value in enumerate(jct_values):
        ax.text(x_pos[i], value,
                f'{value:.2f}',
                ha='center', va='bottom', fontsize=13, fontweight='bold')
    
    # 设置坐标轴
    ax.set_ylabel('Collective Runtime (ms)', fontsize=16, fontweight='bold')
    ax.set_xlabel('Load Balance Modes', fontsize=16, fontweight='bold')
    
    # 隐藏x轴刻度和标签（使用图例标注）
    ax.set_xticks([])
    
    # 添加网格线（仅y轴）
    ax.yaxis.grid(True, linestyle='--', alpha=0.3, linewidth=0.8)
    ax.set_axisbelow(True)
    
    # 设置y轴从0开始，增加顶部空间以容纳数值标注
    ax.set_ylim(bottom=0, top=max(jct_values) * 1.20)
    
    # 创建图例元素
    legend_elements = [bars[i][0] for i in range(num_algos)]
    
    # 根据图例位置和算法数量智能调整布局
    if legend_position == 'bottom':
        # 底部图例 - 最适合大量算法
        # 根据算法数量动态调整列数
        if num_algos <= 4:
            ncol = num_algos
        elif num_algos <= 8:
            ncol = 4
        else:
            ncol = 5
        
        ax.legend(legend_elements, algorithms,
                  loc='upper center',
                  bbox_to_anchor=(0.5, -0.12),  # 放在底部
                  frameon=True,
                  shadow=False,
                  fancybox=False,
                  edgecolor='black',
                  framealpha=0.95,
                  ncol=ncol,
                  columnspacing=1.2,
                  handletextpad=0.5,
                  fontsize=11)
        plt.subplots_adjust(bottom=0.20)  # 为底部图例留出空间
        
    elif legend_position == 'top':
        # 顶部图例 - 适合中等数量算法
        if num_algos <= 4:
            ncol = num_algos
        elif num_algos <= 8:
            ncol = 4
        else:
            ncol = 5
        
        ax.legend(legend_elements, algorithms,
                  loc='upper center',
                  bbox_to_anchor=(0.5, 1.15),  # 放在顶部
                  frameon=True,
                  shadow=False,
                  fancybox=False,
                  edgecolor='black',
                  framealpha=0.95,
                  ncol=ncol,
                  columnspacing=1.2,
                  handletextpad=0.5,
                  fontsize=11)
        plt.subplots_adjust(top=0.88)  # 为顶部图例留出空间
        
    elif legend_position == 'right':
        # 右侧图例 - 适合较少算法
        ax.legend(legend_elements, algorithms,
                  loc='center left',
                  bbox_to_anchor=(1.02, 0.5),  # 放在右侧
                  frameon=True,
                  shadow=False,
                  fancybox=False,
                  edgecolor='black',
                  framealpha=0.95,
                  ncol=1,
                  fontsize=11)
        plt.subplots_adjust(right=0.82)  # 为右侧图例留出空间
        
    elif legend_position == 'left':
        # 左侧图例
        ax.legend(legend_elements, algorithms,
                  loc='center right',
                  bbox_to_anchor=(-0.02, 0.5),  # 放在左侧
                  frameon=True,
                  shadow=False,
                  fancybox=False,
                  edgecolor='black',
                  framealpha=0.95,
                  ncol=1,
                  fontsize=11)
        plt.subplots_adjust(left=0.20)  # 为左侧图例留出空间
    
    # 紧凑布局
    plt.tight_layout()
    
    # 保存为高质量PDF和PNG
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    # plt.savefig(output_file.replace('.pdf', '.png'), dpi=300, bbox_inches='tight')
    
    print(f"图像已保存至: {output_file}")
    print(f"图像已保存至: {output_file.replace('.pdf', '.png')}")
    print(f"图例位置: {legend_position}, 算法数量: {num_algos}")
    
    plt.show()


if __name__ == '__main__':

    """
    绘制针对Ring-AllReduce的平均任务完成时间对比图 JCT(avg)
    """

    algo_files = {
        "aps": "/home/dcn1/fxb/simulator/output/8asy_topo/All-to-All/aps-b64-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
        "aps-v2": "/home/dcn1/fxb/simulator/output/8asy_topo/All-to-All/aps-v2-b64-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
        "rps": "/home/dcn1/fxb/simulator/output/8asy_topo/All-to-All/rps-b64-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
        "reps": "/home/dcn1/fxb/simulator/output/8asy_topo/All-to-All/reps-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
        "ecmp": "/home/dcn1/fxb/simulator/output/8asy_topo/All-to-All/ecmp-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
        # "flowbender": "/home/dcn1/fxb/simulator/output/6int-class-full/flowbender/flowbender_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
        # "letflow": "/home/dcn1/fxb/simulator/output/6int-class-full/letflow/letflow_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",

    }

    jct_data = {}
    throughput_data = {}
    out_dir = "/home/dcn1/fxb/simulator/output/8asy_topo/All-to-All"
    # out_file = out_dir + "/aps-v2-eu_jct_avg_without306.pdf"
    # out_file_throughput = out_dir + "/aps-v2-eu_jct_avg_without306.txt"
    out_file = out_dir + "/jct(avg)_baseline_all2all_1MBpf.pdf"
    out_file_throughput = out_dir + "/jct(avg)_baseline_all2all_1MBpf.txt"

    for algorithm, data_dir in algo_files.items():
        filename = data_dir + "/fct.txt"

        try:
            print(f"\n处理 {algorithm} 的数据文件: {filename}")
            flows = parse_fct_file(filename)
            print(f"  - 共解析 {len(flows)} 个(发端,收端)对")
            
            avg_jct = calculate_jct(flows)
            print(f"  - 平均任务完成时间: {avg_jct:.2f} ms")

            throughput = calculate_avg_throughput(flows)
            print(f"  - 平均吞吐: {throughput:.2f} Gbps")
            
            jct_data[algorithm] = avg_jct
            throughput_data[algorithm] = throughput

        except FileNotFoundError:
            print(f"错误: 文件 '{filename}' 不存在")
        except Exception as e:
            print(f"错误: 处理文件 '{filename}' 时出错: {e}")

    if not jct_data:
        print("\n没有成功处理任何数据文件")
        sys.exit(1)

    print(f"\n开始绘图...")
    plot_jct_comparison(jct_data, output_file=out_file)

    print(f"\n保存平均吞吐...")
    with open(out_file_throughput, "w") as f:
        for label, data in throughput_data.items():
            f.write(f"{label}: {np.mean(data):.2f} Gbps\n")