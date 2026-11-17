import numpy as np
import matplotlib.pyplot as plt

# ==================== 配置选项 ====================
# 方法1: 使用采样
USE_SAMPLING = False  # 是否使用采样
SAMPLE_RATE = 0.1    # 采样率：0.1表示读取10%的数据



# ==================== 快速读取函数（方法3: numpy + 采样 + 过滤0） ====================
def read_column_optimized(filename):
    """使用numpy快速加载，读取第7列除以第8列的值，结合采样和过滤零值"""
    print(f"  使用numpy加载数据...")
    
    # 使用numpy快速读取第7列和第8列
    data = np.loadtxt(filename, usecols=(6, 7))
    original_count = len(data)
    print(f"  原始数据: {original_count:,} 行")
    
    # 计算第7列除以第8列
    # 先过滤掉第8列为0的行，避免除零错误
    valid_mask = data[:, 1] != 0
    data = data[valid_mask]
    after_filter = len(data)
    filtered_out = original_count - after_filter
    print(f"  剔除第8列为0的行: {filtered_out:,} 行，剩余 {after_filter:,} 行")
    
    # 执行除法运算
    data = data[:, 0] / data[:, 1]
    
    # 可选：剔除结果为0的数据（如果需要的话）
    # data = data[data != 0]
    # print(f"  剔除结果为0: ... 行，剩余 {len(data):,} 行")
    
    # 应用采样（如果启用）
    if USE_SAMPLING and SAMPLE_RATE < 1.0:
        n_samples = int(len(data) * SAMPLE_RATE)
        # 随机采样
        np.random.seed(42)  # 设置随机种子以保证可重复性
        indices = np.random.choice(len(data), size=n_samples, replace=False)
        data = data[indices]
        print(f"  采样 {SAMPLE_RATE*100:.1f}%: {len(data):,} 个数据点")
    
    return data


def plot_cdf(file_with_label, output_file):
    # 设置图像风格，使用LaTeX风格的字体
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Times New Roman'] + plt.rcParams['font.serif']
    plt.rcParams['font.size'] = 12
    plt.rcParams['axes.labelsize'] = 14
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['xtick.labelsize'] = 12
    plt.rcParams['ytick.labelsize'] = 12
    plt.rcParams['legend.fontsize'] = 11
    plt.rcParams['figure.titlesize'] = 14

    # 设置线条和标记样式
    plt.rcParams['lines.linewidth'] = 2
    plt.rcParams['lines.markersize'] = 6
    plt.rcParams['axes.linewidth'] = 1.2

    # 设置网格样式
    plt.rcParams['grid.linewidth'] = 0.5
    plt.rcParams['grid.alpha'] = 0.3

    # 设置图例样式
    plt.rcParams['legend.frameon'] = True
    plt.rcParams['legend.framealpha'] = 0.9
    plt.rcParams['legend.edgecolor'] = 'black'
    plt.rcParams['legend.fancybox'] = False    

    # 创建图形（调整为论文常用尺寸，适合单栏或双栏）
    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)

    # 定义颜色和线型（使用学术论文常用的配色和样式）
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    linestyles = ['-', '--', '-.', ':', '-', '--']
    markers = ['o', 's', '^', 'D', 'v', 'p']
    # 创建图形
    # plt.figure(figsize=(12, 7))

    # 定义颜色
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']

    # 处理每个文件
    for idx, (filename, label) in enumerate(file_with_label):
        try:
            print(f"\n处理 {filename}...")
            
            # 读取数据（方法3: numpy + 采样 + 过滤0）
            data = read_column_optimized(filename, column_index=6)
            
            if len(data) == 0:
                print(f"警告: {filename} 过滤后没有有效数据")
                continue
            
            print(f"  最终用于绘图: {len(data):,} 个数据点")
            
            # 计算CDF
            sorted_data = np.sort(data)
            n = len(sorted_data)
            cdf = np.arange(1, n + 1) / n
            
            # 可选：绘图降采样（如果数据点仍然超过10000个）
            if n > 10000 and USE_SAMPLING:
                step = n // 10000
                plot_data = sorted_data[::step]
                plot_cdf = cdf[::step]
                print(f"  绘图降采样到 {len(plot_data):,} 个点")
            else:
                plot_data = sorted_data
                plot_cdf = cdf
            
            # 绘制CDF曲线

            ax.plot(plot_data, plot_cdf, 
               color=colors[idx % len(colors)],
               linestyle=linestyles[idx % len(linestyles)],
               linewidth=2,
               label=label,
               alpha=0.9)
            # color = colors[idx % len(colors)]
            # plt.plot(plot_data, plot_cdf, linewidth=2, color=color, 
            #         label=f'{label}', alpha=0.8)
            
            # 打印统计信息
            print(f"  统计信息:")
            print(f"    最小值: {data.min():.2f}")
            print(f"    最大值: {data.max():.2f}")
            print(f"    中位数: {np.median(data):.2f}")
            print(f"    均值: {np.mean(data):.2f}")
            print(f"    标准差: {np.std(data):.2f}")
            
        except FileNotFoundError:
            print(f"错误: 找不到文件 {filename}")
        except Exception as e:
            print(f"错误: 处理 {filename} 时出错 - {str(e)}")
            import traceback
            traceback.print_exc()

    # 设置图形属性
    # plt.xlabel('Out of Order Degree', fontsize=14, fontweight='bold')
    # plt.ylabel('CDF', fontsize=14, fontweight='bold')
    # plt.title('CDF of Out of Order Degree', fontsize=15, fontweight='bold')
    # plt.grid(True, alpha=0.3, linestyle='--')
    # plt.legend(loc='best', fontsize=11, framealpha=0.9)
    # plt.xlim(left=0)
    # plt.ylim(0, 1)
    # 设置坐标轴标签（英文）
    ax.set_xlabel('Value', fontsize=14, fontweight='normal')
    ax.set_ylabel('CDF', fontsize=14, fontweight='normal')

    # 设置坐标轴范围
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1.0)

    # 添加网格（使用细线）
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.3)

    # 设置图例（放在右下角，学术论文常用位置）
    ax.legend(loc='lower right', fontsize=11, frameon=True, 
            edgecolor='black', fancybox=False, shadow=False)

    # 设置刻度朝内（论文风格）
    ax.tick_params(direction='in', which='both', top=True, right=True)

    # 设置边框
    for spine in ax.spines.values():
        spine.set_linewidth(1.2)
        spine.set_color('black')


    plt.tight_layout()
    plt.show()
    plt.savefig(output_file)

    print("\n处理完成！")

if __name__ == '__main__':

    cases = {
        "aps-v2-b4-8MB": "/home/dcn1/fxb/simulator/output/aps-v2-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAll2All_1024g_EP8_8M",
        "aps-v2-b4-32MB": "/home/dcn1/fxb/simulator/output/aps-v2-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAll2All_1024g_EP8_32M"
    }
    # cases = {
    #     'aps-v2-fattree-allreduce_512M': '/home/dcn1/fxb/simulator/output/5ooo-class/fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M/aps-v2-b306_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M',
    #     'rps-fattree-allreduce_512M': '/home/dcn1/fxb/simulator/output/5ooo-class/fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M/rps-b306_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M'
    # }    
    # cases = {
    #     'rps-fattree-allreduce_512M': '/home/dcn1/fxb/simulator/output/5ooo-class/fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M/rps-b16_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M'
    # }    
    cases_list = []

    for label, data_dir in cases.items():
        fct_data = data_dir + '/fct.txt'
        cases_list.append((fct_data, label))


    # output_file = "/home/dcn1/fxb/simulator/output/1all_figures/fattree-allreduce_128M_ooo_cdf.pdf"
    output_dir = "/home/dcn1/fxb/simulator/output/1all_figures"
    output_file = output_dir + "/fct_cdf.pdf"

    plot_cdf(cases_list, output_file)