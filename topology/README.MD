# 仿真拓扑文件说明

本目录保存 Astra-Sim 与 ns-3 联合仿真使用的网络拓扑，包含 Alibaba HPN、NVIDIA Spectrum-X 和 Fat-Tree 等基础拓扑，以及带宽不均衡、单链路降速和链路间歇故障等异常变体。目录内还提供了 Fat-Tree 生成、异常注入和多路径查询脚本。

## 1. 文件命名

基础拓扑文件名通常编码了拓扑类型、GPU 数量、单机 GPU 数量、网络带宽和 GPU 型号。例如：

```text
fattree_k16_1024g_8gps_400Gbps_A100
│       │   │     │       │       └─ GPU 型号
│       │   │     │       └───────── 网络链路标称带宽
│       │   │     └───────────────── 每台服务器的 GPU 数量
│       │   └─────────────────────── GPU 总数
│       └─────────────────────────── Fat-Tree 参数 k
└─────────────────────────────────── 拓扑类型
```

异常后缀的含义如下：

| 后缀 | 含义 | 构造方式 |
| --- | --- | --- |
| 无后缀 | 基础拓扑 | 使用拓扑设计规定的正常带宽和连接关系 |
| `_asy` | 多链路带宽不均衡 | 将一批原为 `400Gbps` 的链路静态改为 `200Gbps` |
| `_asy_one` | 单链路降速 | 通常只将一条 `400Gbps` 链路改为 `200Gbps`；k=8 样例使用 `half` 动态半速标记 |
| `_failure` | 单链路间歇故障 | 在一条链路末尾追加 `100 600`，使其在指定时间窗内丢弃数据包 |

这里的 `_asy` 表示不同链路之间的带宽不均衡，并非同一链路两个方向具有不同带宽。一条拓扑记录安装出的两个 `QbbNetDevice` 使用相同的 `DataRate`，因此该记录对应的双向链路速率一致。

## 2. 目录内容

### 2.1 基础拓扑

| 文件 | 节点数 | GPU/服务器 | NVSwitch 数 | 普通交换机数 | 链路数 | 说明 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100` | 1244 | 8 | 128 | 92 | 4032 | Alibaba HPN，双 ToR、双平面 |
| `AlibabaHPN_1024g_8gps_DualToR_DualPlane_2Pod_200Gbps_A100` | 1376 | 8 | 128 | 224 | 4224 | Alibaba HPN 双 Pod 版本 |
| `SpectrumX_1024g_8gps_400Gbps_A100` | 1232 | 8 | 128 | 80 | 3072 | 1024 GPU Spectrum-X 拓扑 |
| `SpectrumX_32g_8gps_400Gbps_A100` | 54 | 8 | 4 | 18 | 96 | 用于小规模实验的 32 GPU Spectrum-X 拓扑 |
| `fattree_k16_1024g_8gps_400Gbps_A100` | 1472 | 8 | 128 | 320 | 4096 | k=16 的 1024 GPU Fat-Tree |
| `fattree_k8_128g_2gps_400Gbps_A100` | 272 | 2 | 64 | 80 | 512 | k=8 的 128 GPU Fat-Tree |

除 Alibaba HPN 双 Pod 文件和小规模 Spectrum-X 文件外，其余主要基础拓扑均提供了异常变体。

### 2.2 当前异常变体的实际修改

| 拓扑族 | `_asy` 中的降速链路数 | `_asy_one` | `_failure` |
| --- | ---: | --- | --- |
| Alibaba HPN 1024 GPU | 32 条，`400Gbps -> 200Gbps` | 1 条，`400Gbps -> 200Gbps` | 链路 `1152-1184`，`100~600 us` 故障 |
| Spectrum-X 1024 GPU | 32 条，`400Gbps -> 200Gbps` | 未提供 | 链路 `1152-1168`，`100~600 us` 故障 |
| Fat-Tree k=16 | 256 条，`400Gbps -> 200Gbps` | 1 条，`400Gbps -> 200Gbps` | 链路 `1152-1280`，`100~600 us` 故障 |
| Fat-Tree k=8 | 32 条，`400Gbps -> 200Gbps` | 链路 `192-227` 追加 `half` | 链路 `192-224`，`100~600 us` 故障 |

表中的时间是相对网络仿真起点 `sim_start` 的偏移量，而不是 ns-3 的绝对时间。当前代码中 `sim_start` 默认为 `3 us`，所以 `100 600` 实际会在 ns-3 时间 `103 us` 进入故障、`603 us` 恢复。

## 3. 拓扑文件格式

拓扑文件是空白字符分隔的纯文本文件，无文件扩展名。

### 3.1 第一行：全局信息

```text
node_num gpus_per_server nvswitch_num switch_num link_num gpu_type
```

例如：

```text
1472 8 128 320 4096 A100
```

各字段依次表示节点总数、每台服务器的 GPU 数、NVSwitch 数、普通网络交换机数、链路数和 GPU 型号。`gpu_type` 当前可识别 `A100`、`A800`、`H100` 和 `H800`，其他值会被解析为 `NONE`。

### 3.2 第二行：交换节点 ID

```text
<全部 NVSwitch ID> <全部普通交换机 ID>
```

`SetupNetwork()` 先读取 `nvswitch_num` 个 ID 并将其标记为 NVSwitch，再读取 `switch_num` 个 ID 并将其标记为普通交换机；没有出现在该行中的节点按 GPU/NIC 端节点创建。因此，第二行 ID 的数量和顺序必须与第一行的两个计数一致。

### 3.3 第三行起：链路信息

正常链路至少包含五列：

```text
src dst data_rate link_delay error_rate
```

例如：

```text
0 1024 2880Gbps 0.000025ms 0
0 1152 400Gbps 0.0005ms 0
```

- `src`、`dst`：链路两端的节点 ID。
- `data_rate`：ns-3 可解析的速率字符串，如 `200Gbps`、`400Gbps`、`2880Gbps`。
- `link_delay`：ns-3 可解析的传播时延字符串，如 `0.0005ms`。
- `error_rate`：链路的逐包错误率。值大于 0 时为该链路单独创建 `RateErrorModel`；值为 0 时使用全局 `ERROR_RATE_PER_LINK` 配置所创建的错误模型，通常全局值也为 0。

链路后还可追加异常字段：

```text
src dst data_rate link_delay error_rate [half] [t0 t1 t2 ...]
```

- `half`：在 `sim_start` 时将该链路两端设备的当前速率各乘以 0.5。
- `t0 t1 ...`：以微秒为单位的故障/恢复时间偏移。事件必须从故障开始并严格交替，即 `t0` 故障、`t1` 恢复、`t2` 再次故障，以此类推。
- `half` 和时间序列可以同时出现；解析器会识别任意位置的 `half`，其余附加字段必须能转换为数字。

若时间序列只有奇数个值，最后一次故障之后不会自动恢复。例如：

```text
# 从 sim_start + 100 us 起故障，之后一直保持故障
192 224 400Gbps 0.0005ms 0 100

# 在 [100, 600) 和 [900, 1200) us 两个区间故障
192 224 400Gbps 0.0005ms 0 100 600 900 1200
```

拓扑文件本身不支持注释，上述 `#` 说明行仅用于文档示例，不应写入实际拓扑文件。第一行声明的 `link_num` 必须与后续链路记录数完全一致。

## 4. 异常拓扑如何构造

### 4.1 静态带宽不均衡：`_asy` 和多数 `_asy_one`

最直接的构造方式是复制基础拓扑，并修改目标链路的第三列：

```diff
- 1152 1280 400Gbps 0.0005ms 0
+ 1152 1280 200Gbps 0.0005ms 0
```

`topo_asy_gen.py` 自动完成这一过程：

1. 将 `PRIME_FILE_PATH` 指向基础拓扑，并复制为带后缀的新文件。
2. 用 `START_LINE` 和 `END_LINE` 指定第一列节点 ID 的范围。变量名虽然包含 `LINE`，当前实现实际按第一列节点 ID 分组，并不是按文本行号选择。
3. 在每个节点组内按 `RATIO` 随机抽取链路；抽取数使用向上取整。
4. 当 `BW_FAILURE = True` 时，把所选链路第三列替换为 `[MIN, MAX]` 范围内的随机整数带宽（单位固定为 `Gbps`）。
5. 当 `LINK_FAILURE = True` 时，根据 `link_failure` 字典向精确匹配的有向记录 `(src, dst)` 追加故障时间。

脚本当前使用硬编码参数且未固定随机种子。重新运行可能产生不同的抽样结果；生成可复现实验拓扑时，建议显式设置随机种子并保存生成后的拓扑文件。`link_failure` 的键必须与文件中的 `src dst` 顺序一致。

### 4.2 动态半速：`half`

在链路末尾追加 `half`：

```diff
- 192 227 400Gbps 0.0005ms 0
+ 192 227 400Gbps 0.0005ms 0 half
```

最终设备速率同样由 `400Gbps` 变为 `200Gbps`，但它与直接把第三列写成 `200Gbps` 并不完全等价：

- 静态 `200Gbps` 在链路安装时生效，后续记录的链路带宽、ECN/PFC 阈值及 headroom 初始化都能看到该速率。
- `half` 先按 `400Gbps` 完成链路及交换机参数初始化，到 `sim_start` 才调用 `SetPortRate(0.5)`；当前代码不会同步更新 `nbr2if` 中缓存的带宽，也不会重新计算 ECN/PFC 阈值、headroom 或路由。
- 每出现一次 `half` 事件都会在当前速率上再次乘 0.5；文件中通常只写一次。

因此，需要“从初始化开始就是低速链路”时应直接修改第三列；需要保留正常初始化、在业务开始时触发动态降速时使用 `half`。

### 4.3 间歇链路故障：`_failure`

在链路末尾追加成对的故障和恢复时间：

```diff
- 1152 1280 400Gbps 0.0005ms 0
+ 1152 1280 400Gbps 0.0005ms 0 100 600
```

该方式不删除链路，也不改变路由表，而是在指定时间窗内把链路变成丢包黑洞。这适合观察传输层超时、重传、流量调度和拥塞控制在瞬时故障下的行为。

## 5. 异常在仿真中的生效链路

相关实现位于 [`common.h`](../astra-sim-alibabacloud/astra-sim/network_frontend/ns3/common.h) 的 `SetupNetwork()`、`ChangeLinkState()` 和 `TakeDownLink()`，以及 [`qbb-net-device.cc`](../ns-3-alibabacloud/simulation/src/point-to-point/model/qbb-net-device.cc) 的 `Receive()`、`SetLinkFailed()`、`SetLinkUp()` 和 `SetPortRate()`。

核心调用关系如下：

```text
拓扑链路记录
    |
    v
common.h: SetupNetwork()
    |-- 第 3/4/5 列 --> QbbHelper(DataRate, Delay, ReceiveErrorModel)
    |-- half --------> sim_start 调度 ChangeLinkState(..., 2)
    |                     `-> 两端 QbbNetDevice::SetPortRate(0.5)
    `-- 时间序列 ----> sim_start + ti 调度 ChangeLinkState(..., 0/1)
                          |-- 0: 两端 SetLinkFailed()
                          `-- 1: 两端 SetLinkUp()
                                      |
                                      v
qbb-net-device.cc: QbbNetDevice::Receive()
    `-- m_linkFailed == true 时计数并直接丢包
```

具体过程如下：

1. `SetupNetwork()` 按第一行的 `link_num` 逐行读取链路。每行先解析固定五列，再扫描所有附加字段。
2. 读到 `half` 后，在绝对时间 `MicroSeconds(sim_start)` 调度 `ChangeLinkState(..., 2)`；该函数找到链路两端接口并分别调用 `SetPortRate(0.5)`。
3. 读到数字时间后，按“故障、恢复、故障、恢复……”交替调度事件，事件时刻为 `MicroSeconds(sim_start) + MicroSeconds(time)`。
4. 故障事件在链路两端调用 `SetLinkFailed()`，令两个 `QbbNetDevice` 的 `m_linkFailed = true`；恢复事件调用 `SetLinkUp()` 清除此标志。
5. 数据包到达任一端设备的 `Receive()` 时，如果 `m_linkFailed` 为真，设备增加 `m_linkFailedPktDropCnt` 并直接返回，数据包不再上交协议栈。由于两端都被标记，两个传输方向都会受影响。
6. 若编译时启用了 `SWITCH_DROP_LOG` 和运行时 `TRACE`，故障丢包会输出 `[ERROR:LINK_FAILED]` 日志；状态变化会输出 `[Link_Failed]`，动态速率变化会输出 `[Link_Rate_Change]`。

需要特别注意：这种拓扑内时间序列故障只修改 `m_linkFailed`，不会把 `nbr2if` 的 `up` 状态设为 false，不会清空队列，也不会触发路由重算或 QP 重分配。恢复后原路由立即可以继续使用。

### 5.1 与 `LINK_DOWN` 配置项的区别

网络配置文件中的：

```text
LINK_DOWN <time_us> <node_A> <node_B>
```

走的是另一条处理路径。到达 `sim_start + time_us` 后，`TakeDownLink()` 会：

1. 将 `nbr2if` 中该链路双向的 `up` 状态置为 false；
2. 清空并重新计算路由，重建交换机、NVSwitch 和主机转发表；
3. 调用两端设备的 `TakeDown()` 清理相关队列并令底层 `m_linkUp = false`；
4. 通知主机重新分配 QP。

当前实现没有与 `LINK_DOWN` 对应的恢复事件。因此：

| 机制 | 数据面效果 | 路由重算 | 队列处理 | 可恢复 |
| --- | --- | --- | --- | --- |
| 拓扑行时间序列（`_failure`） | 到达接收端后丢包 | 否 | 不主动清空 | 是，按下一时间点恢复 |
| 配置项 `LINK_DOWN` | 设备永久下线 | 是 | 清理并触发 QP 重分配 | 当前不支持 |
| `error_rate` / `ERROR_RATE_PER_LINK` | 按概率随机损坏并丢包 | 否 | 不主动清空 | 持续按概率生效 |

## 6. 辅助脚本

### `fat-tree.py`

生成带 NVSwitch 的 Fat-Tree 拓扑，节点编号顺序为 GPU、NVSwitch、ToR、Aggregation、Core。示例：

```bash
python3 topology/fat-tree.py \
  --fat-tree-k 16 \
  --gpu-per-server 8 \
  --gpu-version A100 \
  --out-dir-path topology/
```

`--out-dir-path` 当前通过字符串直接与文件名拼接，目录参数末尾需要保留 `/`。

### `topo_asy_gen.py`

从基础拓扑复制并生成带宽降速或链路故障变体。运行前需修改脚本末尾的文件路径、节点范围、比例和异常参数：

```bash
python3 topology/topo_asy_gen.py
```

建议先输出到新文件并使用 `diff` 检查，避免覆盖需要保留的实验拓扑。

### `get_path_from_topo.py`

把拓扑解析为无向图，交互式查询两个端节点之间的所有等长最短路径，并显示沿途交换机出端口及链路带宽。脚本中的 `topology_file` 当前为硬编码路径，使用前需修改。

## 7. 新增或修改拓扑时的检查清单

- 第一行 `node_num` 覆盖所有节点 ID，且节点 ID 可用于直接索引 `[0, node_num)`。
- 第二行正好包含 `nvswitch_num + switch_num` 个有效 ID，且两类 ID 的顺序正确。
- 第一行 `link_num` 与第三行起的实际链路记录数一致。
- 每条链路至少有五列，速率和时延字符串可被 ns-3 解析。
- 故障时间按微秒填写、单调递增，并按故障/恢复成对组织；若故意保持故障，可保留最后一个无配对时间。
- 使用 `half` 前确认是否确实需要“初始化后动态半速”，否则优先直接修改第三列。
- 需要路由绕障时使用 `LINK_DOWN` 或扩展故障处理代码；仅使用 `_failure` 不会使路由避开故障链路。
- 使用随机异常生成脚本时固定随机种子，并记录被修改的链路，确保实验可复现。
