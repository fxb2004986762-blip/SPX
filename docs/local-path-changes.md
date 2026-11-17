# 本地路径替换清单

本次只替换路径文字，未修改程序逻辑、执行权限、编译配置；未创建备份。

共修改 47 个已有文件。
.vscode/settings.json 已使用本机路径，无需修改。

## 路径映射

- `/home/dell/sjw/lb/simulator` → `/home/dcn1/fxb/simulator`
- `/home/dell/sjw/data/output_dir` → `/home/dcn1/fxb/simulator/output`
- `/home/xuemo.lc/AliLMN-Sim/figs/` → `/home/dcn1/fxb/simulator/ns-3-alibabacloud/simulation/monitor_output/figs/`
- `/Users/yikaizhu/alicode/models-perf/deepspeed_baichuan_exp/results/baichuan_13B_zero3/55n_915_comm_log.txt` → `/home/dcn1/fxb/simulator/aicb/results/baichuan_13B_zero3/55n_915_comm_log.txt`
- `/Users/yikaizhu/Desktop/AIBC_clean.txt` → `/home/dcn1/fxb/simulator/aicb/results/AIBC_clean.txt`

AICB 的两个日志地址已改为项目内 aicb/results 下的位置，但对应日志文件目前不存在，需要提供真实日志；未创建空文件冒充输入。历史实验输出同样需要实际生成或导入。

Git 历史、历史终端输出 h -u origin main、二进制、编译缓存、第三方文档示例路径和多机运行示例占位符不在此次替换范围内。

## `aicb/log_analyzer/plot.py`

第 79 行：
```text
原：filename = "/Users/yikaizhu/alicode/models-perf/deepspeed_baichuan_exp/results/baichuan_13B_zero3/55n_915_comm_log.txt"
新：filename = "/home/dcn1/fxb/simulator/aicb/results/baichuan_13B_zero3/55n_915_comm_log.txt"
```

第 80 行：
```text
原：filename = "/Users/yikaizhu/Desktop/AIBC_clean.txt"
新：filename = "/home/dcn1/fxb/simulator/aicb/results/AIBC_clean.txt"
```

## `analysis_script/README.md`

第 60 行：
```text
原：cd /home/dell/sjw/lb/simulator/analysis_script/trace_analysis
新：cd /home/dcn1/fxb/simulator/analysis_script/trace_analysis
```

第 106 行：
```text
原：cd /home/dell/sjw/lb/simulator
新：cd /home/dcn1/fxb/simulator
```

第 115 行：
```text
原：cd /home/dell/sjw/lb/simulator/analysis_script
新：cd /home/dcn1/fxb/simulator/analysis_script
```

第 281 行：
```text
原：cd /home/dell/sjw/lb/simulator
新：cd /home/dcn1/fxb/simulator
```

第 416 行：
```text
原：cd /home/dell/sjw/lb/simulator/analysis_script/trace_analysis
新：cd /home/dcn1/fxb/simulator/analysis_script/trace_analysis
```

第 471 行：
```text
原：cd /home/dell/sjw/lb/simulator/analysis_script
新：cd /home/dcn1/fxb/simulator/analysis_script
```

第 475 行：
```text
原：cd /home/dell/sjw/lb/simulator
新：cd /home/dcn1/fxb/simulator
```

## `analysis_script/configs/result_path.py`

第 2 行：
```text
原："0": "/home/dell/sjw/lb/simulator/output/0research/2packet-bundle-based-lb_in_large_topo/permutation/128gpu/sym/psn-path-k-0.004loss-1/psn-8_dcqcn-leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100-permutation_2048_1M",
新："0": "/home/dcn1/fxb/simulator/output/0research/2packet-bundle-based-lb_in_large_topo/permutation/128gpu/sym/psn-path-k-0.004loss-1/psn-8_dcqcn-leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100-permutation_2048_1M",
```

第 3 行：
```text
原："1": "/home/dell/sjw/lb/simulator/output/0research/2packet-bundle-based-lb_in_large_topo/permutation/128gpu/sym/psn-path-k-0.004loss-1/psn-128_dcqcn-leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100-permutation_2048_1M",
新："1": "/home/dcn1/fxb/simulator/output/0research/2packet-bundle-based-lb_in_large_topo/permutation/128gpu/sym/psn-path-k-0.004loss-1/psn-128_dcqcn-leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100-permutation_2048_1M",
```

第 4 行：
```text
原："2": "/home/dell/sjw/lb/simulator/output/0research/2packet-bundle-based-lb_in_large_topo/permutation/128gpu/sym/psn-path-k-0.004loss-1/psn-64_dcqcn-leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100-permutation_2048_1M",
新："2": "/home/dcn1/fxb/simulator/output/0research/2packet-bundle-based-lb_in_large_topo/permutation/128gpu/sym/psn-path-k-0.004loss-1/psn-64_dcqcn-leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100-permutation_2048_1M",
```

第 5 行：
```text
原："3": "/home/dell/sjw/lb/simulator/output/0research/2packet-bundle-based-lb_in_large_topo/permutation/128gpu/sym/psn-path-k-0.004loss-1/psn-1_dcqcn-leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100-permutation_2048_1M",
新："3": "/home/dcn1/fxb/simulator/output/0research/2packet-bundle-based-lb_in_large_topo/permutation/128gpu/sym/psn-path-k-0.004loss-1/psn-1_dcqcn-leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100-permutation_2048_1M",
```

第 6 行：
```text
原："4": "/home/dell/sjw/lb/simulator/output/0research/2packet-bundle-based-lb_in_large_topo/permutation/128gpu/sym/psn-path-k-0.004loss-1/psn-32_dcqcn-leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100-permutation_2048_1M",
新："4": "/home/dcn1/fxb/simulator/output/0research/2packet-bundle-based-lb_in_large_topo/permutation/128gpu/sym/psn-path-k-0.004loss-1/psn-32_dcqcn-leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100-permutation_2048_1M",
```

第 7 行：
```text
原："5": "/home/dell/sjw/lb/simulator/output/0research/2packet-bundle-based-lb_in_large_topo/permutation/128gpu/sym/psn-path-k-0.004loss-1/psn-16_dcqcn-leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100-permutation_2048_1M",
新："5": "/home/dcn1/fxb/simulator/output/0research/2packet-bundle-based-lb_in_large_topo/permutation/128gpu/sym/psn-path-k-0.004loss-1/psn-16_dcqcn-leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100-permutation_2048_1M",
```

第 8 行：
```text
原："6": "/home/dell/sjw/lb/simulator/output/0research/2packet-bundle-based-lb_in_large_topo/permutation/128gpu/sym/psn-path-k-0.004loss-1/psn-4_dcqcn-leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100-permutation_2048_1M",
新："6": "/home/dcn1/fxb/simulator/output/0research/2packet-bundle-based-lb_in_large_topo/permutation/128gpu/sym/psn-path-k-0.004loss-1/psn-4_dcqcn-leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100-permutation_2048_1M",
```

## `analysis_script/filiter_data.py`

第 18 行：
```text
原："0": "/home/dell/sjw/lb/simulator/output/12asy_topo/topology_type/hpn/alltoall/letflow/letflow_mprdma-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100_asy-microAll2All_1024g_EP8_128M",
新："0": "/home/dcn1/fxb/simulator/output/12asy_topo/topology_type/hpn/alltoall/letflow/letflow_mprdma-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100_asy-microAll2All_1024g_EP8_128M",
```

第 21 行：
```text
原：# "1": "/home/dell/sjw/data/output_dir",
新：# "1": "/home/dcn1/fxb/simulator/output",
```

## `analysis_script/get_case_path_pair.py`

第 7 行：
```text
原：WRITE_OUTPUT_FILE = "/home/dell/sjw/lb/simulator/analysis_script/configs/result_path.py"
新：WRITE_OUTPUT_FILE = "/home/dcn1/fxb/simulator/analysis_script/configs/result_path.py"
```

## `analysis_script/get_config_file.py`

第 12 行：
```text
原：#     source_directory = "/home/dell/sjw/lb/simulator/output/5ooo-class/fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
新：#     source_directory = "/home/dcn1/fxb/simulator/output/5ooo-class/fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
```

第 17 行：
```text
原：SOURCE_DIR = "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-u"
新：SOURCE_DIR = "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-u"
```

第 215 行：
```text
原：#     source_directory = "/home/dell/sjw/lb/simulator/output/5ooo-class/fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
新：#     source_directory = "/home/dcn1/fxb/simulator/output/5ooo-class/fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
```

## `analysis_script/stage2_analysis/acc_path_selected.py`

第 4 行：
```text
原：basePath = "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
新：basePath = "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
```

## `analysis_script/stage2_analysis/all_plot.sh`

第 26 行：
```text
原：fctPy="/home/dell/sjw/lb/simulator/analysis_script/plot_fct.py"
新：fctPy="/home/dcn1/fxb/simulator/analysis_script/plot_fct.py"
```

第 27 行：
```text
原：jctPy="/home/dell/sjw/lb/simulator/analysis_script/plot_jct.py"
新：jctPy="/home/dcn1/fxb/simulator/analysis_script/plot_jct.py"
```

第 28 行：
```text
原：oooPy="/home/dell/sjw/lb/simulator/analysis_script/plot_ooo.py"
新：oooPy="/home/dcn1/fxb/simulator/analysis_script/plot_ooo.py"
```

第 29 行：
```text
原：fctOooPy="/home/dell/sjw/lb/simulator/analysis_script/plot_fct_ooo.py"
新：fctOooPy="/home/dcn1/fxb/simulator/analysis_script/plot_fct_ooo.py"
```

## `analysis_script/stage2_analysis/analysis.py`

第 162 行：
```text
原：log_file = "/home/dell/sjw/lb/simulator/output/tmp.log"
新：log_file = "/home/dcn1/fxb/simulator/output/tmp.log"
```

第 187 行：
```text
原：test_class_file = "/home/dell/sjw/lb/simulator/output/7int-mix-class"
新：test_class_file = "/home/dcn1/fxb/simulator/output/7int-mix-class"
```

第 188 行：
```text
原：tmp_log_file = "/home/dell/sjw/lb/simulator/output/tmp.log"
新：tmp_log_file = "/home/dcn1/fxb/simulator/output/tmp.log"
```

## `analysis_script/stage2_analysis/analysis.sh`

第 3 行：
```text
原：baseDir_aps="/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
新：baseDir_aps="/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
```

第 40 行：
```text
原：cd /home/dell/sjw/lb/simulator/analysis_script &&
新：cd /home/dcn1/fxb/simulator/analysis_script &&
```

## `analysis_script/stage2_analysis/auto_analysis.sh`

第 16 行：
```text
原：# SED_REPLACE_PATTERN='s|baseDir_aps=.*|baseDir_aps=\"/home/dell/sjw/lb/simulator/output/aps-v2-c${current_num}_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAllReduce_128g_TP2\"|g'  # 示例：old_num → old_num_2（当前数字为2时）
新：# SED_REPLACE_PATTERN='s|baseDir_aps=.*|baseDir_aps=\"/home/dcn1/fxb/simulator/output/aps-v2-c${current_num}_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAllReduce_128g_TP2\"|g'  # 示例：old_num → old_num_2（当前数字为2时）
```

第 17 行：
```text
原：SED_REPLACE_PATTERN='s|baseDir_aps=.*|baseDir_aps=\"/home/dell/sjw/lb/simulator/output/6int-class-full/${config_id}/${config_id}-f${current_num}_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g\"|g'  # 示例：old_num → old_num_2（当前数字为2时）
新：SED_REPLACE_PATTERN='s|baseDir_aps=.*|baseDir_aps=\"/home/dcn1/fxb/simulator/output/6int-class-full/${config_id}/${config_id}-f${current_num}_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g\"|g'  # 示例：old_num → old_num_2（当前数字为2时）
```

第 20 行：
```text
原：pathID2Switch_patten='/home/dell/sjw/lb/simulator/output/6int-class-full/${config_id}'
新：pathID2Switch_patten='/home/dcn1/fxb/simulator/output/6int-class-full/${config_id}'
```

第 42 行：
```text
原：eval "./copy_file.sh /home/dell/sjw/lb/simulator/output/6int-class/AllReduce/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g/pathID2Switch $pathID2Switch_patten " &&
新：eval "./copy_file.sh /home/dcn1/fxb/simulator/output/6int-class/AllReduce/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g/pathID2Switch $pathID2Switch_patten " &&
```

## `analysis_script/stage2_analysis/get_acc.py`

第 282 行：
```text
原："aps-v2-f1": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新："aps-v2-f1": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 283 行：
```text
原："aps-v2-eq-f1": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-eq/aps-v2-eq-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新："aps-v2-eq-f1": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-eq/aps-v2-eq-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 284 行：
```text
原："aps-v2-eu-f1": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-eu/aps-v2-eu-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新："aps-v2-eu-f1": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-eu/aps-v2-eu-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 285 行：
```text
原："aps-v2-q-f1": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-q/aps-v2-q-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新："aps-v2-q-f1": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-q/aps-v2-q-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 286 行：
```text
原："aps-v2-qu-f1": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新："aps-v2-qu-f1": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 287 行：
```text
原："aps-v2-u-f1": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-u/aps-v2-u-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新："aps-v2-u-f1": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-u/aps-v2-u-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 288 行：
```text
原：# "aps-v2-u-f306": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-u/aps-v2-u-f306_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
新：# "aps-v2-u-f306": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-u/aps-v2-u-f306_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
```

第 291 行：
```text
原：output_dir = "/home/dell/sjw/lb/simulator/output/1all_figures"
新：output_dir = "/home/dcn1/fxb/simulator/output/1all_figures"
```

## `analysis_script/stage2_analysis/get_path_bw.sh`

第 3 行：
```text
原：# baseDir="/home/dell/sjw/lb/simulator/output/aps-v2-mix-c10_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAllReduce_128g_TP2"
新：# baseDir="/home/dcn1/fxb/simulator/output/aps-v2-mix-c10_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAllReduce_128g_TP2"
```

第 4 行：
```text
原：# baseDir_rps="/home/dell/sjw/lb/simulator/output/rps-mix-b306_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAllReduce_128g_TP2"
新：# baseDir_rps="/home/dcn1/fxb/simulator/output/rps-mix-b306_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAllReduce_128g_TP2"
```

第 14 行：
```text
原：cd /home/dell/sjw/lb/simulator/analysis_script &&
新：cd /home/dcn1/fxb/simulator/analysis_script &&
```

## `analysis_script/stage2_analysis/get_path_qlen.sh`

第 3 行：
```text
原：# baseDir="/home/dell/sjw/lb/simulator/output/aps-v2-mix-c10_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAllReduce_128g_TP2"
新：# baseDir="/home/dcn1/fxb/simulator/output/aps-v2-mix-c10_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAllReduce_128g_TP2"
```

第 4 行：
```text
原：# baseDir_rps="/home/dell/sjw/lb/simulator/output/rps-mix-b306_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAllReduce_128g_TP2"
新：# baseDir_rps="/home/dcn1/fxb/simulator/output/rps-mix-b306_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAllReduce_128g_TP2"
```

第 7 行：
```text
原：baseDir="/home/dell/sjw/lb/simulator/output/aps-v2-mix-c10_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAllReduce_128g_TP2"
新：baseDir="/home/dcn1/fxb/simulator/output/aps-v2-mix-c10_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAllReduce_128g_TP2"
```

第 18 行：
```text
原：cd /home/dell/sjw/lb/simulator/analysis_script &&
新：cd /home/dcn1/fxb/simulator/analysis_script &&
```

第 34 行：
```text
原：# cd /home/dell/sjw/lb/simulator/analysis_script &&
新：# cd /home/dcn1/fxb/simulator/analysis_script &&
```

## `analysis_script/stage2_analysis/plot_avg_jct.py`

第 283 行：
```text
原："aps": "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All/aps-b64-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
新："aps": "/home/dcn1/fxb/simulator/output/8asy_topo/All-to-All/aps-b64-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
```

第 284 行：
```text
原："aps-v2": "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All/aps-v2-b64-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
新："aps-v2": "/home/dcn1/fxb/simulator/output/8asy_topo/All-to-All/aps-v2-b64-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
```

第 285 行：
```text
原："rps": "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All/rps-b64-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
新："rps": "/home/dcn1/fxb/simulator/output/8asy_topo/All-to-All/rps-b64-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
```

第 286 行：
```text
原："reps": "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All/reps-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
新："reps": "/home/dcn1/fxb/simulator/output/8asy_topo/All-to-All/reps-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
```

第 287 行：
```text
原："ecmp": "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All/ecmp-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
新："ecmp": "/home/dcn1/fxb/simulator/output/8asy_topo/All-to-All/ecmp-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
```

第 288 行：
```text
原：# "flowbender": "/home/dell/sjw/lb/simulator/output/6int-class-full/flowbender/flowbender_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：# "flowbender": "/home/dcn1/fxb/simulator/output/6int-class-full/flowbender/flowbender_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 289 行：
```text
原：# "letflow": "/home/dell/sjw/lb/simulator/output/6int-class-full/letflow/letflow_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：# "letflow": "/home/dcn1/fxb/simulator/output/6int-class-full/letflow/letflow_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 295 行：
```text
原：out_dir = "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All"
新：out_dir = "/home/dcn1/fxb/simulator/output/8asy_topo/All-to-All"
```

## `analysis_script/stage2_analysis/plot_bw.py`

第 192 行：
```text
原：#     # "aps-v2": "/home/dell/sjw/lb/simulator/output/aps-v2-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
新：#     # "aps-v2": "/home/dcn1/fxb/simulator/output/aps-v2-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
```

第 193 行：
```text
原：#     "aps-v2-c2": "/home/dell/sjw/lb/simulator/output/aps-v2-c2-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
新：#     "aps-v2-c2": "/home/dcn1/fxb/simulator/output/aps-v2-c2-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
```

第 194 行：
```text
原：#     "aps-v2-c4": "/home/dell/sjw/lb/simulator/output/aps-v2-c4-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
新：#     "aps-v2-c4": "/home/dcn1/fxb/simulator/output/aps-v2-c4-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
```

第 195 行：
```text
原：#     # "aps-v2-c8": "/home/dell/sjw/lb/simulator/output/aps-v2-c8-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
新：#     # "aps-v2-c8": "/home/dcn1/fxb/simulator/output/aps-v2-c8-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
```

第 196 行：
```text
原：#     # "aps-v2-eq": "/home/dell/sjw/lb/simulator/output/aps-v2-eq-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
新：#     # "aps-v2-eq": "/home/dcn1/fxb/simulator/output/aps-v2-eq-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
```

第 197 行：
```text
原：#     "aps-v2-eq-c2": "/home/dell/sjw/lb/simulator/output/aps-v2-eq-c2-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
新：#     "aps-v2-eq-c2": "/home/dcn1/fxb/simulator/output/aps-v2-eq-c2-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
```

第 198 行：
```text
原：#     "aps-v2-eq-c4": "/home/dell/sjw/lb/simulator/output/aps-v2-eq-c4-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
新：#     "aps-v2-eq-c4": "/home/dcn1/fxb/simulator/output/aps-v2-eq-c4-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
```

第 199 行：
```text
原：#     # "aps-v2-eq-c8": "/home/dell/sjw/lb/simulator/output/aps-v2-eq-c8-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
新：#     # "aps-v2-eq-c8": "/home/dcn1/fxb/simulator/output/aps-v2-eq-c8-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
```

第 200 行：
```text
原：#     "aps-v2-q-c4": "/home/dell/sjw/lb/simulator/output/aps-v2-q-c4-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
新：#     "aps-v2-q-c4": "/home/dcn1/fxb/simulator/output/aps-v2-q-c4-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
```

第 201 行：
```text
原：#     "rps": "/home/dell/sjw/lb/simulator/output/rps-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
新：#     "rps": "/home/dcn1/fxb/simulator/output/rps-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M",
```

第 202 行：
```text
原：#     "ecmp": "/home/dell/sjw/lb/simulator/output/ecmp-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M"
新：#     "ecmp": "/home/dcn1/fxb/simulator/output/ecmp-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAllReduce_128g_TP2_256M"
```

第 205 行：
```text
原：#     "aps-v2-f1": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：#     "aps-v2-f1": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 206 行：
```text
原：#     "aps-v2-f4": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2/aps-v2-f4_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：#     "aps-v2-f4": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f4_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 207 行：
```text
原：#     "aps": "/home/dell/sjw/lb/simulator/output/aps-b64_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：#     "aps": "/home/dcn1/fxb/simulator/output/aps-b64_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 208 行：
```text
原：#     "rps": "/home/dell/sjw/lb/simulator/output/6int-class-full/rps/rps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：#     "rps": "/home/dcn1/fxb/simulator/output/6int-class-full/rps/rps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 209 行：
```text
原：#     "ecmp": "/home/dell/sjw/lb/simulator/output/6int-class-full/ecmp/ecmp_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：#     "ecmp": "/home/dcn1/fxb/simulator/output/6int-class-full/ecmp/ecmp_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 210 行：
```text
原：#     "flowbender": "/home/dell/sjw/lb/simulator/output/6int-class-full/flowbender/flowbender_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：#     "flowbender": "/home/dcn1/fxb/simulator/output/6int-class-full/flowbender/flowbender_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 211 行：
```text
原：#     "letflow": "/home/dell/sjw/lb/simulator/output/6int-class-full/letflow/letflow_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
新：#     "letflow": "/home/dcn1/fxb/simulator/output/6int-class-full/letflow/letflow_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
```

第 214 行：
```text
原：#     "aps-v2-b0": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b0_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "aps-v2-b0": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b0_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 215 行：
```text
原：#     "aps-v2-b4": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "aps-v2-b4": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 216 行：
```text
原：#     "aps-v2-b8": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b8_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "aps-v2-b8": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b8_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 217 行：
```text
原：#     "aps-v2-b16": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b16_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "aps-v2-b16": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b16_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 218 行：
```text
原：#     "aps-v2-b32": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b32_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "aps-v2-b32": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b32_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 219 行：
```text
原：#     "aps-v2-b64": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b64_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "aps-v2-b64": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b64_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 220 行：
```text
原：#     "rps-b0": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b0_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "rps-b0": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b0_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 223 行：
```text
原：#     "aps-v2-b0": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b0_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "aps-v2-b0": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b0_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 224 行：
```text
原：#     "aps-v2-b4": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "aps-v2-b4": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 225 行：
```text
原：#     "aps-v2-b8": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b8_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "aps-v2-b8": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b8_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 226 行：
```text
原：#     "aps-v2-b16": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b16_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "aps-v2-b16": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b16_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 227 行：
```text
原：#     "aps-v2-b32": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b32_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "aps-v2-b32": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b32_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 228 行：
```text
原：#     "aps-v2-b64": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b64_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "aps-v2-b64": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b64_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 229 行：
```text
原：#     "aps-v2-b306": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b306_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "aps-v2-b306": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/aps-v2-b306_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 230 行：
```text
原：#     "rps-b0": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b0_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "rps-b0": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b0_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 231 行：
```text
原：#     "rps-b4": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "rps-b4": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 232 行：
```text
原：#     "rps-b8": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b8_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "rps-b8": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b8_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 233 行：
```text
原：#     "rps-b16": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b16_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "rps-b16": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b16_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 234 行：
```text
原：#     "rps-b32": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b32_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "rps-b32": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b32_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 235 行：
```text
原：#     "rps-b64": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b64_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
新：#     "rps-b64": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b64_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M",
```

第 236 行：
```text
原：#     "rps-b306": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b306_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M"
新：#     "rps-b306": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M/rps-b306_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_512M"
```

第 239 行：
```text
原：#     "aps-v2-b4-8MB": "/home/dell/sjw/lb/simulator/output/aps-v2-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAll2All_1024g_EP8_8M",
新：#     "aps-v2-b4-8MB": "/home/dcn1/fxb/simulator/output/aps-v2-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAll2All_1024g_EP8_8M",
```

第 240 行：
```text
原：#     "aps-v2-b4-32MB": "/home/dell/sjw/lb/simulator/output/aps-v2-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAll2All_1024g_EP8_32M"
新：#     "aps-v2-b4-32MB": "/home/dcn1/fxb/simulator/output/aps-v2-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAll2All_1024g_EP8_32M"
```

第 243 行：
```text
原：#     "aps-v2-qu-f1": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：#     "aps-v2-qu-f1": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 244 行：
```text
原：#     "aps-v2-qu-f4": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f4_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：#     "aps-v2-qu-f4": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f4_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 245 行：
```text
原：#     "aps-v2-qu-f8": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f8_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：#     "aps-v2-qu-f8": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f8_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 246 行：
```text
原：#     "aps-v2-qu-f16": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f16_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：#     "aps-v2-qu-f16": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f16_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 247 行：
```text
原：#     "aps-v2-qu-f32": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f32_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：#     "aps-v2-qu-f32": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f32_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 248 行：
```text
原：#     "aps-v2-qu-f64": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f64_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：#     "aps-v2-qu-f64": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f64_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 249 行：
```text
原：#     "aps-v2-qu-f306": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f306_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：#     "aps-v2-qu-f306": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-f306_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 250 行：
```text
原：#     "rps": "/home/dell/sjw/lb/simulator/output/6int-class-full/rps/rps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：#     "rps": "/home/dcn1/fxb/simulator/output/6int-class-full/rps/rps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 251 行：
```text
原：#     "ecmp": "/home/dell/sjw/lb/simulator/output/6int-class-full/ecmp/ecmp_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：#     "ecmp": "/home/dcn1/fxb/simulator/output/6int-class-full/ecmp/ecmp_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 252 行：
```text
原：#     "flowbender": "/home/dell/sjw/lb/simulator/output/6int-class-full/flowbender/flowbender_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：#     "flowbender": "/home/dcn1/fxb/simulator/output/6int-class-full/flowbender/flowbender_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 253 行：
```text
原：#     "letflow": "/home/dell/sjw/lb/simulator/output/6int-class-full/letflow/letflow_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
新：#     "letflow": "/home/dcn1/fxb/simulator/output/6int-class-full/letflow/letflow_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
```

第 258 行：
```text
原："aps-v2": "/home/dell/sjw/lb/simulator/output/3lb-class/aps-v2/All-to-All/aps-v2_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_64M",
新："aps-v2": "/home/dcn1/fxb/simulator/output/3lb-class/aps-v2/All-to-All/aps-v2_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_64M",
```

第 259 行：
```text
原："rps": "/home/dell/sjw/lb/simulator/output/3lb-class/rps/All-to-All/rps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_64M",
新："rps": "/home/dcn1/fxb/simulator/output/3lb-class/rps/All-to-All/rps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_64M",
```

第 260 行：
```text
原：# "aps": "/home/dell/sjw/lb/simulator/output/3lb-class/aps/aps-b64_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：# "aps": "/home/dcn1/fxb/simulator/output/3lb-class/aps/aps-b64_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 261 行：
```text
原："reps": "/home/dell/sjw/lb/simulator/output/3lb-class/reps/reps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_64M",
新："reps": "/home/dcn1/fxb/simulator/output/3lb-class/reps/reps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_64M",
```

第 262 行：
```text
原："ecmp": "/home/dell/sjw/lb/simulator/output/3lb-class/ecmp/ecmp_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_64M",
新："ecmp": "/home/dcn1/fxb/simulator/output/3lb-class/ecmp/ecmp_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_64M",
```

第 263 行：
```text
原：# "flowbender": "/home/dell/sjw/lb/simulator/output/6int-class-full/flowbender/flowbender_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：# "flowbender": "/home/dcn1/fxb/simulator/output/6int-class-full/flowbender/flowbender_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 264 行：
```text
原：# "letflow": "/home/dell/sjw/lb/simulator/output/6int-class-full/letflow/letflow_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新：# "letflow": "/home/dcn1/fxb/simulator/output/6int-class-full/letflow/letflow_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 267 行：
```text
原：out_dir = "/home/dell/sjw/lb/simulator/output/1all_figures"
新：out_dir = "/home/dcn1/fxb/simulator/output/1all_figures"
```

第 272 行：
```text
原：# out_dir = "/home/dell/sjw/lb/simulator/output/1all_figures"
新：# out_dir = "/home/dcn1/fxb/simulator/output/1all_figures"
```

## `analysis_script/stage2_analysis/plot_cdf_bw_diff.py`

第 243 行：
```text
原："aps-v2-f1": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-u/aps-v2-u-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新："aps-v2-f1": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-u/aps-v2-u-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 244 行：
```text
原："aps-v2-f4": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2/aps-v2-f4_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新："aps-v2-f4": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f4_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 245 行：
```text
原："aps-v2-f8": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2/aps-v2-f8_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新："aps-v2-f8": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f8_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 246 行：
```text
原："aps-v2-f16": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2/aps-v2-f16_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新："aps-v2-f16": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f16_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 247 行：
```text
原："aps-v2-f32": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2/aps-v2-f32_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新："aps-v2-f32": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f32_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 248 行：
```text
原："aps-v2-f64": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2/aps-v2-f64_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新："aps-v2-f64": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f64_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 249 行：
```text
原："aps-v2-f306": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2/aps-v2-f306_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
新："aps-v2-f306": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f306_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
```

## `analysis_script/stage2_analysis/plot_cdf_cnp.py`

第 185 行：
```text
原："aps-v2-b4-8MB": "/home/dell/sjw/lb/simulator/output/aps-v2-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAll2All_1024g_EP8_8M",
新："aps-v2-b4-8MB": "/home/dcn1/fxb/simulator/output/aps-v2-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAll2All_1024g_EP8_8M",
```

第 186 行：
```text
原："aps-v2-b4-32MB": "/home/dell/sjw/lb/simulator/output/aps-v2-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAll2All_1024g_EP8_32M"
新："aps-v2-b4-32MB": "/home/dcn1/fxb/simulator/output/aps-v2-b4_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAll2All_1024g_EP8_32M"
```

第 189 行：
```text
原：#     'aps-v2-fattree-allreduce_512M': '/home/dell/sjw/lb/simulator/output/5ooo-class/fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M/aps-v2-b306_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M',
新：#     'aps-v2-fattree-allreduce_512M': '/home/dcn1/fxb/simulator/output/5ooo-class/fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M/aps-v2-b306_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M',
```

第 190 行：
```text
原：#     'rps-fattree-allreduce_512M': '/home/dell/sjw/lb/simulator/output/5ooo-class/fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M/rps-b306_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M'
新：#     'rps-fattree-allreduce_512M': '/home/dcn1/fxb/simulator/output/5ooo-class/fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M/rps-b306_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M'
```

第 193 行：
```text
原：#     'rps-fattree-allreduce_512M': '/home/dell/sjw/lb/simulator/output/5ooo-class/fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M/rps-b16_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M'
新：#     'rps-fattree-allreduce_512M': '/home/dcn1/fxb/simulator/output/5ooo-class/fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M/rps-b16_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M'
```

第 202 行：
```text
原：# output_file = "/home/dell/sjw/lb/simulator/output/1all_figures/fattree-allreduce_128M_ooo_cdf.pdf"
新：# output_file = "/home/dcn1/fxb/simulator/output/1all_figures/fattree-allreduce_128M_ooo_cdf.pdf"
```

第 203 行：
```text
原：output_dir = "/home/dell/sjw/lb/simulator/output/1all_figures"
新：output_dir = "/home/dcn1/fxb/simulator/output/1all_figures"
```

## `analysis_script/stage2_analysis/plot_cdf_fct.py`

第 209 行：
```text
原："rps": "/home/dell/sjw/lb/simulator/output/6int-class-full/rps/rps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新："rps": "/home/dcn1/fxb/simulator/output/6int-class-full/rps/rps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 219 行：
```text
原：# output_dir = "/home/dell/sjw/lb/simulator/output/1all_figures"
新：# output_dir = "/home/dcn1/fxb/simulator/output/1all_figures"
```

## `analysis_script/stage2_analysis/plot_cdf_ooo.py`

第 176 行：
```text
原："aps-v2-u-f1": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-u/aps-v2-u-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新："aps-v2-u-f1": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-u/aps-v2-u-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 177 行：
```text
原："aps-v2-u-f4": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-u/aps-v2-u-f4_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
新："aps-v2-u-f4": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-u/aps-v2-u-f4_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g",
```

第 178 行：
```text
原："aps-v2-u-f64": "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-u/aps-v2-u-f64_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
新："aps-v2-u-f64": "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-u/aps-v2-u-f64_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
```

第 181 行：
```text
原：output_dir = "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-u/aps-v2-u-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
新：output_dir = "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-u/aps-v2-u-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
```

## `analysis_script/stage2_analysis/plot_ct.py`

第 310 行：
```text
原：#     "aps": "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All/aps-b64-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
新：#     "aps": "/home/dcn1/fxb/simulator/output/8asy_topo/All-to-All/aps-b64-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
```

第 311 行：
```text
原：#     "aps-v2": "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All/aps-v2-b64-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
新：#     "aps-v2": "/home/dcn1/fxb/simulator/output/8asy_topo/All-to-All/aps-v2-b64-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
```

第 312 行：
```text
原：#     "rps": "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All/rps-b64-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
新：#     "rps": "/home/dcn1/fxb/simulator/output/8asy_topo/All-to-All/rps-b64-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
```

第 313 行：
```text
原：#     "reps": "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All/reps-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
新：#     "reps": "/home/dcn1/fxb/simulator/output/8asy_topo/All-to-All/reps-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
```

第 314 行：
```text
原：#     "ecmp": "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All/ecmp-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
新：#     "ecmp": "/home/dcn1/fxb/simulator/output/8asy_topo/All-to-All/ecmp-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
```

第 315 行：
```text
原：#     "flowbender": "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All/flowbender-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
新：#     "flowbender": "/home/dcn1/fxb/simulator/output/8asy_topo/All-to-All/flowbender-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
```

第 316 行：
```text
原：#     "letflow": "/home/dell/sjw/lb/simulator/output/8asy_topo/All-to-All/letflow-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
新：#     "letflow": "/home/dcn1/fxb/simulator/output/8asy_topo/All-to-All/letflow-asy_dcqcn-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
```

第 321 行：
```text
原："aps": "/home/dell/sjw/lb/simulator/output/3lb-class/aps/All-to-All/aps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
新："aps": "/home/dcn1/fxb/simulator/output/3lb-class/aps/All-to-All/aps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
```

第 322 行：
```text
原："aps-v2": "/home/dell/sjw/lb/simulator/output/3lb-class/aps-v2/All-to-All/aps-v2_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
新："aps-v2": "/home/dcn1/fxb/simulator/output/3lb-class/aps-v2/All-to-All/aps-v2_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
```

第 323 行：
```text
原："rps": "/home/dell/sjw/lb/simulator/output/3lb-class/rps/All-to-All/rps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
新："rps": "/home/dcn1/fxb/simulator/output/3lb-class/rps/All-to-All/rps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
```

第 324 行：
```text
原：# "reps": "/home/dell/sjw/lb/simulator/output/3lb-class/reps/All-to-All/reps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
新：# "reps": "/home/dcn1/fxb/simulator/output/3lb-class/reps/All-to-All/reps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
```

第 325 行：
```text
原："ecmp": "/home/dell/sjw/lb/simulator/output/3lb-class/ecmp/All-to-All/ecmp_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
新："ecmp": "/home/dcn1/fxb/simulator/output/3lb-class/ecmp/All-to-All/ecmp_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
```

第 326 行：
```text
原："flowbender": "/home/dell/sjw/lb/simulator/output/3lb-class/flowbender/All-to-All/flowbender_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
新："flowbender": "/home/dcn1/fxb/simulator/output/3lb-class/flowbender/All-to-All/flowbender_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
```

第 327 行：
```text
原："letflow": "/home/dell/sjw/lb/simulator/output/3lb-class/letflow/All-to-All/letflow_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
新："letflow": "/home/dcn1/fxb/simulator/output/3lb-class/letflow/All-to-All/letflow_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_16M",
```

第 330 行：
```text
原：out_dir = "/home/dell/sjw/lb/simulator/output/1all_figures/aps-v2_vs._baseline/jct"
新：out_dir = "/home/dcn1/fxb/simulator/output/1all_figures/aps-v2_vs._baseline/jct"
```

第 345 行：
```text
原：# out_pdf_jct_file = "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-jct.pdf"
新：# out_pdf_jct_file = "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-jct.pdf"
```

第 346 行：
```text
原：# out_pdf_fct_avg_file = "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-fct_avg.pdf"
新：# out_pdf_fct_avg_file = "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-fct_avg.pdf"
```

第 347 行：
```text
原：# out_pdf_fct_p99_file = "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-fct_p99.pdf"
新：# out_pdf_fct_p99_file = "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2-qu/aps-v2-qu-fct_p99.pdf"
```

第 348 行：
```text
原：# out_pdf_jct_file = "/home/dell/sjw/lb/simulator/output/6int-class/freq_compare/jct/f1-jct.pdf"
新：# out_pdf_jct_file = "/home/dcn1/fxb/simulator/output/6int-class/freq_compare/jct/f1-jct.pdf"
```

第 349 行：
```text
原：# out_pdf_fct_avg_file = "/home/dell/sjw/lb/simulator/output/6int-class/freq_compare/fct_avg/f1-fct_avg.pdf"
新：# out_pdf_fct_avg_file = "/home/dcn1/fxb/simulator/output/6int-class/freq_compare/fct_avg/f1-fct_avg.pdf"
```

第 350 行：
```text
原：# out_pdf_fct_p99_file = "/home/dell/sjw/lb/simulator/output/6int-class/freq_compare/fct_p99/f1-fct_p99.pdf"
新：# out_pdf_fct_p99_file = "/home/dcn1/fxb/simulator/output/6int-class/freq_compare/fct_p99/f1-fct_p99.pdf"
```

## `analysis_script/stage2_analysis/plot_flow_lifecycle.py`

第 157 行：
```text
原：# data_dir = "/home/dell/sjw/lb/simulator/output/5ooo-class/fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M/rps-b8_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M"
新：# data_dir = "/home/dcn1/fxb/simulator/output/5ooo-class/fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M/rps-b8_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g_512M"
```

第 159 行：
```text
原：data_dir = "/home/dell/sjw/lb/simulator/output/aps-v2_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_1024M"
新：data_dir = "/home/dcn1/fxb/simulator/output/aps-v2_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g_1024M"
```

## `analysis_script/stage2_analysis/plot_pathBw.py`

第 10 行：
```text
原：basePath = "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
新：basePath = "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
```

## `analysis_script/stage2_analysis/plot_pathQlen.py`

第 9 行：
```text
原：basePath = "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
新：basePath = "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
```

## `analysis_script/stage2_analysis/plot_qlen.py`

第 166 行：
```text
原："reps": "/home/dell/sjw/lb/simulator/output/reps_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M",
新："reps": "/home/dcn1/fxb/simulator/output/reps_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M",
```

第 167 行：
```text
原：# "aps-v2-b16": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g/aps-v2-b16_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g",
新：# "aps-v2-b16": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g/aps-v2-b16_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g",
```

第 168 行：
```text
原：# "aps-v2-b64": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g/aps-v2-b64_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g",
新：# "aps-v2-b64": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g/aps-v2-b64_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g",
```

第 169 行：
```text
原：# "rps-b0": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g/rps-b0_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g",
新：# "rps-b0": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g/rps-b0_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g",
```

第 170 行：
```text
原：# "rps-b16": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g/rps-b16_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g",
新：# "rps-b16": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g/rps-b16_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g",
```

第 171 行：
```text
原：# "rps-b64": "/home/dell/sjw/lb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g/rps-b64_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g",
新：# "rps-b64": "/home/dcn1/fxb/simulator/output/5ooo-class/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g/rps-b64_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAllReduce_1024g",
```

第 175 行：
```text
原：output_dir = "/home/dell/sjw/lb/simulator/output/reps_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M"
新：output_dir = "/home/dcn1/fxb/simulator/output/reps_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M"
```

## `analysis_script/stage3_analysis/plot_avg_port.py`

第 36 行：
```text
原：#     "0": "/home/dell/sjw/lb/simulator/output/12asy_topo/topology_type/hpn/alltoall/ecmp/ecmp_mprdma-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100_asy-microAll2All_1024g_EP8_128M",
新：#     "0": "/home/dcn1/fxb/simulator/output/12asy_topo/topology_type/hpn/alltoall/ecmp/ecmp_mprdma-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100_asy-microAll2All_1024g_EP8_128M",
```

## `analysis_script/stage3_analysis/plot_jct_summary.py`

第 42 行：
```text
原：DEFAULT_INPUT_CSV = "/home/dell/sjw/lb/simulator/output/1all_figures/stage3/sym/sym_speedup_data.csv"
新：DEFAULT_INPUT_CSV = "/home/dcn1/fxb/simulator/output/1all_figures/stage3/sym/sym_speedup_data.csv"
```

## `analysis_script/stage3_analysis/plot_jct_summary_heatmap.py`

第 51 行：
```text
原："0": "/home/dell/sjw/lb/simulator/output/1all_figures/stage3/jct_summary/asy",
新："0": "/home/dcn1/fxb/simulator/output/1all_figures/stage3/jct_summary/asy",
```

第 52 行：
```text
原："1": "/home/dell/sjw/lb/simulator/output/1all_figures/stage3/jct_summary/failure",
新："1": "/home/dcn1/fxb/simulator/output/1all_figures/stage3/jct_summary/failure",
```

第 53 行：
```text
原："2": "/home/dell/sjw/lb/simulator/output/1all_figures/stage3/jct_summary/sym",
新："2": "/home/dcn1/fxb/simulator/output/1all_figures/stage3/jct_summary/sym",
```

## `analysis_script/stage3_analysis/plot_ooo.py`

第 50 行：
```text
原：#     "1": "/home/dell/sjw/lb/simulator/output/aps-v2_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAll2All_1024g_EP8_128M",
新：#     "1": "/home/dcn1/fxb/simulator/output/aps-v2_dcqcn-AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100-microAll2All_1024g_EP8_128M",
```

## `analysis_script/stage3_analysis/plot_ooo_trace.py`

第 36 行：
```text
原：#     "o4": "/home/dell/sjw/lb/simulator/output/rps-o4-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o4": "/home/dcn1/fxb/simulator/output/rps-o4-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 37 行：
```text
原：#     "o8": "/home/dell/sjw/lb/simulator/output/rps-o8-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o8": "/home/dcn1/fxb/simulator/output/rps-o8-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 38 行：
```text
原：#     "o16": "/home/dell/sjw/lb/simulator/output/rps-o16-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o16": "/home/dcn1/fxb/simulator/output/rps-o16-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 39 行：
```text
原：#     "o32": "/home/dell/sjw/lb/simulator/output/rps-o32-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o32": "/home/dcn1/fxb/simulator/output/rps-o32-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 40 行：
```text
原：#     "o64": "/home/dell/sjw/lb/simulator/output/rps-o64-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o64": "/home/dcn1/fxb/simulator/output/rps-o64-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 41 行：
```text
原：#     "o128": "/home/dell/sjw/lb/simulator/output/rps-o128-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o128": "/home/dcn1/fxb/simulator/output/rps-o128-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 42 行：
```text
原：#     "o306": "/home/dell/sjw/lb/simulator/output/rps-o306-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o306": "/home/dcn1/fxb/simulator/output/rps-o306-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 45 行：
```text
原：#     "o4": "/home/dell/sjw/lb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o4-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o4": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o4-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 46 行：
```text
原：#     "o8": "/home/dell/sjw/lb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o8-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o8": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o8-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 47 行：
```text
原：#     "o16": "/home/dell/sjw/lb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o16-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o16": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o16-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 48 行：
```text
原：#     "o32": "/home/dell/sjw/lb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o32-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o32": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o32-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 49 行：
```text
原：#     "o64": "/home/dell/sjw/lb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o64-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o64": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o64-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 50 行：
```text
原：#     "o128": "/home/dell/sjw/lb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o128-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o128": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o128-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 51 行：
```text
原：#     "o306": "/home/dell/sjw/lb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o306-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o306": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_win_RP10/aps-v2/aps-v2-o306-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 54 行：
```text
原：#     "o4": "/home/dell/sjw/lb/simulator/output/reps-o4-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o4": "/home/dcn1/fxb/simulator/output/reps-o4-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 55 行：
```text
原：#     "o8": "/home/dell/sjw/lb/simulator/output/reps-o8-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o8": "/home/dcn1/fxb/simulator/output/reps-o8-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 56 行：
```text
原：#     "o16": "/home/dell/sjw/lb/simulator/output/reps-o16-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o16": "/home/dcn1/fxb/simulator/output/reps-o16-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 57 行：
```text
原：#     "o32": "/home/dell/sjw/lb/simulator/output/reps-o32-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o32": "/home/dcn1/fxb/simulator/output/reps-o32-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 58 行：
```text
原：#     "o64": "/home/dell/sjw/lb/simulator/output/reps-o64-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o64": "/home/dcn1/fxb/simulator/output/reps-o64-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 59 行：
```text
原：#     "o128": "/home/dell/sjw/lb/simulator/output/reps-o128-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o128": "/home/dcn1/fxb/simulator/output/reps-o128-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 60 行：
```text
原：#     "o306": "/home/dell/sjw/lb/simulator/output/reps-o306-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "o306": "/home/dcn1/fxb/simulator/output/reps-o306-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 63 行：
```text
原：#     "0": "/home/dell/sjw/lb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_noWin_RP10/aps-v2/aps-v2-o32-noWin-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "0": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_noWin_RP10/aps-v2/aps-v2-o32-noWin-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 64 行：
```text
原：#     "1": "/home/dell/sjw/lb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_noWin_RP10/aps-v2/aps-v2-o306-noWin-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "1": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_noWin_RP10/aps-v2/aps-v2-o306-noWin-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 65 行：
```text
原：#     "2": "/home/dell/sjw/lb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_noWin_RP10/reps/reps-o32-noWin-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "2": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_noWin_RP10/reps/reps-o32-noWin-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 66 行：
```text
原：#     "3": "/home/dell/sjw/lb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_noWin_RP10/reps/reps-o306-noWin-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "3": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_noWin_RP10/reps/reps-o306-noWin-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 67 行：
```text
原：#     "4": "/home/dell/sjw/lb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_noWin_RP10/rps/rps-o306-noWin-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "4": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_noWin_RP10/rps/rps-o306-noWin-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 68 行：
```text
原：#     "5": "/home/dell/sjw/lb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_noWin_RP10/rps/rps-o32-noWin-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
新：#     "5": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/128GPU/dcqcn_noWin_RP10/rps/rps-o32-noWin-100_300KB_10RP_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_128M",
```

第 72 行：
```text
原：#     "0": "/home/dell/sjw/lb/simulator/output/0research/7what_ooo_perform_after_tune/1024GPU/dcqcn_noWin_RP10/aps-v2/aps-v2-o32-noWin-100_300KB_10RP_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
新：#     "0": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/1024GPU/dcqcn_noWin_RP10/aps-v2/aps-v2-o32-noWin-100_300KB_10RP_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
```

第 73 行：
```text
原：#     "1": "/home/dell/sjw/lb/simulator/output/0research/7what_ooo_perform_after_tune/1024GPU/dcqcn_noWin_RP10/aps-v2/aps-v2-o306-noWin-100_300KB_10RP_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
新：#     "1": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/1024GPU/dcqcn_noWin_RP10/aps-v2/aps-v2-o306-noWin-100_300KB_10RP_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
```

第 74 行：
```text
原：#     "2": "/home/dell/sjw/lb/simulator/output/0research/7what_ooo_perform_after_tune/1024GPU/dcqcn_noWin_RP10/reps/reps-o32-noWin-100_300KB_10RP_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
新：#     "2": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/1024GPU/dcqcn_noWin_RP10/reps/reps-o32-noWin-100_300KB_10RP_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
```

第 75 行：
```text
原：#     "3": "/home/dell/sjw/lb/simulator/output/0research/7what_ooo_perform_after_tune/1024GPU/dcqcn_noWin_RP10/reps/reps-o306-noWin-100_300KB_10RP_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
新：#     "3": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/1024GPU/dcqcn_noWin_RP10/reps/reps-o306-noWin-100_300KB_10RP_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
```

第 76 行：
```text
原：#     "4": "/home/dell/sjw/lb/simulator/output/0research/7what_ooo_perform_after_tune/1024GPU/dcqcn_noWin_RP10/rps/rps-o306-noWin-100_300KB_10RP_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
新：#     "4": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/1024GPU/dcqcn_noWin_RP10/rps/rps-o306-noWin-100_300KB_10RP_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
```

第 77 行：
```text
原：#     "5": "/home/dell/sjw/lb/simulator/output/0research/7what_ooo_perform_after_tune/1024GPU/dcqcn_noWin_RP10/rps/rps-o32-noWin-100_300KB_10RP_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
新：#     "5": "/home/dcn1/fxb/simulator/output/0research/7what_ooo_perform_after_tune/1024GPU/dcqcn_noWin_RP10/rps/rps-o32-noWin-100_300KB_10RP_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
```

第 81 行：
```text
原：# "0": "/home/dell/sjw/lb/simulator/output/reps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
新：# "0": "/home/dcn1/fxb/simulator/output/reps_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAll2All_1024g_EP8_128M",
```

第 82 行：
```text
原："1": "/home/dell/sjw/lb/simulator/output/aps-v2_mprdma-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
新："1": "/home/dcn1/fxb/simulator/output/aps-v2_mprdma-fattree_k8_128g_2gps_400Gbps_A100_asy-microAll2All_128g_EP8_8M",
```

## `analysis_script/stage3_analysis/plot_switch_bw_qlen.py`

第 18 行：
```text
原：#     "0": "/home/dell/sjw/lb/simulator/output/12asy_topo/topology_type/spectrumx/allreduce/flowbender/flowbender_mprdma-SpectrumX_1024g_8gps_400Gbps_A100_asy-microAllReduce_1024g_2048M",
新：#     "0": "/home/dcn1/fxb/simulator/output/12asy_topo/topology_type/spectrumx/allreduce/flowbender/flowbender_mprdma-SpectrumX_1024g_8gps_400Gbps_A100_asy-microAllReduce_1024g_2048M",
```

## `analysis_script/topo_parser.py`

第 88 行：
```text
原：case_file = "/home/dell/sjw/lb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
新：case_file = "/home/dcn1/fxb/simulator/output/6int-class-full/aps-v2/aps-v2-f1_dcqcn-fattree_k16_1024g_8gps_400Gbps_A100-microAllReduce_1024g"
```

## `astra-sim-alibabacloud/astra-sim/system/MockNcclLog.h`

第 29 行：
```text
原：#define LOG_PATH  "/home/dell/sjw/lb/simulator/output/simulation/"
新：#define LOG_PATH  "/home/dcn1/fxb/simulator/output/simulation/"
```

## `astra-sim-alibabacloud/astra-sim/system/System-utils.h`

第 34 行：
```text
原：inline std::string debug_log_file = "/home/dell/sjw/lb/simulator/output/simulation/debug.log";
新：inline std::string debug_log_file = "/home/dcn1/fxb/simulator/output/simulation/debug.log";
```

## `astra-sim-alibabacloud/inputs/config/SimAI.conf`

第 6 行：
```text
原：FLOW_FILE /home/dell/sjw/lb/simulator/output/simulation/flow1.txt
新：FLOW_FILE /home/dcn1/fxb/simulator/output/simulation/flow1.txt
```

第 7 行：
```text
原：TRACE_FILE /home/dell/sjw/lb/simulator/output/simulation/trace1.txt
新：TRACE_FILE /home/dcn1/fxb/simulator/output/simulation/trace1.txt
```

第 8 行：
```text
原：TRACE_OUTPUT_FILE /home/dell/sjw/lb/simulator/output/simulation/llama_hpn7_mix.tr
新：TRACE_OUTPUT_FILE /home/dcn1/fxb/simulator/output/simulation/llama_hpn7_mix.tr
```

第 9 行：
```text
原：FCT_OUTPUT_FILE /home/dell/sjw/lb/simulator/output/simulation/llama_hpn7_fct.txt
新：FCT_OUTPUT_FILE /home/dcn1/fxb/simulator/output/simulation/llama_hpn7_fct.txt
```

第 10 行：
```text
原：PFC_OUTPUT_FILE /home/dell/sjw/lb/simulator/output/simulation/llama_hpn7_pfc.txt
新：PFC_OUTPUT_FILE /home/dcn1/fxb/simulator/output/simulation/llama_hpn7_pfc.txt
```

第 11 行：
```text
原：SWITCH_FORWARD_OUTPUT_FILE /home/dell/sjw/lb/simulator/output/simulation/switch_forward.txt
新：SWITCH_FORWARD_OUTPUT_FILE /home/dcn1/fxb/simulator/output/simulation/switch_forward.txt
```

第 68 行：
```text
原：QLEN_MON_FILE /home/dell/sjw/lb/simulator/output/simulation/llama_hpn7_qlen.txt
新：QLEN_MON_FILE /home/dcn1/fxb/simulator/output/simulation/llama_hpn7_qlen.txt
```

第 69 行：
```text
原：BW_MON_FILE /home/dell/sjw/lb/simulator/output/simulation/llama_hpn7_bw.txt
新：BW_MON_FILE /home/dcn1/fxb/simulator/output/simulation/llama_hpn7_bw.txt
```

第 70 行：
```text
原：RATE_MON_FILE /home/dell/sjw/lb/simulator/output/simulation/llama_hpn7_rate.txt
新：RATE_MON_FILE /home/dcn1/fxb/simulator/output/simulation/llama_hpn7_rate.txt
```

第 71 行：
```text
原：CNP_MON_FILE /home/dell/sjw/lb/simulator/output/simulation/llama_hpn7_cnp.txt
新：CNP_MON_FILE /home/dcn1/fxb/simulator/output/simulation/llama_hpn7_cnp.txt
```

## `ns-3-alibabacloud/analysis/bw_analysis.py`

第 117 行：
```text
原：#     plt.savefig("/home/xuemo.lc/AliLMN-Sim/figs/" + fig_name)
新：#     plt.savefig("/home/dcn1/fxb/simulator/ns-3-alibabacloud/simulation/monitor_output/figs/" + fig_name)
```

## `ns-3-alibabacloud/analysis/qlen_analysis.py`

第 93 行：
```text
原：#     plt.savefig("/home/xuemo.lc/AliLMN-Sim/figs/" + fig_name)
新：#     plt.savefig("/home/dcn1/fxb/simulator/ns-3-alibabacloud/simulation/monitor_output/figs/" + fig_name)
```

## `run_script/base_params.yml`

第 76 行：
```text
原：SWITCH_FAILURE: /home/dell/sjw/lb/simulator/run_script/switch_failure.cfg
新：SWITCH_FAILURE: /home/dcn1/fxb/simulator/run_script/switch_failure.cfg
```

## `run_script/experiment_plan.csv`

第 2 行：
```text
原：1,0,ecmp_dcqcn,"ecmp, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=0,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dell/sjw/lb/simulator/custom_trace/permutation_2048_1M,,,,
新：1,0,ecmp_dcqcn,"ecmp, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=0,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dcn1/fxb/simulator/custom_trace/permutation_2048_1M,,,,
```

第 3 行：
```text
原：1,1,psn-4_dcqcn,"psn, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=6,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dell/sjw/lb/simulator/custom_trace/permutation_2048_1M,PSN_PATH_K=4,,,
新：1,1,psn-4_dcqcn,"psn, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=6,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dcn1/fxb/simulator/custom_trace/permutation_2048_1M,PSN_PATH_K=4,,,
```

第 4 行：
```text
原：1,0,reps_dcqcn,"reps, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=5,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dell/sjw/lb/simulator/custom_trace/permutation_2048_1M,,,,
新：1,0,reps_dcqcn,"reps, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=5,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dcn1/fxb/simulator/custom_trace/permutation_2048_1M,,,,
```

第 5 行：
```text
原：1,0,flowbender_dcqcn,"flowbender, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=3,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dell/sjw/lb/simulator/custom_trace/permutation_2048_1M,,,,
新：1,0,flowbender_dcqcn,"flowbender, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=3,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dcn1/fxb/simulator/custom_trace/permutation_2048_1M,,,,
```

第 6 行：
```text
原：1,1,psn-8_dcqcn,"psn, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=6,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dell/sjw/lb/simulator/custom_trace/permutation_2048_1M,PSN_PATH_K=8,,,
新：1,1,psn-8_dcqcn,"psn, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=6,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dcn1/fxb/simulator/custom_trace/permutation_2048_1M,PSN_PATH_K=8,,,
```

第 7 行：
```text
原：1,1,psn-16_dcqcn,"psn, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=6,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dell/sjw/lb/simulator/custom_trace/permutation_2048_1M,PSN_PATH_K=16,,,
新：1,1,psn-16_dcqcn,"psn, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=6,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dcn1/fxb/simulator/custom_trace/permutation_2048_1M,PSN_PATH_K=16,,,
```

第 8 行：
```text
原：1,1,psn-32_dcqcn,"psn, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=6,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dell/sjw/lb/simulator/custom_trace/permutation_2048_1M,PSN_PATH_K=32,,,
新：1,1,psn-32_dcqcn,"psn, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=6,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dcn1/fxb/simulator/custom_trace/permutation_2048_1M,PSN_PATH_K=32,,,
```

第 9 行：
```text
原：1,1,psn-1_dcqcn,"psn, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=6,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dell/sjw/lb/simulator/custom_trace/permutation_2048_1M,PSN_PATH_K=1,,,
新：1,1,psn-1_dcqcn,"psn, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=6,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dcn1/fxb/simulator/custom_trace/permutation_2048_1M,PSN_PATH_K=1,,,
```

第 10 行：
```text
原：1,1,psn-64_dcqcn,"psn, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=6,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dell/sjw/lb/simulator/custom_trace/permutation_2048_1M,PSN_PATH_K=64,,,
新：1,1,psn-64_dcqcn,"psn, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=6,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dcn1/fxb/simulator/custom_trace/permutation_2048_1M,PSN_PATH_K=64,,,
```

第 11 行：
```text
原：1,1,psn-128_dcqcn,"psn, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=6,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dell/sjw/lb/simulator/custom_trace/permutation_2048_1M,PSN_PATH_K=128,,,
新：1,1,psn-128_dcqcn,"psn, 4flow, 4uplink",,,leafspine_16tor_2048g_128gptor_8gps_1conv_400Gbps_A100,permutation_2048_1M,LB_MODE=6,MAX_OOO_SIZE=306,KMAX_MAP=6 25000000000 400 50000000000 800 100000000000 1600 200000000000 300 400000000000 300 1600000000000 2400,KMIN_MAP=6 25000000000 100 50000000000 200 100000000000 400 200000000000 100 400000000000 100 1600000000000 600,CC_MODE=1,HAS_WIN=0,RETRANS_TIME_OUT=0,HASH_TYPE=0,RP_TIMER=1,DROP_RATE=0.004,FLOW_FILE=/home/dcn1/fxb/simulator/custom_trace/permutation_2048_1M,PSN_PATH_K=128,,,
```

## `run_script/generate_confs.py`

第 12 行：
```text
原：simulator_dir = "/home/dell/sjw/lb/simulator"
新：simulator_dir = "/home/dcn1/fxb/simulator"
```

第 13 行：
```text
原：base_running_dir = "/home/dell/sjw/lb/simulator/output"
新：base_running_dir = "/home/dcn1/fxb/simulator/output"
```

第 14 行：
```text
原：topology_base_dir = "/home/dell/sjw/lb/simulator/topology"
新：topology_base_dir = "/home/dcn1/fxb/simulator/topology"
```

第 15 行：
```text
原：workload_base_dir = "/home/dell/sjw/lb/simulator/workload"
新：workload_base_dir = "/home/dcn1/fxb/simulator/workload"
```

第 16 行：
```text
原：baseline_file = "/home/dell/sjw/lb/simulator/run_script/base_params.yml"
新：baseline_file = "/home/dcn1/fxb/simulator/run_script/base_params.yml"
```

第 18 行：
```text
原：output_dir = "/home/dell/sjw/lb/simulator/output"
新：output_dir = "/home/dcn1/fxb/simulator/output"
```

## `run_script/getConfig.py`

第 20 行：
```text
原：FLOW_FILE: str = "/home/dell/sjw/lb/simulator/custom_trace/trace_test.txt"
新：FLOW_FILE: str = "/home/dcn1/fxb/simulator/custom_trace/trace_test.txt"
```

第 21 行：
```text
原：# FLOW_FILE: str = "/home/dell/sjw/lb/simulator/custom_trace/alltoall_128g_1MB.txt"
新：# FLOW_FILE: str = "/home/dcn1/fxb/simulator/custom_trace/alltoall_128g_1MB.txt"
```

第 118 行：
```text
原：SWITCH_FAILURE: str = "/home/dell/sjw/lb/simulator/run_script/switch_failure.cfg"
新：SWITCH_FAILURE: str = "/home/dcn1/fxb/simulator/run_script/switch_failure.cfg"
```

## `run_script/plan_run.sh`

第 3 行：
```text
原：python3 /home/dell/sjw/lb/simulator/run_script/generate_confs.py --plan /home/dell/sjw/lb/simulator/run_script/experiment_plan.csv &&
新：python3 /home/dcn1/fxb/simulator/run_script/generate_confs.py --plan /home/dcn1/fxb/simulator/run_script/experiment_plan.csv &&
```

第 4 行：
```text
原：nohup python3 /home/dell/sjw/lb/simulator/run_script/sim_scheduler.py > /home/dell/sjw/lb/simulator/output/scheduler_status.log 2>&1 &
新：nohup python3 /home/dcn1/fxb/simulator/run_script/sim_scheduler.py > /home/dcn1/fxb/simulator/output/scheduler_status.log 2>&1 &
```

## `run_script/run.sh`

第 156 行：
```text
原：simdir="/home/dell/sjw/lb/simulator"
新：simdir="/home/dcn1/fxb/simulator"
```

## `run_script/sim_scheduler.py`

第 12 行：
```text
原：TASK_FILE = "/home/dell/sjw/lb/simulator/output/work.list"          # 每行一条完整命令
新：TASK_FILE = "/home/dcn1/fxb/simulator/output/work.list"          # 每行一条完整命令
```

第 26 行：
```text
原：SCHEDULER_LOG = "/home/dell/sjw/lb/simulator/output/scheduler_status.log"
新：SCHEDULER_LOG = "/home/dcn1/fxb/simulator/output/scheduler_status.log"
```

第 233 行：
```text
原：subprocess.run(["python3", "/home/dell/sjw/lb/simulator/run_script/notify.py", "--path", summary_msg])
新：subprocess.run(["python3", "/home/dcn1/fxb/simulator/run_script/notify.py", "--path", summary_msg])
```

## `run_script/simai_config.cfg`

第 4 行：
```text
原：FLOW_FILE /home/dell/sjw/lb/simulator/custom_trace/trace_test.txt
新：FLOW_FILE /home/dcn1/fxb/simulator/custom_trace/trace_test.txt
```

第 5 行：
```text
原：TRACE_FILE /home/dell/sjw/lb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/trace1.txt
新：TRACE_FILE /home/dcn1/fxb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/trace1.txt
```

第 6 行：
```text
原：TRACE_OUTPUT_FILE /home/dell/sjw/lb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/mix.tr
新：TRACE_OUTPUT_FILE /home/dcn1/fxb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/mix.tr
```

第 7 行：
```text
原：FCT_OUTPUT_FILE /home/dell/sjw/lb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/fct.txt
新：FCT_OUTPUT_FILE /home/dcn1/fxb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/fct.txt
```

第 8 行：
```text
原：PFC_OUTPUT_FILE /home/dell/sjw/lb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/pfc.txt
新：PFC_OUTPUT_FILE /home/dcn1/fxb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/pfc.txt
```

第 9 行：
```text
原：QLEN_MON_FILE /home/dell/sjw/lb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/qlen.txt
新：QLEN_MON_FILE /home/dcn1/fxb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/qlen.txt
```

第 10 行：
```text
原：BW_MON_FILE /home/dell/sjw/lb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/bw.txt
新：BW_MON_FILE /home/dcn1/fxb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/bw.txt
```

第 11 行：
```text
原：RATE_MON_FILE /home/dell/sjw/lb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/rate.txt
新：RATE_MON_FILE /home/dcn1/fxb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/rate.txt
```

第 12 行：
```text
原：OOO_MON_FILE /home/dell/sjw/lb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/ooo.txt
新：OOO_MON_FILE /home/dcn1/fxb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/ooo.txt
```

第 13 行：
```text
原：CNP_MON_FILE /home/dell/sjw/lb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/cnp.txt
新：CNP_MON_FILE /home/dcn1/fxb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/cnp.txt
```

第 14 行：
```text
原：SWITCH_FORWARD_OUTPUT_FILE /home/dell/sjw/lb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/switch_forward.txt
新：SWITCH_FORWARD_OUTPUT_FILE /home/dcn1/fxb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/switch_forward.txt
```

第 15 行：
```text
原：SEND_OUTPUT_FILE /home/dell/sjw/lb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/send.txt
新：SEND_OUTPUT_FILE /home/dcn1/fxb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/send.txt
```

第 16 行：
```text
原：OOO_BUFFER_OUTPUT_FILE /home/dell/sjw/lb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/ooo_buffer.txt
新：OOO_BUFFER_OUTPUT_FILE /home/dcn1/fxb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/ooo_buffer.txt
```

第 17 行：
```text
原：APS_SELECTED_OUTPUT_FILE /home/dell/sjw/lb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/aps_selected.txt
新：APS_SELECTED_OUTPUT_FILE /home/dcn1/fxb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/aps_selected.txt
```

第 18 行：
```text
原：HASH_MON_FILE /home/dell/sjw/lb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/hash_mon.txt
新：HASH_MON_FILE /home/dcn1/fxb/simulator/output/ecmp_dcqcn-fattree_k8_128g_2gps_400Gbps_A100-microAll2All_128g_EP8_8M/hash_mon.txt
```

第 75 行：
```text
原：SWITCH_FAILURE /home/dell/sjw/lb/simulator/run_script/switch_failure.cfg
新：SWITCH_FAILURE /home/dcn1/fxb/simulator/run_script/switch_failure.cfg
```

## `topology/get_path_from_topo.py`

第 123 行：
```text
原：topology_file = '/home/dell/sjw/lb/simulator/topology/SpectrumX_1024g_8gps_400Gbps_A100'
新：topology_file = '/home/dcn1/fxb/simulator/topology/SpectrumX_1024g_8gps_400Gbps_A100'
```

第 124 行：
```text
原：topology_file = '/home/dell/sjw/lb/simulator/topology/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100'
新：topology_file = '/home/dcn1/fxb/simulator/topology/AlibabaHPN_1024g_8gps_DualToR_DualPlane_200Gbps_A100'
```

第 125 行：
```text
原：# topology_file = '/home/dell/sjw/lb/simulator/topology/fattree_k16_1024g_8gps_400Gbps_A100'
新：# topology_file = '/home/dcn1/fxb/simulator/topology/fattree_k16_1024g_8gps_400Gbps_A100'
```

## `topology/topo_asy_gen.py`

第 119 行：
```text
原：PRIME_FILE_PATH  = "/home/dell/sjw/lb/simulator/topology/SpectrumX_1024g_8gps_400Gbps_A100"   # 原始拓扑文件路径
新：PRIME_FILE_PATH  = "/home/dcn1/fxb/simulator/topology/SpectrumX_1024g_8gps_400Gbps_A100"   # 原始拓扑文件路径
```
