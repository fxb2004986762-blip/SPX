import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

# 设置论文级别的绘图风格
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman'] + plt.rcParams['font.serif']
plt.rcParams['font.size'] = 11
plt.rcParams['axes.linewidth'] = 1.2
plt.rcParams['grid.linewidth'] = 0.8
plt.rcParams['lines.linewidth'] = 1.5
plt.rcParams['patch.linewidth'] = 0.8
plt.rcParams['xtick.major.width'] = 1.2
plt.rcParams['ytick.major.width'] = 1.2
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42

def parse_fct_file(filename):
    """
    解析FCT文件
    返回格式: list of dict，每个dict包含流量的所有信息
    """
    flows = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 7:
                flow = {
                    'src_id': int(parts[0]),
                    'dst_id': int(parts[1]),
                    'src_port': int(parts[2]),
                    'bytes': int(parts[4]),
                    'start_time': int(parts[5]),
                    'duration': int(parts[6]),
                    'end_time': int(parts[5]) + int(parts[6])
                }
                flows.append(flow)
    return flows

def plot_flow_timeline(filename, src_id, dst_id, port_range=None, out_file=None,  figsize=(10, 6)):
    """
    绘制指定发端和收端组合的流量传输时刻表
    
    参数:
        filename: FCT数据文件路径
        src_id: 发端ID
        dst_id: 收端ID
        port_range: 源端口号范围，格式为(min_port, max_port)，None表示不限制
        out_file: 输出PDF文件路径，None表示只显示不保存
        figsize: 图像尺寸
    """
    # 解析数据
    flows = parse_fct_file(filename)
    
    # 筛选符合条件的流量
    filtered_flows = []
    for flow in flows:
        if flow['src_id'] == src_id and flow['dst_id'] == dst_id:
            # if port_range is None or (port_range[0] <= flow['src_port'] <= port_range[1]):
            if port_range is None or (flow['src_port'] in port_range):
                filtered_flows.append(flow)
    
    if not filtered_flows:
        print(f"未找到满足条件的流量: src={src_id}, dst={dst_id}, port_range={port_range}")
        return
    
    # 按源端口号排序
    filtered_flows.sort(key=lambda x: x['src_port'])
    
    # 获取所有唯一的源端口号
    src_ports = sorted(set(flow['src_port'] for flow in filtered_flows))
    port_to_y = {port: idx for idx, port in enumerate(src_ports)}
    
    # 计算时间范围（转换为合适的单位）
    min_time = min(flow['start_time'] for flow in filtered_flows)
    max_time = max(flow['end_time'] for flow in filtered_flows)
    time_range = max_time - min_time
    
    # 自适应时间单位
    if time_range < 1e6:  # < 1ms
        time_unit = 1e3
        time_label = '(μs)'
    elif time_range < 1e9:  # < 1s
        time_unit = 1e6
        time_label = '(ms)'
    else:
        time_unit = 1e9
        time_label = '(s)'
    
    # 创建图像
    fig, ax = plt.subplots(figsize=figsize, dpi=300)
    
    # 使用更专业的配色方案
    colors = plt.cm.Set2(np.linspace(0, 1, 8))
    
    for idx, flow in enumerate(filtered_flows):
        y_pos = port_to_y[flow['src_port']]
        start = (flow['start_time'] - min_time) / time_unit
        duration = flow['duration'] / time_unit
        
        # 绘制横向条形
        rect = Rectangle((start, y_pos - 0.4), duration, 0.8,
                         facecolor=colors[idx % len(colors)],
                         edgecolor='black', linewidth=0.6, alpha=0.85)
        ax.add_patch(rect)
    
    # 设置坐标轴标签
    xlabel = f'src:{src_id} → dst:{dst_id} Flow Timeline ' + time_label
    ax.set_xlabel(xlabel, fontsize=13, fontweight='normal')
    ax.set_ylabel('Source Port', fontsize=13, fontweight='normal')
    # ax.set_title(f'Flow Timeline: {src_id} → {dst_id}', 
    #              fontsize=14, fontweight='bold', pad=15)
    
    # 设置y轴刻度
    ax.set_ylim(-0.5, len(src_ports) - 0.5)
    ax.set_yticks(range(len(src_ports)))
    ax.set_yticklabels(src_ports, fontsize=10)
    
    # 设置x轴范围和刻度
    x_margin = time_range / time_unit * 0.02
    ax.set_xlim(-x_margin, (max_time - min_time) / time_unit + x_margin)
    ax.tick_params(axis='x', labelsize=10)
    
    # 精简的网格线
    ax.grid(True, axis='x', alpha=0.25, linestyle='-', linewidth=0.5, color='gray')
    ax.set_axisbelow(True)
    
    # 美化边框
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    
    plt.tight_layout()
    
    # 保存或显示
    if out_file:
        plt.savefig(out_file, format='pdf', bbox_inches='tight', dpi=300)
        print(f"\n图像已保存至: {out_file}")
    
    plt.show()
    
    # 打印统计信息
    print(f"\n===== 流量统计 =====")
    print(f"发端 → 收端: {src_id} → {dst_id}")
    print(f"流量数量: {len(filtered_flows)}")
    print(f"源端口范围: {min(src_ports)} - {max(src_ports)}")
    # print(f"总传输字节: {total_bytes:,}")
    print(f"时间跨度: {time_range / time_unit:.2f} {time_label.split('(')[1].strip(')')}")


# 使用示例
if __name__ == "__main__":
    # data_dir = "/home/dcn1/fxb/simulator/output/5ooo-class/fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M/rps-b8_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M"
    # 数据文件所在目录
    data_dir = "/home/dcn1/fxb/simulator/output/aps-v2_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_1024M"

    fct_file = data_dir + "/fct.txt"
    # src_id = 511
    # dst_id = 519
    src_id = 699
    dst_id = 707
    port_pair = (10000, 10031) # (start_port, end_port)
    port_pair = (10095, 10127)
    # port_pair = (10223, 10254)
    STEP = 1
    port_list = list(range(port_pair[0], port_pair[1], STEP))

    out_file = data_dir + f"/{src_id}->{dst_id}:{port_pair[0]}-flow_lifecycle.pdf"

    # 示例1: 绘制283->291的所有流量
    # plot_flow_timeline(fct_file, out_file, src_id=src_id, dst_id=dst_id)
    
    # 示例2: 绘制283->291，端口号在10000-10010范围内的流量
    plot_flow_timeline(fct_file, src_id=src_id, dst_id=dst_id, out_file=out_file, 
                      port_range=port_list)
    