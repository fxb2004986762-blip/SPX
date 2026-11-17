# PSN-PATH 核心算法 ns-3 简化复现说明

## 0. 文档目标

本文档的目标不是逐行复刻 PSN-PATH 官方 ns-3 artifact，而是：

> **在已有 ns-3 RDMA 仿真框架中，以尽可能少的代码完整复现论文提出的核心算法思想。**

实现应保留以下五个核心机制：

1. **PSN-to-Path Mapping**：利用 PSN 确定性地将 packet 映射到 logical path / physical path；
2. **Per-Path Continuity Check**：只检查同一路径内部的 PSN 连续性，以区分跨路径 OOO 与真实 packet loss；
3. **Fast Selective Retransmission**：确认同路径丢包后立即 NACK，只重传真正丢失的数据；
4. **Safe Path Remapping**：通过 (FPSN_\ell) 区分切路前后的 packet，避免 remapping 引入错误 loss detection；
5. **Path Manager / DT-Switch**：利用 ACK/NACK 反馈评估路径质量，探索、移除并替换异常路径。

---

# 1. 核心算法思想

## 1.1 问题：传统 RDMA 无法区分 OOO 与真实丢包

传统 RDMA receiver 使用全局 PSN：

[
0,1,2,3,4,\ldots
]

判断 packet 是否连续。

若当前：

[
ePSN=7
]

却先收到：

[
PSN=8
]

传统机制看到：

[
7\rightarrow8
]

之间存在 gap，因此容易认为 PSN 7 丢失。

但在 packet-level multipath 中，可能只是：

* PSN 7 走慢路径；
* PSN 8 走快路径；

所以：

[
PSN\ gap
\not\Rightarrow
packet\ loss
]

这就是 PSN-PATH 要解决的核心问题。论文将其概括为：OOO 和真实 loss 都表现为 PSN discontinuity，因此单一 global PSN continuity 对 multipath 网络是过度约束。

---

## 1.2 核心改变：从 Global Ordering 改为 Per-Path Ordering

PSN-PATH 假设：

> packet 在不同路径之间可能发生 OOO，但同一条物理路径内部通常保持 FIFO。

因此定义：

[
\ell = PSN\bmod K
]

其中：

* (K)：该 QP 当前使用的 logical path 数；
* (\ell)：该 packet 所属 logical path index。

例如：

[
K=4
]

则：

```text
logical path 0 : PSN 0, 4, 8, 12, 16, ...
logical path 1 : PSN 1, 5, 9, 13, 17, ...
logical path 2 : PSN 2, 6, 10, 14, 18, ...
logical path 3 : PSN 3, 7, 11, 15, 19, ...
```

因此对于：

[
PSN=11
]

不应该检查：

[
10
]

是否到达，而应该检查同一路径上的 predecessor：

[
PSN_{prev}=11-K=7
]

于是核心判定变成：

[
\boxed{
PSN_{prev}\ 已收到
\Rightarrow
当前 packet 是合法 OOO
}
]

[
\boxed{
PSN_{prev}\ 未收到
\Rightarrow
同一路径 PSN 不连续
\Rightarrow
真实 loss
}
]

这是整个 PSN-PATH 最核心的算法思想。

---

# 2. Sender：PSN-to-Path Mapping

## 2.1 Logical Path

定义：

[
\ell=PSN\bmod K
]

logical path 是一个稳定的逻辑编号。

即使 physical path 后续发生切换：

[
PSN=3,7,11,15
]

依然属于 logical path 3。

---

## 2.2 Physical Path

每个 logical path (\ell) 维护：

[
O_\ell
]

实际 UDP source port 为：

P_{base}+\ell+O_\ell
]

交换机继续执行普通 ECMP：

```text
PSN
 ↓
logical path = PSN % K
 ↓
offset O[l]
 ↓
UDP source port
 ↓
ECMP hash
 ↓
physical network path
```

因此：

> **PSN-PATH 不需要修改交换机。**

官方 artifact 同样通过修改 UDP source port 接入现有 ECMP；其 sender packet path-selection 位于 `RdmaHw::GetNxtPacket()`。

---

# 3. Receiver：Per-Path Loss Detection

receiver 已有一个 per-QP arrival bitmap：

```text
bitmap[PSN] = 1  packet 已到达
bitmap[PSN] = 0  packet 尚未到达
```

收到 packet (P)：

```text
P < ePSN
    ↓
duplicate / old packet

P == ePSN
    ↓
in-order packet

P > ePSN
    ↓
OOO packet
    ↓
检查同路径 predecessor
```

核心：

[
prev=P-K
]

如果：

[
bitmap[prev]=1
]

说明：

```text
同一路径：
prev 已到 → current 后到

该路径内部没有 gap
```

所以当前 global OOO 是其他路径造成的：

```text
CROSS_PATH_OOO
→ 接受
→ 不生成 NACK
```

反之：

[
bitmap[prev]=0
]

说明：

```text
同一路径：
prev 未到
current 已到
```

在 FIFO 假设下：

```text
SAME_PATH_GAP
→ 确认 prev 丢失
→ 立即生成 NACK(prev)
```

官方 artifact 对这一逻辑进行了更通用的实现：它会扫描 `[ePSN, currentPSN)` 中所有映射到当前 physical path 的缺失 PSN，而不只检查 `PSN-K`，以适配其动态 `activePathMask/epoch` 实现。

本项目为了复现**论文算法思想**，第一版建议严格实现：

[
prev=PSN-K
]

即可。

---

# 4. Path Remapping 与 FPSN

只实现：

[
PSN\bmod K
]

还不够。

例如 logical path 3：

```text
PSN:       3 ---- 7 ---- 11 ---- 15
physical:  A      A      B       B
                         ↑
                      remap
```

假设：

* PSN 7 还在旧路径 A 中；
* PSN 11 已经通过新路径 B 到达。

如果直接检查：

[
11-4=7
]

会错误认为 PSN 7 丢失。

因此每个 logical path (\ell) 维护：

[
FPSN_\ell
]

即：

> 当前 physical mapping 下发送的第一个 PSN。

例如：

```text
旧 mapping:
offset[3] = 0
FPSN[3]   = 3

新 mapping:
offset[3] = 1
FPSN[3]   = 11
```

packet 11 携带：

```text
logicalPath = 3
FPSN        = 11
```

receiver 看到：

```text
packet.FPSN > localFPSN[3]
```

即可知道：

> 这是 remapping 后新 physical path 的第一个 packet。

此时：

```text
更新 localFPSN[3] = 11
接受 packet 11
跳过 11 - K = 7 的 continuity check
```

从而允许旧路径上的 PSN 7 继续飞行。论文专门利用 `FPSN` 作为 remapping boundary 解决这个问题。

---

# 5. 推荐的数据结构

建议主要放在：

```text
rdma-queue-pair.h
```

中。

---

## 5.1 Sender Mapping State

```cpp
struct PsnPathMappingState {
    uint16_t offset = 0;       // O_l
    uint32_t fpsn = 0;         // 当前 mapping 的 First PSN

    bool active = true;

    // DT-Switch
    bool probing = false;
    uint16_t candidateOffset = 0;
    uint32_t probeStep = 10;   // paper default f = 10
    uint32_t candidateAckCnt = 0;
};
```

每个 QP：

```cpp
struct PsnPathTxState {
    bool enabled = false;

    uint32_t k = 4;
    uint16_t basePort = 10000;
    uint32_t packetSize = 0;

    std::vector<PsnPathMappingState> mapping;

    std::deque<PsnRetransRequest> retransQueue;
};
```

---

## 5.2 Path Quality State

```cpp
struct PsnPathQuality {
    uint64_t ackCount = 0;
    uint64_t nackCount = 0;

    double score = 0.0;
};
```

每个 physical candidate path / logical mapping 维护一份。

---

## 5.3 Retransmission State

```cpp
struct PsnRetransRequest {
    uint32_t startPsn = 0;
    uint32_t endPsn = 0;

    // 用于保持原始 mapping 语义
    uint32_t originalFpsn = 0;
};
```

官方 artifact 同样维护 `PsnRetransRequest` 队列，并在发送时优先处理该队列。

---

## 5.4 Receiver State

```cpp
struct PsnPathRxState {
    uint32_t expectedPsn = 0;

    // 可直接复用现有 RDMA receiver bitmap
    std::vector<bool> bitmap;

    // 每个 logical path 当前观察到的 mapping boundary
    std::vector<uint32_t> localFpsn;
};
```

官方 artifact 的 `RdmaRxQueuePair` 同样保存 arrival bitmap 和 mapping history。

---

# 6. Packet Metadata

建议定义在：

```text
psn-path.h
psn-path.cc
```

使用 ns-3 `PacketTag` 模拟论文中的 RDMA extension header。

```cpp
class PsnPathTag : public Tag {
public:
    void SetK(uint32_t k);
    uint32_t GetK() const;

    void SetOffset(uint16_t offset);
    uint16_t GetOffset() const;

    void SetFpsn(uint32_t fpsn);
    uint32_t GetFpsn() const;

    void SetFlowSport(uint16_t sport);
    uint16_t GetFlowSport() const;

private:
    uint32_t m_k;
    uint16_t m_offset;
    uint32_t m_fpsn;

    // 用于 receiver 找回原始 QP
    uint16_t m_flowSport;
};
```

论文真正需要的 path metadata 本质上是：

```text
K
O_l
FPSN_l
```

官方 artifact 的 `PsnPathTag` 额外保存：

```text
epoch
activePathMask
pathId
probe
flowSport
```

这是其 ns-3 工程实现所需状态，不是复现论文基本算法必须全部保留的字段。

---

# 7. 核心函数接口

---

## 7.1 PSN 基础映射函数

### 文件

```text
psn-path.h
psn-path.cc
```

### 接口

```cpp
uint32_t GetPsnFromSeq(
    uint32_t seq,
    uint32_t packetSize
);
```

### 功能

将 ns-3 RDMA 使用的 byte sequence number 转换为 PSN：

[
PSN=\frac{seq}{packetSize}
]

### 输入

```text
seq        = packet byte offset
packetSize = 每个 PSN packet 对应的数据大小
```

### 输出

```text
PSN
```

官方 artifact 已提供同名函数。

---

## 7.2 获取 Logical Path

### 文件

```text
psn-path.h
psn-path.cc
```

### 接口

```cpp
uint32_t GetLogicalPath(
    uint32_t psn,
    uint32_t k
);
```

### 功能

```cpp
return psn % k;
```

即：

[
\ell=PSN\bmod K
]

---

## 7.3 获取 Same-Path Predecessor

### 文件

```text
psn-path.h
psn-path.cc
```

### 接口

```cpp
bool GetSamePathPredecessor(
    uint32_t psn,
    uint32_t k,
    uint32_t fpsn,
    uint32_t& prevPsn
);
```

### 功能

正常情况：

[
prevPsn=PSN-K
]

但如果：

```text
PSN == FPSN
```

或者：

[
PSN-K<FPSN
]

说明该 packet 是当前 mapping 中的第一个 packet，没有合法 same-path predecessor。

此时：

```cpp
return false;
```

否则：

```cpp
prevPsn = psn - k;
return true;
```

---

## 7.4 计算发送端 Source Port

### 文件

```text
psn-path.h
psn-path.cc
```

### 接口

```cpp
uint16_t GetPsnPathSourcePort(
    uint32_t psn,
    uint32_t k,
    uint16_t basePort,
    const std::vector<PsnPathMappingState>& mapping
);
```

### 逻辑

```cpp
uint32_t l = psn % k;

return basePort
       + l
       + mapping[l].offset;
```

即：

[
P_{source}=P_{base}+\ell+O_\ell
]

---

# 8. Sender Data Path 接口

## 8.1 ApplyPsnPathMapping()

### 文件

```text
rdma-hw.h
rdma-hw.cc
```

### 接口

```cpp
uint16_t ApplyPsnPathMapping(
    Ptr<RdmaQueuePair> qp,
    Ptr<Packet> packet,
    uint32_t psn,
    bool isRetransmission
);
```

### 功能

执行完整 sender-side Path Mapper：

```text
PSN
 ↓
logicalPath = PSN % K
 ↓
读取 O_l / FPSN_l
 ↓
计算 UDP source port
 ↓
构造 PsnPathTag
 ↓
附加至 packet
```

### 返回

```text
最终 UDP source port
```

### 正常 packet

```cpp
l = psn % K;

sourcePort =
    basePort
    + l
    + mapping[l].offset;

tag.K      = K;
tag.offset = mapping[l].offset;
tag.fpsn   = mapping[l].fpsn;
```

---

## 8.2 SelectNextTxPsn()

### 文件

```text
rdma-hw.h
rdma-hw.cc
```

### 接口

```cpp
uint32_t SelectNextTxPsn(
    Ptr<RdmaQueuePair> qp,
    bool& isRetransmission
);
```

### 功能

发送优先级：

```text
retransQueue 非空
        ↓ yes
发送重传 packet

        ↓ no
发送 snd_nxt 对应的新 packet
```

即：

```cpp
if (!retransQueue.empty()) {
    isRetransmission = true;
    return retransQueue.front().startPsn;
}

isRetransmission = false;
return snd_nxt / packetSize;
```

官方 artifact 的 `GetNxtPacket()` 就采用这种“PSN retransmission queue 优先于新数据”的方式。

---

# 9. Receiver 核心接口

这是整个实现中**最重要的函数**。

## 9.1 ReceiverCheckSeqPsnPath()

### 文件

```text
rdma-hw.h
rdma-hw.cc
```

### 接口

推荐：

```cpp
enum class PsnRxResult {
    IN_ORDER,
    CROSS_PATH_OOO,
    SAME_PATH_LOSS,
    REMAP_FIRST_PACKET,
    OLD_MAPPING_PACKET,
    DUPLICATE
};

struct PsnRxDecision {
    PsnRxResult result;

    bool sendNack = false;
    uint32_t nackPsn = 0;
};

PsnRxDecision ReceiverCheckSeqPsnPath(
    Ptr<RdmaRxQueuePair> qp,
    uint32_t psn,
    uint32_t packetSize,
    const PsnPathTag& tag
);
```

官方 artifact 也使用 `RdmaHw::ReceiverCheckSeqPsnPath()` 作为 PSN-PATH receiver 的核心入口。

---

## 9.2 ReceiverCheckSeqPsnPath() 推荐核心逻辑

```cpp
PsnRxDecision
ReceiverCheckSeqPsnPath(...)
{
    uint32_t epsn = qp->psnPath.expectedPsn;
    uint32_t k = tag.GetK();

    uint32_t l = psn % k;

    // ------------------------------------------------
    // Case 1: duplicate / old packet
    // ------------------------------------------------
    if (psn < epsn) {
        return {DUPLICATE, false, 0};
    }

    // ------------------------------------------------
    // Case 2: in-order packet
    // ------------------------------------------------
    if (psn == epsn) {
        MarkReceived(psn);
        AdvanceExpectedPsn();
        return {IN_ORDER, false, 0};
    }

    // 到这里一定满足 psn > epsn
    MarkReceived(psn);

    uint32_t packetFpsn = tag.GetFpsn();
    uint32_t localFpsn  = qp->psnPath.localFpsn[l];

    // ------------------------------------------------
    // Case 3: first packet after remapping
    // ------------------------------------------------
    if (packetFpsn > localFpsn) {

        qp->psnPath.localFpsn[l] = packetFpsn;

        // 不能跨 remapping boundary 检查 predecessor
        return {REMAP_FIRST_PACKET, false, 0};
    }

    // ------------------------------------------------
    // Case 4: old-path packet after remapping
    // ------------------------------------------------
    bool oldMapping =
        packetFpsn < localFpsn;

    // ------------------------------------------------
    // Case 5: same-path predecessor
    // ------------------------------------------------
    uint32_t prevPsn;

    if (!GetSamePathPredecessor(
            psn,
            k,
            packetFpsn,
            prevPsn)) {

        return {
            oldMapping
                ? OLD_MAPPING_PACKET
                : CROSS_PATH_OOO,
            false,
            0
        };
    }

    // ------------------------------------------------
    // Case 6: same-path continuity holds
    // ------------------------------------------------
    if (IsReceived(prevPsn)) {

        return {
            oldMapping
                ? OLD_MAPPING_PACKET
                : CROSS_PATH_OOO,
            false,
            0
        };
    }

    // ------------------------------------------------
    // Case 7: real loss
    // ------------------------------------------------
    return {
        SAME_PATH_LOSS,
        true,
        prevPsn
    };
}
```

---

# 10. Receiver Bitmap 接口

建议继续使用现有 receiver bitmap，而不是重新实现一套。

### 文件

```text
rdma-queue-pair.h
rdma-hw.cc
```

### 接口

```cpp
bool IsReceived(
    Ptr<RdmaRxQueuePair> qp,
    uint32_t psn
);

void MarkReceived(
    Ptr<RdmaRxQueuePair> qp,
    uint32_t psn
);

void AdvanceExpectedPsn(
    Ptr<RdmaRxQueuePair> qp
);
```

### AdvanceExpectedPsn()

典型逻辑：

```cpp
while (bitmap[expectedPsn]) {
    bitmap[expectedPsn] = false;
    expectedPsn++;
}
```

官方 artifact 同样在 in-order packet 到达后持续扫描 bitmap，将已经提前到达的连续 OOO 数据一起消费掉。

---

# 11. Fast Retransmission

## 11.1 SendPsnPathNack()

### 文件

```text
rdma-hw.h
rdma-hw.cc
```

如果现有 NACK header 不支持 selective retransmission：

```text
qbb-header.h
qbb-header.cc
```

需要加入 missing PSN 字段。

### 接口

```cpp
void SendPsnPathNack(
    Ptr<RdmaRxQueuePair> qp,
    uint32_t missingPsn
);
```

至少携带：

```text
missing PSN
```

若完全复现论文：

```text
<Path ID, K, Start_PSN, End_PSN>
```

论文使用该 tuple 指定需要重传的 PSN 范围。

官方 artifact 复用了已有 IRN NACK：

```cpp
SetIrnNack(seq);
SetIrnNackSize(size);
```

对应字段位于 `qbb-header.h`。

---

## 11.2 HandlePsnPathNack()

### 文件

```text
rdma-hw.h
rdma-hw.cc
```

### 接口

```cpp
void HandlePsnPathNack(
    Ptr<RdmaQueuePair> qp,
    uint32_t startPsn,
    uint32_t endPsn
);
```

### 功能

```text
收到 NACK
 ↓
检查 retransQueue 是否已经存在
 ↓
不存在
 ↓
加入 retransQueue
 ↓
TriggerTransmit()
```

建议去重：

```cpp
for (auto& r : retransQueue) {
    if (r.startPsn == startPsn &&
        r.endPsn   == endPsn)
        return;
}
```

官方 artifact 也会对 retransmission request 去重后加入 `pendingRetrans`。

---

# 12. Path Feedback

## 12.1 UpdatePsnPathFeedback()

### 文件

```text
rdma-hw.h
rdma-hw.cc
```

### 接口

```cpp
void UpdatePsnPathFeedback(
    Ptr<RdmaQueuePair> qp,
    uint32_t psn,
    bool isNack
);
```

### 功能

先：

```cpp
logicalPath = psn % K;
```

然后：

```cpp
if (isNack)
    quality[path].nackCount++;
else
    quality[path].ackCount++;
```

官方 artifact 在 `ReceiveAck()` 中完成相同的 ACK/NACK path statistics 更新。

---

# 13. Path Score

## 13.1 ComputePathScore()

### 文件

```text
psn-path.h
psn-path.cc
```

### 接口

```cpp
double ComputePathScore(
    uint64_t ackCount,
    uint64_t nackCount,
    double beta
);
```

论文写为：

[
Score=
ACK_{count}
-\beta NACK_{count}
]

默认：

[
\beta=0.5
]

Path Manager 每约一个 RTT 统计一次 ACK/NACK。

---

## 13.2 一个必须注意的论文歧义

论文同时给出：

[
T_{explore}=0.95
]

[
T_{remove}=0.85
]

但正文又将 Score 写成：

[
ACK-\beta NACK
]

原始 count-score 与 `0.95/0.85` 的数值尺度并不直接一致。

因此：

> **论文在这里没有把 score normalization 过程描述完整。**

不要在复现时假装不存在这个问题。

当前 GitHub artifact 实际使用：

```text
score = ACK - beta * NACK

beta      = 1.0
TExplore  = 2
TRemove   = 0
```

而不是论文正文的 `0.5 / 0.95 / 0.85`。

因此推荐：

### 第一版

先不追求阈值数值完全一致，只实现：

```text
healthy
degraded
failed
```

三档状态机。

随后再单独校准 score。

---

# 14. Path Manager / DT-Switch

## 14.1 EvaluatePsnPaths()

### 文件

```text
rdma-hw.h
rdma-hw.cc
```

### 接口

```cpp
void EvaluatePsnPaths(
    Ptr<RdmaQueuePair> qp
);
```

建议每：

```text
1 RTT
```

调用一次。

---

## 14.2 Path Manager 状态机

### Healthy

```text
Score >= T_explore
```

输出：

```text
KEEP
```

---

### Degraded

```text
T_remove <= Score < T_explore
```

输出：

```text
START_PROBE
```

开始探索 candidate path。

---

### Failed

```text
Score < T_remove
```

输出：

```text
REMOVE_AND_REMAP
```

立即降低或停止使用该 physical path。

论文明确提出 exploration threshold 与 removal threshold 两级机制。

---

# 15. StartPathProbe()

### 文件

```text
rdma-hw.h
rdma-hw.cc
```

### 接口

```cpp
void StartPathProbe(
    Ptr<RdmaQueuePair> qp,
    uint32_t logicalPath,
    uint16_t candidateOffset
);
```

初始化：

```cpp
mapping[l].probing = true;
mapping[l].candidateOffset = candidateOffset;
mapping[l].probeStep = 10;
mapping[l].candidateAckCnt = 0;
```

论文默认：

[
f=10
]

---

# 16. SelectProbeOrCurrentPath()

### 文件

```text
psn-path.cc
```

### 接口

```cpp
uint16_t SelectProbeOrCurrentOffset(
    PsnPathMappingState& state
);
```

正常：

```text
每 f 个 current-path packet
```

发送：

```text
1 个 candidate-path packet
```

即候选路径流量比例约：

[
\frac{1}{f+1}
]

---

# 17. HandleProbeAck()

### 文件

```text
rdma-hw.cc
```

### 接口

```cpp
void HandleProbeAck(
    Ptr<RdmaQueuePair> qp,
    uint32_t logicalPath
);
```

candidate path 每获得：

[
f
]

个 ACK：

```cpp
f--;
```

例如：

```text
f = 10
 ↓
9
 ↓
8
 ↓
...
```

逐步提高 candidate path 流量。

---

# 18. HandleProbeNack()

### 文件

```text
rdma-hw.cc
```

### 接口

```cpp
void HandleProbeNack(
    Ptr<RdmaQueuePair> qp,
    uint32_t logicalPath
);
```

输出：

```text
ABORT_PROBE
```

操作：

```cpp
probing = false;
candidateAckCnt = 0;
```

继续使用原路径。

---

# 19. CommitPathRemap()

这是 remapping 最核心的接口。

### 文件

```text
rdma-hw.h
rdma-hw.cc
```

### 接口

```cpp
void CommitPathRemap(
    Ptr<RdmaQueuePair> qp,
    uint32_t logicalPath,
    uint16_t newOffset
);
```

### 输入

```text
logicalPath = l
newOffset   = new O_l
```

### 操作

```cpp
mapping[l].offset = newOffset;

mapping[l].fpsn =
    snd_nxt / packetSize;
```

即：

\text{下一包的 PSN}
]

从这一 packet 开始：

```text
新的 physical mapping 生效
```

官方 artifact 在 active path set 变化后同样：

* 更新 FPSN；
* 更新 mapping state；
* 让后续 packet 携带新 mapping metadata。

---

# 20. 整套函数的逻辑关系

```text
                         AddQueuePair()
                              │
                              ▼
                    初始化 PsnPathTxState
                    K / offset / FPSN
                              │
                              ▼
┌──────────────────────────────────────────────────────┐
│                     Sender                           │
│                                                      │
│ SelectNextTxPsn()                                    │
│       │                                              │
│       ▼                                              │
│ ApplyPsnPathMapping()                                │
│       │                                              │
│       ├─ GetLogicalPath()                            │
│       ├─ GetPsnPathSourcePort()                      │
│       └─ Attach PsnPathTag                           │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
                    Network
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│                    Receiver                          │
│                                                      │
│ ReceiverCheckSeqPsnPath()                            │
│       │                                              │
│       ├── IN_ORDER ───────────► ACK                  │
│       │                                              │
│       ├── CROSS_PATH_OOO ─────► accept               │
│       │                                              │
│       ├── REMAP_FIRST_PACKET ─► accept               │
│       │                                              │
│       ├── OLD_MAPPING_PACKET ─► accept / check       │
│       │                                              │
│       └── SAME_PATH_LOSS                             │
│                  │                                   │
│                  ▼                                   │
│          SendPsnPathNack()                           │
└──────────────────────┬───────────────────────────────┘
                       │
                    ACK/NACK
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│                     Sender                           │
│                                                      │
│ UpdatePsnPathFeedback()                              │
│       │                                              │
│       ├─ ACK  → ackCount++                           │
│       └─ NACK → nackCount++                          │
│                │                                     │
│                ▼                                     │
│        HandlePsnPathNack()                           │
│                │                                     │
│                ▼                                     │
│          retransQueue                                │
│                │                                     │
│                └────────► SelectNextTxPsn()           │
└──────────────────────────────────────────────────────┘


每 RTT：

EvaluatePsnPaths()
        │
        ├── Healthy
        │     └── keep
        │
        ├── Degraded
        │     └── StartPathProbe()
        │            │
        │            ├── ACK → HandleProbeAck()
        │            └── NACK → HandleProbeNack()
        │
        └── Failed / Better Candidate
                    │
                    ▼
             CommitPathRemap()
                    │
                    ├── update O_l
                    └── update FPSN_l
```

---

# 21. 全逻辑覆盖示例

以下示例建议直接作为后续单元测试 / debug testcase。

统一设定：

```text
K = 4
basePort = 10000

offset[0] = 0
offset[1] = 0
offset[2] = 0
offset[3] = 0
```

因此：

```text
path 0 : 0,4,8,12,...
path 1 : 1,5,9,13,...
path 2 : 2,6,10,14,...
path 3 : 3,7,11,15,...
```

---

## Case 1：正常发送映射

输入：

```text
PSN = 7
K   = 4
```

计算：

[
7\bmod4=3
]

输出：

```text
logicalPath = 3
sourcePort  = 10003
FPSN        = 当前 mapping[3].fpsn
```

---

# Case 2：正常 In-order packet

receiver：

```text
ePSN = 7
```

输入：

```text
PSN = 7
```

输出：

```text
result = IN_ORDER
NACK   = no
```

状态：

```text
ePSN → 8
```

如果 bitmap 中：

```text
8 = received
9 = received
10 = missing
```

则进一步：

```text
ePSN → 10
```

---

# Case 3：典型跨路径 OOO

当前：

```text
ePSN = 7
```

收到：

```text
PSN = 8
```

两者：

```text
7 % 4 = 3
8 % 4 = 0
```

PSN 8 的 same-path predecessor：

[
8-4=4
]

假设：

```text
bitmap[4] = 1
```

说明 path 0 连续。

输出：

```text
result = CROSS_PATH_OOO
NACK   = no
bitmap[8] = received
ePSN 仍然 = 7
```

这是 PSN-PATH 必须正确处理的最基本场景。

---

# Case 4：OOO，但当前路径内部完全正常

当前：

```text
ePSN = 6
```

输入：

```text
PSN = 11
```

PSN 11：

```text
logicalPath = 3
prev        = 7
```

假设：

```text
bitmap[7] = 1
```

虽然：

```text
6 尚未到达
```

但 6 属于 path 2。

因此：

```text
path 3:
3 → 7 → 11
```

连续。

输出：

```text
result = CROSS_PATH_OOO
NACK   = no
```

绝不能因为 global gap `6...11` 而 NACK。

---

# Case 5：真实 Same-Path Loss

当前：

```text
ePSN = 7
```

输入：

```text
PSN = 11
```

计算：

```text
11 % 4 = 3
prev = 11 - 4 = 7
```

bitmap：

```text
bitmap[7] = 0
```

说明：

```text
path 3:
3 → [7 missing] → 11 received
```

在 FIFO 假设下：

```text
PSN 7 = real loss
```

输出：

```text
result  = SAME_PATH_LOSS
sendNack = true
nackPsn  = 7
```

随后：

```text
sender.retransQueue.push(7)
```

---

# Case 6：Duplicate Packet

当前：

```text
ePSN = 12
```

输入：

```text
PSN = 7
```

满足：

[
7<12
]

输出：

```text
result = DUPLICATE
NACK   = no
```

packet：

```text
直接丢弃
或按现有 RDMA 逻辑返回 ACK
```

不能产生新的 loss event。

---

# Case 7：第一次 Path Remapping

原 mapping：

```text
logical path 3
offset[3] = 0
FPSN[3]   = 3
```

已发送：

```text
PSN 3
PSN 7
```

Path Manager 决定切路。

执行：

```cpp
CommitPathRemap(
    qp,
    3,
    1
);
```

假设：

```text
next PSN on logical path 3 = 11
```

新状态：

```text
offset[3] = 1
FPSN[3]   = 11
```

后续：

```text
PSN 11
PSN 15
...
```

使用新 physical path。

---

# Case 8：Remap 后新 packet 先到

网络中：

```text
PSN 7  → old path A → 慢
PSN 11 → new path B → 快
```

PSN 11 先到。

packet：

```text
PSN        = 11
packetFPSN = 11
```

receiver：

```text
localFPSN[3] = 3
```

满足：

[
11>3
]

输出：

```text
result = REMAP_FIRST_PACKET
localFPSN[3] = 11
NACK = no
```

关键：

```text
不要检查 11 - 4 = 7
```

否则会把仍在 old path 上的 7 错误判断为丢包。

---

# Case 9：Old-path Packet 在 remap 后到达

在 Case 8 后：

```text
localFPSN[3] = 11
```

此时旧 packet 7 到达：

```text
PSN        = 7
packetFPSN = 3
```

满足：

[
3<11
]

因此知道：

```text
PSN 7 属于历史 mapping
```

其 old-path predecessor：

[
7-4=3
]

假设：

```text
bitmap[3] = 1
```

输出：

```text
result = OLD_MAPPING_PACKET
NACK = no
```

这样允许 old/new mapping packet 在网络中同时存在。

---

# Case 10：切路前最后一个 packet 丢失

这是必须覆盖的 edge case。

旧 path：

```text
3 → 7
```

其中：

```text
PSN 7 丢失
```

随后 remap：

```text
11 → new path
```

PSN 11 是：

```text
FPSN = 11
```

因此 receiver 对 11：

```text
跳过 predecessor check
```

于是：

```text
7 的 loss 无法通过 PSN 11 发现
```

这是正确行为。

因为 7 和 11 已经不属于同一个 physical mapping。

因此：

```text
PSN 7
 ↓
最终由 timeout recovery 发现
```

论文明确指出：

> remapping boundary 前最后一个 packet 如果丢失，需要由正常 timeout-based retransmission 恢复。

---

# Case 11：Flow Tail Loss

例如：

```text
最后一个 packet = PSN 103
```

103 丢失。

之后没有：

```text
PSN 107
```

作为 same-path successor。

因此没有证据：

```text
103 → ? → later same-path packet
```

PSN-PATH 无法立即利用 continuity check 检测。

结果：

```text
FAST NACK = 无法触发
```

最终：

```text
timeout recovery
```

这是 per-path successor-based detection 必然存在的边界。

---

# Case 12：收到 Fast NACK

sender 收到：

```text
NACK:
missingPsn = 7
```

输入：

```text
retransQueue = empty
```

执行：

```text
enqueue 7
```

输出：

```text
retransQueue = [7]
```

随后 sender：

```text
先发 PSN 7
再继续发新 packet
```

---

# Case 13：重复 NACK

当前：

```text
retransQueue = [7]
```

再次收到：

```text
NACK(7)
```

输出：

```text
不重复 enqueue
```

保持：

```text
retransQueue = [7]
```

避免冗余重传。

---

# Case 14：重传 packet 已经成功收到

可能发生：

```text
原 packet 7 最终晚到
```

同时：

```text
retransmitted 7
```

也到达。

第一个：

```text
bitmap[7] = received
```

第二个属于：

```text
PSN < ePSN
```

输出：

```text
DUPLICATE
discard
```

保证 data consistency。

---

# Case 15：重传时路径已经切换

原始：

```text
PSN 7
logical path = 3
old physical path = A
```

A 发生异常。

Path Manager 已将 logical path 3 remap 到 B。

重传：

```text
PSN = 7
```

仍然保持：

```text
original PSN
original FPSN
```

但实际 UDP source port 可以选择：

```text
healthy physical path B
```

因此：

> **retransmission 不要求走原来的坏路径。**

论文明确允许 retransmitted packet 经不同的健康路径传输。

---

# Case 16：Healthy Path

一个 evaluation epoch：

```text
ACK = many
NACK = few / zero
Score >= T_explore
```

输出：

```text
KEEP
```

状态：

```text
active = true
probing = false
```

---

# Case 17：Degraded Path

输入：

```text
T_remove <= Score < T_explore
```

输出：

```text
START_PROBE
```

假设：

```text
current offset   = 0
candidate offset = 1
f                = 10
```

流量：

```text
current current current ... ×10
candidate ×1
```

---

# Case 18：Candidate Path 持续成功

candidate 收到：

```text
10 ACK
```

执行：

```text
f: 10 → 9
```

之后 candidate probe 频率增加。

继续成功：

```text
9 ACK
 ↓
f: 9 → 8
```

最终 candidate 被证明质量不低于原 path：

```text
CommitPathRemap()
```

---

# Case 19：Candidate Path Probe 失败

candidate packet 返回：

```text
NACK
```

输出：

```text
ABORT_PROBE
```

保持：

```text
old offset
old FPSN
```

不执行 remapping。

---

# Case 20：严重异常 Path

输入：

```text
Score < T_remove
```

输出：

```text
REMOVE / REMAP
```

选择新的 candidate offset：

```text
offset[l] = newOffset
FPSN[l]   = nextPsn
```

从下一 packet 开始新 mapping。

---

# Case 21：所有路径都异常

论文没有详细定义所有 candidate 同时失效时的完整状态机。

工程实现应加入防御规则：

```text
至少保留一个 path
或
回退到默认 ECMP / timeout recovery
```

这是：

> **仿真实现安全措施，不属于论文核心创新。**

官方 artifact 也显式避免 active path 数降为 0。

---

# Case 22：Bitmap Window Overflow

如果：

```text
PSN - ePSN
```

超过 receiver bitmap 能表示的最大窗口：

PSN-PATH 本身并未发明新的 bitmap overflow 处理方式。

推荐：

```text
继续使用你现有 ns-3 RDMA / IRN 的处理逻辑
```

例如：

```text
timeout
NACK
drop
```

具体取决于当前 transport。

不要把 bitmap 管理问题和 PSN-PATH 的：

```text
OOO-loss discrimination
```

混在一起。

---

# 22. 推荐实现顺序

虽然完整算法包含上述所有模块，但实际编码建议分三阶段。

## Phase 1：最核心算法

只实现：

```text
GetPsnFromSeq()
GetLogicalPath()
GetSamePathPredecessor()
ApplyPsnPathMapping()
ReceiverCheckSeqPsnPath()
SendPsnPathNack()
HandlePsnPathNack()
SelectNextTxPsn()
```

固定：

```text
K = 4
offset = 0
不切路
```

目标：

> 验证 PSN-PATH 是否能够区分 cross-path OOO 与 real loss，并消除 spurious retransmission。

这是论文最本质的创新。

---

## Phase 2：Safe Remapping

增加：

```text
offset[l]
FPSN[l]
localFPSN[l]

CommitPathRemap()
```

重点测试：

```text
new-path packet 先到
old-path packet 后到
boundary packet loss
```

---

## Phase 3：Path Manager

最后增加：

```text
ACK/NACK statistics
ComputePathScore()
EvaluatePsnPaths()
StartPathProbe()
HandleProbeAck()
HandleProbeNack()
CommitPathRemap()
```

这样如果最终性能出现问题，可以清楚判断问题来自：

```text
loss detection
```

还是：

```text
path switching
```

---

# 23. 建议最终修改的文件

```text
src/point-to-point/model/
│
├── psn-path.h
│   ├── PsnPathTag
│   ├── PsnRxResult
│   ├── PsnRxDecision
│   ├── GetPsnFromSeq()
│   ├── GetLogicalPath()
│   ├── GetSamePathPredecessor()
│   ├── GetPsnPathSourcePort()
│   └── ComputePathScore()
│
├── psn-path.cc
│   └── 上述纯算法函数实现
│
├── rdma-queue-pair.h
│   ├── PsnPathMappingState
│   ├── PsnPathQuality
│   ├── PsnRetransRequest
│   ├── PsnPathTxState
│   └── PsnPathRxState
│
├── rdma-hw.h
│   ├── ApplyPsnPathMapping()
│   ├── ReceiverCheckSeqPsnPath()
│   ├── SendPsnPathNack()
│   ├── HandlePsnPathNack()
│   ├── UpdatePsnPathFeedback()
│   ├── EvaluatePsnPaths()
│   ├── StartPathProbe()
│   ├── HandleProbeAck()
│   ├── HandleProbeNack()
│   └── CommitPathRemap()
│
├── rdma-hw.cc
│   └── PSN-PATH 与现有 sender/receiver 数据路径的集成
│
└── qbb-header.h/.cc
    └── 仅当现有 NACK 无法携带 missing PSN 时修改
```

---

# 24. 最终应满足的核心不变量

实现完成后，可以用下面四条判断你的版本是否真正复现了 PSN-PATH。

## 不变量 1：固定 Mapping

在没有 remapping 时：

PSN_b\bmod K
]

意味着两 packet 属于同一个 logical path sequence。

---

## 不变量 2：不同路径乱序不能触发 Fast NACK

如果：

[
Path(A)\neq Path(B)
]

则：

```text
B 先到、A 后到
```

不能仅凭 global PSN gap 判断 A 丢失。

---

## 不变量 3：同路径后继到达可以证明前序丢失

如果：

[
Path(A)=Path(B)
]

且：

[
A<B
]

同时：

```text
B received
A missing
```

则：

[
A=\text{confirmed loss}
]

立即触发 selective retransmission。

---

## 不变量 4：Continuity Check 绝不能跨 Remapping Boundary

如果：

```text
A 属于 old mapping
B 属于 new mapping
```

即使：

[
B=A+K
]

也不能根据 B 的到达判断 A 丢失。

这正是：

[
FPSN_\ell
]

存在的意义。

---

# 25. 一句话总结整个实现

最终整个 PSN-PATH 可以压缩为：

```text
Sender:
PSN
 → PSN % K
 → UDP source port
 → deterministic per-path sequence

Receiver:
OOO packet
 → 找同路径 predecessor
 → predecessor arrived
      → legal cross-path OOO
 → predecessor missing
      → real packet loss
      → immediate selective retransmission

Path Manager:
ACK/NACK
 → path quality
 → probe / remove
 → update offset
 → establish new FPSN boundary
```

即：

[
\boxed{
\text{PSN-to-Path Mapping}
+
\text{Per-Path Continuity}
+
\text{Fast SR}
+
\text{Safe Remapping}
+
\text{Adaptive Path Management}
}
]

这五部分构成论文提出的完整 PSN-PATH 算法思想。
