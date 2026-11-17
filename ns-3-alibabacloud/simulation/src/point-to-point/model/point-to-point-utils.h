// This file contains utils for point-to-point modules
#ifndef __POINT_TO_POINT_UTILS_H__
#define __POINT_TO_POINT_UTILS_H__

#include <fstream>
#include <string>
#include <iomanip>
#include <iostream>
#include <unordered_set>

using namespace std;

/* ns3 backend */
#define SRC 99
#define DST 227
#define SRC_SW 192
#define DST_SW 194
#define SRC_AGG_SW 224


/* Common */
/** QP */
// #define QP_INIT_INFO
// #define QP_FINISH_INFO

/** Switch */
// #define SWITCH_INIT_INFO
// #define HASH_EGRESSPORT_OBSERVATION
// #define SWITCH_PORT_SELECT // get switch port lb info
// #define SWITCH_OPORT_LOG // get switch out port info
// #define SWITCH_ECN_LOG // switch tag ecn
// #define SWITCH_ECN_DEBUG // mannually add ecn
// #define SWITCH_PFC_PAUSE_LOG // switch pfc happened, should be as rare as switch drop
// #define SWITCH_FAILED_LOG
// #define SWITCH_DROP_LOG // switch drop happened, should be rare
// #define SWITCH_DROP_DEBUG // mannually drop 3 continuous packets for test

/* Congestion Control */
/** HPCC */
// #define HPCC_LOG

/** MPRDMA */
// #define MPRDMA_INFO


/* Reliable Transmission */
/** Selective Retransmit(SR) */
// #define SR_SND_LOG // sender log
// #define SR_SND_RT_LOG // sender retrans log
// #define SR_RCV_LOG // receiver log
// #define OOO_SR_INFO
// #define OOO_INFO
// #define OOO_WARN
// #define OOO_BUFF_INFO
// #define OOO_DEBUG

/** Go-Back-N */ 
// #define GBN_INFO


/* Load Balancing */ 
/** APS_V2 */
#define APS_V2 
// #define APS_CACHED_PATH_INFO
// #define APS_PROBE_INFO
// #define APS_PATH_SWITCHID_INFO // should open for aps-v2

/** APS */
// #define APS_OLD
// #define APS_INIT_INFO
// #define APS_SELECT_INFO
// #define APS_PATH_INFO
// #define APS_INT_PER_HOP_INFO
// #define APS_INIT_RRB_INFO
// #define APS_DEBUG
// #define APS_INIT_DEBUG // debug aps initial phase
// #define APS_TMP_DEBUG
// #define APS_FREEZING_INFO
// #define APS_BITMAP_INFO

/** IOPS */
// IOPS INFO
// #define IOPS_CACHE_INFO
// #define IOPS_SEND_INFO
// #define IOPS_ACK_DEBUG

/** REPS */
// #define REPS_PROBE_INFO
// #define REPS_BITMAP_INFO
// #define REPS_FREEZING_INFO

/** FlowBender */
// #define FLOWBENDER_INFO
// Random Packet Spraying
// #define RPS_ENABLED

/** LetFlow */
// #define LETFLOW_INFO
// #define LETFLOW_DEBUG


/* Background Traffic */ 
// #define BG_DEBUG



#endif