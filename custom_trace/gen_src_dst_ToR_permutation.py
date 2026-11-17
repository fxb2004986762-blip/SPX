#!/usr/bin/env python3
"""
generate_tor_to_tor_traffic.py

Generate simple ToR-to-ToR traffic for ns-3.

Assumptions
-----------
1. GPU/node IDs are contiguous and grouped by ToR.
2. ToR IDs are zero-based.
3. Each ToR contains exactly n nodes.
4. The first line of the output file is the number of flows.
5. Each flow line uses the format:

       src dst 3 flow_size start_time 0

Example
-------
For:
    src_tor = 0
    dst_tor = 1
    nodes_per_tor = 128
    flows = 128

the generated mappings are:

    0   -> 128
    1   -> 129
    2   -> 130
    ...
    127 -> 255
"""

import argparse
import os


def generate_tor_to_tor_traffic(args):
    src_tor = args.src_tor
    dst_tor = args.dst_tor
    nodes_per_tor = args.nodes_per_tor
    flows = args.flows
    flow_size = args.flow_size
    start_time_us = args.start_time_us
    output = args.output

    # ------------------------------------------------------------
    # Parameter validation
    # ------------------------------------------------------------
    if src_tor < 0:
        raise ValueError("src_tor must be >= 0")

    if dst_tor < 0:
        raise ValueError("dst_tor must be >= 0")

    if src_tor == dst_tor:
        raise ValueError("src_tor and dst_tor must be different")

    if nodes_per_tor <= 0:
        raise ValueError("nodes_per_tor must be > 0")

    if flows <= 0:
        raise ValueError("flows must be > 0")

    if flow_size <= 0:
        raise ValueError("flow_size must be > 0")

    if start_time_us < 0:
        raise ValueError("start_time_us must be >= 0")

    # ------------------------------------------------------------
    # Node-ID ranges
    #
    # ToR 0: [0, n-1]
    # ToR 1: [n, 2n-1]
    # ToR 2: [2n, 3n-1]
    # ...
    # ------------------------------------------------------------
    src_start = src_tor * nodes_per_tor
    dst_start = dst_tor * nodes_per_tor

    # Convert us to seconds because the trace uses seconds.
    start_time_sec = start_time_us * 1e-6

    flow_lines = []

    # ------------------------------------------------------------
    # Flow generation
    #
    # Flow i:
    #   src = src_start + (i % nodes_per_tor)
    #   dst = dst_start + (i % nodes_per_tor)
    #
    # Therefore:
    #
    #   flows <= n:
    #       use the first 'flows' node pairs once.
    #
    #   flows > n:
    #       wrap around and generate another round of flows.
    #
    # Example, n=4, flows=6:
    #
    #   0 -> 4
    #   1 -> 5
    #   2 -> 6
    #   3 -> 7
    #   0 -> 4
    #   1 -> 5
    # ------------------------------------------------------------
    for i in range(flows):
        local_id = i % nodes_per_tor

        src = src_start + local_id
        dst = dst_start + local_id

        line = (
            f"{src} "
            f"{dst} "
            f"3 "
            f"{flow_size} "
            f"{start_time_sec:.9f} "
            f"0"
        )

        flow_lines.append(line)

    # ------------------------------------------------------------
    # Write output
    # ------------------------------------------------------------
    parent_dir = os.path.dirname(output)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    with open(output, "w") as f:
        # According to the trace format supplied by the user,
        # the first line is the number of generated flows.
        f.write(f"{flows}\n")

        for line in flow_lines:
            f.write(line + "\n")

    # ------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------
    print("========== ToR-to-ToR Traffic ==========")
    print(f"Output file      : {output}")
    print(f"Source ToR       : {src_tor}")
    print(f"Destination ToR  : {dst_tor}")
    print(f"Nodes per ToR    : {nodes_per_tor}")
    print(
        f"Source node IDs  : "
        f"{src_start} ~ {src_start + nodes_per_tor - 1}"
    )
    print(
        f"Dest node IDs    : "
        f"{dst_start} ~ {dst_start + nodes_per_tor - 1}"
    )
    print(f"Flows            : {flows}")
    print(f"Flow size        : {flow_size} bytes")
    print(
        f"Flow size        : "
        f"{flow_size / (1024 * 1024):.3f} MiB"
    )
    print(f"Start time       : {start_time_us} us")
    print("========================================")


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Generate simple one-to-one ToR-to-ToR traffic "
            "for an ns-3 traffic trace."
        )
    )

    parser.add_argument(
        "-s",
        "--src-tor",
        type=int,
        required=True,
        help="source ToR index, starting from 0",
    )

    parser.add_argument(
        "-d",
        "--dst-tor",
        type=int,
        required=True,
        help="destination ToR index, starting from 0",
    )

    parser.add_argument(
        "-n",
        "--nodes-per-tor",
        type=int,
        required=True,
        help="number of GPU/nodes under each ToR",
    )

    parser.add_argument(
        "-m",
        "--flows",
        type=int,
        required=True,
        help="number of flows to generate",
    )

    parser.add_argument(
        "-f",
        "--flow-size",
        type=int,
        default=1048576,
        help="flow size in bytes, default: 1048576 (1 MiB)",
    )

    parser.add_argument(
        "-t",
        "--start-time-us",
        type=float,
        default=5.0,
        help="flow start time in microseconds, default: 5 us",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="output traffic trace file",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    generate_tor_to_tor_traffic(args)


if __name__ == "__main__":
    main()
