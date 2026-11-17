#!/usr/bin/env python3
"""
generate_fat_tree.py

生成 fat-tree 拓扑并写入文本文件。
要求：
1. 节点编号顺序：server -> NVSwitch -> ToR -> Agg -> Core
2. NVSwitch 仅与服务器互联，不与任何交换机互联
3. NVSwitch 链路带宽 2880Gbps, 延迟 0.000025ms; 其他链路带宽 400Gbps, 延迟 0.0005ms
"""

import argparse

def generate_fat_tree(args):
    k = args.fat_tree_k
    gps = args.gpu_per_server
    gpu = args.gpu_version
    out_dir_path = args.out_dir_path
    
    if k % 2 != 0:
        raise ValueError("k must be even for fat-tree")
    if (k // 2) % gps != 0:
        raise ValueError("k/2 must be divisible by gps (gpu per server)")

    pods = k
    hosts = k**3 // 4  # total servers (GPU)
    num_edge = k * (k // 2)  # ToR
    num_agg = k * (k // 2)   # Agg
    num_core = (k // 2) ** 2

    # NVSwitch: 8 servers per NVSwitch
    nv_group_size = gps
    num_nvswitch = (hosts + nv_group_size - 1) // nv_group_size

    # numbering ranges
    server_start = 0
    server_end = hosts - 1

    nv_start = hosts
    nv_end = nv_start + num_nvswitch - 1

    tor_start = nv_end + 1
    tor_end = tor_start + num_edge - 1

    agg_start = tor_end + 1
    agg_end = agg_start + num_agg - 1

    core_start = agg_end + 1
    core_end = core_start + num_core - 1

    total_nodes = hosts + num_nvswitch + (num_edge + num_agg + num_core)
    total_switches = num_edge + num_agg + num_core

    # params
    nv_band = "2880Gbps"
    nv_delay = "0.000025ms"
    other_band = "400Gbps"
    other_delay = "0.0005ms"

    edges = []

    # -------- server <-> NVSwitch --------
    for sid in range(hosts):
        nv_idx = sid // nv_group_size
        nv_id = nv_start + nv_idx
        edges.append((sid, nv_id, nv_band, nv_delay, 0))

    # -------- server <-> ToR --------
    servers = []
    s_id = 0
    hosts_per_edge = k // 2
    for pod in range(pods):
        for edge in range(k // 2):
            for h in range(hosts_per_edge):
                servers.append((s_id, pod, edge, h))
                s_id += 1

    for s in servers:
        sid, pod, edge, _ = s
        tor_id = tor_start + pod * (k // 2) + edge
        edges.append((sid, tor_id, other_band, other_delay, 0))

    # -------- ToR <-> Agg --------
    for pod in range(pods):
        for edge in range(k // 2):
            tor_id = tor_start + pod * (k // 2) + edge
            for a_in_pod in range(k // 2):
                agg_id = agg_start + pod * (k // 2) + a_in_pod
                edges.append((tor_id, agg_id, other_band, other_delay, 0))

    # -------- Agg <-> Core --------
    core_ids = list(range(core_start, core_end + 1))
    group_size = k // 2
    core_matrix = [core_ids[i*group_size:(i+1)*group_size] for i in range(group_size)]

    for pod in range(pods):
        for a_in_pod in range(k // 2):
            agg_id = agg_start + pod * (k // 2) + a_in_pod
            core_row = core_matrix[a_in_pod]
            for c in core_row:
                edges.append((agg_id, c, other_band, other_delay, 0))

    # -------- output --------
    header_line = f"{total_nodes} {nv_group_size} {num_nvswitch} {total_switches} {len(edges)} {gpu}"
    nvswitch_ids = list(range(nv_start, nv_end + 1))
    switch_ids = list(range(tor_start, tor_end + 1)) + list(range(agg_start, agg_end + 1)) + list(range(core_start, core_end + 1))
    second_line = " ".join(str(x) for x in (nvswitch_ids + switch_ids))

    edge_lines = [f"{a} {b} {bw} {delay} {err}" for (a, b, bw, delay, err) in edges]
    out_file_path = out_dir_path + "fattree_k{}_{}g_{}gps_{}_{}".format(k, hosts, gps, other_band, gpu)

    return header_line, second_line, edge_lines, out_file_path

def write_topology_file(out_path, header, second, edges):
    with open(out_path, "w") as f:
        f.write(header + "\n")
        f.write(second + "\n")
        for line in edges:
            f.write(line + "\n")
    print(f"Topology written to {out_path}")

def parse_args():
    p = argparse.ArgumentParser(description="Generate fat-tree topology with NVSwitch (only server interconnect).")
    p.add_argument("-k", "--fat-tree-k", type=int, required=True, help="fat-tree parameter k (must be even)")
    p.add_argument("-g", "--gpu-per-server", type=int, required=True, help="gpu number per server")
    p.add_argument("-o", "--out-dir-path", type=str, default="./", help="output dir path")
    p.add_argument("-v", "--gpu-version", type=str, default="A100", help="GPU Version")
    return p.parse_args()

def main():
    args = parse_args()
    header, second, edges, out_file_path = generate_fat_tree(args)
    write_topology_file(out_file_path, header, second, edges)

if __name__ == "__main__":
    main()
