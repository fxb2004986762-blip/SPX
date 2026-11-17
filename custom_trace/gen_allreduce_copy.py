#!/usr/bin/env python3
"""
This script generates traffic flows that approximate a single round of Ring-AllReduce communication.

Functionality:
- GPUs are divided into multiple rings based on the specified group size.
- Within each ring, every GPU sends one flow to its next neighbor (forming a logical ring).
- Only a single communication round is modeled (no multi-round pipeline or chunking).
- The generated flows are written to a file in the format:
  src dst 3 flow_size start_time 0

Parameters:
- nodes:        Total number of GPUs in the system.
- groupsize:    Number of GPUs in each ring (must divide nodes).
- flowsize:     Size of each flow in bytes.
- start_time:   Flow start time in microseconds (will be converted to seconds in output).
- locality:     Ring construction strategy:
                  "local"  - contiguous GPUs form a ring (better locality)
                  "global" - GPUs are distributed across rings (higher network stress)
- output_file:  Path to the output file storing generated flows.

Example:
    python gen_allreduce.py 8 4 1000000 2000000 local flows.txt

This example:
- Creates 2 rings with 4 GPUs each from 8 GPUs total
- Each GPU sends a 1 MB flow to its neighbor
- All flows start at 2.0 seconds
- Output is written to 'flows.txt'
"""

import sys


def build_rings(nodes, groupsize, locality):
    rings = []

    if locality == "1":
        # 连续分组（局部性强）
        for i in range(0, nodes, groupsize):
            rings.append(list(range(i, i + groupsize)))

    elif locality == "0":
        # 跨节点分布（最大化网络压力）
        num_groups = nodes // groupsize
        rings = [[] for _ in range(num_groups)]

        for i in range(nodes):
            rings[i % num_groups].append(i)

    else:
        raise ValueError("locality must be 'local' or 'global'")

    return rings


def gen_single_round_flows(nodes, groupsize, flowsize, start_time_us, locality):
    if nodes % groupsize != 0:
        raise ValueError("nodes must be divisible by groupsize")

    rings = build_rings(nodes, groupsize, locality)

    # us → s
    start_time_s = start_time_us / 1e6

    flows = []

    for ring in rings:
        N = len(ring)

        for i in range(N):
            src = ring[i]
            dst = ring[(i + 1) % N]

            # 单轮：直接发送完整flowsize（不再拆chunk）
            flows.append((src, dst, flowsize, start_time_s))

    return flows


def main():
    if len(sys.argv) != 7:
        print("Usage: python gen_allreduce.py <nodes> <groupsize> <flowsize> <start_time(us)> <locality> <output_file>")
        sys.exit(1)

    output_file = sys.argv[1]
    nodes = int(sys.argv[2])
    groupsize = int(sys.argv[3])
    flowsize = int(sys.argv[4])
    start_time_us = float(sys.argv[5])
    locality = sys.argv[6]

    flows = gen_single_round_flows(
        nodes, groupsize, flowsize, start_time_us, locality
    )

    with open(output_file, "w") as f:
        f.write("{}\n".format(len(flows)))  # 写入流数量
        for (src, dst, size, t) in flows:
            # 输出格式：
            # 源节点 目的节点 3 流量大小 开始时间 0
            f.write(f"{src} {dst} 3 {size} {t:.9f} 0\n")


if __name__ == "__main__":
    main()