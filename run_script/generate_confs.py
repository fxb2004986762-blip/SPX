#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path
from typing import Dict, Optional
import yaml
import shutil
import subprocess

# python3 generate_confs.py --plan experiment_plan.csv

simulator_dir = "/home/dell/sjw/lb/simulator"
base_running_dir = "/home/dell/sjw/lb/simulator/output"
topology_base_dir = "/home/dell/sjw/lb/simulator/topology"
workload_base_dir = "/home/dell/sjw/lb/simulator/workload"
baseline_file = "/home/dell/sjw/lb/simulator/run_script/base_params.yml"
# 默认输出目录
output_dir = "/home/dell/sjw/lb/simulator/output"
worklist_dir = output_dir + "/work.list"
def load_baseline(path: Path) -> Dict[str, object]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Baseline file must be a key-value mapping: {path}")
    return data


def parse_diff_items(row: Dict[str, str]) -> Dict[str, str]:
    updates: Dict[str, str] = {}
    for key, value in row.items():
        if not key.startswith("Diff"):
            continue
        value = (value or "").strip()
        if not value:
            continue
        if "=" not in value:
            raise ValueError(f"{row.get('ExpID','<unknown>')} has invalid diff item: {value}. Expected key=value")
        k, v = value.split("=", 1)
        k = k.strip()
        v = v.strip()
        if not k:
            raise ValueError(f"{row.get('ExpID','<unknown>')} has empty parameter name in diff item: {value}")
        updates[k] = v
    return updates


def normalize_token(text: str) -> str:
    """
    Convert text into a stable filesystem-friendly token.
    Keep letters, digits, '-', '_', '.', replace other chars with '_'.
    """
    text = (text or "").strip()
    if not text:
        return "unknown"
    out = []
    for ch in text:
        if ch.isalnum() or ch in "-_.":
            out.append(ch)
        else:
            out.append("_")
    normalized = "".join(out).strip("_.")
    return normalized or "unknown"


def get_topology(row: Dict[str, str]) -> str:
    return normalize_token((row.get("Topology") or row.get("topology") or "").strip() or "unknown_topology")


def get_workload(row: Dict[str, str]) -> str:
    return normalize_token((row.get("Workload") or row.get("workload") or "").strip() or "unknown_workload")


def get_base_tag(row: Dict[str, str]) -> str:
    """
    Priority:
    1. CSV column Tag
    2. CSV column Name
    3. ExpID
    """
    tag = (row.get("Tag") or row.get("tag") or "").strip()
    if tag:
        return normalize_token(tag)

    name = (row.get("Name") or row.get("name") or "").strip()
    if name:
        return normalize_token(name)

    exp_id = (row.get("ExpID") or "").strip()
    return normalize_token(exp_id or "untitled")


def get_composed_tag(row: Dict[str, str]) -> str:
    base_tag = get_base_tag(row)
    topology = get_topology(row)
    workload = get_workload(row)
    return f"{base_tag}-{topology}-{workload}"


def build_auto_context(row: Dict[str, str], exp_dir: Path, conf_path: Path) -> Dict[str, str]:
    """
    Context variables available to auto-generated directory/path parameters.
    You can reference them inside baseline placeholders, for example:
      result_dir: results/{tag}
      trace_dir: traces/{tag}
      log_file: logs/{tag}/sim.log
    """
    exp_id = (row.get("ExpID") or "").strip()
    name = (row.get("Name") or "").strip()
    base_tag = get_base_tag(row)
    topology = get_topology(row)
    workload = get_workload(row)
    tag = get_composed_tag(row)

    context = {
        "exp_id": exp_id,
        "name": name,
        "base_tag": base_tag,
        "topology": topology,
        "workload": workload,
        "tag": tag,
        "conf_dir": exp_dir.as_posix(),
        "conf_file": conf_path.as_posix(),
        "conf_name": conf_path.name,
        "work_dir": exp_dir.as_posix(),
        "base_dir": base_running_dir,
    }
    return context


def maybe_format_value(value: object, context: Dict[str, str]) -> object:
    """
    Auto-format baseline string values that contain placeholders such as:
      {tag}, {base_tag}, {topology}, {workload}, {exp_id}, {conf_dir}, {conf_file}, {conf_name}, {name}, {work_dir}
    Non-string values are returned unchanged.
    """
    if not isinstance(value, str):
        return value

    if "{" not in value or "}" not in value:
        return value

    try:
        return value.format(**context)
    except KeyError as e:
        missing = str(e).strip("'")
        raise ValueError(
            f"Unknown placeholder {{{missing}}} in baseline path template: {value}. "
            f"Available placeholders: {sorted(context.keys())}"
        ) from e


def apply_auto_generated_paths(conf: Dict[str, object], row: Dict[str, str], exp_dir: Path, conf_path: Path) -> Dict[str, object]:
    """
    Auto-generate directory/path-related configuration from composed tag:
      tag-topology-workload

    Recommended usage:
    Put path-like parameters directly in baseline with placeholders, e.g.
      result_dir: results/{tag}
      trace_dir: traces/{tag}
      packet_log: logs/{tag}/packet.log
    """
    context = build_auto_context(row, exp_dir, conf_path)

    rendered: Dict[str, object] = {}
    for key, value in conf.items():
        rendered[key] = maybe_format_value(value, context)

    # 添加额外非Baseline中的参数
    # Inject commonly useful explicit fields so ns3/conf can consume them directly
    rendered["base_tag"] = context["base_tag"]
    rendered["topology"] = topology_base_dir + "/" + context["topology"]
    rendered["workload"] = workload_base_dir + "/" + context["workload"]
    rendered["tag"] = context["tag"]
    rendered.setdefault("conf_dir", context["conf_dir"])
    rendered.setdefault("conf_file", context["conf_file"])

    return rendered


def merge_config(
    baseline: Dict[str, object],
    row: Dict[str, str],
    exp_dir: Optional[Path] = None,
    conf_path: Optional[Path] = None,
) -> Dict[str, object]:
    conf = dict(baseline)
    diff = parse_diff_items(row)
    conf.update(diff)

    # 添加额外非Baseline中的参数
    seed = (row.get("Seed") or "").strip()
    if seed:
        conf["seed"] = seed

    git_commit = (row.get("GitCommit") or "").strip()
    if git_commit:
        conf["git_commit"] = git_commit

    exp_id = (row.get("ExpID") or "").strip()
    if exp_id:
        conf["exp_id"] = exp_id

    name = (row.get("Name") or "").strip()
    if name:
        conf["exp_name"] = name

    conf["base_tag"] = get_base_tag(row)
    conf["topology"] = get_topology(row)
    conf["workload"] = get_workload(row)
    conf["tag"] = get_composed_tag(row)

    # Auto-generate directory/path-like params after basic fields are known.
    if exp_dir is not None and conf_path is not None:
        conf = apply_auto_generated_paths(conf, row, exp_dir, conf_path)

    return conf


def write_conf(path: Path, conf: Dict[str, object], baseline: Dict[str, object]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        # for key in sorted(conf.keys()):
            # f.write(f"{key} {conf[key]}\n")
        for key, values in conf.items():
            # 如果key未在baseline中定义，则不添加
            if key not in baseline:
                continue
            f.write(f"{key} {values}\n")


def append_worklist(worklist_path: Path, conf_dir: Path, topology: str, workload: str, env_info: Dict[str, str]) -> None:
    cmd = f"AS_SEND_LAT=3 {env_info.get('execfile')} -t 16 -n {topology} -w {workload} -c {conf_dir}/SimAI.conf > {env_info.get('logfile')} && echo 'Simulator finished'>> {env_info.get('logfile')}"
    with open(worklist_path, "a", encoding="utf-8") as f:
        f.write(cmd + "\n")


def prepare_simulation_env(simdir: Path, row: Dict[str, str], conf: Dict[str, object]) -> Dict[str, str]:
    """
    Replicate the bash configpath() logic:
    - validate simdir
    - locate workload / topology files
    - build tag = base_tag-topology-workload
    - create output directory
    - copy workload & topology files
    """

    if not simdir.exists():
        raise FileNotFoundError(f"Error: {simdir} does not exist.")

    # === 获取参数 ===
    workload = conf.get("workload")
    network = conf.get("topology")
    tag = conf.get("tag")

    if not workload or not network:
        raise ValueError("Missing workload or topology in config")

    # === 文件路径 ===
    workload_file = simdir / "workload" / str(workload)
    workload_file_custom = simdir / "custom_trace" / Path(workload).name
    network_file = simdir / "topology" / str(network)

    # === 检查文件 ===
    if workload_file.exists():
        print(f"[OK] find workload: {workload_file}")
    elif workload_file_custom.exists():
        print(f"[OK] find workload: {workload_file_custom}")
    else:
        raise FileNotFoundError(f"Error: workload not found: {workload_file}, or {workload_file_custom}")

    if network_file.exists():
        print(f"[OK] find network topology: {network_file}")
    else:
        raise FileNotFoundError(f"Error: network topology not found: {network_file}")

    # === 输出目录 ===
    outdir = simdir / "output" / tag
    logfile = outdir / "output.log"

    # 删除旧目录
    if outdir.exists():
        shutil.rmtree(outdir)

    outdir.mkdir(parents=True, exist_ok=True)

    # === 执行文件 ===
    execfile = simdir / "bin" / "SimAI_simulator"

    # === 复制文件 ===
    if workload_file.exists():
        shutil.copy(workload_file, outdir)
    else:
        shutil.copy(workload_file_custom, outdir)
    shutil.copy(network_file, outdir)

    print(f"[OK] prepared simulation dir: {outdir}")

    if workload_file.exists():    
        return {
            "outdir": outdir.as_posix(),
            "logfile": logfile.as_posix(),
            "execfile": execfile.as_posix(),
            "workload_file": workload_file.as_posix(),
            "network_file": network_file.as_posix(),
        }
    else:
        return {
            "outdir": outdir.as_posix(),
            "logfile": logfile.as_posix(),
            "execfile": execfile.as_posix(),
            "workload_file": workload_file_custom.as_posix(),
            "network_file": network_file.as_posix(),
        }

def generate(plan_csv: Path, output_root: Path, worklist_path: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)

    generated = 0
    skipped = 0

    # Reset work.list on each full generation run
    if worklist_path.exists():
        worklist_path.unlink()

    with open(plan_csv, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = ["ExpID", "Enabled", "Tag", "Topology", "Workload"]
        for col in required:
            if col not in reader.fieldnames:
                raise ValueError(f"Missing required column in plan CSV: {col}")

        plan_dir = plan_csv.parent

        for row in reader:
            enabled = str(row.get("Enabled", "")).strip().lower()
            if enabled in {"0", "false", "no", ""}:
                skipped += 1
                continue

            exp_id = (row.get("ExpID") or "").strip()
            tag = get_composed_tag(row)
            if not exp_id:
                raise ValueError("Found enabled row without ExpID")

            if not baseline_file:
                raise ValueError(f"{exp_id} missing Baseline File")

            baseline = load_baseline(Path(baseline_file))

            # subdir = (row.get("OutputSubdir") or exp_id).strip()
            subdir = (row.get("OutputSubdir") or tag).strip()
            exp_dir = output_root / subdir
            exp_dir.mkdir(parents=True, exist_ok=True)

            conf_path = exp_dir / f"SimAI.conf"
            conf = merge_config(baseline, row, exp_dir=exp_dir, conf_path=conf_path)
            
            env_info = prepare_simulation_env(Path(simulator_dir), row, conf)        
            # 可选：把路径写回配置文件
            # conf.update(env_info)    

            write_conf(conf_path, conf, baseline)
            append_worklist(worklist_path, exp_dir, conf["topology"], conf["workload"], env_info)

            generated += 1
            print(f"[OK] {exp_id}: Successed, config written to {conf_path}")

    print(f"\nGenerated {generated} experiment conf files.")
    print(f"Skipped {skipped} disabled rows.")
    print(f"Work list written to: {worklist_path}")
    # print("Tip: baseline path/directory parameters can use placeholders like {tag}, {base_tag}, {topology}, {workload}, {exp_id}, {conf_dir}, {conf_file}.")


def main():
    parser = argparse.ArgumentParser(description="Generate ns3 .conf files from baseline + diff experiment plan.")
    parser.add_argument("--plan", default="experiment_plan_template.csv", help="Experiment plan CSV path")
    parser.add_argument("--output-dir", default=output_dir, help="Directory to store generated conf folders")
    parser.add_argument("--worklist", default=worklist_dir, help="Path to output work.list")
    args = parser.parse_args()

    plan_csv = Path(args.plan).resolve()
    output_root = Path(args.output_dir).resolve()
    worklist_path = Path(args.worklist).resolve()
    generate(plan_csv, output_root, worklist_path)


if __name__ == "__main__":
    main()
