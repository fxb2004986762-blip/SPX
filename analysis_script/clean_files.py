import os


# =========================
# User Config
# =========================

CONFIG_LIST = {

}

# 如果本文件的CONFIG_LIST为空，则使用共享配置文件中的 CONFIG_LIST
if not CONFIG_LIST:
    from configs.result_path import CONFIG_LIST


# =========================
# Clean Config
# =========================
# 如果为 None，则从 CONFIG_LIST 中收集所有目录。
# 如果只想清理指定目录，可以写：
# CLEAN_TARGET_DIRS = ["/path/to/dir1", "/path/to/dir2"]
CLEAN_TARGET_DIRS = None

# 是否递归清理子目录。
# False：只清理 CONFIG_LIST 指定目录下的文件。
# True：递归清理其所有子目录。
CLEAN_RECURSIVE = False

# 安全模式：
# True：只打印将要删除的文件，不真正删除。
# False：真正删除。
CLEAN_DRY_RUN = False

# 只清理文件名前缀匹配的文件。
# 例如 ["fct_cdf"] 只清理 fct_cdf.png、fct_cdf.pdf。
# 如果想清理所有指定后缀文件，设为 None。
# CLEAN_NAME_PREFIXES = ["fct_cdf"]
CLEAN_NAME_PREFIXES = None


# ======================
# 清理指定名称的文件：关键词+后缀
# ======================
# 只清理文件名包含指定关键词的文件。
# 例如 ["cdf"]。
# 如果不需要，设为 None。
CLEAN_NAME_CONTAINS = ["port"]
# 要清理的文件后缀。
# 例如 [".png"]、[".png", ".pdf"]
CLEAN_SUFFIXES = [".png"]



# =========================
# Core Functions
# =========================
def collect_output_dirs_from_config(config):
    """
    从 CONFIG_LIST 中收集所有实验输出目录。
    """
    output_dirs = []

    for algo, size_map in config.items():
        for size, path in size_map.items():
            if path is not None:
                output_dirs.append(path)

    # 去重，同时保持顺序
    seen = set()
    unique_dirs = []

    for d in output_dirs:
        if d not in seen:
            unique_dirs.append(d)
            seen.add(d)

    return unique_dirs


def normalize_suffixes(suffixes):
    """
    规范化后缀列表，同时避免危险清理规则。
    """
    if suffixes is None or len(suffixes) == 0:
        raise ValueError("CLEAN_SUFFIXES cannot be empty.")

    normalized = []

    for s in suffixes:
        if not isinstance(s, str):
            raise ValueError(f"Invalid suffix type: {s}")

        s = s.strip()

        if s in ["", "*", "*.*"]:
            raise ValueError(f"Dangerous suffix is not allowed: {s}")

        if not s.startswith("."):
            s = "." + s

        normalized.append(s)

    return tuple(normalized)


def match_clean_rule(
    filename,
    suffixes,
    name_prefixes=None,
    name_contains=None,
):
    """
    判断某个文件名是否满足清理规则。
    """
    if not filename.endswith(suffixes):
        return False

    if name_prefixes is not None:
        if not any(filename.startswith(prefix) for prefix in name_prefixes):
            return False

    if name_contains is not None:
        if not any(keyword in filename for keyword in name_contains):
            return False

    return True


def collect_matched_files(
    root_dirs,
    suffixes,
    recursive=False,
    name_prefixes=None,
    name_contains=None,
):
    """
    收集所有满足清理规则的文件路径。
    """
    suffixes = normalize_suffixes(suffixes)

    if isinstance(root_dirs, str):
        root_dirs = [root_dirs]

    # 目录去重
    seen = set()
    unique_root_dirs = []

    for d in root_dirs:
        if d is None:
            continue

        d = os.path.abspath(d)

        if d not in seen:
            unique_root_dirs.append(d)
            seen.add(d)

    matched_files = []

    for root_dir in unique_root_dirs:
        if not os.path.isdir(root_dir):
            print(f"[Clean] Warning: directory does not exist, skipping: {root_dir}")
            continue

        if recursive:
            for cur_dir, _, files in os.walk(root_dir):
                for filename in files:
                    if match_clean_rule(
                        filename=filename,
                        suffixes=suffixes,
                        name_prefixes=name_prefixes,
                        name_contains=name_contains,
                    ):
                        matched_files.append(os.path.join(cur_dir, filename))
        else:
            for filename in os.listdir(root_dir):
                fp = os.path.join(root_dir, filename)

                if not os.path.isfile(fp):
                    continue

                if match_clean_rule(
                    filename=filename,
                    suffixes=suffixes,
                    name_prefixes=name_prefixes,
                    name_contains=name_contains,
                ):
                    matched_files.append(fp)

    return matched_files


def clean_files(
    root_dirs,
    suffixes,
    recursive=False,
    dry_run=True,
    name_prefixes=None,
    name_contains=None,
):
    """
    清理指定目录下满足规则的文件。
    """
    matched_files = collect_matched_files(
        root_dirs=root_dirs,
        suffixes=suffixes,
        recursive=recursive,
        name_prefixes=name_prefixes,
        name_contains=name_contains,
    )

    print("=" * 80)
    print("[Clean] Clean configuration:")
    print(f"  root_dirs count = {len(root_dirs) if isinstance(root_dirs, list) else 1}")
    print(f"  suffixes        = {suffixes}")
    print(f"  recursive       = {recursive}")
    print(f"  dry_run         = {dry_run}")
    print(f"  name_prefixes   = {name_prefixes}")
    print(f"  name_contains   = {name_contains}")
    print(f"  matched count   = {len(matched_files)}")
    print("=" * 80)

    for fp in matched_files:
        if dry_run:
            print(f"[DryRun] Would remove: {fp}")
        else:
            try:
                os.remove(fp)
                print(f"[Removed] {fp}")
            except Exception as e:
                print(f"[Error] Failed to remove {fp}: {e}")

    print("=" * 80)

    if dry_run:
        print("[Clean] Dry run finished. No files were deleted.")
        print("[Clean] Set CLEAN_DRY_RUN = False to actually delete files.")
    else:
        print("[Clean] Finished.")

    return matched_files


def main():
    if CLEAN_TARGET_DIRS is None:
        clean_dirs = collect_output_dirs_from_config(CONFIG_LIST)
    else:
        clean_dirs = CLEAN_TARGET_DIRS

    clean_files(
        root_dirs=clean_dirs,
        suffixes=CLEAN_SUFFIXES,
        recursive=CLEAN_RECURSIVE,
        dry_run=CLEAN_DRY_RUN,
        name_prefixes=CLEAN_NAME_PREFIXES,
        name_contains=CLEAN_NAME_CONTAINS,
    )


if __name__ == "__main__":
    main()