#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import defaultdict

# ==============================
# 1. 解析 Fat-tree 拓扑（区分交换机 / 服务器）
# ==============================
def parse_topology(topology_file):
    """
    返回：
    switch_ports[sw][neighbor] = port_id
    switch_set = 所有交换机 ID
    """
    switch_ports = defaultdict(dict)
    port_counter = defaultdict(int)

    with open(topology_file, 'r') as f:
        lines = [line.strip() for line in f]
    

    # 第二行：交换机 ID
    switch_set = set(lines[1].split())

    # 第三行起：连接关系
    for line in lines[2:]:
        a = line.split()[0]
        b = line.split()[1]

        # a 是交换机：为 a 分配端口
        if a in switch_set:
            if b not in switch_ports[a]:
                port_counter[a] += 1
                switch_ports[a][b] = port_counter[a]

        # b 是交换机：为 b 分配端口
        if b in switch_set:
            if a not in switch_ports[b]:
                port_counter[b] += 1
                switch_ports[b][a] = port_counter[b]

    return switch_ports, switch_set


# ==============================
# 2. 补全 pathID2Switch 中的端口信息
# ==============================
def enrich_paths_with_ports(path_file, switch_ports, output_file):
    """
    输出每条路径中：
    交换机(port) -> 交换机(port)
    """
    with open(path_file, 'r') as fin, open(output_file, 'w') as fout:
        fout.write(f"pathID sw1ID sw1Port -> sw2ID sw2Port -> ... -> dst\n")
        for line in fin:
            line = line.strip()
            if not line:
                continue

            tokens = line.split()
            pid = tokens[0]
            switches = tokens[1:]

            fout.write(f"{pid}")

            for i in range(len(switches) - 1):
                src = switches[i]
                dst = switches[i + 1]

                if dst not in switch_ports[src]:
                    raise RuntimeError(
                        f"Topology error: no link {src} -> {dst}"
                    )

                src_port = switch_ports[src][dst]

                fout.write(
                    f" {src} {src_port}"
                )

            fout.write("\n")


# ==============================
# 3. Main
# ==============================
if __name__ == "__main__":
    case_file = "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
    topology_file = case_file + "/" + case_file.split("-")[-2]
    path_file = case_file + "/" + "pathID2Switch"
    output_file = case_file + "/" + "pathID2Switch_with_ports.txt"

    switch_ports, switch_set = parse_topology(topology_file)
    enrich_paths_with_ports(path_file, switch_ports, output_file)



    print(f"Done. Output written to {output_file}")

