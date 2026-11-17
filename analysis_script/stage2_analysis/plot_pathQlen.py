import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np
import os

# =========================
# 文件路径
# =========================
basePath = "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
PATH_FILE = basePath + "/" + "pathID2Switch_with_ports.txt"
QLEN_FILE = basePath + "/" + "qlen.txt"
pathQlen_file = basePath + "/" + "pathQlen.txt"

# =========================
# 数据处理，聚合
# =========================
WINDOW_US = 1000          # 1 ms
SAMPLE_US = 50            # 原始采样周期
# allreduce 推荐 20；all2all 推荐 5
step = os.environ.get("STEP", str(WINDOW_US // SAMPLE_US))
STEP = int(step)

def aggregate(series, step, mode="mean"):
    out = []
    for i in range(0, len(series), step):
        chunk = series[i:i + step]
        if not chunk:
            continue
        t0 = chunk[0][0]
        values = [v for _, v in chunk]
        if mode == "mean":
            val = sum(values) / len(values)
        elif mode == "max":
            val = max(values)
        elif mode == "p95":
            values.sort()
            val = values[int(0.95 * len(values))]
        out.append((t0, val))
    return out

# =========================
# 1. 读取路径文件
#    path_id -> list of (sw_id, port_id)
# =========================
paths = {}

with open(PATH_FILE) as f:
    next(f)
    for line in f:
        if "#" in line:
            break
        fields = line.strip().split()
        if not fields or not fields[0].isdigit():
            continue
        path_id = int(fields[0])
        pairs = []
        for i in range(1, len(fields), 2):
            pairs.append((int(fields[i]), int(fields[i + 1])))
        paths[path_id] = pairs

# =========================
# 2. 读取 qlen 文件
#    只保留 q_id == 3
#    (time, sw, port) -> q_len
# =========================
qlen_map = {}
times = set()

with open(QLEN_FILE) as f:
    next(f)
    for line in f:
        if not line.strip() or line.startswith("time"):
            continue
        time, sw, port, qid, qlen, _ = [x.strip() for x in line.split(",")]
        if int(qid) != 3:
            continue
        key = (int(time), int(sw), int(port))
        qlen_map[key] = int(qlen)
        times.add(int(time))

times = sorted(times)
BASE_TIME = times[0]
# =========================
# 3. 统计每条路径在每个时刻的队列字节总和
#    path_id -> list of (time, total_bytes)
# =========================
path_time_series = defaultdict(list)
cached_sw_port_qlen = {}
for path_id, hops in paths.items():
        for t in times:
            total = 0
            for sw, port in hops:
                # 维护一个 上个t时刻 sw port 字节数的缓存
                qlen = qlen_map.get((t, sw, port), -1)
                if qlen == -1:
                    qlen = cached_sw_port_qlen.get((sw, port), 0)
                cached_sw_port_qlen[(sw, port)] = qlen
                total += qlen

            path_time_series[path_id].append((t, total))

# 将路径Qlen数据写入文件
cached_sw_port_qlen = {}
with open(pathQlen_file, 'w') as f:
    f.write(f"time, path_id, qlen\n")
    for t in times:
        for path_id, hops in paths.items():
            total = 0
            for sw, port in hops:
                # 维护一个 上个t时刻 sw port 字节数的缓存
                qlen = qlen_map.get((t, sw, port), -1)
                if qlen == -1:
                    qlen = cached_sw_port_qlen.get((sw, port), 0)
                cached_sw_port_qlen[(sw, port)] = qlen
                total += qlen_map.get((t, sw, port), 0)
            f.write(f"{t} {path_id} {total}\n")


# =========================
# 4. 绘图
# =========================
# plt.figure(figsize=(10, 6))

# # for path_id, series in path_time_series.items():
# #     t_vals = [x[0] for x in series]
# #     y_vals = [x[1] for x in series]
# #     plt.plot(t_vals, y_vals, label=f"Path {path_id}")
# for path_id, series in path_time_series.items():
#     t_vals = [x[0] for x in series]
#     y_vals = [np.log1p(x[1]) for x in series]
#     plt.plot(t_vals, y_vals, label=f"Path {path_id}")


# plt.xlabel("Time")
# plt.ylabel("Total Queue Bytes")
# plt.title("Per-Path Total Queue Occupancy Over Time")
# plt.legend()
# # plt.grid(True)
# plt.grid(True, which="both", linestyle="--", alpha=0.4)
# plt.tight_layout()
# plt.show()

# figname = basePath + "/" + "pathQlen.pdf"
# plt.savefig(figname)

markers = ["o", "s", "^", "x", "D"]
plt.figure(figsize=(16, 6))

for path_id, series in path_time_series.items():
    series = aggregate(series, STEP, mode="mean")
    t_vals = [(t - BASE_TIME) / 1000 for t, _ in series]  # us
    y_vals = [v for _, v in series]
    plt.plot(t_vals, y_vals, label=f"Path {path_id}", marker=markers[path_id % len(markers)], markevery=5)

plt.yscale("log", nonpositive="clip")
plt.xlabel("Time (µs)", fontsize=14)
plt.ylabel("Total Queue Bytes (mean)", fontsize=14)
plt.grid(True, which="both", linestyle="--", alpha=0.4)
plt.tight_layout()
figname = basePath + "/" + "pathQlen.pdf"
plt.legend()
plt.savefig(figname)