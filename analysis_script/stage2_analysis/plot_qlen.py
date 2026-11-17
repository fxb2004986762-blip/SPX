import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

def load_and_process_data(data_file):
    """加载数据文件并进行预处理（支持.txt和.csv格式）"""
    df = pd.read_csv(data_file, skipinitialspace=True)
    df.columns = df.columns.str.strip()
    return df

def fill_missing_samples(df):
    """补全缺失的采样数据"""
    # 获取所有唯一的时间点
    all_times = sorted(df['time'].unique())
    
    # 获取所有交换机-端口组合
    switch_ports = df.groupby(['sw_id', 'port_id'])['port_len'].last().to_dict()
    
    filled_data = []
    
    for time in all_times:
        # 获取当前时间点的数据
        current_data = df[df['time'] == time]
        sampled_ports = set(zip(current_data['sw_id'], current_data['port_id']))
        
        # 添加当前时间点已采样的数据
        for _, row in current_data.iterrows():
            filled_data.append({
                'time': time,
                'sw_id': row['sw_id'],
                'port_id': row['port_id'],
                'port_len': row['port_len']
            })
            # 更新最后已知队列长度
            switch_ports[(row['sw_id'], row['port_id'])] = row['port_len']
        
        # 补全未采样的端口（使用上一次的队列长度）
        for (sw_id, port_id), port_len in switch_ports.items():
            if (sw_id, port_id) not in sampled_ports:
                filled_data.append({
                    'time': time,
                    'sw_id': sw_id,
                    'port_id': port_id,
                    'port_len': port_len
                })
    
    return pd.DataFrame(filled_data)

def calculate_statistics(df):
    """计算每个时间点的平均值和方差"""
    results = []
    
    for time in sorted(df['time'].unique()):
        time_data = df[df['time'] == time]
        
        # 按交换机分组
        switch_means = []
        switch_vars = []
        
        for sw_id in time_data['sw_id'].unique():
            sw_data = time_data[time_data['sw_id'] == sw_id]['port_len'].values
            switch_means.append(sw_data.mean())
            # 使用ddof=0计算总体方差
            # switch_vars.append(sw_data.var(ddof=0) if len(sw_data) > 1 else 0)
        
        # 计算全网平均值和方差
        avg_mean = np.mean(switch_means)
        # avg_var = np.mean(switch_vars)
        
        results.append({
            'time': time,
            'avg_mean': avg_mean,
            # 'avg_var': avg_var
        })
    
    return pd.DataFrame(results)

def plot_results(stats_dict, output_file='queue_analysis.pdf'):
    """绘制符合顶会论文风格的图像（双Y轴）"""
    # 设置论文风格
    plt.rcParams.update({
        'font.size': 10,
        'font.family': 'serif',
        'axes.labelsize': 11,
        'axes.titlesize': 11,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 9,
        'figure.figsize': (7, 4),
        'lines.linewidth': 1.5,
        'lines.markersize': 4,
        'grid.alpha': 0.3,
        'axes.grid': True,
        'grid.linestyle': '--',
        'pdf.fonttype': 42,  # 确保PDF中嵌入字体
        'ps.fonttype': 42
    })
    
    fig, ax1 = plt.subplots(figsize=(7, 4))
    
    # 创建第二个Y轴
    # ax2 = ax1.twinx()
    
    # 颜色方案（顶会常用配色）
    colors_mean = ['#1f77b4', '#2ca02c', '#9467bd']  # 平均值用蓝色系
    colors_var = ['#ff7f0e', '#d62728', '#8c564b']   # 方差用橙红色系
    markers = ['o', 's', '^', 'v', 'D', 'p']
    linestyles_mean = ['-', '-', '-']
    linestyles_var = ['--', '--', '--']
    
    color_idx = 0
    lines1, labels1 = [], []
    lines2, labels2 = [], []
    
    for label, stats in stats_dict.items():
        # 转换时间单位为100us
        time_100us = stats['time'] / 100000
        
        # 绘制平均值（左Y轴）
        line1 = ax1.plot(time_100us, stats['avg_mean'], 
                label=f'{label} (Mean)',
                color=colors_mean[color_idx % len(colors_mean)],
                marker=markers[color_idx % len(markers)],
                markevery=max(1, len(time_100us)//10),
                linestyle=linestyles_mean[color_idx % len(linestyles_mean)])
        lines1.extend(line1)
        labels1.append(f'{label} (Mean)')
        
        # 绘制方差（右Y轴）
        # line2 = ax2.plot(time_100us, stats['avg_var'],
        #         label=f'{label} (Variance)',
        #         color=colors_var[color_idx % len(colors_var)],
        #         marker=markers[color_idx % len(markers)],
        #         markevery=max(1, len(time_100us)//10),
        #         linestyle=linestyles_var[color_idx % len(linestyles_var)])
        # lines2.extend(line2)
        # labels2.append(f'{label} (Variance)')
        
        color_idx += 1
    
    # 设置左Y轴（平均值）
    ax1.set_xlabel('Time (×100 μs)', fontweight='bold')
    ax1.set_ylabel('Average Queue Length (Bytes)', fontweight='bold')
    ax1.tick_params(axis='y')
    ax1.grid(True, alpha=0.3)
    
    # 设置右Y轴（方差）
    # ax2.set_ylabel('Variance of Queue Length (Bytes²)', fontweight='bold', color='#ff7f0e')
    # ax2.tick_params(axis='y', labelcolor='#ff7f0e')
    
    # 合并图例
    lines = lines1 + lines2
    labels = labels1 + labels2
    ax1.legend(lines, labels, loc='best', framealpha=0.9)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"图像已保存至: {output_file}")
    plt.show()

# 主程序
if __name__ == "__main__":
    # 示例：处理单个或多个文件
    data_files = {
        "reps": "/home/dcn1/fxb/simulator/output/reps_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M",
        # "aps-v2-b16": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g/aps-v2-b16_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g",
        # "aps-v2-b64": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g/aps-v2-b64_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g",
        # "rps-b0": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g/rps-b0_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g",
        # "rps-b16": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g/rps-b16_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g",
        # "rps-b64": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g/rps-b64_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g",
    }


    output_dir = "/home/dcn1/fxb/simulator/output/reps_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M"
    output_file = output_dir + "/qlen.pdf"
    for label, data_file in data_files.items():
        data_files[label] = data_file + "/qlen.txt"

    stats_dict = {}
    
    for label, data_file in data_files.items():
        print(f"处理文件: {data_file}")
        
        # 加载数据
        df = load_and_process_data(data_file)
        
        # 补全缺失数据
        df_filled = fill_missing_samples(df)
        print(f"  原始样本数: {len(df)}, 补全后样本数: {len(df_filled)}")
        
        # 计算统计量
        stats = calculate_statistics(df_filled)
        stats_dict[label] = stats
        
        print(f"  时间范围: {stats['time'].min()/1e6:.2f}ms - {stats['time'].max()/1e6:.2f}ms")
        print(f"  平均队列长度: {stats['avg_mean'].mean():.2f} bytes")
        print()
    
    # 绘制结果
    plot_results(stats_dict, output_file=output_file)