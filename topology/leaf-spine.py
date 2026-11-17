#!/usr/bin/env python3
"""
generate_leaf_spine.py

生成 Leaf-Spine 拓扑并写入文本文件。

节点编号顺序：
    GPU -> NVSwitch -> ToR(Leaf) -> Spine

拓扑结构：
    1. 每张 GPU 连接一个 ToR
    2. 每台服务器内部的 GPU 连接一个 NVSwitch
    3. NVSwitch 仅连接服务器内部 GPU，不连接 ToR/Spine
    4. 每个 ToR 与所有 Spine 互联

收敛比定义：
    convergence_ratio = ToR下行总带宽 / ToR上行总带宽

例如：
    每个 ToR 8 张 GPU，单链路均为 400Gbps：

    1:1 -> 8 条 ToR 上行 -> 8 个 Spine
    2:1 -> 4 条 ToR 上行 -> 4 个 Spine
    4:1 -> 2 条 ToR 上行 -> 2 个 Spine

默认链路参数：
    GPU <-> NVSwitch : 2880Gbps, 0.000025ms
    GPU <-> ToR      : 400Gbps,  0.0005ms
    ToR <-> Spine    : 400Gbps,  0.0005ms
"""

import argparse
import os
from fractions import Fraction


def parse_convergence_ratio(value):
    """
    支持以下写法：
        1
        2
        4
        1:1
        2:1
        4:1
        1.5

    返回：
        Fraction

    定义：
        ratio = downlink_bandwidth / uplink_bandwidth
    """
    value = value.strip()

    try:
        if ":" in value:
            down, up = value.split(":")
            down = Fraction(down)
            up = Fraction(up)

            if down <= 0 or up <= 0:
                raise ValueError

            return down / up

        ratio = Fraction(value)

        if ratio <= 0:
            raise ValueError

        return ratio

    except (ValueError, ZeroDivisionError):
        raise argparse.ArgumentTypeError(
            "Invalid convergence ratio. "
            "Use formats such as 1:1, 2:1, 4:1, 2, or 1.5"
        )


def generate_leaf_spine(args):
    num_tor = args.num_tor
    gpu_per_tor = args.gpu_per_tor
    gps = args.gpu_per_server
    convergence_ratio = args.convergence_ratio
    gpu = args.gpu_version
    out_dir_path = args.out_dir_path

    # ------------------------------------------------------------
    # Parameter checking
    # ------------------------------------------------------------

    if num_tor <= 0:
        raise ValueError("num_tor must be greater than 0")

    if gpu_per_tor <= 0:
        raise ValueError("gpu_per_tor must be greater than 0")

    if gps <= 0:
        raise ValueError("gpu_per_server must be greater than 0")

    # 保证一台服务器不会跨两个 ToR
    if gpu_per_tor % gps != 0:
        raise ValueError(
            "gpu_per_tor must be divisible by gpu_per_server, "
            "otherwise one server may span multiple ToRs"
        )

    # ------------------------------------------------------------
    # Calculate topology scale
    # ------------------------------------------------------------

    # GPU 总数
    num_gpu = num_tor * gpu_per_tor

    # 每 gps 张 GPU 构成一台服务器，对应一个 NVSwitch
    num_nvswitch = num_gpu // gps

    # 每 ToR 下行端口数量
    num_downlinks_per_tor = gpu_per_tor

    #
    # convergence_ratio =
    #
    #       downlink bandwidth
    #     ----------------------
    #        uplink bandwidth
    #
    # 因为上下行单链路都是 400Gbps，所以：
    #
    #     num_uplinks =
    #         num_downlinks / convergence_ratio
    #
    uplink_fraction = (
        Fraction(num_downlinks_per_tor, 1) / convergence_ratio
    )

    if uplink_fraction.denominator != 1:
        raise ValueError(
            f"Cannot exactly construct convergence ratio "
            f"{convergence_ratio} with {gpu_per_tor} GPUs per ToR.\n"
            f"Required uplinks per ToR = {uplink_fraction}.\n"
            f"Please choose parameters that produce an integer "
            f"number of uplinks."
        )

    num_uplinks_per_tor = int(uplink_fraction)

    if num_uplinks_per_tor <= 0:
        raise ValueError(
            "Calculated uplinks per ToR must be greater than 0"
        )

    #
    # 简单 Leaf-Spine：
    #
    # 每个 ToR 与所有 Spine 各连接一条链路。
    #
    # 因此：
    #
    #     Spine 数量 = 每 ToR 上行链路数量
    #
    num_spine = num_uplinks_per_tor

    # ------------------------------------------------------------
    # Node numbering
    #
    # GPU -> NVSwitch -> ToR -> Spine
    # ------------------------------------------------------------

    gpu_start = 0
    gpu_end = gpu_start + num_gpu - 1

    nv_start = gpu_end + 1
    nv_end = nv_start + num_nvswitch - 1

    tor_start = nv_end + 1
    tor_end = tor_start + num_tor - 1

    spine_start = tor_end + 1
    spine_end = spine_start + num_spine - 1

    total_switches = num_tor + num_spine

    total_nodes = (
        num_gpu
        + num_nvswitch
        + num_tor
        + num_spine
    )

    # ------------------------------------------------------------
    # Link parameters
    # ------------------------------------------------------------

    nv_band = "2880Gbps"
    nv_delay = "0.000025ms"

    other_band = "400Gbps"
    other_delay = "0.0005ms"

    edges = []

    # ------------------------------------------------------------
    # GPU <-> NVSwitch
    # ------------------------------------------------------------

    for gpu_id in range(num_gpu):
        nv_idx = gpu_id // gps
        nv_id = nv_start + nv_idx

        edges.append(
            (
                gpu_id,
                nv_id,
                nv_band,
                nv_delay,
                0,
            )
        )

    # ------------------------------------------------------------
    # GPU <-> ToR
    #
    # 每 gpu_per_tor 张 GPU 属于一个 ToR
    # ------------------------------------------------------------

    for gpu_id in range(num_gpu):
        tor_idx = gpu_id // gpu_per_tor
        tor_id = tor_start + tor_idx

        edges.append(
            (
                gpu_id,
                tor_id,
                other_band,
                other_delay,
                0,
            )
        )

    # ------------------------------------------------------------
    # ToR <-> Spine
    #
    # Full bipartite Leaf-Spine topology
    #
    # 每个 ToR 都连接全部 Spine
    # ------------------------------------------------------------

    for tor_idx in range(num_tor):
        tor_id = tor_start + tor_idx

        for spine_idx in range(num_spine):
            spine_id = spine_start + spine_idx

            edges.append(
                (
                    tor_id,
                    spine_id,
                    other_band,
                    other_delay,
                    0,
                )
            )

    # ------------------------------------------------------------
    # Output header
    #
    # 保持与你原 Fat-Tree 文件完全一致：
    #
    # total_nodes
    # gpu_per_server
    # num_nvswitch
    # total_switches
    # num_links
    # gpu_version
    # ------------------------------------------------------------

    header_line = (
        f"{total_nodes} "
        f"{gps} "
        f"{num_nvswitch} "
        f"{total_switches} "
        f"{len(edges)} "
        f"{gpu}"
    )

    # NVSwitch + network switches
    nvswitch_ids = list(
        range(nv_start, nv_end + 1)
    )

    switch_ids = (
        list(range(tor_start, tor_end + 1))
        + list(range(spine_start, spine_end + 1))
    )

    second_line = " ".join(
        str(x)
        for x in (nvswitch_ids + switch_ids)
    )

    edge_lines = [
        f"{a} {b} {bw} {delay} {err}"
        for (a, b, bw, delay, err) in edges
    ]

    # ------------------------------------------------------------
    # Output filename
    # ------------------------------------------------------------

    ratio_str = (
        f"{convergence_ratio.numerator}"
        if convergence_ratio.denominator == 1
        else
        f"{convergence_ratio.numerator}to"
        f"{convergence_ratio.denominator}"
    )

    out_file_name = (
        f"leafspine_"
        f"{num_tor}tor_"
        f"{num_gpu}g_"
        f"{gpu_per_tor}gptor_"
        f"{gps}gps_"
        f"{ratio_str}conv_"
        f"{other_band}_"
        f"{gpu}"
    )

    out_file_path = os.path.join(
        out_dir_path,
        out_file_name
    )

    # ------------------------------------------------------------
    # Print topology information
    # ------------------------------------------------------------

    actual_downlink_bw = (
        gpu_per_tor * 400
    )

    actual_uplink_bw = (
        num_uplinks_per_tor * 400
    )

    print("========== Leaf-Spine Topology ==========")
    print(f"GPU number             : {num_gpu}")
    print(f"GPU per server         : {gps}")
    print(f"Server / NVSwitch      : {num_nvswitch}")
    print(f"ToR number             : {num_tor}")
    print(f"GPU per ToR            : {gpu_per_tor}")
    print(f"Spine number           : {num_spine}")
    print(
        f"Uplinks per ToR        : "
        f"{num_uplinks_per_tor}"
    )
    print(
        f"Downlink BW per ToR    : "
        f"{actual_downlink_bw} Gbps"
    )
    print(
        f"Uplink BW per ToR      : "
        f"{actual_uplink_bw} Gbps"
    )
    print(
        f"Convergence ratio      : "
        f"{actual_downlink_bw / actual_uplink_bw:.4f}:1"
    )
    print(f"Total switches         : {total_switches}")
    print(f"Total nodes            : {total_nodes}")
    print(f"Total links            : {len(edges)}")
    print("=========================================")

    return (
        header_line,
        second_line,
        edge_lines,
        out_file_path,
    )


def write_topology_file(
    out_path,
    header,
    second,
    edges,
):
    os.makedirs(
        os.path.dirname(out_path) or ".",
        exist_ok=True,
    )

    with open(out_path, "w") as f:
        f.write(header + "\n")
        f.write(second + "\n")

        for line in edges:
            f.write(line + "\n")

    print(f"Topology written to {out_path}")


def parse_args():
    p = argparse.ArgumentParser(
        description=(
            "Generate Leaf-Spine topology "
            "with NVSwitch for intra-server GPU interconnect."
        )
    )

    p.add_argument(
        "-t",
        "--num-tor",
        type=int,
        required=True,
        help="number of ToR / Leaf switches",
    )

    p.add_argument(
        "-n",
        "--gpu-per-tor",
        type=int,
        required=True,
        help="number of GPUs connected to each ToR",
    )

    p.add_argument(
        "-g",
        "--gpu-per-server",
        type=int,
        required=True,
        help="number of GPUs per server",
    )

    p.add_argument(
        "-r",
        "--convergence-ratio",
        type=parse_convergence_ratio,
        required=True,
        help=(
            "ToR downlink/uplink convergence ratio, "
            "e.g. 1:1, 2:1, 4:1"
        ),
    )

    p.add_argument(
        "-o",
        "--out-dir-path",
        type=str,
        default="./",
        help="output directory path",
    )

    p.add_argument(
        "-v",
        "--gpu-version",
        type=str,
        default="A100",
        help="GPU version",
    )

    return p.parse_args()


def main():
    args = parse_args()

    (
        header,
        second,
        edges,
        out_file_path,
    ) = generate_leaf_spine(args)

    write_topology_file(
        out_file_path,
        header,
        second,
        edges,
    )


if __name__ == "__main__":
    main()