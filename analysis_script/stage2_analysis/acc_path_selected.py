import pandas as pd
import numpy as np

basePath = "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
selectedPath = basePath + "/aps_selected.txt"
pathQlen = basePath + "/pathQlen.txt"
pathBw = basePath + "/pathBw.txt"
outputFile_Qlen = basePath + "/acc_path_selected_by_qlen.txt"
outputFile_Bw = basePath + "/acc_path_selected_by_bw.txt"

def get_selected_paths(selectedPath):
    # selectedPath: time(ns), src, dst, pathID
    sel = pd.read_csv(
        selectedPath,
        sep=r"\s+",
        skiprows=1,
        names=["time", "src", "dst", "pathID"]
    )
    return sel

def get_acc_by_util(selectedPath, pathBw, outputFile):
    # selectedPath: time(ns), src, dst, pathID
    sel = get_selected_paths(selectedPath)

    # pathBw.txt: time(ns), pathID, bw
    bw = pd.read_csv(
        pathBw,
        sep=r"\s+",
        skiprows=1,
        names=["time", "pathID", "bw"]
    )

    # 以 time 为 key，缓存每个时刻的路径带宽情况
    bw_by_time = {
        t: df for t, df in bw.groupby("time")
    }

    # 所有 pathBw 的时间点（用于快速查找）
    bw_times = np.array(sorted(bw_by_time.keys()))
    TIME_WINDOW = 50  # ns

    def find_matching_time(t):
        """
        返回与 t 最接近、且 |delta| <= 100ns 的 pathBw 时间
        若不存在，返回 None
        """
        idx = np.searchsorted(bw_times, t)

        candidates = []
        if idx > 0:
            candidates.append(bw_times[idx - 1])
        if idx < len(bw_times):
            candidates.append(bw_times[idx])

        best_t = None
        best_delta = TIME_WINDOW + 1

        for tq in candidates:
            delta = abs(tq - t)
            if delta <= TIME_WINDOW and delta < best_delta:
                best_t = tq
                best_delta = delta

        return best_t


    measurable = 0
    accurate = 0
    zero_bw_accurate = 0
    none_zero_bw_accurate = 0

    with open(outputFile, "w") as f:
        for _, row in sel.iterrows():
            ts = row.time
            pid = row.pathID

            # 对于aps_selected.txt中的一条记录时刻，在指定时间窗口内，bw中是否存在记录
            tq = find_matching_time(ts)
            if tq is None:
                continue  # 不可测量

            df = bw_by_time[tq]

            # 该时刻是否包含所选路径
            sel_row = df[df.pathID == pid]
            if sel_row.empty:
                continue  # 视为不可测量（数据不完整）

            sel_bw = sel_row.iloc[0].bw
            min_bw = df.bw.min()

            measurable += 1
            if sel_bw == min_bw: # 所选路径是否最短
                f.write(f"{ts} {row.src} {row.dst} {pid} {sel_bw} {min_bw} 1\n")
                accurate += 1
                if sel_bw == 0:
                    zero_bw_accurate += 1
                else:
                    none_zero_bw_accurate += 1
            else:
                f.write(f"{ts} {row.src} {row.dst} {pid} {sel_bw} {min_bw} 0\n")

        accuracy = accurate / measurable if measurable > 0 else 0.0

        # 将准确率录入outputFile中
        f.write(f"\n############## Summary ##############\n")
        f.write(f"Measurable selections    : {measurable}\n")
        f.write(f"Accurate selections      : {accurate}\n")
        f.write(f"Routing accuracy         : {accuracy:.6f}\n")
        f.write(f"#######################################\n")
        f.write(f"\n############## For easy copy ##############\n")
        f.write(f"Measurable selections:Accurate selections\n")
        f.write(f"{measurable}\t{accurate}\t")



        print(f"############## Summary ###############")
        print(f"Measurable selections    : {measurable}")
        print(f"Accurate selections      : {accurate}")
        print(f"Routing accuracy         : {accuracy:.6f}")
        print(f"#######################################") 



def get_acc_by_qlen(selectedPath, pathQlen, outputFile):
    # selectedPath: time(ns), src, dst, pathID
    sel = get_selected_paths(selectedPath)

    # pathQlen.txt: time(ns), pathID, qlen
    qlen = pd.read_csv(
        pathQlen,
        sep=r"\s+",
        skiprows=1,
        names=["time", "pathID", "qlen"]
    )

    # 以 time 为 key，缓存每个时刻的路径队列情况
    qlen_by_time = {
        t: df for t, df in qlen.groupby("time")
    }

    # 所有 pathQlen 的时间点（用于快速查找）
    qlen_times = np.array(sorted(qlen_by_time.keys()))

    TIME_WINDOW = 50  # ns

    def find_matching_time(t):
        """
        返回与 t 最接近、且 |delta| <= 100ns 的 pathQlen 时间
        若不存在，返回 None
        """
        idx = np.searchsorted(qlen_times, t)

        candidates = []
        if idx > 0:
            candidates.append(qlen_times[idx - 1])
        if idx < len(qlen_times):
            candidates.append(qlen_times[idx])

        best_t = None
        best_delta = TIME_WINDOW + 1

        for tq in candidates:
            delta = abs(tq - t)
            if delta <= TIME_WINDOW and delta < best_delta:
                best_t = tq
                best_delta = delta

        return best_t


    measurable = 0
    accurate = 0
    zero_qlen_accurate = 0
    none_zero_qlen_accurate = 0

    with open(outputFile, "w") as f:
        for _, row in sel.iterrows():
            ts = row.time
            pid = row.pathID

            # 对于aps_selected.txt中的一条记录时刻，在指定时间窗口内，qlen中是否存在记录
            tq = find_matching_time(ts)
            if tq is None:
                continue  # 不可测量

            df = qlen_by_time[tq]

            # 该时刻是否包含所选路径
            sel_row = df[df.pathID == pid]
            if sel_row.empty:
                continue  # 视为不可测量（数据不完整）

            sel_qlen = sel_row.iloc[0].qlen
            min_qlen = df.qlen.min()

            measurable += 1
            if sel_qlen == min_qlen: # 所选路径是否最短
                f.write(f"{ts} {row.src} {row.dst} {pid} {sel_qlen} {min_qlen} 1\n")
                accurate += 1
                if sel_qlen == 0:
                    zero_qlen_accurate += 1
                else:
                    none_zero_qlen_accurate += 1
            else:
                f.write(f"{ts} {row.src} {row.dst} {pid} {sel_qlen} {min_qlen} 0\n")

        accuracy = accurate / measurable if measurable > 0 else 0.0

        # 将准确率录入outputFile中
        f.write(f"\n############## Summary ##############\n")
        f.write(f"Measurable selections    : {measurable}\n")
        f.write(f"Accurate selections      : {accurate}\n")
        f.write(f"Accurate (Zero Qlen)     : {zero_qlen_accurate}\n")
        f.write(f"Accurate (None-zero Qlen): {none_zero_qlen_accurate}\n")
        f.write(f"Routing accuracy         : {accuracy:.6f}\n")
        f.write(f"#######################################\n")
        f.write(f"\n############## For easy copy ##############\n")
        f.write(f"Measurable selections:Accurate selections:Accurate (Zero Qlen):Accurate (None-zero Qlen)\n")
        f.write(f"{measurable}\t{accurate}\t{zero_qlen_accurate}\t{none_zero_qlen_accurate}\n")


        print(f"############## Summary ###############")
        print(f"Measurable selections    : {measurable}")
        print(f"Accurate selections      : {accurate}")
        print(f"Accurate (Zero Qlen)     : {zero_qlen_accurate}")
        print(f"Accurate (None-zero Qlen): {none_zero_qlen_accurate}")
        print(f"Routing accuracy         : {accuracy:.6f}")
        print(f"#######################################")    

        

if __name__ == "__main__":

    get_acc_by_util(selectedPath, pathBw, outputFile_Bw)
    get_acc_by_qlen(selectedPath, pathQlen, outputFile_Qlen)
    