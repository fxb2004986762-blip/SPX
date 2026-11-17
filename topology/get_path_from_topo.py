import sys
from collections import defaultdict, deque

def parse_topology(filename):
    """解析拓扑文件"""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # 跳过第一行
    # 第二行获取交换机ID列表
    switch_ids = list(map(int, lines[1].split()))
    num_hosts = switch_ids[0] - 1  # 第一个数字是主机数量-1，实际主机ID为0到这个数字
    
    # 构建图结构
    # graph[node] = [(neighbor, port_on_node, port_on_neighbor), ...]
    graph = defaultdict(list)
    
    # 端口计数器，key为节点ID，value为该节点已分配的端口数
    port_counter = defaultdict(int)
    
    # 从第三行开始解析连接关系
    for line in lines[2:]:
        parts = line.strip().split()
        if len(parts) < 2:
            continue
        
        node1 = int(parts[0])
        node2 = int(parts[1])
        bw = str(parts[2])
        
        # 为node1分配端口号
        port_counter[node1] += 1
        port_on_node1 = port_counter[node1]
        
        # 为node2分配端口号
        port_counter[node2] += 1
        port_on_node2 = port_counter[node2]
        
        # 添加双向连接
        graph[node1].append((node2, port_on_node1, port_on_node2, bw))
        graph[node2].append((node1, port_on_node2, port_on_node1, bw))
    
    return graph, num_hosts

def find_all_shortest_paths(graph, src, dst):
    """使用BFS查找所有最短路径"""
    if src == dst:
        return [[src]], [[]]
    
    # BFS找到最短路径长度
    queue = deque([(src, [src], [])])  # (当前节点, 路径节点列表, 路径端口信息列表)
    visited = {src: 0}  # 记录到达每个节点的最短距离
    all_paths = []
    all_port_info = []
    shortest_length = None
    
    while queue:
        current, path, port_info = queue.popleft()
        
        # 如果已经找到最短路径，且当前路径更长，则停止
        if shortest_length is not None and len(path) > shortest_length:
            continue
        
        for neighbor, port_on_current, port_on_neighbor, bw in graph[current]:
            new_path = path + [neighbor]
            new_port_info = port_info + [(current, port_on_current, neighbor, port_on_neighbor, bw)]
            
            # 到达目的地
            if neighbor == dst:
                if shortest_length is None:
                    shortest_length = len(new_path)
                    all_paths.append(new_path)
                    all_port_info.append(new_port_info)
                elif len(new_path) == shortest_length:
                    all_paths.append(new_path)
                    all_port_info.append(new_port_info)
                continue
            
            # 检查是否应该继续探索这个节点
            if neighbor not in visited:
                visited[neighbor] = len(new_path)
                queue.append((neighbor, new_path, new_port_info))
            elif visited[neighbor] == len(new_path):
                # 相同长度的路径，继续探索
                queue.append((neighbor, new_path, new_port_info))
    
    return all_paths, all_port_info

def format_output(src, dst, path, port_info):
    """
    格式化输出 - 只输出交换机的出端口
    输出格式：源主机ID 交换机1_ID 交换机1_出端口 交换机2_ID 交换机2_出端口 ... 目的主机ID
    """
    if path is None or len(path) == 0:
        return None
    
    if len(path) == 1:  # 源和目的相同
        return str(src)
    
    result = [str(src)]
    
    # path中第一个是源主机，最后一个是目的主机，中间都是交换机
    # port_info包含了每一跳的端口信息
    
    # 遍历path中的交换机节点（跳过源主机和目的主机）
    for i in range(1, len(path) - 1):
        switch_id = path[i]
        result.append(str(switch_id))
        
        # 找到该交换机的出端口（连接到下一个节点）
        # port_info[i] 表示从 path[i] 到 path[i+1] 的连接信息
        node1, port1, node2, port2, bw = port_info[i]
        # node1 应该是当前交换机，port1 是出端口
        result.append(str(port1) + " (" + str(bw) + ")")  # 可以选择是否输出带宽信息
    
    # 添加目的主机
    result.append(str(dst))
    
    return ' '.join(result)

def main():
    # 读取拓扑文件 (修改为你的拓扑文件名)
    topology_file = '/home/dell/sjw/lb/simulator/topology/SpectrumX_1024g_8gps_400Gbps_A100' 
    topology_file = '/home/dell/sjw/lb/simulator/topology/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100'  
    # topology_file = '/home/dell/sjw/lb/simulator/topology/fattree_k16_1024g_8gps_400Gbps_A100'  
    
    print(f"正在解析拓扑: {topology_file.split('/')[-1]}")
    graph, num_hosts = parse_topology(topology_file)
    print(f"拓扑解析完成，主机数量: {num_hosts + 1} (ID: 0-{num_hosts})")
    
    # 交互式查询
    print("\n请输入查询 (格式: 源主机ID 目的主机ID)，输入 'quit' 退出:")
    
    while True:
        try:
            user_input = input("> ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            parts = user_input.split()
            if len(parts) != 2:
                print("输入格式错误，请输入: 源主机ID 目的主机ID")
                continue
            
            src = int(parts[0])
            dst = int(parts[1])
            
            # 查找所有最短路径
            all_paths, all_port_info = find_all_shortest_paths(graph, src, dst)
            
            if len(all_paths) == 0:
                print(f"无法找到从主机{src}到主机{dst}的路径")
            else:
                print(f"找到 {len(all_paths)} 条等长最短路径:")
                for i, (path, port_info) in enumerate(zip(all_paths, all_port_info), 1):
                    output = format_output(src, dst, path, port_info)
                    if output:
                        print(f"路径{i}: {output}")
            
        except ValueError:
            print("请输入有效的数字")
        except KeyboardInterrupt:
            print("\n程序退出")
            break
        except Exception as e:
            print(f"发生错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()