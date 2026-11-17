#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多算法准确率对比分析脚本
计算不同算法在不同阈值下的准确率并绘制对比柱状图
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import sys
import os
from io import StringIO

# 设置论文级别的绘图风格
def setup_plot_style():
    """配置高质量论文绘图参数"""
    # 使用LaTeX风格字体
    rcParams['font.family'] = 'serif'
    rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
    rcParams['font.size'] = 12
    rcParams['axes.labelsize'] = 14
    rcParams['axes.titlesize'] = 16
    rcParams['xtick.labelsize'] = 12
    rcParams['ytick.labelsize'] = 12
    rcParams['legend.fontsize'] = 11
    rcParams['figure.figsize'] = (12, 7)
    rcParams['figure.dpi'] = 300
    
    # 设置线条和网格样式
    rcParams['axes.linewidth'] = 1.2
    rcParams['grid.linewidth'] = 0.5
    rcParams['lines.linewidth'] = 2
    rcParams['grid.alpha'] = 0.3
    
    # 其他美化设置
    rcParams['axes.grid'] = True
    rcParams['grid.linestyle'] = '--'
    rcParams['savefig.bbox'] = 'tight'
    rcParams['savefig.pad_inches'] = 0.1


def load_algorithm_data(filename):
    """
    加载单个算法的数据文件
    
    参数:
        filename: 数据文件路径
    
    返回:
        第6列和第7列的数据数组
    """
    try:
        # 读取文件，遇到空行则停止
        valid_lines = []
        with open(filename, 'r') as f:
            for line in f:
                # 检查是否为空行（只包含空白字符）
                if line.strip() == '':
                    break
                valid_lines.append(line)
        # print(valid_lines[-1])
        if not valid_lines:
            print(f"警告: 数据文件 {filename} 为空")
            return None, None
        
        # 使用StringIO来处理数据，只读取第5列和第6列（索引4和5）
        data_str = ''.join(valid_lines)
        data = np.loadtxt(StringIO(data_str), usecols=(4, 5))
        
        # 如果只有一行数据，需要reshape
        if data.ndim == 1:
            data = data.reshape(1, -1)
        
        col6 = data[:, 0]  # 第6列
        col7 = data[:, 1]  # 第7列
        
        print(f"  成功加载: {len(col6)} 条记录")
        return col6, col7
    
    except Exception as e:
        print(f"  加载失败: {e}")
        return None, None


def calculate_accuracy(col6, col7, type="threshold", thresholds=[400, 400, 400], percentiles=[1, 5, 10]):
    """
    计算准确率：差值小于阈值的数据比例
    
    参数:
        col6: 第6列数据
        col7: 第7列数据
        thresholds: 阈值列表（对应每个百分位）
        percentiles: 百分位列表
    
    返回:
        准确率列表
    """
    if col6 is None or col7 is None:
        return [0.0, 0.0, 0.0]
    

    if type == "threshold":
        diff = np.abs(col6 - col7)  # 计算差值的绝对值
    elif type == "percentile":
        diff = np.abs((col6 - col7) / np.where(col7 == 0, 1, col7))
        diff = np.where(col7 == 0, 0, diff)    
    
    accuracies = []
    if type == "threshold":
        for threshold in thresholds:
            # 计算差值小于阈值的比例
            accuracy = np.sum(diff < threshold) / len(diff) * 100
            accuracies.append(accuracy)
    elif type == "percentile":
        for percent in percentiles:
            percent = percent / 100.0
            # 计算差值小于阈值的比例
            accuracy = np.sum(diff < percent) / len(diff) * 100
            accuracies.append(accuracy)
    
    return accuracies


def plot_accuracy_comparison(algorithms_data, output_file='accuracy_comparison.pdf', type="acc_path_selected_by_bw.txt"):
    """
    绘制多算法准确率对比柱状图
    
    参数:
        algorithms_data: 字典，键为算法名称，值为准确率列表 [1%, 5%, 10%]
        output_file: 输出文件名
    """
    setup_plot_style()
    
    # 准备数据
    algorithms = list(algorithms_data.keys())
    num_algorithms = len(algorithms)
    
    # 每个算法的三个准确率值
    accuracy_1pct = [algorithms_data[alg][0] for alg in algorithms]
    accuracy_5pct = [algorithms_data[alg][1] for alg in algorithms]
    accuracy_10pct = [algorithms_data[alg][2] for alg in algorithms]
    
    # 不同的填充纹理（hatch patterns）
    # hatches = ['', '//', '\\\\', '||', '--', '++', 'xx', '**', 'oo', '..', '///', '|||']
    # num_algos = len(algorithms)
    # hatches = hatches[:num_algos]

    # 设置柱状图参数
    x = np.arange(num_algorithms)  # 算法位置
    width = 0.30  # 柱子宽度
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(max(12, num_algorithms * 1.5), 7))
    
    # 绘制三组柱子
    bars1 = ax.bar(x - width, accuracy_1pct, width,
                   label='Threshold < 1%', 
                   color='#2E86AB', edgecolor='black', linewidth=1.2,
                   alpha=0.85)
    # for i, bar in enumerate(bars1):
    #     if i < len(hatches):
    #         bar.set_hatch(hatches[i])
    bars2 = ax.bar(x, accuracy_5pct, width, 
                   label='Threshold < 5%', 
                   color='#A23B72', edgecolor='black', linewidth=1.2,
                   alpha=0.85)
    # for i, bar in enumerate(bars2):
    #     if i < len(hatches):
    #         bar.set_hatch(hatches[i])
    bars3 = ax.bar(x + width, accuracy_10pct, width, 
                   label='Threshold < 10%', 
                   color='#F18F01', edgecolor='black', linewidth=1.2,
                   alpha=0.85)
    # for i, bar in enumerate(bars3):
    #     if i < len(hatches):
    #         bar.set_hatch(hatches[i])
    
    # 在柱子上方添加数值标签
    def add_value_labels(bars):
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%',
                   ha='center', va='bottom', fontsize=8.5, fontweight='bold')
    
    add_value_labels(bars1)
    add_value_labels(bars2)
    add_value_labels(bars3)
    if type == "acc_path_selected_by_bw.txt":
        type_name = "(Link Utilization)"
    elif type == "acc_path_selected_by_qlen.txt":
        type_name = "(Queue Length)"
    
    # 设置坐标轴
    ax.set_xlabel('Algorithms', fontsize=14, fontweight='bold')
    ax.set_ylabel('Accuracy (%)', fontsize=14, fontweight='bold')
    ax.set_title('Comparison of Accuracy at Different Frequencies\n' + type_name, 
                 fontsize=16, fontweight='bold', pad=20)
    
    # 设置X轴刻度标签
    ax.set_xticks(x)
    # 设置x轴刻度标签居中
    ax.set_xticklabels(algorithms, fontsize=12, 
                    #    rotation=45,
                       ha='center')
    
    # 设置Y轴范围
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f'{y:.0f}%'))
    
    # 添加网格
    ax.grid(True, axis='y', linestyle='--', alpha=0.3, zorder=0)
    ax.set_axisbelow(True)
    
    # 添加图例（放在底部，多行多列自适应）
    # 计算最佳列数
    ncol = min(3, len(algorithms))
    legend = ax.legend(loc='upper center', 
                      bbox_to_anchor=(0.5, -0.15),
                      ncol=ncol, frameon=True, fancybox=True, 
                      shadow=True, framealpha=0.9, edgecolor='black')
    
    # 调整布局以适应图例
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.2)
    
    # 保存图形
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    # plt.savefig(output_file.replace('.pdf', '.png'), dpi=300, bbox_inches='tight')
    
    print(f"\n图形已保存到: {output_file} 和 {output_file.replace('.pdf', '.png')}")
    
    # 显示图形
    plt.show()


def print_statistics(algorithms_data):
    """
    打印统计信息
    
    参数:
        algorithms_data: 字典，键为算法名称，值为准确率列表
    """
    print("\n" + "="*80)
    print("准确率统计汇总 (差值 < 400)".center(80))
    print("="*80)
    print(f"{'算法名称':<30} {'1% 准确率':<15} {'5% 准确率':<15} {'10% 准确率':<15}")
    print("-"*80)
    
    for alg, accuracies in algorithms_data.items():
        print(f"{alg:<30} {accuracies[0]:>12.2f}%  {accuracies[1]:>12.2f}%  {accuracies[2]:>12.2f}%")
    
    print("="*80 + "\n")


def main():
    """主函数"""
    # if len(sys.argv) < 2:
    #     print("用法: python plot_accuracy_comparison.py <算法1数据文件> [算法2数据文件] ... [输出文件名]")
    #     print("\n示例:")
    #     print("  python plot_accuracy_comparison.py algo1.txt algo2.txt algo3.txt")
    #     print("  python plot_accuracy_comparison.py algo1.txt algo2.txt output.pdf")
    #     print("\n说明:")
    #     print("  - 每个数据文件代表一个算法的测试结果")
    #     print("  - 文件名（不含扩展名）将作为算法名称显示在图中")
    #     print("  - 可选：最后一个参数如果是.pdf/.png结尾，将作为输出文件名")
    #     sys.exit(1)
    
    # 解析命令行参数
    # args = sys.argv[1:]
    
    # 检查最后一个参数是否为输出文件名
    # if args[-1].endswith('.pdf') or args[-1].endswith('.png'):
    #     output_file = args[-1]
    #     data_files = args[:-1]
    # else:
    #     output_file = 'accuracy_comparison.pdf'
    #     data_files = args

    algo_files = {
        "aps-v2-f1": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
        "aps-v2-eq-f1": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-eq/aps-v2-eq-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
        "aps-v2-eu-f1": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-eu/aps-v2-eu-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
        "aps-v2-q-f1": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-q/aps-v2-q-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
        "aps-v2-qu-f1": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
        "aps-v2-u-f1": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-u/aps-v2-u-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
        # "aps-v2-u-f306": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-u/aps-v2-u-f306_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
    }

    output_dir = "/home/dell/sjw/lb/simulator/output/1all_figures"
    # data_name = "acc_path_selected_by_bw.txt" # "acc_path_selected_by_bw.txt" "acc_path_selected_by_qlen.txt"
    # compare_type = "threshold"
    data_name = "acc_path_selected_by_qlen.txt" # "acc_path_selected_by_bw.txt" "acc_path_selected_by_qlen.txt"
    compare_type = "percentile"

    # output_file = output_dir + "/" + data_name.replace('.txt', '_' + compare_type + '_without306.pdf')
    output_file = output_dir + "/" + data_name.replace('.txt', '_' + compare_type + '.pdf')
    
    # print(f"开始处理 {len(data_files)} 个算法的数据...")
    # print(f"输出文件: {output_file}\n")
    
    # 加载所有算法的数据
    algorithms_data = {}
    
    for alg_name, data_file in algo_files.items():
        print(f"正在加载算法: {alg_name}")
        print(f"  文件: {data_file}")
        data_file = data_file + "/" + data_name
        # 加载数据
        col6, col7 = load_algorithm_data(data_file)
        
        if col6 is not None and col7 is not None:
            # 计算准确率（三个阈值都是400，对应1%、5%、10%）
            accuracies = calculate_accuracy(col6, col7,
                            type=compare_type,
                            thresholds=[4, 20, 40],
                            percentiles=[1, 5, 10])
            algorithms_data[alg_name] = accuracies
            print(f"  准确率: 1%={accuracies[0]:.2f}%, 5%={accuracies[1]:.2f}%, 10%={accuracies[2]:.2f}%")
        else:
            print(f"  跳过该算法（加载失败）")
        
        print()
    
    if not algorithms_data:
        print("错误: 没有成功加载任何算法数据")
        sys.exit(1)
    
    # 打印统计信息
    print_statistics(algorithms_data)
    
    # 绘制对比图
    plot_accuracy_comparison(algorithms_data, output_file, type=data_name)
    
    print("处理完成!")


if __name__ == '__main__':
    main()