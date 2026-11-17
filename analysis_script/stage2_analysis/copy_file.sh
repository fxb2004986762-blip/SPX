#!/bin/bash
#
# 将指定文件复制到指定目录下的所有子目录中
#

# 显示使用方法
usage() {
    cat << EOF
用法: $0 [选项] <源文件> <目标目录>

将源文件复制到目标目录下的所有子目录中

选项:
    -r, --recursive     递归处理所有层级的子目录（默认只处理直接子目录）
    -h, --help         显示此帮助信息

示例:
    # 复制文件到直接子目录
    $0 /path/to/file.txt /path/to/target_dir
    
    # 递归复制到所有层级的子目录
    $0 -r /path/to/file.txt /path/to/target_dir

EOF
    exit 1
}

# 初始化变量
RECURSIVE=0
SOURCE_FILE=""
TARGET_DIR=""

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--recursive)
            RECURSIVE=1
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            if [[ -z "$SOURCE_FILE" ]]; then
                SOURCE_FILE="$1"
            elif [[ -z "$TARGET_DIR" ]]; then
                TARGET_DIR="$1"
            else
                echo "错误: 参数过多"
                usage
            fi
            shift
            ;;
    esac
done

# 检查参数
if [[ -z "$SOURCE_FILE" ]] || [[ -z "$TARGET_DIR" ]]; then
    echo "错误: 缺少必需参数"
    usage
fi

# 检查源文件是否存在
if [[ ! -f "$SOURCE_FILE" ]]; then
    echo "错误: 源文件 '$SOURCE_FILE' 不存在"
    exit 1
fi

# 检查目标目录是否存在
if [[ ! -d "$TARGET_DIR" ]]; then
    echo "错误: 目标目录 '$TARGET_DIR' 不存在"
    exit 1
fi

# 获取源文件名
SOURCE_FILENAME=$(basename "$SOURCE_FILE")

# 初始化计数器
COPIED_COUNT=0
FAILED_COUNT=0

echo "开始复制文件: $SOURCE_FILE"
echo "目标目录: $TARGET_DIR"
echo "------------------------------------------------------------"

# 获取子目录列表
if [[ $RECURSIVE -eq 1 ]]; then
    # 递归查找所有子目录
    SUBDIRS=$(find "$TARGET_DIR" -mindepth 1 -type d)
else
    # 只查找直接子目录
    SUBDIRS=$(find "$TARGET_DIR" -mindepth 1 -maxdepth 1 -type d)
fi

# 检查是否找到子目录
if [[ -z "$SUBDIRS" ]]; then
    echo "未找到任何子目录"
    exit 0
fi

# 计算子目录数量
SUBDIR_COUNT=$(echo "$SUBDIRS" | wc -l)
echo "找到 $SUBDIR_COUNT 个子目录"
echo ""

# 复制文件到每个子目录
while IFS= read -r subdir; do
    DEST_PATH="$subdir/$SOURCE_FILENAME"
    if cp -p "$SOURCE_FILE" "$DEST_PATH" 2>/dev/null; then
        echo "✓ 已复制到: $DEST_PATH"
        ((COPIED_COUNT++))
    else
        echo "✗ 复制失败: $subdir"
        ((FAILED_COUNT++))
    fi
done <<< "$SUBDIRS"

# 打印总结
echo "------------------------------------------------------------"
echo ""
echo "总结:"
echo "  成功复制: $COPIED_COUNT 个"
echo "  失败: $FAILED_COUNT 个"