#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件复制脚本 - 调试版本
显示详细的目录扫描和处理信息
"""

import os
import shutil
from pathlib import Path

#     source_directory = "/home/dell/sjw/lb/simulator/output/5ooo-class/fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
#     files_to_copy = ["fattree_k16_1024g_8gps_400Gbps_A100", "microAllReduce_1024g", "SimAI.conf"]

# ========== 配置区域 ==========
# 源目录路径
SOURCE_DIR = "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-u"

# 要复制的文件列表
FILES_TO_COPY = [
    "fattree_k16_1024g_8gps_400Gbps_A100",
    "microAllReduce_1024g",
    "SimAI.conf"
]

# 目录名称分隔符
SEPARATOR = "_dcqcn"

# 调试模式：True=只显示信息不复制，False=正常复制
DRY_RUN = False
# ==============================


def debug_scan_directory(source_dir):
    """调试：显示目录扫描详情"""
    source_path = Path(source_dir).resolve()
    
    print("🔍 详细扫描信息:")
    print(f"📁 扫描目录: {source_path}")
    print(f"📁 目录存在: {source_path.exists()}")
    print(f"📁 是否为目录: {source_path.is_dir()}")
    print()
    
    if not source_path.exists() or not source_path.is_dir():
        return []
    
    print("📋 目录内容:")
    all_items = list(source_path.iterdir())
    print(f"   总计 {len(all_items)} 个项目")
    print()
    
    subdirs = []
    files = []
    
    for item in all_items:
        if item.is_dir():
            subdirs.append(item)
            print(f"  📂 [目录] {item.name}")
        elif item.is_file():
            files.append(item)
            print(f"  📄 [文件] {item.name}")
        else:
            print(f"  ❓ [其他] {item.name}")
    
    print()
    print(f"📊 统计: {len(subdirs)} 个子目录, {len(files)} 个文件")
    print()
    
    return subdirs


def copy_files_from_subdirs(source_dir, target_files, separator="_dcqcn", dry_run=False):
    """
    从指定目录的子目录中复制指定文件
    """
    source_path = Path(source_dir).resolve()
    
    if not source_path.exists():
        print(f"❌ 错误: 源目录不存在: {source_dir}")
        return
    
    if not source_path.is_dir():
        print(f"❌ 错误: 路径不是目录: {source_dir}")
        return
    
    print("=" * 70)
    print("📁 配置信息")
    print("=" * 70)
    print(f"源目录: {source_path}")
    print(f"要复制的文件: {target_files}")
    print(f"分隔符: '{separator}'")
    print(f"模式: {'🔍 预览模式（不实际复制）' if dry_run else '✅ 执行模式'}")
    print("=" * 70)
    print()
    
    # 调试扫描
    all_subdirs = debug_scan_directory(source_path)
    
    if not all_subdirs:
        print("⚠️  没有找到任何子目录")
        return
    
    print("=" * 70)
    print("📊 目录映射分析")
    print("=" * 70)
    
    # 分析每个子目录应该映射到哪个目标目录
    mapping = {}  # {目标目录名: [源子目录列表]}
    
    for subdir in all_subdirs:
        subdir_name = subdir.name
        
        # 提取目标目录名
        if separator in subdir_name:
            target_name = subdir_name.split(separator)[0]
            print(f"📂 {subdir_name}")
            print(f"   → 包含分隔符 '{separator}'")
            print(f"   → 目标目录: {target_name}")
        else:
            target_name = subdir_name
            print(f"📂 {subdir_name}")
            print(f"   → 不包含分隔符")
            print(f"   → 目标目录: {target_name} (使用原名)")
        
        if target_name not in mapping:
            mapping[target_name] = []
        mapping[target_name].append(subdir)
        print()
    
    print("=" * 70)
    print("📋 处理计划")
    print("=" * 70)
    for target_name, source_list in mapping.items():
        print(f"\n目标目录: {target_name}")
        print(f"来源子目录 ({len(source_list)} 个):")
        for src in source_list:
            print(f"  - {src.name}")
    
    print("\n" + "=" * 70)
    print("🚀 开始处理文件")
    print("=" * 70)
    
    total_copied = 0
    total_skipped = 0
    total_failed = 0
    
    for target_dir_name, source_subdirs in mapping.items():
        print(f"\n{'='*70}")
        print(f"📁 处理目标目录: {target_dir_name}")
        print(f"{'='*70}")
        
        target_dir = source_path / target_dir_name
        
        # 创建目标目录
        if not target_dir.exists():
            if not dry_run:
                target_dir.mkdir(parents=True, exist_ok=True)
            print(f"✨ {'[预览] ' if dry_run else ''}创建目录: {target_dir_name}")
        else:
            print(f"ℹ️  目录已存在: {target_dir_name}")
        
        # 处理每个源子目录
        for idx, subdir in enumerate(source_subdirs, 1):
            print(f"\n  [{idx}/{len(source_subdirs)}] 处理子目录: {subdir.name}")
            print(f"  {'─'*66}")
            
            # 复制文件
            for file_name in target_files:
                source_file = subdir / file_name
                target_file = target_dir / file_name
                
                if source_file.exists() and source_file.is_file():
                    try:
                        if not dry_run:
                            shutil.copy2(source_file, target_file)
                        print(f"  ✅ {'[预览] ' if dry_run else ''}复制: {file_name}")
                        print(f"     从: {subdir.name}/{file_name}")
                        print(f"     到: {target_dir_name}/{file_name}")
                        total_copied += 1
                    except Exception as e:
                        print(f"  ❌ 复制失败: {file_name}")
                        print(f"     错误: {e}")
                        total_failed += 1
                else:
                    print(f"  ⊘  文件不存在: {file_name}")
                    total_skipped += 1
    
    print("\n" + "=" * 70)
    print("📊 处理统计")
    print("=" * 70)
    print(f"✅ 成功复制: {total_copied} 个文件")
    print(f"⊘  跳过(不存在): {total_skipped} 个文件")
    print(f"❌ 失败: {total_failed} 个文件")
    print(f"{'='*70}")
    
    if dry_run:
        print("\n💡 这是预览模式，没有实际复制文件")
        print("   将 DRY_RUN 设置为 False 以执行实际复制")


if __name__ == "__main__":
    copy_files_from_subdirs(SOURCE_DIR, FILES_TO_COPY, SEPARATOR, dry_run=DRY_RUN)

# def main():
#     """主函数"""
#     # # 配置参数
#     # source_directory = input("请输入源目录路径: ").strip()
    
#     # # 如果路径带引号，去除引号
#     # source_directory = source_directory.strip('"').strip("'")
    
#     # 输入要复制的文件名（用逗号分隔）
#     # files_input = input("请输入要复制的文件名（用逗号分隔）: ").strip()
#     # files_to_copy = [f.strip() for f in files_input.split(',')]
#     source_directory = "/home/dell/sjw/lb/simulator/output/5ooo-class/fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
#     files_to_copy = ["fattree_k16_1024g_8gps_400Gbps_A100", "microAllReduce_1024g", "SimAI.conf"]

    
    
#     print(f"\n开始处理...")
#     print(f"源目录: {source_directory}")
#     print(f"要复制的文件: {files_to_copy}")
#     print("-" * 60)
    
#     # 执行复制操作
#     copy_files_from_subdirs(source_directory, files_to_copy)
    
#     print("\n" + "-" * 60)
#     print("处理完成！")


# if __name__ == "__main__":
#     main()