# Simulation Automation Pipeline

## 1. 设计目的

该工具链用于**自动化仿真实验流程**，实现：

- 批量生成实验配置（baseline + diff）
- 自动创建实验运行目录
- 自动生成任务执行列表（work.list）
- 按设备资源限制（默认最多3并发）自动调度执行实验
- 自动检测实验完成状态，无需人工值守

目标是将“人工逐个跑实验”转变为**一键按计划、批量、并发自动执行**。

---

## 2. 核心逻辑

**通过“实验计划表驱动 + 配置自动生成 + 并发调度执行”，实现从参数设计到仿真运行的全自动流水线。**

---

## 3. 整体流程
```bash
experiment_plan.csv # 编写计划表
↓
generate_confs.py # 自动生成实验环境、实验命令
↓
生成：
- 每个实验目录（output/<tag>/worload, topology）
- SimAI.conf（output/<tag>/SimAI.conf）
- output/work.list（任务列表）
    ↓
sim_scheduler.py # 自动化调度、并行控制执行命令
    ↓
    最多3个并发执行任务(可在脚本中通过配置MAX_PARALLEL参数调整)
    ↓
    每个任务输出 output.log
    ↓
    检测 "Simulator finished"
```

---

## 4. 文件结构说明
```bash
├── run_script/
│ ├──experiment_plan.csv # 实验计划表
│ ├──generate_confs.py # 配置生成脚本
│ ├──sim_scheduler.py # 并发调度脚本
│ ├──base_params.yml # baseline配置
├── output/
│ ├── work.list # 自动生成的任务列表
```

---

## 5. 使用方法

### Step 1：编写实验计划表

编辑 `experiment_plan.csv`，核心字段：

- `ExpID`：实验ID
- `Enabled`：是否执行（1/0）
- `Tag`：实验标签
- `Topology`
- `Workload`
- `DiffX`：参数差分（格式 `key=value`）

---

### Step 2：生成配置 + 任务列表

```bash
python3 generate_confs.py --plan experiment_plan.csv
```
自动完成：
- 生成每个实验目录
- 生成 `SimAI.conf`
- 复制 `workload、topology`
- 生成 `output/work.list`

其中每一行类似:
```bash
SimAI_simulator ... > output.log && echo "Simulator finished" >> output.log
```

### Step 3：启动任务调度
```bash
nohup python3 sim_scheduler.py > scheduler_status.log 2>&1 &
```
调度器行为：
- 最多同时运行 3 个任务
- 自动补充空闲任务
- 直到所有任务完成

### Step 4：查看任务完成情况
检查 `scheduler_status.log` 查看任务完成情况