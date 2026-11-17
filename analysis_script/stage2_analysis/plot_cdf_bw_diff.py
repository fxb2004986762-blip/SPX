#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
链路利用率差值CDF分析脚本
分析所选路径与最低路径链路利用率的差值分布
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import sys

# 设置论文级别的绘图风格
def setup_plot_style():
    """配置高质量论文绘图参数"""
    # 使用LaTeX风格字体
    rcParams['font.family'] = 'serif'
    rcParams['font.serif'] = ["Times New Roman", "Times", "DejaVu Serif"]
    rcParams['font.size'] = 12
    rcParams['axes.labelsize'] = 14
    rcParams['axes.titlesize'] = 16
    rcParams['xtick.labelsize'] = 12
    rcParams['ytick.labelsize'] = 12
    rcParams['legend.fontsize'] = 11
    rcParams['figure.figsize'] = (8, 6)
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


def load_data(filename):
    """
    加载数据文件
    
    参数:
        filename: 数据文件路径
    
    返回:
        利用率差值数组
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
        
        # 将有效行转换为临时文件内容
        if not valid_lines:
            print("数据文件为空或格式错误")
            sys.exit(1)
        
        # 使用StringIO来处理数据，只读取第5列和第6列（索引4和5）
        from io import StringIO
        data_str = ''.join(valid_lines)
        data = np.loadtxt(StringIO(data_str), usecols=(4, 5))
        
        # 如果只有一行数据，需要reshape
        if data.ndim == 1:
            data = data.reshape(1, -1)
        
        # 第1列(索引0)是所选路径的链路利用率
        # 第2列(索引1)是所有路径中最低的链路利用率
        selected_util = data[:, 0]
        min_util = data[:, 1]
        
        # 计算差值
        # diff = selected_util - min_util
        diff = selected_util - min_util
        
        print(f"成功加载数据: {len(diff)} 条记录")
        print(f"数据范围: [{np.min(diff):.2f}, {np.max(diff):.2f}]")
        return diff
    
    except Exception as e:
        print(f"加载数据文件失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def calculate_statistics(data):
    """
    计算统计信息
    
    参数:
        data: 数据数组
    
    返回:
        统计信息字典
    """
    stats = {
        'mean': np.mean(data),
        'variance': np.var(data),
        'std': np.std(data),
        'p95': np.percentile(data, 95),
        'p99': np.percentile(data, 99),
        'min': np.min(data),
        'max': np.max(data),
        'median': np.median(data)
    }
    
    return stats


def plot_cdf(data, stats, output_file='cdf_plot.pdf'):
    """
    绘制CDF图并标注统计信息
    
    参数:
        data: 利用率差值数据
        stats: 统计信息字典
        output_file: 输出文件名
    """
    setup_plot_style()
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # 计算CDF
    sorted_data = np.sort(data)
    cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    
    # 绘制CDF曲线
    ax.plot(cdf * 100, sorted_data, 'b-', linewidth=2.5, label='CDF', zorder=3)
    
    # 定义标注信息
    annotations = [
        ('mean', stats['mean'], 'Mean', 'red', 'o'),
        ('p95', stats['p95'], 'P95', 'green', 's'),
        ('p99', stats['p99'], 'P99', 'orange', '^')
    ]
    
    # 为每个统计量添加标注
    for key, value, label, color, marker in annotations:
        # 找到对应的CDF值
        idx = np.searchsorted(sorted_data, value)
        if idx >= len(cdf):
            idx = len(cdf) - 1
        cdf_value = cdf[idx] * 100
        
        # 绘制水平虚线
        ax.axhline(y=value, color=color, linestyle='--', 
                   linewidth=1.5, alpha=0.7, zorder=1)
        
        # 绘制垂直虚线
        ax.axvline(x=cdf_value, color=color, linestyle='--', 
                   linewidth=1.5, alpha=0.7, zorder=1)
        
        # 绘制标记点
        ax.plot(cdf_value, value, marker=marker, markersize=10, 
                color=color, markeredgecolor='black', markeredgewidth=1.5,
                label=f'{label}: {value:.2f}', zorder=4)
        
        # 添加文本标注
        offset_x = -8 if cdf_value > 50 else 5
        offset_y = 3
        ax.annotate(f'{label}\n({cdf_value:.1f}%, {value:.2f})',
                   xy=(cdf_value, value),
                   xytext=(offset_x, offset_y),
                   textcoords='offset points',
                   fontsize=10,
                   bbox=dict(boxstyle='round,pad=0.5', facecolor=color, 
                            alpha=0.15, edgecolor=color),
                   ha='right' if cdf_value > 50 else 'left',
                   zorder=5)
    
    # 设置坐标轴标签
    ax.set_xlabel('Cumulative Probability (%)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Link Utilization Difference', fontsize=14, fontweight='bold')
    ax.set_title('CDF of Link Utilization Difference\n(Selected Path - Minimum Path)', 
                 fontsize=16, fontweight='bold', pad=20)
    
    # 设置坐标轴范围和刻度
    ax.set_xlim(0, 100)
    ax.set_xticks(np.arange(0, 101, 10))
    
    # Y轴刻度保留2位小数
    y_min, y_max = ax.get_ylim()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}'))
    
    # 添加网格
    ax.grid(True, linestyle='--', alpha=0.3, zorder=0)
    
    # 添加图例
    ax.legend(loc='best', framealpha=0.9, edgecolor='black', 
             fancybox=True, shadow=True)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图形
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    # plt.savefig(output_file.replace('.pdf', '.png'), dpi=300, bbox_inches='tight')
    
    print(f"\n图形已保存到: {output_file} 和 {output_file.replace('.pdf', '.png')}")
    
    # 显示图形
    plt.show()


def print_statistics(stats):
    """
    打印统计信息
    
    参数:
        stats: 统计信息字典
    """
    print("\n" + "="*60)
    print("统计信息汇总".center(60))
    print("="*60)
    print(f"均值 (Mean):          {stats['mean']:.2f}")
    print(f"方差 (Variance):      {stats['variance']:.2f}")
    print(f"标准差 (Std Dev):     {stats['std']:.2f}")
    print(f"中位数 (Median):      {stats['median']:.2f}")
    print(f"最小值 (Min):         {stats['min']:.2f}")
    print(f"最大值 (Max):         {stats['max']:.2f}")
    print(f"P95:                  {stats['p95']:.2f}")
    print(f"P99:                  {stats['p99']:.2f}")
    print("="*60 + "\n")

def main():
    """主函数"""
    # 检查命令行参数
    # if len(sys.argv) < 2:
    #     print("用法: python plot_cdf.py <数据文件路径> [输出文件名]")
    #     print("示例: python plot_cdf.py data.txt cdf_output.pdf")
    #     sys.exit(1)
    algo_files = {
        "aps-v2-f1": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-u/aps-v2-u-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
        "aps-v2-f4": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f4_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
        "aps-v2-f8": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f8_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
        "aps-v2-f16": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f16_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
        "aps-v2-f32": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f32_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
        "aps-v2-f64": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f64_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
        "aps-v2-f306": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f306_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
    }
    for case, data_dir in algo_files.items():
        input_file = data_dir + '/acc_path_selected_by_bw.txt'
        output_file = data_dir + '/bw_error_cdf.pdf'

        
        print(f"正在处理数据文件: {input_file}")
        
        # 加载数据
        diff_data = load_data(input_file)
        
        # 计算统计信息
        stats = calculate_statistics(diff_data)
        
        # 打印统计信息
        print_statistics(stats)
        
        # 绘制CDF图
        plot_cdf(diff_data, stats, output_file)
        
        print("处理完成!")


if __name__ == '__main__':
    main()