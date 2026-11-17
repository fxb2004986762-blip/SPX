#!/bin/bash

#!/bin/bash
##############################################################################
# 脚本功能：循环遍历数字列表[2,3,4,5,6]，使用sed修改指定文件的内容
# 适用场景：批量替换文件中特定模式的内容（可根据需求修改sed命令）
# 使用方法：1. 修改下方的 TARGET_FILE 和 SED_REPLACE_PATTERN 变量
#          2. 执行脚本：./modify_file_loop.sh
##############################################################################

# ========================== 配置参数（根据需求修改）==========================
# 目标文件路径（请替换为你要修改的文件绝对路径或相对路径）
TARGET_FILE="auto_run.sh"

# sed替换
# SED_REPLACE_PATTERN='s|apsTag=.*|apsTag="${current_num}"|g'  # 示例：old_num → old_num_2（当前数字为2时）
# SED_REPLACE_PATTERN='s|rpsTag=.*|rpsTag="${current_num}"|g'  # 示例：old_num → old_num_2（当前数字为2时）
SED_REPLACE_PATTERN='s|repsTag=.*|repsTag="${current_num}"|g'  # 示例：old_num → old_num_2（当前数字为2时）

# lb_mode 0: ECMP 1: APS 2: RPS 3: FlowBender 4: LetFlow 5: REPS 6: IOPS
LB_MODE=5
# LB_MODE=2

# 数字列表（固定为[2,3,4,5,6]）
# NUM_LIST=(0)
# NUM_LIST=(1)
# NUM_LIST=(4)
# NUM_LIST=(8)
# NUM_LIST=(0 4)
# NUM_LIST=(1 4)
# NUM_LIST=(4 8)
# NUM_LIST=(0 4 8)
# NUM_LIST=(1 4 8)
# NUM_LIST=(8 16)
# NUM_LIST=(16)
# NUM_LIST=(16 32)
# NUM_LIST=(16 32 64)
# NUM_LIST=(32)
# NUM_LIST=(32 64)
# NUM_LIST=(4 8 16)
# NUM_LIST=(8 16 32)
# NUM_LIST=(32 64)
# NUM_LIST=(16 32 64)
# NUM_LIST=(32 64 306)
# NUM_LIST=(64)
# NUM_LIST=(306)
# NUM_LIST=(1 306)
# NUM_LIST=(32 306)
NUM_LIST=(64 306)
# NUM_LIST=(1 64 306)

# =============================================================================

# 检查目标文件是否存在
if [ ! -f "$TARGET_FILE" ]; then
    echo "错误：目标文件 $TARGET_FILE 不存在！"
    exit 1
fi

# 检查目标文件是否可写
if [ ! -w "$TARGET_FILE" ]; then
    echo "错误：目标文件 $TARGET_FILE 没有写入权限！"
    exit 1
fi

# 循环遍历数字列表
for current_num in "${NUM_LIST[@]}"; do
    echo "========================================"
    echo "当前处理编号：$current_num"

    eval "sed -i \"$SED_REPLACE_PATTERN\" $TARGET_FILE"
    
    # 检查sed命令执行结果
    if [ $? -eq 0 ]; then
        echo "执行脚本"
        ./auto_run.sh $LB_MODE
    else
        echo "错误：修改数字 $current_num 时失败！"
        exit 1
    fi
    
    echo ""  # 空行分隔不同数字的处理日志
done

echo "========================================"
echo "所有任务执行完毕！"