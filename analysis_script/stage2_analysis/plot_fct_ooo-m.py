import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import re

# =========================
# Global Plot Style (SIGCOMM / NSDI style)
# =========================
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "axes.linewidth": 1.2,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

topo2bdp = {
    "fattree": 306000,
    "SpectrumX": 204000,
    "AlibabaHPN": 103000,
}

hatches = ['/', '\\', 'x', '-', '+', 'o', '.']

def getFilePath():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    print("File directory: {}".format(dir_path))
    return dir_path

def get_flow_size(filename):
    with open(filename, "r") as f:
        line = f.readline()
        flow_size = float(line.split()[4])
    return round(flow_size / (1024 * 1024), 1)

def get_config_from_history(history_filename, data_dir):
    fct_files = []
    LBs = []
    ooo_config = []
    config = []
    configId = []
    new_data_dir = ""

    with open(history_filename, "r") as f:
        for line in f.readlines():
            if line == "\n":
                break
            for topo in topo2bdp.keys():
                if topo in line:
                    parsed_line = re.sub(r'\[.*?\]', '', line).strip()
                    parsed_line = parsed_line.split('\t')
                    config_id = parsed_line[-1]

                    if config_id in configId:
                        continue
                    configId.append(config_id)

                    lb_mode = parsed_line[0].split('_')[0].lower()
                    ooo_buffer_size = parsed_line[0].split('_')[0].split('-')[-1].strip('b')
                    cc_mode = parsed_line[0].split('_')[1].lower() if len(parsed_line[0].split('_')) >= 2 else "None"

                    netload = parsed_line[1]
                    topo = parsed_line[2]

                    if os.path.exists(data_dir + "/" + config_id):
                        fct_files.append(data_dir + "/" + config_id + "/fct.txt")
                        new_data_dir = data_dir
                    elif os.path.exists(data_dir + "/" + topo + "-" + netload + "/" + config_id):
                        fct_files.append(data_dir + "/" + topo + "-" + netload + "/" + config_id + "/fct.txt")
                        new_data_dir = data_dir + "/" + topo + "-" + netload
                    else:
                        continue

                    LBs.append(lb_mode)
                    ooo_config.append(ooo_buffer_size)
                    config.append([topo, netload, cc_mode])

    return new_data_dir, fct_files, LBs, ooo_config, config

def parse_file(filename, type):
    flows = []
    with open(filename, "r") as f:
        for line in f:
            if not line.strip():
                continue
            parts = line.split()
            fct = float(parts[6])
            standalone = float(parts[7])
            if standalone <= 0:
                continue
            flows.append(fct / standalone)

    if type == "avg":
        return np.mean(flows) if flows else 0
    elif type == "p99":
        return np.percentile(flows, 99) if flows else 0

def plot_results(history_filename, data_dir, fig_filename, type):
    data = {}
    configId = []

    with open(history_filename, "r") as f:
        for line in f.readlines():
            if line == "\n":
                break
            parsed_line = re.sub(r'\[.*?\]', '', line).strip().split('\t')
            config_id = parsed_line[-1]
            if config_id in configId:
                continue
            configId.append(config_id)

            lb_mode = parsed_line[0].split('_')[0].lower()
            buffer_size = int(lb_mode.split('-')[-1].strip('b'))
            algo = lb_mode.rsplit('-', 1)[0]

            fct_file = data_dir + "/" + config_id + "/fct.txt"
            fct_slowdown = parse_file(fct_file, type)
            data.setdefault(algo, {})[buffer_size] = fct_slowdown

    algorithms = sorted(data.keys())
    buffers = sorted({b for a in data for b in data[a]})

    color_map = {
        algo: plt.cm.tab10(i)
        for i, algo in enumerate(algorithms)
    }

    x = np.arange(len(buffers))
    bar_width = 0.75 / len(algorithms)

    fig, ax = plt.subplots(figsize=(7.5, 4.5))

    for i, algo in enumerate(algorithms):
        fcts = [data[algo].get(b, np.nan) for b in buffers]
        bars = ax.bar(
            x + i * bar_width,
            fcts,
            width=bar_width,
            color=color_map[algo],
            edgecolor='black',
            linewidth=0.8,
            hatch=hatches[i % len(hatches)],
            label=algo
        )

        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h,
                f"{h:.2f}",
                ha='center',
                va='bottom',
                fontsize=8
            )

    ax.set_xticks(x + bar_width * (len(algorithms) - 1) / 2)
    ax.set_xticklabels(buffers)
    ax.set_xlabel("OOO Buffer Window Size")

    ylabel = "FCT Slowdown (Avg)" if type == "avg" else "FCT Slowdown (P99)"
    ax.set_ylabel(ylabel)
    ax.set_axisbelow(True)   # 网格线在 bar 后面（非常重要）

    ax.yaxis.grid(
        True,
        linestyle='--',
        linewidth=0.6,
        alpha=0.5
    )


    # ax.spines['top'].set_visible(False)
    # ax.spines['right'].set_visible(False)
    ax.tick_params(direction='out', length=4, width=1)

    ax.legend(
        loc='upper right',
        frameon=False,
        fontsize=10.5,          # 比正文略大，论文友好
        handlelength=1.6,
        handletextpad=0.6,
        borderaxespad=0.3
    )

    # 不遮挡柱状图的图例
    ax.legend(
        loc='upper right',
        # bbox_to_anchor=(1.02, 1.0),   # 轴外右侧
        frameon=False,
        fontsize=10.5,
        handlelength=1.6,
        handletextpad=0.6,
        borderaxespad=0.0
    )

    # fig.tight_layout(rect=[0, 0, 0.85, 1])
    fig.tight_layout(pad=0.5)
    fig.savefig(fig_filename, format="pdf")
    plt.close(fig)

if __name__ == "__main__":
    file_dir = getFilePath()
    fig_dir = file_dir + "/../output/1all_figures"
    os.makedirs(fig_dir, exist_ok=True)

    data_dir = file_dir + "/../output/5ooo-class"
    history_filename = file_dir + "/../output/fct_ooo_compare.history"

    data_dir, fct_files, LBs, ooo_config, config = get_config_from_history(history_filename, data_dir)
    if len(config) == 0:
        sys.exit(0)

    fig_filename_avg = fig_dir + "/{}.pdf".format("style_AVG_FCT(ooo-fct):[{}]+[{}]+[CC:{}]".format(config[0][0], config[0][1], config[0][2]))
    fig_filename_p99 = fig_dir + "/{}.pdf".format("style_P99_FCT(ooo-fct):[{}]+[{}]+[CC:{}]".format(config[0][0], config[0][1], config[0][2]))

    plot_results(history_filename, data_dir, fig_filename_avg, "avg")
    plot_results(history_filename, data_dir, fig_filename_p99, "p99")
