#!/bin/bash

# PROJECT=AstraSimNetwork
PROJECT=third
export PROJECT
SCRIPT_DIR=$(dirname "$(realpath $0)")
ROOT_DIR=$(realpath "${SCRIPT_DIR:?}"/..)
NS3_DIR="${ROOT_DIR:?}"/ns-3-alibabacloud
SIMAI_DIR="${ROOT_DIR:?}"/astra-sim-alibabacloud
SOURCE_NS3_BIN_DIR="${SIMAI_DIR:?}"/extern/network_backend/ns3-interface/simulation/build/scratch/ns3.36.1-${PROJECT}-debug
SOURCE_ANA_BIN_DIR="${SIMAI_DIR:?}"/build/simai_analytical/build/simai_analytical/SimAI_analytical
SOURCE_PHY_BIN_DIR="${SIMAI_DIR:?}"/build/simai_phy/build/simai_phynet/SimAI_phynet

TARGET_BIN_DIR="${SCRIPT_DIR:?}"/../bin

# Copy the ns-3 source tree used by SimAI, but never reuse generated CMake
# state from the standalone ns-3 directory.  CMake caches and the ns-3 lock
# file contain absolute paths and therefore cannot be moved to ns3-interface.
function sync_ns3_source {
    local target_ns3_dir="${SIMAI_DIR:?}/extern/network_backend/ns3-interface"

    mkdir -p "${target_ns3_dir:?}"
    cp -ru "${NS3_DIR:?}"/* "${target_ns3_dir:?}"
    # rm -rf "${target_ns3_dir:?}/simulation/build"
    # rm -rf "${target_ns3_dir:?}/simulation/cmake-cache"
    # rm -f "${target_ns3_dir:?}/simulation/.lock-ns3_linux_build"
}

function compile {
    local option="$1" 
    case "$option" in
    "ns3")
        mkdir -p "${TARGET_BIN_DIR:?}"
        # rm -rf "${SIMAI_DIR:?}"/extern/network_backend/ns3-interface/
        if [ -L "${TARGET_BIN_DIR:?}/SimAI_simulator" ]; then
            rm -rf "${TARGET_BIN_DIR:?}"/SimAI_simulator
        fi
        sync_ns3_source
        cd "${SIMAI_DIR:?}"
        # ./build.sh -lr ns3
        ./build.sh -c ns3    
        ln -s "${SOURCE_NS3_BIN_DIR:?}" "${TARGET_BIN_DIR:?}"/SimAI_simulator;;
    "phy")
        mkdir -p "${TARGET_BIN_DIR:?}"
        if [ -L "${TARGET_BIN_DIR:?}/SimAI_phynet" ]; then
            rm -rf "${TARGET_BIN_DIR:?}"/SimAI_phynet
        fi
        cd "${SIMAI_DIR:?}"
        ./build.sh -lr phy
        ./build.sh -c phy 
        ln -s "${SOURCE_PHY_BIN_DIR:?}" "${TARGET_BIN_DIR:?}"/SimAI_phynet;;
    "analytical")
        mkdir -p "${TARGET_BIN_DIR:?}"
        mkdir -p "${ROOT_DIR:?}"/results
        if [ -L "${TARGET_BIN_DIR:?}/SimAI_analytical" ]; then
            rm -rf "${TARGET_BIN_DIR:?}"/SimAI_analytical
        fi
        cd "${SIMAI_DIR:?}"
        ./build.sh -lr analytical
        ./build.sh -c analytical 
        ln -s "${SOURCE_ANA_BIN_DIR:?}" "${TARGET_BIN_DIR:?}"/SimAI_analytical;;
    esac
}

function debug {
    local option="$1" 
    mkdir -p "${TARGET_BIN_DIR:?}"
    # rm -rf "${SIMAI_DIR:?}"/extern/network_backend/ns3-interface/
    if [ -L "${TARGET_BIN_DIR:?}/SimAI_simulator" ]; then
        rm -rf "${TARGET_BIN_DIR:?}"/SimAI_simulator
    fi
    sync_ns3_source
    cd "${SIMAI_DIR:?}"
    # ./build.sh -lr ns3
    ./build.sh -d ns3    
    # ln -s "${SOURCE_NS3_BIN_DIR:?}" "${TARGET_BIN_DIR:?}"/SimAI_simulator;;
}

function cleanup_build {
    local option="$1"
    case "$option" in
    "ns3")
        if [ -L "${TARGET_BIN_DIR:?}/SimAI_simulator" ]; then
            rm -rf "${TARGET_BIN_DIR:?}"/SimAI_simulator
        fi
        rm -rf "${SIMAI_DIR:?}"/extern/network_backend/ns3-interface/
        cd "${SIMAI_DIR:?}"
        ./build.sh -lr ns3;;
    "phy")
        if [ -L "${TARGET_BIN_DIR:?}/SimAI_phynet" ]; then
            rm -rf "${TARGET_BIN_DIR:?}"/SimAI_phynet
        fi
        cd "${SIMAI_DIR:?}"
        ./build.sh -lr phy;;
    "analytical")
        if [ -L "${TARGET_BIN_DIR:?}/SimAI_analytical" ]; then
            rm -rf "${TARGET_BIN_DIR:?}"/SimAI_analytical
        fi
        cd "${SIMAI_DIR:?}"
        ./build.sh -lr analytical;;
    esac
}

# Main Script
case "$1" in
-l|--clean)
    cleanup_build "$2";;
-c|--compile)
    compile "$2";;
-d|--debug)
    debug "$2";;
-h|--help|*)
    printf -- "help message\n"
    printf -- "-c|--compile mode supported ns3/phy/analytical  (example:./build.sh -c ns3)\n"
    printf -- "-l|--clean  (example:./build.sh -l ns3)\n"
    printf -- "-lr|--clean-result mode  (example:./build.sh -lr ns3)\n"
esac
