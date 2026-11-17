# Simulator 数据分析脚本说明

本目录用于整理和分析网络仿真实验产生的结果，主要覆盖：

- 实验目录发现、批量配置生成与完成度检查；
- FCT、JCT、吞吐、ECN、重传、PFC、队列和端口带宽分析；
- 路径级队列/带宽统计与选路准确率评估；
- 乱序（Out-of-Order，OOO）缓存分析；
- 二进制 packet trace 的读取、过滤和文本化输出。

> 本目录中的脚本来自不同分析阶段。`stage3_analysis/` 中的脚本配置方式较统一，通常优先使用；`stage2_analysis/` 中保留了较多历史脚本和针对单次实验的硬编码配置，运行前需要逐个检查路径。

## 1. 目录结构

```text
analysis_script/
├── configs/                 # 共享实验目录配置
├── stage2_analysis/         # 单实验诊断、旧版对比绘图和自动化脚本
├── stage3_analysis/         # 当前批量统计与论文图表脚本
├── trace_analysis/          # 二进制 packet trace 解析器
├── check_if_finish.py       # 检查实验结果是否完整
├── clean_files.py           # 批量清理生成的图像
├── filiter_data.py          # 按列过滤文本数据并打印
├── get_case_path_pair.py    # 扫描结果目录并生成 CONFIG_LIST
├── get_config_file.py       # 在实验子目录之间归并/复制配置文件
└── topo_parser.py           # 为路径中的交换机补充出端口信息
```

推荐的数据流如下：

```text
仿真输出目录
   │
   ├─ get_case_path_pair.py ──> configs/result_path.py
   │                                  │
   │                                  ├─ stage3_analysis/*
   │                                  ├─ check_if_finish.py
   │                                  └─ clean_files.py
   │
   ├─ output.log + 拓扑文件 ──> topo_parser.py
   │                                  │
   │                                  ├─ plot_pathQlen.py
   │                                  ├─ plot_pathBw.py
   │                                  └─ acc_path_selected.py
   │
   └─ 二进制 trace ──> trace_analysis/trace_reader ──> 可读文本
```

## 2. 环境与依赖

建议使用 Python 3.8 或更高版本。Python 脚本主要依赖：

```bash
python3 -m pip install numpy pandas matplotlib cycler
```

`trace_analysis/` 还需要 GNU Make 和支持 C++11 的 `g++`：

```bash
cd /home/dell/sjw/lb/simulator/analysis_script/trace_analysis
make
```

服务器没有图形桌面时，可以使用非交互式 Matplotlib 后端：

```bash
export MPLBACKEND=Agg
```

## 3. 共享目录配置

大部分 `stage3_analysis/` 脚本以及部分顶层工具使用：

```python
# configs/result_path.py
CONFIG_LIST = {
    "算法名": {
        "工作负载或消息大小": "/absolute/path/to/experiment",
    },
}
```

例如：

```python
CONFIG_LIST = {
    "ecmp": {
        "1MB": "/path/to/ecmp-1MB",
        "4MB": "/path/to/ecmp-4MB",
    },
    "aps-v2": {
        "1MB": "/path/to/aps-v2-1MB",
        "4MB": "/path/to/aps-v2-4MB",
    },
}
```

许多脚本内部也有一个本地 `CONFIG_LIST`：

- 本地字典非空时，使用脚本内配置；
- 本地字典为空时，从 `configs/result_path.py` 导入共享配置。

为了让 `configs` 包能够被正确导入，建议从 `analysis_script/` 目录运行顶层脚本，从项目根目录运行 stage 目录中的脚本：

```bash
cd /home/dell/sjw/lb/simulator
python3 analysis_script/stage3_analysis/plot_cdf_fct.py
```

### 自动生成共享配置

`get_case_path_pair.py` 会扫描实验目录，将结果写入 `configs/result_path.py`。最稳妥的用法是进入交互模式：

```bash
cd /home/dell/sjw/lb/simulator/analysis_script
python3 get_case_path_pair.py
```

四种扫描模式的差别主要在于扫描深度以及第二层字典 key 的生成方式。下面的路径均为示意；脚本实际写入的是绝对路径。

#### 模式 0：将一层子目录编号为扁平字典

适合一个目录下直接存放若干实验用例，并且后续分析只需要按编号区分用例的情况。模式 0 只检查直接子目录，普通文件会被忽略。

例如：

```text
/data/runs/single-group/
├── aps-v2-b16_dcqcn-.../
├── aps-v2-b64_dcqcn-.../
└── run.log
```

选择模式 `0` 并输入 `/data/runs/single-group` 后，会生成类似结果：

```python
CONFIG_LIST = {
    "0": "/data/runs/single-group/aps-v2-b16_dcqcn-...",
    "1": "/data/runs/single-group/aps-v2-b64_dcqcn-...",
}
```

模式 0 不按目录名排序，编号取决于 `os.listdir()` 返回顺序，因此不同文件系统上的 `0`、`1` 对应关系可能不同。需要稳定且有语义的 key 时，优先考虑模式 1 或模式 3。

#### 模式 1：从目录名计算消息大小 key

适合同一算法目录下包含多个消息大小，并且目录名使用 `_EP并行度_总消息大小M` 形式的情况。当前主程序默认分隔符为 `EP8`；活跃代码并不是提取算法名，而是把分隔符后的消息大小除以 EP 并行度，得到每个 endpoint/flow 对应的大小。

例如：

```text
/data/runs/aps-v2/
├── aps-v2_mprdma-fattree_..._EP8_8M/
├── aps-v2_mprdma-fattree_..._EP8_32M/
└── aps-v2_mprdma-fattree_..._EP8_128M/
```

选择模式 `1`，输入 `/data/runs/aps-v2`，并使用分隔符 `EP8` 时，key 的计算为 `8/8`、`32/8`、`128/8`：

```python
CONFIG_LIST = {
    "1 M": "/data/runs/aps-v2/aps-v2_mprdma-fattree_..._EP8_8M",
    "4 M": "/data/runs/aps-v2/aps-v2_mprdma-fattree_..._EP8_32M",
    "16 M": "/data/runs/aps-v2/aps-v2_mprdma-fattree_..._EP8_128M",
}
```

目录名必须包含完整的 `_EP8_` 片段，否则会被跳过。自定义分隔符也应采用 `EP<number>` 形式，例如 `EP4`；如果多个目录计算出相同 key，后扫描到的目录会覆盖前一个目录。

#### 模式 2：将“算法/用例”两层目录转成嵌套字典（绘图脚本默认输入格式）

适合根目录第一层按算法分组、第二层存放实验用例，但暂时不需要从目录名提取 workload 大小的情况。第一层目录和每组中的用例目录都会按名称排序，再从 `0` 开始编号。

例如：

```text
/data/runs/compare/
├── aps-v2/
│   ├── aps-v2-b16_dcqcn-.../
│   └── aps-v2-b64_dcqcn-.../
└── rps/
    ├── rps-b16_dcqcn-.../
    └── rps-b64_dcqcn-.../
```

选择模式 `2` 并输入 `/data/runs/compare` 后，会生成：

```python
CONFIG_LIST = {
    "aps-v2": {
        "0": "/data/runs/compare/aps-v2/aps-v2-b16_dcqcn-...",
        "1": "/data/runs/compare/aps-v2/aps-v2-b64_dcqcn-...",
    },
    "rps": {
        "0": "/data/runs/compare/rps/rps-b16_dcqcn-...",
        "1": "/data/runs/compare/rps/rps-b64_dcqcn-...",
    },
}
```

这种结果已经符合 `CONFIG_LIST[algorithm][case] = path` 的通用结构，但内层 key 只是排序后的编号，不表示真实消息大小。

#### 模式 3：筛选两层目录并以 `fct.txt` 消息大小作为 key

适合模式 2 的两层目录中混有不同拥塞控制、拓扑或并行度，希望只选择一组条件，并让内层 key 直接表示消息大小的情况。多个筛选字段采用 AND 关系：用例目录名必须同时包含所有字段。

例如：

```text
/data/runs/compare/
├── aps-v2/
│   ├── aps-v2_dcqcn-fattree_..._EP8_8M/       # fct.txt 首行第5列为 8388608
│   ├── aps-v2_dcqcn-fattree_..._EP8_32M/      # fct.txt 首行第5列为 33554432
│   └── aps-v2_mprdma-fattree_..._EP8_32M/
└── rps/
    ├── rps_dcqcn-fattree_..._EP8_8M/          # fct.txt 首行第5列为 8388608
    └── rps_dcqcn-fattree_..._EP8_32M/         # fct.txt 首行第5列为 33554432
```

选择模式 `3`，输入 `/data/runs/compare`，再输入筛选字段 `dcqcn EP8` 后，`mprdma` 用例会被排除。脚本读取每个匹配目录下 `fct.txt` 第一行第 5 列，以 Byte 除以 `1024 * 1024` 得到 MB，并按该数值排序：

```python
CONFIG_LIST = {
    "aps-v2": {
        "8MB": "/data/runs/compare/aps-v2/aps-v2_dcqcn-fattree_..._EP8_8M",
        "32MB": "/data/runs/compare/aps-v2/aps-v2_dcqcn-fattree_..._EP8_32M",
    },
    "rps": {
        "8MB": "/data/runs/compare/rps/rps_dcqcn-fattree_..._EP8_8M",
        "32MB": "/data/runs/compare/rps/rps_dcqcn-fattree_..._EP8_32M",
    },
}
```

缺少 `fct.txt`、首行不足 5 列或第 5 列无法解析的目录会被跳过。同一算法下若两个匹配用例的消息大小相同，后一个会覆盖前一个并打印警告。

四种模式都会把生成结果写成 `WRITE_OUTPUT_VAR_NAME` 指定的变量名，默认即 `CONFIG_LIST`。当前主程序使用持续扫描循环；得到所需结果并写入文件后，可按 `Ctrl+C` 结束脚本。

默认 `WRITE_DIRECTLY = True`，会直接覆盖 `configs/result_path.py`。运行前应确认 `WRITE_OUTPUT_FILE`，需要先预览时可将 `WRITE_DIRECTLY` 改为 `False`。

## 4. 常见输入文件

不同仿真配置可能增加列。下表只描述当前脚本实际读取的核心字段，修改列格式时应同步检查脚本中的列索引。

| 文件 | 主要用途 | 当前脚本关注的字段 |
| --- | --- | --- |
| `fct.txt` | 流完成时间、JCT、ECN、重传 | flow size、start time、duration/end time、standalone FCT、flow type、重传计数、ECN 计数 |
| `bw.txt` | 节点/端口带宽 | `time,node_id,port_id,bandwidth` |
| `qlen.txt` | 交换机队列和端口总队列 | `time,sw_id,port_id,q_id,q_len,port_len` |
| `pfc.txt` | PFC pause/resume 事件 | `time_ns device_id device_type port_id pfc_state` |
| `ooo.txt` | 采样式 OOO 缓存峰值 | `time src dst sport dport ooo_buffer_size` |
| `ooo_buffer.txt` | 旧版/事件式 OOO 缓存记录 | `time src dst sport dport occupancy` |
| `aps_selected.txt` | APS 选路结果 | `time src dst pathID` |
| `pathID2Switch` | path ID 对应的交换机序列 | `pathID sw1 sw2 ...` |
| `pathID2Switch_with_ports.txt` | path ID 对应交换机及出端口 | `pathID sw1 port1 sw2 port2 ...` |
| `lb_compare.history` | 旧版批量实验索引 | 算法、负载、拓扑、配置目录 ID |

> `fct.txt` 在不同脚本中既有“第 7 列是 duration”的处理，也有“第 6/7 列相减”的处理。运行 FCT/JCT 脚本前，务必核对该脚本顶部的 `*_COL` 配置和当前仿真输出格式。

## 5. 顶层工具脚本

| 脚本 | 功能 | 配置与用法 |
| --- | --- | --- |
| `configs/result_path.py` | 保存共享 `CONFIG_LIST`，供批量脚本导入。 | 可手动编辑，也可由 `get_case_path_pair.py` 生成。 |
| `get_case_path_pair.py` | 扫描输出目录，按算法、消息大小或筛选字段生成扁平/嵌套路径字典。 | 运行后按提示选择模式；默认直接覆盖共享配置。 |
| `check_if_finish.py` | 递归检查 `CONFIG_LIST` 中每个实验目录的 `fct.txt` 是否存在且行数正确。路径含 `allreduce` 时期望 6144 行，含 `alltoall` 时期望 7168 行。 | `python3 check_if_finish.py`；或 `python3 check_if_finish.py --config configs/result_path.py --output unfinished.txt`。可用 `--fct-name` 检查其他文件名。 |
| `clean_files.py` | 按后缀、文件名前缀和关键词清理实验目录中的生成文件。 | 编辑 `CLEAN_*` 配置后运行。建议先设 `CLEAN_DRY_RUN = True`。当前默认值会真实删除文件。 |
| `filiter_data.py` | 对空格或逗号分隔的数值文本按列执行 `>、>=、<、<=、==、!=、between` 过滤，可限速打印和显示终端条形图。 | 编辑 `CONFIG_LIST`、`SELECT_GROUP`、`SELECT_ID`、`INPUT_FILE_NAME` 和 `FILTERS` 后运行。文件名保留了原有拼写 `filiter_data.py`。 |
| `get_config_file.py` | 扫描一个根目录，将子目录名在 `_dcqcn` 前的部分作为目标目录名，并复制指定拓扑、workload 和 `SimAI.conf` 文件。 | 编辑 `SOURCE_DIR`、`FILES_TO_COPY`、`SEPARATOR`；先使用 `DRY_RUN = True` 预览。 |
| `topo_parser.py` | 读取拓扑连接，为 `pathID2Switch` 中的每一跳补充交换机出端口，生成 `pathID2Switch_with_ports.txt`。 | 编辑文件底部 `case_file` 后运行；通常由路径分析 shell 脚本调用。 |

## 6. Stage 3：推荐的批量分析脚本

这组脚本普遍使用共享 `CONFIG_LIST`，结果通常写回每个实验目录。一般用法是：

1. 配置 `configs/result_path.py`；
2. 检查目标脚本顶部的列索引、目标节点/端口、时间单位和覆盖策略；
3. 从项目根目录执行脚本。

```bash
cd /home/dell/sjw/lb/simulator
python3 analysis_script/stage3_analysis/plot_cdf_fct.py
```

### 6.1 FCT、JCT、ECN 与重传

| 脚本 | 输入 | 功能与输出 |
| --- | --- | --- |
| `plot_cdf_fct.py` | `fct.txt` | 按 `FCT_START_COL`、`FCT_END_COL` 计算 FCT，绘制 CDF 并标注均值、P95、P99；输出 `cdf_fct.png`。已有图片默认跳过。 |
| `plot_cdf_ecn.py` | `fct.txt` | 读取 `ECN_COUNT_COL`（默认最后一列），绘制每流累计 ECN 数量 CDF；输出 `cdf_ecn.png`。 |
| `plot_cdf_retrans.py` | `fct.txt` | 根据 flow size 和包载荷估算总包数，分别绘制 RTO 重传比例与总重传比例 CDF；输出 `cdf_rto.png`、`cdf_retrans.png`。 |
| `plot_jct_bl.py` | `fct.txt` | 按算法和 workload/message size 计算 collective JCT，绘制规模变化曲线；可输出原始 JCT CSV 和相对 baseline 的 speedup PDF。 |
| `plot_jct_summary.py` | 汇总 CSV | 读取 `scenario,algorithm,workload,jct_ms` 标准 CSV 或 block-style CSV，生成 speedup 气泡热图 PNG/PDF。该脚本支持命令行参数。 |
| `plot_jct_summary_heatmap.py` | 每个配置目录下的 `speedup_data.csv` | 批量绘制 2×2 workload 子单元格 speedup 热图；默认 baseline 为 `rps`，输出文件名会根据路径中的 `asy`、`failure`、`sym` 添加后缀。当前代码只保存 PNG。 |

`plot_jct_summary.py` 示例：

```bash
python3 analysis_script/stage3_analysis/plot_jct_summary.py \
  --input /path/to/speedup_data.csv \
  --baseline ecmp \
  --output-png /path/to/jct_speedup.png \
  --output-pdf /path/to/jct_speedup.pdf
```

### 6.2 带宽与队列

| 脚本 | 输入 | 功能与输出 |
| --- | --- | --- |
| `plot_avg_port.py` | `bw.txt`、`qlen.txt` | 对选定交换机和端口做平均或逐项聚合。支持 `both/bw/qlen` 绘图模式以及 `port/switch/all/switch_port` 聚合模式；可补全缺失采样，输出 PNG/PDF。 |
| `plot_switch_bw_qlen.py` | `bw.txt`、`qlen.txt` | 为 `TARGET_NODE_IDS` 中每台交换机绘制指定端口的带宽/队列双轴时序图；支持仅带宽或仅队列模式，当前输出 PNG。 |

`plot_avg_port.py` 的选择器支持三种形式：

```python
TARGET_SWITCH_SELECTOR = {"type": "list", "values": [1152, 1153]}
TARGET_SWITCH_SELECTOR = {"type": "range", "start": 1152, "end": 1160, "step": 1}
TARGET_SWITCH_SELECTOR = {"type": "expr", "expr": "1152 <= id <= 1160"}
```

### 6.3 OOO 与 PFC

| 脚本 | 输入 | 功能与输出 |
| --- | --- | --- |
| `plot_ooo.py` | `ooo.txt` | 推荐的采样式 OOO 分析器。按采样周期重建每个 QP 的状态区间，生成目标连接曲线、Top-K 热图、统计图和 summary CSV；使用 `.ooo_cache/` 缓存大文件解析结果。 |
| `plot_ooo_trace.py` | `ooo_buffer.txt` | 兼容旧版事件式 OOO 日志的缓存分析器，生成单连接曲线、Top-K 热图、统计图和 summary CSV。 |
| `plot_pfc.py` | `pfc.txt` | 重建 pause 区间，分析全局 PFC 压力、Top 设备、单设备端口暂停时间；在实验目录下创建 `pfc_analysis/`，保存多张图和标准化 CSV。 |

OOO 脚本常用配置：

- `TARGET_SRC_IDS`、`TARGET_DST_IDS`、`TARGET_SRC_PORTS`、`TARGET_DST_PORTS`：选择单连接；
- `PLOT_MODE`：`single`、`heatmap`、`summary` 或 `all`；
- `TOP_K_CONNECTIONS`、`TOPK_SORT_BY`：Top-K 数量与排序指标；
- `CACHE_MODE`：`auto`、`reuse`、`rebuild` 或 `off`；
- `SAMPLE_PERIOD_US`：`plot_ooo.py` 对采样日志进行状态重建时使用的采样周期。

修改原始日志解释方式、采样周期或目标过滤条件后，如果怀疑缓存失效，可将 `CACHE_MODE` 临时设置为 `rebuild`。

## 7. Stage 2：单实验诊断与历史脚本

### 7.1 路径级分析

| 脚本 | 输入 | 功能与输出 |
| --- | --- | --- |
| `plot_pathQlen.py` | `pathID2Switch_with_ports.txt`、`qlen.txt` | 汇总一条路径上各交换机出端口的队列长度，生成 `pathQlen.txt` 和 `pathQlen.pdf`。采样聚合步长可由环境变量 `STEP` 控制。 |
| `plot_pathBw.py` | `pathID2Switch_with_ports.txt`、`bw.txt` | 计算路径各跳平均带宽，生成 `pathBw.txt` 和 `pathBw.pdf`。 |
| `acc_path_selected.py` | `aps_selected.txt`、`pathQlen.txt`、`pathBw.txt` | 在约 50 ns 匹配窗口内判断所选路径是否达到最小队列/最小带宽指标，生成 `acc_path_selected_by_qlen.txt` 和 `acc_path_selected_by_bw.txt`。 |
| `get_acc.py` | 上述准确率文本 | 按绝对阈值或百分位阈值比较多个算法的选路准确率，输出对比 PDF。配置目前写在 `main()` 中。 |
| `plot_cdf_bw_diff.py` | `acc_path_selected_by_bw.txt` | 计算所选路径指标与最优路径指标之差，并绘制误差 CDF。 |
| `get_path_qlen.sh` | `output.log`、拓扑、`qlen.txt` | 串联提取 `pathID2Switch`、端口补全和路径队列绘图。 |
| `get_path_bw.sh` | `output.log`、拓扑、`bw.txt` | 串联提取 `pathID2Switch`、端口补全和路径带宽绘图。 |
| `analysis.sh` | 单个实验目录 | 调用路径队列、路径带宽、选路准确率和 timeout 统计。 |
| `auto_analysis.sh` | 一组配置目录 | 循环修改 `analysis.sh` 的实验目录并批量执行，还会分发 `pathID2Switch`。 |

路径分析的逻辑顺序为：

```text
output.log
  └─ grep APS_PATH_SWITCHID
       └─ pathID2Switch
            └─ topo_parser.py
                 └─ pathID2Switch_with_ports.txt
                      ├─ plot_pathQlen.py ──> pathQlen.txt/pdf
                      ├─ plot_pathBw.py   ──> pathBw.txt/pdf
                      └─ acc_path_selected.py ──> accuracy txt
```

> 注意：这几份 shell 脚本会使用 `sed -i` 修改 Python 文件中的硬编码路径，而且当前脚本路径仍按搬迁前的目录布局书写。例如部分命令在 `analysis_script/` 下查找实际位于 `stage2_analysis/` 的文件。直接运行前需要先修正工作目录和脚本路径，并备份未提交的本地修改。

### 7.2 FCT、JCT、吞吐与队列对比

| 脚本 | 功能 |
| --- | --- |
| `analysis.py` | 遍历“配置目录/用例目录”两层结构，从 `fct.txt` 粗略计算 JCT 和平均 FCT slowdown，并写入汇总日志。根目录和日志路径写在文件底部。 |
| `plot_fct.py` | 读取 `lb_compare.history` 和各实验 `fct.txt`，比较平均/P99 FCT slowdown。 |
| `plot_jct.py` | 读取 history 对应实验，计算并绘制 JCT；也保留了小流/大流 FCT 统计函数。 |
| `plot_ct.py` | 综合版 completion-time 脚本，可绘制 JCT、平均/P95/P99 FCT。当前 `main()` 使用硬编码实验字典。 |
| `conweave_plot_fct.py` | 按 flow size 百分位分桶，比较 ECMP/APS 的平均和 P99 FCT slowdown；支持 `-sT`、`-fT` 时间范围参数。 |
| `plot_avg_jct.py` | 按 `(src,dst)` 流组计算平均 JCT/吞吐并绘制算法对比，实验目录写在 `main()` 中。 |
| `plot_bw.py` | 对 `bw.txt` 做时间分桶和 NIC 补零，计算全网 NIC 平均吞吐随时间变化，并输出 PDF 和平均吞吐文本。 |
| `plot_qlen.py` | 补全交换机端口缺失采样，计算全网平均队列长度并绘制时序曲线。 |
| `plot_flow_lifecycle.py` | 从 `fct.txt` 选择指定 src/dst/port 范围，绘制单组 flow 的生命周期时间线。 |
| `all_plot.sh` | 依次运行旧版 JCT/FCT/OOO 绘图，并用 `sed` 修改数据目录。当前内部路径仍指向旧位置，运行前需修正。 |

`conweave_plot_fct.py` 示例：

```bash
python3 analysis_script/stage2_analysis/conweave_plot_fct.py \
  -sT 0 -fT 10000000000
```

### 7.3 CDF 与 OOO buffer 对比

| 脚本 | 功能 |
| --- | --- |
| `plot_cdf_fct.py` | 读取 `fct.txt` 第 7/8 列之比，绘制 FCT slowdown 的百分位曲线。 |
| `plot_cdf_cnp.py` | 当前实现同样从 `fct.txt` 第 7/8 列计算比值并绘图；文件名虽为 CNP，但代码并未读取独立 CNP 计数字段，使用前应核对分析意图。 |
| `plot_cdf_ooo.py` | 读取 `ooo_buffer.txt` 的 occupancy 列，过滤 0 后绘制 OOO CDF。 |
| `plot_ooo.py` | 旧版 OOO 分析：从 `ooo_buffer.txt` 提取峰值、指定源流时序和 `ooo_summary.txt`，支持按 history 批量绘图。 |
| `plot_fct_ooo.py` | 比较不同 OOO buffer 配置下的平均/P99 FCT slowdown。 |
| `plot_fct_ooo-m.py` | `plot_fct_ooo.py` 的论文绘图风格变体。 |

### 7.4 文件分发工具

| 脚本 | 功能与用法 |
| --- | --- |
| `copy_file.sh` | 将一个源文件复制到目标目录的所有直接子目录；加 `-r` 可递归。示例：`./copy_file.sh pathID2Switch /path/to/cases`。会覆盖同名目标文件。 |

## 8. Trace 二进制解析

`trace_analysis/trace_reader` 读取仿真器输出的二进制 trace：文件开头是 `SimSetting`，后续是连续的 `TraceFormat` 记录。解析器将其打印为文本，并支持过滤表达式。

### 编译与运行

```bash
cd /home/dell/sjw/lb/simulator/analysis_script/trace_analysis
make
./trace_reader /path/to/trace_file
```

过滤单个队列：

```bash
./trace_reader /path/to/trace_file 'queue=1152,9,3'
```

组合过滤条件：

```bash
./trace_reader /path/to/trace_file 'node=1152&intf=9&qlen>0'
./trace_reader /path/to/trace_file '(event=2|event=3)&nodeType=1'
```

过滤指定单向/双向流：

```bash
./trace_reader /path/to/trace_file 'flow=167772161,167772162,10000,100'
./trace_reader /path/to/trace_file 'biflow=167772161,167772162,10000,100'
```

支持的常用字段包括：`time`、`node`、`nodeType`、`intf`、`qidx`、`qlen`、`sip`、`dip`、`size`、`l3Prot`、`event`、`ecn`、`data.sport`、`data.dport`、`data.seq`、`ack.sport`、`ack.dport`、`ack.flags`、`qp.sport`、`qp.dport`。比较操作符包括 `=、!=、>、>=、<、<=`，逻辑操作符为 `&、|`，复杂表达式应使用单引号保护，避免被 shell 解释。

事件编号定义为：

| 编号 | 含义 |
| --- | --- |
| `0` | `Recv` |
| `1` | `Enqu` |
| `2` | `Dequ` |
| `3` | `Drop` |

`trace_analysis/` 中其他文件：

- `trace-format.h`：二进制 trace 记录结构及事件类型；
- `trace_filter.hpp`：过滤表达式解析与匹配；
- `sim-setting.h`：trace 文件头中的端口速率和窗口配置；
- `utils.hpp`：flow 标识、协议字符和文本输出格式；
- `trace_reader.cpp`：解析器主程序，负责读取文件头、逐条反序列化、执行过滤并打印；
- `Makefile`：构建 `trace_reader`；
- `trace_reader`：已编译的本机二进制文件；
- `mix.tr`：二进制 trace 样例/调试数据；
- `tmp`：历史文本输出或调试产物，不是构建所必需的源码。

二进制格式依赖 C++ 结构体布局和当前头文件定义。若 trace 由不同版本、不同架构或不同编译布局的仿真器生成，解析结果异常时应使用与生成端一致的头文件重新编译。

## 9. 推荐工作流

### 批量生成单实验 CDF/时序图

```bash
cd /home/dell/sjw/lb/simulator/analysis_script
python3 get_case_path_pair.py
python3 check_if_finish.py

cd /home/dell/sjw/lb/simulator
python3 analysis_script/stage3_analysis/plot_cdf_fct.py
python3 analysis_script/stage3_analysis/plot_cdf_ecn.py
python3 analysis_script/stage3_analysis/plot_cdf_retrans.py
python3 analysis_script/stage3_analysis/plot_avg_port.py
```

### 分析 OOO 与 PFC

```bash
# 先编辑脚本顶部的目标连接、采样周期和 PLOT_MODE
python3 analysis_script/stage3_analysis/plot_ooo.py

# 先编辑 TARGET_DEVICES、TIME_BIN_NS 等配置
python3 analysis_script/stage3_analysis/plot_pfc.py
```

### 清理旧图后重新生成

1. 编辑 `clean_files.py` 的匹配规则；
2. 先设置 `CLEAN_DRY_RUN = True` 并检查输出；
3. 确认目标无误后改为 `False`；
4. 再运行对应绘图脚本。

## 10. 使用注意事项

- 多数脚本没有完整命令行接口，实验路径、列索引和绘图选项位于文件顶部或 `main()` 中。
- `clean_files.py`、`get_config_file.py`、`copy_file.sh`、`get_case_path_pair.py` 和部分自动化 shell 会删除、覆盖或复制文件，执行前先使用 dry-run 或检查目标目录。
- Stage 3 的多个脚本检测到输出图片已存在时会跳过。修改配置后若需要重画，请删除旧图、开启覆盖选项或修改输出名。
- `plot_ooo.py` 和 `plot_ooo_trace.py` 会创建缓存。改变原始数据语义或关键解析配置后，应重建缓存。
- 部分 Stage 2 脚本会调用 `plt.show()`；在无桌面环境中建议设置 `MPLBACKEND=Agg`。
- Stage 2 的 history 驱动脚本依赖 `output/lb_compare.history` 的格式以及特定目录命名规则，目录名变化后可能无法发现实验。
- 路径、时间单位和列索引是结果正确性的关键。生成图像不代表统计口径一定匹配当前仿真版本。
