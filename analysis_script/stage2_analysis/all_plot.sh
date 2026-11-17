#!/bin/bash

function run {

    python3 plot_jct.py 
    python3 plot_fct.py 
    python3 plot_ooo.py 
    # python3 plot_fct_ooo.py

}

function modify_Dir {

    sed -i "s|data_dir \= file_dir.*|data_dir \= file_dir \+ \"$baseDir\"|" $fctPy
    sed -i "s|data_dir \= file_dir.*|data_dir \= file_dir \+ \"$baseDir\"|" $jctPy
    # sed -i "s|data_dir \= file_dir.*|data_dir \= file_dir \+ \"$baseDir\"|" $oooPy
}

# 修改 base file path
baseDir="/../output"
# baseDir="/../output/4config-class"
# baseDir="/../output/5ooo-class"


# 绘图文件
fctPy="/home/dell/sjw/lb/simulator/analysis_script/plot_fct.py"
jctPy="/home/dell/sjw/lb/simulator/analysis_script/plot_jct.py"
oooPy="/home/dell/sjw/lb/simulator/analysis_script/plot_ooo.py"
fctOooPy="/home/dell/sjw/lb/simulator/analysis_script/plot_fct_ooo.py"

modify_Dir
run