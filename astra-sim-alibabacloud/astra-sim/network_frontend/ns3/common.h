/* 
*Copyright (c) 2024, Alibaba Group;
*Licensed under the Apache License, Version 2.0 (the "License");
*you may not use this file except in compliance with the License.
*You may obtain a copy of the License at

*   http://www.apache.org/licenses/LICENSE-2.0

*Unless required by applicable law or agreed to in writing, software
*distributed under the License is distributed on an "AS IS" BASIS,
*WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
*See the License for the specific language governing permissions and
*limitations under the License.
*/

#ifndef __COMMON_H__
#define __COMMON_H__

#undef PGO_TRAINING
#define PATH_TO_PGO_CONFIG "path_to_pgo_config"

// my log define
// #define COMMON_RTT_LOG // for maxRTT calculation

#include <fstream>
#include <iostream>
#include <time.h>
#include <unordered_map>

#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/error-model.h"
#include "ns3/global-route-manager.h"
#include "ns3/internet-module.h"
#include "ns3/ipv4-static-routing-helper.h"
#include "ns3/packet.h"
#include "ns3/point-to-point-helper.h"
#include "ns3/qbb-helper.h"

#include <ns3/rdma-client-helper.h>
#include <ns3/rdma-client.h>
#include <ns3/rdma-driver.h>
#include <ns3/rdma.h>
#include <ns3/sim-setting.h>
#include <ns3/switch-node.h>
#include <ns3/nvswitch-node.h>
#include "ns3/point-to-point-utils.h"
#include <random>
#include <atomic>

using namespace ns3;
using namespace std;

NS_LOG_COMPONENT_DEFINE("GENERIC_SIMULATION");
uint32_t sim_start = 3; // simulation start time (us)
/** LB config */
double mix_lb_ratio = 0; // ECMP, aps run in a mix
uint32_t lb_mode = 0; 
uint32_t hash_type = 0;
uint32_t max_ooo_size = 0; // 0 means disable OOO buffer
// APS
uint8_t aps_indMask = 0; // 3 bit mask for INT indicator, 001:ecn, 010:qlen, 100:util, ..., 111:all
uint32_t aps_updateFreq = 1; // aps INT info update frequency
// APS-v2
uint32_t aps_path_credit = 1;
uint64_t sw_sample_time_interval = 1000; // ns
uint32_t aps_estimate_window_size = 3;
uint32_t retrans_time_out = 100; //us
// flowbender
double flowbender_ecn_t = 0.05;
uint32_t flowbender_switch_n = 1;
// Letflow params
Time letflow_flowletTimeout = MicroSeconds(100);  // 100us
Time letflow_agingTime = MilliSeconds(2);  // just to clear the unused map entries for simul speed
// REPS
uint32_t reps_bufferSize = 8; // buffer size for each QP
// PSN-PATH
uint32_t psn_path_k = 4;
// IOPS
uint32_t iops_bufferSize = 8; // buffer size for each QP


/** CC config */
uint32_t cc_mode = 1;
bool enable_qcn = true, use_dynamic_pfc_threshold = true;
uint32_t packet_payload_size = 1000, l2_chunk_size = 0, l2_ack_interval = 0;
double pause_time = 5, simulator_stop_time = 3.01;
std::string data_rate, link_delay, topology_file, flow_file, trace_file,
    trace_output_file, switch_failure_file;
std::string fct_output_file = "fct.txt";
std::string pfc_output_file = "pfc.txt";
std::string send_output_file = "send.txt";
std::string switch_forward_output_file = "switch_forward.txt";
std::string ooo_buffer_output_file = "ooo_buffer.txt";
std::string aps_selected_output_file = "aps_selected.txt";

double alpha_resume_interval = 55, rp_timer, ewma_gain = 1 / 16;
double rate_decrease_interval = 4;
uint32_t fast_recovery_times = 5;
std::string rate_ai, rate_hai, min_rate = "100Mb/s";
std::string dctcp_rate_ai = "1000Mb/s";

bool clamp_target_rate = false, l2_back_to_zero = false;
double error_rate_per_link = 0.0;
uint32_t has_win = 1;
uint32_t global_t = 0;
uint32_t mi_thresh = 5;
bool var_win = false, ooo_ack = false, ack_psn = false, fast_react = true;
bool multi_rate = true;
bool sample_feedback = false;
double pint_log_base = 1.05;
double pint_prob = 1.0;
double u_target = 0.95;
uint32_t int_multi = 1;
bool rate_bound = true;
int nic_total_pause_time = 0; 
unordered_map<uint32_t, Ptr<SwitchNode>> idxNodeToR;  // Id -> ToR Ptr


uint32_t ack_high_prio = 0;
uint64_t link_down_time = 0;
uint32_t link_down_A = 0, link_down_B = 0;

uint32_t enable_trace = 1;
uint32_t enable_ooo_trace = 1;

/* Switch config */
uint32_t buffer_size = 16;
double sw_packetDropRate = 0.0;

uint32_t node_num, switch_num, link_num, trace_num, nvswitch_num, gpus_per_server, switch_failure_num;
GPUType gpu_type;
std::vector<int>NVswitchs;

#ifdef HASH_EGRESSPORT_OBSERVATION
uint32_t hash_mon_interval = 100;
#endif
uint32_t qp_mon_interval = 100; 
uint32_t bw_mon_interval = 10000; 
uint32_t qlen_mon_interval = 10000; 
uint32_t aps_selected_mon_interval = 10000;
uint32_t aps_selected_traced_node = 0;
uint32_t switch_outport_mon_interval = 1;
uint64_t mon_start = 0, mon_end = 0; // us

string qlen_mon_file;
string bw_mon_file;
#ifdef HASH_EGRESSPORT_OBSERVATION
string hash_mon_file;
#endif
string rate_mon_file;
string ooo_mon_file;
string cnp_mon_file;
FILE* total_flow_output = nullptr;

unordered_map<uint64_t, uint32_t> rate2kmax, rate2kmin;
unordered_map<uint64_t, double> rate2pmax;

std::ifstream topof, flowf, tracef, switch_failuref;

NodeContainer n;

uint64_t nic_rate;

uint64_t maxRtt, maxBdp;

std::vector<Ipv4Address> serverAddress;

std::unordered_map<uint32_t, unordered_map<uint32_t, uint16_t>> portNumber;

struct Interface {
  uint32_t idx;
  bool up;
  uint64_t delay;
  uint64_t bw;

  Interface() : idx(0), up(false) {}
};
map<Ptr<Node>, map<Ptr<Node>, Interface>> nbr2if; // (src node -> dst node) -> interface
map<Ptr<Node>, map<Ptr<Node>, vector<Ptr<Node>>>> nextHop;
map<Ptr<Node>, map<Ptr<Node>, uint64_t>> pairDelay;
map<Ptr<Node>, map<Ptr<Node>, uint64_t>> pairTxDelay;
map<uint32_t, map<uint32_t, uint64_t>> pairBw;
map<Ptr<Node>, map<Ptr<Node>, uint64_t>> pairBdp;
map<uint32_t, map<uint32_t, uint64_t>> pairRtt;
// [currentSrc][finalDstHost], pair<[nexthopNode], [overWhichPort]>
map<Ptr<Node>, map<Ptr<Node>, vector<pair<Ptr<Node>, uint32_t> >>> NVSwitch, NetSwitch, Host; 


struct FlowInput {
  uint32_t src, dst, pg, maxPacketCount, port, dport;
  double start_time;
  uint32_t idx;
  int32_t tag;
};

FlowInput flow_input = {0};
uint32_t flow_num;
Ipv4Address node_id_to_ip(uint32_t id) {
  return Ipv4Address(0x0a000001 + ((id / 256) * 0x00010000) +
                     ((id % 256) * 0x00000100));
}

uint32_t ip_to_node_id(Ipv4Address ip) { return (ip.Get() >> 8) & 0xffff; }
uint32_t ip_to_node_id(uint32_t ip) { return (ip >> 8) & 0xffff; }


// trace the forwarding of packets in files
void get_switch_forward(FILE *fout, uint32_t switchNode, int outPort, CustomHeader &ch) {
  if (switch_outport_mon_interval == 0) return;
  // sip, dip, sport, dport, switch node, selected outPort
  uint16_t buf[2];
  uint64_t seq;
	if (ch.l3Prot == 0x6)
		buf[0] = ch.tcp.sport, buf[1] = ch.tcp.dport, seq = ch.tcp.seq;
	else if (ch.l3Prot == 0x11)
		buf[0] = ch.udp.sport, buf[1] = ch.udp.dport, seq = ch.udp.seq;
	else if (ch.l3Prot == 0xFC || ch.l3Prot == 0xFD)
		buf[0] = ch.ack.sport, buf[1] = ch.ack.dport, seq = ch.ack.seq;
  fprintf(fout, "%ld %u %u %u %u %u:%u %lu\n", Simulator::Now().GetTimeStep(),
          ip_to_node_id(ch.sip), ip_to_node_id(ch.dip), buf[0], buf[1], switchNode, outPort, seq);
  fflush(fout);
}

void get_ooo_buf(FILE *fout, Ptr<RdmaRxQueuePair> q, uint32_t cnt) {
  if (enable_ooo_trace == 0) return;
  fprintf(fout, "%ld %u %u %u %u %u\n", Simulator::Now().GetTimeStep(),
          ip_to_node_id(q->dip), ip_to_node_id(q->sip), q->dport, q->sport, cnt);
}

void get_pfc(FILE *fout, Ptr<QbbNetDevice> dev, uint32_t type) {
  fprintf(fout, "%lu %u %u %u %u\n", Simulator::Now().GetTimeStep(),
          dev->GetNode()->GetId(), dev->GetNode()->GetNodeType(),
          dev->GetIfIndex(), type);
}

struct QlenDistribution {
  vector<uint32_t>
      cnt;

  void add(uint32_t qlen) {
    uint32_t kb = qlen / 1000;
    if (cnt.size() < kb + 1)
      cnt.resize(kb + 1);
    cnt[kb]++;
  }
};

// monitor accuracy of aps
void monitor_aps_selected(FILE* aps_selected_output, NodeContainer *n) {
  if (lb_mode != 1) return; // only for aps
  if (aps_selected_mon_interval == 0 || Simulator::Now().GetMicroSeconds() > mon_end || mon_end == 0) return; // do not start monitor
	for (uint32_t i = 0; i < n->GetN(); i++){
		if(n->Get(i)->GetNodeType() == 0 && n->Get(i)->GetId() == aps_selected_traced_node){  // host and traced node
        Ptr<Node> host = n->Get(i);
        // host->GetObject<RdmaDriver>()->m_rdma->PrintAPSSelected(aps_selected_output, Host, NetSwitch);
        host->GetObject<RdmaDriver>()->m_rdma->PrintPathSelected(aps_selected_output);
		}
	}
	Simulator::Schedule(NanoSeconds(aps_selected_mon_interval), &monitor_aps_selected, aps_selected_output, n);
}
void monitor_qlen(FILE* qlen_output, NodeContainer *n){
  if (qlen_mon_interval == 0 || Simulator::Now().GetMicroSeconds() > mon_end || mon_end == 0) return; // do not start monitor
	for (uint32_t i = 0; i < n->GetN(); i++){
		if(n->Get(i)->GetNodeType() == 1){ 
			Ptr<SwitchNode> sw = DynamicCast<SwitchNode>(n->Get(i));
			sw->PrintSwitchQlen(qlen_output);
		}
    // if(n->Get(i)->GetNodeType() == 2){ 
		// 	Ptr<NVSwitchNode> sw = DynamicCast<NVSwitchNode>(n->Get(i));
		// 	sw->PrintSwitchQlen(qlen_output);
		// }
	}
	Simulator::Schedule(MicroSeconds(qlen_mon_interval), &monitor_qlen, qlen_output, n);
}
void monitor_bw(FILE* bw_output, NodeContainer *n){
  if (bw_mon_interval == 0 || Simulator::Now().GetMicroSeconds() > mon_end || mon_end == 0) return; // do not start monitor
	for (uint32_t i = 0; i < n->GetN(); i++){
		if(n->Get(i)->GetNodeType() == 1){ 
			Ptr<SwitchNode> sw = DynamicCast<SwitchNode>(n->Get(i));
			sw->PrintSwitchBw(bw_output, bw_mon_interval);
		// } else if(n->Get(i)->GetNodeType() == 2){ 
		// 	Ptr<NVSwitchNode> sw = DynamicCast<NVSwitchNode>(n->Get(i));
		// 	sw->PrintSwitchBw(bw_output, bw_mon_interval);
		}else if (n->Get(i)->GetNodeType() == 0){ 
			Ptr<Node> host = n->Get(i);
			host->GetObject<RdmaDriver>()->m_rdma->PrintHostBW(bw_output, bw_mon_interval);
		}
	}
	Simulator::Schedule(MicroSeconds(bw_mon_interval), &monitor_bw, bw_output, n);
}

#ifdef HASH_EGRESSPORT_OBSERVATION
void monitor_hash_load_balancing(FILE* hash_load_output,NodeContainer *n){
  if (hash_mon_interval == 0 || Simulator::Now().GetMicroSeconds() > mon_end || mon_end == 0) return; // do not start monitor
	for (uint32_t i = 0; i < n->GetN(); i++){
		if(n->Get(i)->GetNodeType() == 1){ 
			Ptr<SwitchNode> sw = DynamicCast<SwitchNode>(n->Get(i));
			sw->PrintSwitchHASHload(hash_load_output, hash_mon_interval);
		}
	}
	Simulator::Schedule(NanoSeconds(hash_mon_interval), &monitor_hash_load_balancing, hash_load_output, n);
}
#endif

void monitor_qp_rate(FILE* rate_output, NodeContainer *n){
  if (qp_mon_interval == 0 || Simulator::Now().GetMicroSeconds() > mon_end || mon_end == 0) return; // do not start monitor
	for(uint32_t i = 0; i < n->GetN(); i++){
		if(n->Get(i)->GetNodeType() == 0){ 
			Ptr<Node> host = n->Get(i);
			host->GetObject<RdmaDriver>()->m_rdma->PrintQPRate(rate_output);
		}
	}
	Simulator::Schedule(MicroSeconds(qp_mon_interval), &monitor_qp_rate, rate_output, n);
}

void monitor_qp_ooo(FILE* ooo_output, NodeContainer *n){
  if (qp_mon_interval == 0 || Simulator::Now().GetMicroSeconds() > mon_end || mon_end == 0) return; // do not start monitor
	for(uint32_t i = 0; i < n->GetN(); i++){
		if(n->Get(i)->GetNodeType() == 0){ 
			Ptr<Node> host = n->Get(i);
			host->GetObject<RdmaDriver>()->m_rdma->PrintRxQpOoO(ooo_output);
		}
	}
	Simulator::Schedule(MicroSeconds(qp_mon_interval), &monitor_qp_ooo, ooo_output, n);
}
void monitor_qp_cnp_number(FILE* cnp_output, NodeContainer *n){
  if (qp_mon_interval == 0 || (Simulator::Now().GetMicroSeconds() > mon_end || mon_end == 0)) return; // do not start monitor
	for(uint32_t i = 0; i < n->GetN(); i++){
		if(n->Get(i)->GetNodeType() == 0){ 
			Ptr<Node> host = n->Get(i);
			host->GetObject<RdmaDriver>()->m_rdma->PrintQPCnpNumber(cnp_output);
		}
	}
	Simulator::Schedule(MicroSeconds(qp_mon_interval), &monitor_qp_cnp_number, cnp_output, n);
}
void schedule_monitor(){
  if (Simulator::Now().GetMicroSeconds() > mon_end || mon_end == 0) return;
  FILE* aps_selected_output = fopen(aps_selected_output_file.c_str(), "w");
	assert(aps_selected_output != nullptr);
  fprintf(aps_selected_output, "%s, %s, %s, %s\n", "time", "src", "dst", "pathID");
	fflush(aps_selected_output);
  Simulator::Schedule(MicroSeconds(mon_start), &monitor_aps_selected, aps_selected_output, &n);

	FILE* qlen_output = fopen(qlen_mon_file.c_str(), "w"); 
	assert(qlen_output != nullptr);
	fprintf(qlen_output, "%s, %s, %s, %s, %s, %s\n", "time", "sw_id", "port_id", "q_id", "q_len", "port_len");
	fflush(qlen_output);
	Simulator::Schedule(MicroSeconds(mon_start), &monitor_qlen, qlen_output, &n);

	FILE* bw_output = fopen(bw_mon_file.c_str(), "w");
	assert(bw_output != nullptr);
	fprintf(bw_output, "%s, %s, %s, %s\n", "time", "node_id", "port_id", "bandwidth");
	fflush(bw_output);
	Simulator::Schedule(MicroSeconds(mon_start), &monitor_bw, bw_output, &n);

  #ifdef HASH_EGRESSPORT_OBSERVATION
	FILE* hash_output = fopen(hash_mon_file.c_str(), "w");
	assert(hash_output != nullptr);
	fprintf(hash_output, "%s, %s, %s, %s, %s, %s, %s, %s\n", "time", "node_id", "outport", "sip", "dip", "sport", "dport", "m_txBytes");
	fflush(hash_output);
	Simulator::Schedule(MicroSeconds(mon_start), &monitor_hash_load_balancing, hash_output, &n);
  #endif

	FILE* rate_output = fopen(rate_mon_file.c_str(), "w");
	assert(rate_output != nullptr);
	fprintf(rate_output, "%s, %s, %s, %s, %s, %s, %s\n", "time", "src", "dst", "sport", "dport", "size", "curr_rate");
	fflush(rate_output);
	Simulator::Schedule(MicroSeconds(mon_start), &monitor_qp_rate, rate_output, &n);

	FILE* ooo_output = fopen(ooo_mon_file.c_str(), "w");
	assert(ooo_output != nullptr);
	fprintf(ooo_output, "%s, %s, %s, %s, %s, %s\n", "time", "src", "dst", "sport", "dport", "ooo_buffer_size");
	fflush(ooo_output);
	Simulator::Schedule(MicroSeconds(mon_start), &monitor_qp_ooo, ooo_output, &n);

	FILE* cnp_output = fopen(cnp_mon_file.c_str(), "w");
	assert(cnp_output != nullptr);
	fprintf(cnp_output, "%s, %s, %s, %s, %s, %s, %s\n", "time", "src", "dst", "sport", "dport", "size", "cnp_number");
	fflush(cnp_output);
	Simulator::Schedule(MicroSeconds(mon_start), &monitor_qp_cnp_number, cnp_output, &n);
}

void CalculateRoute(Ptr<Node> host) {
  vector<Ptr<Node>> q;
  map<Ptr<Node>, int> dis;
  map<Ptr<Node>, uint64_t> delay;
  map<Ptr<Node>, uint64_t> txDelay;
  map<Ptr<Node>, uint64_t> bw;
  q.push_back(host);
  dis[host] = 0;
  delay[host] = 0;
  txDelay[host] = 0;
  bw[host] = 0xfffffffffffffffflu;
  for (int i = 0; i < (int)q.size(); i++) {
    Ptr<Node> now = q[i];
    int d = dis[now];
    for (auto it = nbr2if[now].begin(); it != nbr2if[now].end(); it++) {
      if (!it->second.up)
        continue;
      Ptr<Node> next = it->first;  
      if (dis.find(next) == dis.end()) {
        dis[next] = d + 1;
        delay[next] = delay[now] + it->second.delay;
        txDelay[next] = txDelay[now] +
                        packet_payload_size * 1000000000lu * 8 / it->second.bw; // 180ns during 400Gbps
        bw[next] = std::min(bw[now], it->second.bw);
        if (next->GetNodeType() == 1 || next->GetNodeType() == 2) {
          q.push_back(next);
        }
          
      }
      bool via_nvswitch = false;
      if (d + 1 == dis[next]) {
        for(auto x : nextHop[next][host]) {
          if(x->GetNodeType() == 2) via_nvswitch = true;
        }
        if(via_nvswitch == false) {
          if(now->GetNodeType() == 2) {
            while(nextHop[next][host].size() != 0) 
            nextHop[next][host].pop_back();
          }
          nextHop[next][host].push_back(now);
        } else if(via_nvswitch == true && now->GetNodeType() == 2) {
          nextHop[next][host].push_back(now);
        }
        if(next->GetNodeType() == 0 && nextHop[next][now].size() == 0) {
          nextHop[next][now].push_back(now);
          pairBw[next->GetId()][now->GetId()] = pairBw[now->GetId()][next->GetId()] = it->second.bw;
        }
      }
    }
  }
  for (auto it : delay) {
    pairDelay[it.first][host] = it.second;
  }
  for (auto it : txDelay)
    pairTxDelay[it.first][host] = it.second;
  for (auto it : bw) {
    pairBw[it.first->GetId()][host->GetId()] = it.second;
  }
}

void CalculateRoutes(NodeContainer &n) {
  for (int i = 0; i < (int)n.GetN(); i++) {
    Ptr<Node> node = n.Get(i);
    if (node->GetNodeType() == 0)
      CalculateRoute(node);
  }
}

void SetRoutingEntries() {
  for (auto i = nextHop.begin(); i != nextHop.end(); i++) {
    Ptr<Node> node = i->first;
    auto &table = i->second;
    for (auto j = table.begin(); j != table.end(); j++) {
      Ptr<Node> dst = j->first;
      Ipv4Address dstAddr = dst->GetObject<Ipv4>()->GetAddress(1, 0).GetLocal();
      vector<Ptr<Node>> nexts = j->second;
      for (int k = 0; k < (int)nexts.size(); k++) {
        Ptr<Node> next = nexts[k];
        uint32_t interface = nbr2if[node][next].idx;
        if (node->GetNodeType() == 1) {
          Ptr<SwitchNode> sw = DynamicCast<SwitchNode>(node);
          sw->AddTableEntry(dstAddr, interface);
          if (next->GetNodeType() == 0) {
            sw->AddDownlinkPort(interface);
          }

        } else if(node->GetNodeType() == 2){
					DynamicCast<NVSwitchNode>(node)->AddTableEntry(dstAddr, interface);
          node->GetObject<RdmaDriver>()->m_rdma->AddTableEntry(dstAddr, interface, true);
				} else {
          bool is_nvswitch = false;
					if(next->GetNodeType() == 2){ 
						is_nvswitch = true;
					}
					node->GetObject<RdmaDriver>()->m_rdma->AddTableEntry(dstAddr, interface, is_nvswitch);
          if(next->GetId() == dst->GetId())  {
            node->GetObject<RdmaDriver>()->m_rdma->add_nvswitch(dst->GetId());
          }
        }
      }
    }
  }
}
void recordRoutingEntries() {
  for (auto i = nextHop.begin(); i != nextHop.end(); i++) {
    Ptr<Node> src = i -> first;
    auto &table = i->second;
    for (auto j = table.begin(); j != table.end(); j++) { 
      Ptr<Node> dst = j->first;
      // Ipv4Address dstAddr = dst->GetObject<Ipv4>()->GetAddress(1, 0).GetLocal();
      vector<Ptr<Node>> nexts = j->second;
      for (int k = 0; k < (int)nexts.size(); k++) {
        Ptr<Node> firstHop = nexts[k];
        uint32_t interface = nbr2if[src][firstHop].idx;
        if(src->GetNodeType() == 0) {
          Host[src][dst].push_back(pair<Ptr<Node>, uint32_t>(firstHop, interface));
        } else if(src->GetNodeType() == 1) {
          NetSwitch[src][dst].push_back(pair<Ptr<Node>, uint32_t>(firstHop, interface));
        } else if(src->GetNodeType() == 2) {
          NVSwitch[src][dst].push_back(pair<Ptr<Node>, uint32_t>(firstHop, interface));
        }
      }
    }
  }
}

void printRoutingEntries() {
  map<uint32_t, string> types;
  types[0] = "HOST";
  types[1] = "SWITCH";
  types[2] = "NVSWITCH";

  cout << "*********************    PRINT SWITCH ROUTING TABLE    *********************" << endl << endl << endl;
  for(auto it = NetSwitch.begin(); it != NetSwitch.end(); ++ it) {
    Ptr<Node> src = it -> first;
    auto table = it -> second;
    cout << "SWITCH: " << src->GetId() << "'s routing entries are as follows:" << endl;
    for(auto j = table.begin(); j != table.end(); ++ j) {
      Ptr<Node> dst = j -> first;
      auto entries = j -> second;
      for(auto k = entries.begin(); k != entries.end(); ++ k) {
        Ptr<Node> nextHop = k->first;
        uint32_t interface = k->second;
        cout << "To " << dst->GetId() << "[" << types[dst->GetNodeType()] << "] via " << nextHop->GetId() << "[" << types[nextHop->GetNodeType()] << "]" << " from port: " << interface << endl;
      }
    }
  } 

  cout << "*********************    PRINT NVSWITCH ROUTING TABLE    *********************" << endl  << endl << endl;
  for(auto it = NVSwitch.begin(); it != NVSwitch.end(); ++ it) {
    Ptr<Node> src = it -> first;
    auto table = it -> second;
    cout << "NVSWITCH: " << src->GetId() << "'s routing entries are as follows:" << endl;
    for(auto j = table.begin(); j != table.end(); ++ j) {
      Ptr<Node> dst = j -> first;
      auto entries = j -> second;
      for(auto k = entries.begin(); k != entries.end(); ++ k) {
        Ptr<Node> nextHop = k->first;
        uint32_t interface = k->second;
        cout << "To " << dst->GetId() << "[" << types[dst->GetNodeType()] << "] via " << nextHop->GetId() << "[" << types[nextHop->GetNodeType()] << "]" << " from port: " << interface << endl;
      }
    }
  } 

  cout << "*********************    HOST ROUTING TABLE    *********************" << endl << endl << endl;
  for(auto it = Host.begin(); it != Host.end(); ++ it) {
    Ptr<Node> src = it -> first;
    auto table = it -> second;
    cout << "HOST: " << src->GetId() << "'s routing entries are as follows:" << endl;
    for(auto j = table.begin(); j != table.end(); ++ j) {
      Ptr<Node> dst = j -> first;
      auto entries = j -> second;
      for(auto k = entries.begin(); k != entries.end(); ++ k) {
        Ptr<Node> nextHop = k->first;
        uint32_t interface = k->second;
        cout << "To " << dst->GetId() << "[" << types[dst->GetNodeType()] << "] via " << nextHop->GetId() << "[" << types[nextHop->GetNodeType()] << "]" << " from port: " << interface << endl;
      }
    }
  } 

}

bool validateRoutingEntries() {
  return false;
}

void ChangeLinkState(Ptr<Node> a, Ptr<Node> b, int type) {
  if (type == 0) {
    DynamicCast<QbbNetDevice>(a->GetDevice(nbr2if[a][b].idx))->SetLinkFailed();
    DynamicCast<QbbNetDevice>(b->GetDevice(nbr2if[b][a].idx))->SetLinkFailed();
  } else if (type == 1) {
    DynamicCast<QbbNetDevice>(a->GetDevice(nbr2if[a][b].idx))->SetLinkUp();
    DynamicCast<QbbNetDevice>(b->GetDevice(nbr2if[b][a].idx))->SetLinkUp();
  } else if (type == 2) {
    DynamicCast<QbbNetDevice>(a->GetDevice(nbr2if[a][b].idx))->SetPortRate(0.5);
    DynamicCast<QbbNetDevice>(b->GetDevice(nbr2if[b][a].idx))->SetPortRate(0.5);
  }
}

void ChangeSwitchState(Ptr<SwitchNode> a, bool failed) {
  if (failed) {
    a->SetSwitchFailed();
  } else {
    a->SetSwitchUp();
  }
}

void TakeDownLink(NodeContainer n, Ptr<Node> a, Ptr<Node> b) {
  if (!nbr2if[a][b].up)
    return;
  printf("[Link_Down] Update Link State\n");
  nbr2if[a][b].up = nbr2if[b][a].up = false;
  nextHop.clear();
  CalculateRoutes(n);
	for (uint32_t i = 0; i < n.GetN(); i++){
		if (n.Get(i)->GetNodeType() == 1)
			DynamicCast<SwitchNode>(n.Get(i))->ClearTable();
		else if(n.Get(i)->GetNodeType() == 2)
			DynamicCast<NVSwitchNode>(n.Get(i))->ClearTable();
		else
			n.Get(i)->GetObject<RdmaDriver>()->m_rdma->ClearTable();
	}
  DynamicCast<QbbNetDevice>(a->GetDevice(nbr2if[a][b].idx))->TakeDown();
  DynamicCast<QbbNetDevice>(b->GetDevice(nbr2if[b][a].idx))->TakeDown();
  SetRoutingEntries();

  for (uint32_t i = 0; i < n.GetN(); i++) {
    if (n.Get(i)->GetNodeType() == 0)
      n.Get(i)->GetObject<RdmaDriver>()->m_rdma->RedistributeQp();
  }
}

string get_output_file_name(string config_file, string output_file){
	auto idx = config_file.find_last_of('/');
	string ans = output_file.substr(0, output_file.length()-4) + config_file.substr(idx+7);
	return ans;
}

uint64_t get_nic_rate(NodeContainer &n) {
  for (uint32_t i = 0; i < n.GetN(); i++)
    if (n.Get(i)->GetNodeType() == 0)
      return DynamicCast<QbbNetDevice>(n.Get(i)->GetDevice(1))
          ->GetDataRate()
          .GetBitRate();
}

bool ReadConf(string network_topo,string network_conf) {

    std::ifstream conf;
    conf.open(network_conf);
    topology_file = network_topo;
    while (!conf.eof()) {
      std::string key;
      conf >> key;

      if (key.compare("ENABLE_QCN") == 0) {
        uint32_t v;
        conf >> v;
        enable_qcn = v;
      } else if (key.compare("USE_DYNAMIC_PFC_THRESHOLD") == 0) {
        uint32_t v;
        conf >> v;
        use_dynamic_pfc_threshold = v;
      } else if (key.compare("CLAMP_TARGET_RATE") == 0) {
        uint32_t v;
        conf >> v;
        clamp_target_rate = v;
      } else if (key.compare("PAUSE_TIME") == 0) {
        double v;
        conf >> v;
        pause_time = v;
      } else if (key.compare("DATA_RATE") == 0) {
        std::string v;
        conf >> v;
        data_rate = v;
      } else if (key.compare("LINK_DELAY") == 0) {
        std::string v;
        conf >> v;
        link_delay = v;
      } else if (key.compare("PACKET_PAYLOAD_SIZE") == 0) {
        uint32_t v;
        conf >> v;
        packet_payload_size = v;
      } else if (key.compare("L2_CHUNK_SIZE") == 0) {
        uint32_t v;
        conf >> v;
        l2_chunk_size = v;
      } else if (key.compare("L2_ACK_INTERVAL") == 0) {
        uint32_t v;
        conf >> v;
        l2_ack_interval = v;
      } else if (key.compare("L2_BACK_TO_ZERO") == 0) {
        uint32_t v;
        conf >> v;
        l2_back_to_zero = v;
      } else if (key.compare("FLOW_FILE") == 0) {
        std::string v;
        conf >> v;
        flow_file = v;
      } else if (key.compare("TRACE_FILE") == 0) {
        std::string v;
        conf >> v;
        trace_file = v;
      } else if (key.compare("TRACE_OUTPUT_FILE") == 0) {
        std::string v;
        conf >> v;
        trace_output_file = v;
      } else if (key.compare("SIMULATOR_STOP_TIME") == 0) {
        double v;
        conf >> v;
        simulator_stop_time = v;
      } else if (key.compare("ALPHA_RESUME_INTERVAL") == 0) {
        double v;
        conf >> v;
        alpha_resume_interval = v;
      } else if (key.compare("RP_TIMER") == 0) {
        double v;
        conf >> v;
        rp_timer = v;
      } else if (key.compare("EWMA_GAIN") == 0) {
        double v;
        conf >> v;
        ewma_gain = v;
      } else if (key.compare("FAST_RECOVERY_TIMES") == 0) {
        uint32_t v;
        conf >> v;
        fast_recovery_times = v;
      } else if (key.compare("RATE_AI") == 0) {
        std::string v;
        conf >> v;
        rate_ai = v;
      } else if (key.compare("RATE_HAI") == 0) {
        std::string v;
        conf >> v;
        rate_hai = v;
      } else if (key.compare("ERROR_RATE_PER_LINK") == 0) {
        double v;
        conf >> v;
        error_rate_per_link = v;
      } else if (key.compare("CC_MODE") == 0) {
        conf >> cc_mode;
      } else if (key.compare("RATE_DECREASE_INTERVAL") == 0) {
        double v;
        conf >> v;
        rate_decrease_interval = v;
      } else if (key.compare("MIN_RATE") == 0) {
        conf >> min_rate;
      } else if (key.compare("FCT_OUTPUT_FILE") == 0) {
        conf >> fct_output_file;
      } else if (key.compare("SEND_OUTPUT_FILE") == 0) {
        conf >> send_output_file;
      } else if (key.compare("SWITCH_FORWARD_OUTPUT_FILE") == 0) {
        conf >> switch_forward_output_file;
      } else if (key.compare("OOO_BUFFER_OUTPUT_FILE") == 0) {
        conf >> ooo_buffer_output_file;
      } else if (key.compare("APS_SELECTED_OUTPUT_FILE") == 0) {
        conf >> aps_selected_output_file;
      } else if (key.compare("HAS_WIN") == 0) {
        conf >> has_win;
      } else if (key.compare("GLOBAL_T") == 0) {
        conf >> global_t;
      } else if (key.compare("MI_THRESH") == 0) {
        conf >> mi_thresh;
      } else if (key.compare("VAR_WIN") == 0) {
        uint32_t v;
        conf >> v;
        var_win = v;
      } else if (key.compare("OOO_ACK") == 0) {
        uint32_t v;
        conf >> v;
        ooo_ack = v;
      } else if (key.compare("ACK_PSN") == 0) {
        uint32_t v;
        conf >> v;
        ack_psn = v;
      } else if (key.compare("FAST_REACT") == 0) {
        uint32_t v;
        conf >> v;
        fast_react = v;
      } else if (key.compare("U_TARGET") == 0) {
        conf >> u_target;
      } else if (key.compare("INT_MULTI") == 0) {
        conf >> int_multi;
      } else if (key.compare("RATE_BOUND") == 0) {
        uint32_t v;
        conf >> v;
        rate_bound = v;
      } else if (key.compare("ACK_HIGH_PRIO") == 0) {
        conf >> ack_high_prio;
      } else if (key.compare("DCTCP_RATE_AI") == 0) {
        conf >> dctcp_rate_ai;
      } else if (key.compare("NIC_TOTAL_PAUSE_TIME") == 0) {
        conf >> nic_total_pause_time;
      } else if (key.compare("PFC_OUTPUT_FILE") == 0) {
        conf >> pfc_output_file;
      } else if (key.compare("LINK_DOWN") == 0) {
        conf >> link_down_time >> link_down_A >> link_down_B;
      } else if (key.compare("ENABLE_TRACE") == 0) {
        conf >> enable_trace;
      } else if (key.compare("ENABLE_OOO_TRACE") == 0) {
        conf >> enable_ooo_trace;
      } else if (key.compare("KMAX_MAP") == 0) {
        int n_k;
        conf >> n_k;
        for (int i = 0; i < n_k; i++) {
          uint64_t rate;
          uint32_t k;
          conf >> rate >> k;
          rate2kmax[rate] = k;
        }
      } else if (key.compare("KMIN_MAP") == 0) {
        int n_k;
        conf >> n_k;
        for (int i = 0; i < n_k; i++) {
          uint64_t rate;
          uint32_t k;
          conf >> rate >> k;
          rate2kmin[rate] = k;
        }
      } else if (key.compare("PMAX_MAP") == 0) {
        int n_k;
        conf >> n_k;
        for (int i = 0; i < n_k; i++) {
          uint64_t rate;
          double p;
          conf >> rate >> p;
          rate2pmax[rate] = p;
        }
      } else if (key.compare("BUFFER_SIZE") == 0) {
        conf >> buffer_size;
      } else if (key.compare("DROP_RATE") == 0) {
        double v; 
        conf >> v;
        sw_packetDropRate = v;
      } else if (key.compare("QLEN_MON_FILE") == 0){
				conf >> qlen_mon_file;
				// qlen_mon_file = get_output_file_name(network_conf, qlen_mon_file);
			}else if(key.compare("BW_MON_FILE") == 0){
				conf >> bw_mon_file;
				// bw_mon_file = get_output_file_name(network_conf, bw_mon_file);
			}else if(key.compare("OOO_MON_FILE") == 0){
				conf >> ooo_mon_file;
			}else if(key.compare("RATE_MON_FILE") == 0){
				conf >> rate_mon_file;
				// rate_mon_file = get_output_file_name(network_conf, rate_mon_file);
			}else if(key.compare("CNP_MON_FILE") == 0){
				conf >> cnp_mon_file;
				// cnp_mon_file = get_output_file_name(network_conf, cnp_mon_file);
			}
      #ifdef HASH_EGRESSPORT_OBSERVATION
      else if (key.compare("HASH_MON_FILE") == 0){
        conf >> hash_mon_file;
      }
      #endif
      else if (key.compare("MON_START") == 0){
				conf >> mon_start;
			}else if (key.compare("MON_END") == 0){
				conf >> mon_end;
			}else if(key.compare("QP_MON_INTERVAL") == 0){
				conf >> qp_mon_interval;
			}else if(key.compare("BW_MON_INTERVAL") == 0){
				conf >> bw_mon_interval;
			}else if(key.compare("QLEN_MON_INTERVAL") == 0){
				conf >> qlen_mon_interval;
      } else if(key.compare("APS_SELECTED_MON_INTERVAL") == 0) {
        conf >> aps_selected_mon_interval;
      } else if(key.compare("APS_SELECTED_TRACED_NODE") == 0) {
        conf >> aps_selected_traced_node;
      } else if(key.compare("SWITCH_OUTPORT_MON_INTERVAL") == 0) {
        conf >> switch_outport_mon_interval;
      } else if (key.compare("MULTI_RATE") == 0) {
        int v;
        conf >> v;
        multi_rate = v;
      } else if (key.compare("SAMPLE_FEEDBACK") == 0) {
        int v;
        conf >> v;
        sample_feedback = v;
      } else if (key.compare("PINT_LOG_BASE") == 0) {
        conf >> pint_log_base;
      } else if (key.compare("PINT_PROB") == 0) {
        conf >> pint_prob;
      } else if (key.compare("LB_MODE") == 0) {
        conf >> lb_mode;
      } else if (key.compare("MIX_LB_RATIO") == 0) {
        double v;
        conf >> v;
        mix_lb_ratio = v;
      } else if (key.compare("HASH_TYPE") == 0) {
        conf >> hash_type;
      } else if (key.compare("APS_INDICATOR_MASK") == 0) { // aps
        uint32_t v;
        conf >> v;
        aps_indMask = v;
      } else if (key.compare("APS_UPDATE_FREQUENCY") == 0) { 
        conf >> aps_updateFreq;
      } else if (key.compare("FLOWBENDER_ECN_T") == 0) { // flowbender
        double v;
        conf >> v;
        if (v > 1) v = 1.0;
        else if ( v < 0 ) v = 0;
        else flowbender_ecn_t = v;
      } else if (key.compare("FLOWBENDER_SWITCH_N") == 0) { // flowbender
        uint32_t v;
        conf >> v;
        flowbender_switch_n = v;
      } else if (key.compare("LETFLOW_TIMEOUT") == 0) { // letflow
        uint64_t v;
        conf >> v;
        letflow_flowletTimeout = MicroSeconds(v);
      } else if (key.compare("LETFLOW_AGING_TIME") == 0) {
        uint64_t v;
        conf >> v;
        letflow_agingTime = MilliSeconds(v);
      } else if (key.compare("MAX_OOO_SIZE") == 0) {
        conf >> max_ooo_size;
      } else if (key.compare("REPS_BUFFER_SIZE") == 0) {
        uint32_t v;
        conf >> v;
        reps_bufferSize = v;
      } else if (key.compare("PSN_PATH_K") == 0) {
        uint32_t v;
        conf >> v;
        psn_path_k = v;
      } else if (key.compare("IOPS_BUFFER_SIZE") == 0) {
        uint32_t v;
        conf >> v;
        iops_bufferSize = v;
      } else if (key.compare("APS_PATH_CREDIT") == 0) {
        uint32_t v;
        conf >> v;
        aps_path_credit = v;
      } else if (key.compare("SWITCH_SAMPLE_TIME_INTERVAL") == 0) {
        uint64_t v;
        conf >> v;
        sw_sample_time_interval = v;
      } else if (key.compare("APS_ESTIMATE_WINDOW_SIZE") == 0) {
        uint32_t v;
        conf >> v;
        aps_estimate_window_size = v;
      } else if (key.compare("RETRANS_TIME_OUT") == 0) {
        uint32_t v;
        conf >> v;
        retrans_time_out = v;
      } else if (key.compare("SWITCH_FAILURE") == 0) {
        conf >> switch_failure_file;
      }

      fflush(stdout);
    }
    conf.close();
    return true;
}

void SetConfig() {
  bool dynamicth = use_dynamic_pfc_threshold;

  Config::SetDefault("ns3::QbbNetDevice::PauseTime", UintegerValue(pause_time));
  Config::SetDefault("ns3::QbbNetDevice::QcnEnabled", BooleanValue(enable_qcn));
  Config::SetDefault("ns3::QbbNetDevice::DynamicThreshold",
                     BooleanValue(dynamicth));

  IntHop::multi = int_multi;
  if (cc_mode == 7) 
    IntHeader::mode = IntHeader::TS;
  else if (cc_mode == 3 || lb_mode == 1 || lb_mode == 6) 
    IntHeader::mode = IntHeader::NORMAL;
  else if (cc_mode == 10) 
    IntHeader::mode = IntHeader::PINT;
  else
    IntHeader::mode = IntHeader::NONE;

  if (cc_mode == 10) {
    Pint::set_log_base(pint_log_base);
    IntHeader::pint_bytes = Pint::get_n_bytes();
    printf("PINT bits: %d bytes: %d\n", Pint::get_n_bits(),
           Pint::get_n_bytes());
  }
}
uint32_t get_random_lb(double mix_lb_ratio, uint32_t lb_mode1, uint32_t lb_mode2){
    static std::mt19937 rng(0xb214);  // 使用梅森旋转算法，固定种子  
    static std::uniform_real_distribution<double> dist(0.0, 1.0);
    return (dist(rng) < mix_lb_ratio) ? lb_mode1 : lb_mode2;
}
static Ptr<Node>
FindNodeById(const std::vector<Ptr<Node>> &nodes, uint32_t nodeId)
{
    for (auto node : nodes) {
        if (node->GetId() == nodeId) {
            return node;
        }
    }
    return nullptr;
}

static uint64_t
EncodeLetflowPathId(const std::vector<uint32_t> &ports)
{
    NS_ASSERT_MSG(ports.size() <= 8, "LetFlow path supports at most 8 hops");

    uint64_t pathId = 0;

    for (size_t i = 0; i < ports.size(); i++) {
        NS_ASSERT_MSG(ports[i] > 0 && ports[i] <= 255,
                      "LetFlow path port must be in range [1, 255]");

        pathId |= ((uint64_t)(ports[i] & 0xff)) << (8 * i);
    }

    return pathId;
}
void SetupNetwork(void (*qp_finish)(FILE *, Ptr<RdmaQueuePair>),void (*send_finish)(FILE *, Ptr<RdmaQueuePair>))
{

  topof.open(topology_file.c_str());
  flowf.open(flow_file.c_str());
  tracef.open(trace_file.c_str());
  switch_failuref.open(switch_failure_file.c_str());
  string gpu_type_str;

  topof >> node_num >> gpus_per_server >> nvswitch_num >> switch_num >>
      link_num >> gpu_type_str;
  flowf >> flow_num;
  tracef >> trace_num;
  switch_failuref >> switch_failure_num;
  if(gpu_type_str == "A100"){
    gpu_type = GPUType::A100;
  } else if(gpu_type_str == "A800"){
    gpu_type = GPUType::A800;
  } else if(gpu_type_str == "H100"){
    gpu_type = GPUType::H100;
  } else if(gpu_type_str == "H800"){
    gpu_type = GPUType::H800;
  } else{
    gpu_type = GPUType::NONE;
  }

  std::vector<uint32_t> node_type(node_num, 0);
  for (uint32_t i = 0; i < nvswitch_num; i++) {
    uint32_t sid;
    topof >> sid;
    node_type[sid] = 2;
	}
	for (uint32_t i = 0; i < switch_num; i++)
	{
		uint32_t sid;
		topof >> sid;
		node_type[sid] = 1;
	}
  FILE *switch_forward_output = fopen(switch_forward_output_file.c_str(), "w"); // switch forward output file
	for (uint32_t i = 0; i < node_num; i++){
		if (node_type[i] == 0)
			n.Add(CreateObject<Node>()); // GPU/NIC
		else if(node_type[i] == 1){
			Ptr<SwitchNode> sw = CreateObject<SwitchNode>(); // Switch
			n.Add(sw);
			sw->SetAttribute("EcnEnabled", BooleanValue(enable_qcn));
      sw->TraceConnectWithoutContext(
          "SwitchForward", MakeBoundCallback(&get_switch_forward, switch_forward_output, n.Get(i)->GetId()));
		}else if(node_type[i] == 2){
			Ptr<NVSwitchNode> sw = CreateObject<NVSwitchNode>(); // NVSwitch
			n.Add(sw);
		}
	}

  NS_LOG_INFO("Create nodes.");
  InternetStackHelper internet;
  internet.Install(n);

  for (uint32_t i = 0; i < node_num; i++) { // assgin 10.xx.xx.1 to the first interface of each node
    if (n.Get(i)->GetNodeType() == 0) {
      serverAddress.resize(i + 1);
      serverAddress[i] = node_id_to_ip(i);
    } else if(n.Get(i)->GetNodeType() == 2) {
      serverAddress.resize(i + 1);
      serverAddress[i] = node_id_to_ip(i);
    }
  }

  NS_LOG_INFO("Create channels.");

  Ptr<RateErrorModel> rem = CreateObject<RateErrorModel>();
  Ptr<UniformRandomVariable> uv = CreateObject<UniformRandomVariable>();
  rem->SetRandomVariable(uv);
  uv->SetStream(50);
  rem->SetAttribute("ErrorRate", DoubleValue(error_rate_per_link));
  rem->SetAttribute("ErrorUnit", StringValue("ERROR_UNIT_PACKET"));

  FILE *pfc_file = fopen(pfc_output_file.c_str(), "w");

  QbbHelper qbb;
  Ipv4AddressHelper ipv4;
  std::vector<std::pair<uint32_t, uint32_t>> link_pairs;  // src, dst link pairs
  for (uint32_t i = 0; i < link_num; i++) {
    uint32_t src, dst;
    Ptr<Node> snode, dnode;
    std::string data_rate, link_delay;
    vector<double> link_failed_time;
    bool half_speed = false;
    double error_rate;
    // topof >> src >> dst >> data_rate >> link_delay >> error_rate;
    // 支持读取变长列
    string line;
    if (getline(topof >> std::ws, line)) {  // 吃掉前导空白/残留换行
      std::istringstream iss(line);
      if (!(iss >> src >> dst >> data_rate >> link_delay >> error_rate)) {
        printf("Error: Invalid topology line format at link index %u: %s\n", i, line.c_str());
        return;
      }
      string val;
      snode = n.Get(src), dnode = n.Get(dst);
      while (iss >> val) {
        if (val.compare("half") == 0) half_speed = true;
        else link_failed_time.push_back(stod(val));
      }
      if (half_speed) Simulator::Schedule(MicroSeconds(sim_start), &ChangeLinkState, snode, dnode, 2);

      // 调度链路故障、启用 (故障、启用必须交替出现，且必须以故障开始)，时间单位为 us
      bool tick = true; // true means link is up, false means link is down
      for (const auto &time : link_failed_time) {
        if (tick) {
          Simulator::Schedule(MicroSeconds(sim_start) + MicroSeconds(time), &ChangeLinkState, snode, dnode, 0);
        } else {
          Simulator::Schedule(MicroSeconds(sim_start) + MicroSeconds(time), &ChangeLinkState, snode, dnode, 1);
        }
        tick = !tick;        
      }

    } else {
      printf("Error: Topology file has fewer lines than expected. Expected %u links.\n", link_num);
      return;
    }

    link_pairs.push_back(std::make_pair(src, dst));
    
    qbb.SetDeviceAttribute("DataRate", StringValue(data_rate));
    qbb.SetChannelAttribute("Delay", StringValue(link_delay));

    if (error_rate > 0) {
      Ptr<RateErrorModel> rem = CreateObject<RateErrorModel>();
      Ptr<UniformRandomVariable> uv = CreateObject<UniformRandomVariable>();
      rem->SetRandomVariable(uv);
      uv->SetStream(50);
      rem->SetAttribute("ErrorRate", DoubleValue(error_rate));
      rem->SetAttribute("ErrorUnit", StringValue("ERROR_UNIT_PACKET"));
      qbb.SetDeviceAttribute("ReceiveErrorModel", PointerValue(rem));
    } else {
      qbb.SetDeviceAttribute("ReceiveErrorModel", PointerValue(rem));
    }

    fflush(stdout);

    NetDeviceContainer d = qbb.Install(snode, dnode);
    if (snode->GetNodeType() == 0 || snode->GetNodeType() == 2) {
      Ptr<Ipv4> ipv4 = snode->GetObject<Ipv4>();
      ipv4->AddInterface(d.Get(0));
      ipv4->AddAddress(
          1, Ipv4InterfaceAddress(serverAddress[src], Ipv4Mask(0xff000000)));
    }
    if (dnode->GetNodeType() == 0 || dnode->GetNodeType() == 2) {
      Ptr<Ipv4> ipv4 = dnode->GetObject<Ipv4>();
      ipv4->AddInterface(d.Get(1));
      ipv4->AddAddress(
          1, Ipv4InterfaceAddress(serverAddress[dst], Ipv4Mask(0xff000000)));
    }

    nbr2if[snode][dnode].idx =
        DynamicCast<QbbNetDevice>(d.Get(0))->GetIfIndex();
    nbr2if[snode][dnode].up = true;
    nbr2if[snode][dnode].delay =
        DynamicCast<QbbChannel>(
            DynamicCast<QbbNetDevice>(d.Get(0))->GetChannel())
            ->GetDelay()
            .GetTimeStep();
    nbr2if[snode][dnode].bw =
        DynamicCast<QbbNetDevice>(d.Get(0))->GetDataRate().GetBitRate();
    nbr2if[dnode][snode].idx =
        DynamicCast<QbbNetDevice>(d.Get(1))->GetIfIndex();
    nbr2if[dnode][snode].up = true;
    nbr2if[dnode][snode].delay =
        DynamicCast<QbbChannel>(
            DynamicCast<QbbNetDevice>(d.Get(1))->GetChannel())
            ->GetDelay()
            .GetTimeStep();
    nbr2if[dnode][snode].bw =
        DynamicCast<QbbNetDevice>(d.Get(1))->GetDataRate().GetBitRate();

    char ipstring[16];
    sprintf(ipstring, "10.%d.%d.0", i / 254 + 1, i % 254 + 1);
    ipv4.SetBase(ipstring, "255.255.255.0");
    ipv4.Assign(d);

    DynamicCast<QbbNetDevice>(d.Get(0))->TraceConnectWithoutContext(
        "QbbPfc", MakeBoundCallback(&get_pfc, pfc_file,
                                    DynamicCast<QbbNetDevice>(d.Get(0))));
    DynamicCast<QbbNetDevice>(d.Get(1))->TraceConnectWithoutContext(
        "QbbPfc", MakeBoundCallback(&get_pfc, pfc_file,
                                    DynamicCast<QbbNetDevice>(d.Get(1))));
  }

  /* Get IP address <-> NodeID pairs */
  Ipv4Address empty_ip;
  for (uint32_t i = 0; i < node_num; ++i) {
      if (n.Get(i)->GetNodeType() == 0 || n.Get(i)->GetNodeType() == 2) {  // is server
          if (serverAddress[i].Get() == empty_ip.Get()) {
              printf("XXX ERROR %d\n", i);
              printf("size of serverAddress: %lu", serverAddress.size());
              NS_FATAL_ERROR("An end-host belongs to no link");
          }
        Settings::hostId2IpMap[i] = serverAddress[i].Get();
      }
  }

  // 支持读取变长序列
  string line;
  for (int i = 0; i < switch_failure_num; i++) {
    if (getline(switch_failuref >> std::ws, line)) {  // 吃掉前导空白/残留换行
      std::istringstream iss(line);
      vector<double> switch_failed_time;
      uint32_t switch_node;    

      if (!(iss >> switch_node)) {
        printf("Error: Invalid Switch failure line format\n");
        return;
      }
      double val;
      while (iss >> val) {
        switch_failed_time.push_back(val);
      }

      // 调度交换机故障、启用 (故障、启用必须交替出现，且必须以故障开始)，时间单位为 us
      bool tick = true; // true means link is up, false means link is down
      for (const auto &time : switch_failed_time) {
        if (tick) {
          Simulator::Schedule(MicroSeconds(sim_start) + MicroSeconds(time), &ChangeSwitchState, DynamicCast<SwitchNode>(n.Get(switch_node)), true);
        } else {
          Simulator::Schedule(MicroSeconds(sim_start) + MicroSeconds(time), &ChangeSwitchState, DynamicCast<SwitchNode>(n.Get(switch_node)), false);
        }
        tick = !tick;
      }  
    } else {
      printf("Error: Switch failure file has fewer lines than expected. Expected %u switch failure.\n", switch_failure_num);
      return;
    }
  }

  nic_rate = get_nic_rate(n);
  for (uint32_t i = 0; i < node_num; i++) {
    if (n.Get(i)->GetNodeType() == 1) { // set switch node
      Ptr<SwitchNode> sw = DynamicCast<SwitchNode>(n.Get(i));
      uint32_t shift = 3; 

      for (uint32_t j = 1; j < sw->GetNDevices(); j++) {
        Ptr<QbbNetDevice> dev = DynamicCast<QbbNetDevice>(sw->GetDevice(j));
        uint64_t rate = dev->GetDataRate().GetBitRate();
        NS_ASSERT_MSG(rate2kmin.find(rate) != rate2kmin.end(),
                      "must set kmin for each link speed");
        NS_ASSERT_MSG(rate2kmax.find(rate) != rate2kmax.end(),
                      "must set kmax for each link speed");
        NS_ASSERT_MSG(rate2pmax.find(rate) != rate2pmax.end(),
                      "must set pmax for each link speed");
        sw->m_mmu->ConfigEcn(j, rate2kmin[rate], rate2kmax[rate],
                             rate2pmax[rate]);
        uint64_t delay = DynamicCast<QbbChannel>(dev->GetChannel())
                             ->GetDelay()
                             .GetTimeStep();
        uint32_t headroom = rate * delay / 8 / 1000000000 * 3;
        sw->m_mmu->ConfigHdrm(j, headroom);
        sw->m_mmu->pfc_a_shift[j] = shift;
        while (rate > nic_rate && sw->m_mmu->pfc_a_shift[j] > 0) {
          sw->m_mmu->pfc_a_shift[j]--;
          rate /= 2;
        }
      }
      sw->m_mmu->ConfigNPort(sw->GetNDevices() - 1);
      sw->m_mmu->ConfigBufferSize(buffer_size * 1024 * 1024);
      sw->m_mmu->node_id = sw->GetId();
    } else if(n.Get(i)->GetNodeType() == 2){ // set nvswitch node
			Ptr<NVSwitchNode> sw = DynamicCast<NVSwitchNode>(n.Get(i));
      uint32_t shift = 3; 
      for (uint32_t j = 1; j < sw->GetNDevices(); j++) {
        Ptr<QbbNetDevice> dev = DynamicCast<QbbNetDevice>(sw->GetDevice(j));
        uint64_t rate = dev->GetDataRate().GetBitRate();
        uint64_t delay = DynamicCast<QbbChannel>(dev->GetChannel())
                             ->GetDelay()
                             .GetTimeStep();
        uint32_t headroom = rate * delay / 8 / 1000000000 * 3;
        sw->m_mmu->ConfigHdrm(j, headroom);
        sw->m_mmu->pfc_a_shift[j] = shift;
        while (rate > nic_rate && sw->m_mmu->pfc_a_shift[j] > 0) {
          sw->m_mmu->pfc_a_shift[j]--;
          rate /= 2;
        }
      }
			sw->m_mmu->ConfigNPort(sw->GetNDevices()-1);
			sw->m_mmu->ConfigBufferSize(buffer_size* 1024 * 1024);
			sw->m_mmu->node_id = sw->GetId();
		}
  }
// void SetOutPutPath() {
//   fct_output_file 
//     std::string path = "test_dir";

//     if (!fs::exists(path)) {   // 不存在
//         if (fs::create_directory(path)) {
//             std::cout << "目录已创建: " << path << "\n";
//         } else {
//             std::cerr << "创建失败\n";
//         }
//     } else {
//         std::cout << "目录已存在: " << path << "\n";
//     }  
// }
#if ENABLE_QP // enable rdma
  FILE *fct_output = fopen(fct_output_file.c_str(), "w");
  FILE *send_output = fopen(send_output_file.c_str(), "w");
  FILE *ooo_buffer_output = fopen(ooo_buffer_output_file.c_str(), "w");
  for (uint32_t i = 0; i < node_num; i++) {
    if (n.Get(i)->GetNodeType() == 0 || n.Get(i)->GetNodeType() == 2) { 
      Ptr<RdmaHw> rdmaHw = CreateObject<RdmaHw>();
      rdmaHw->SetAttribute("ClampTargetRate", BooleanValue(clamp_target_rate));
      rdmaHw->SetAttribute("AlphaResumInterval",
                           DoubleValue(alpha_resume_interval));
      rdmaHw->SetAttribute("RPTimer", DoubleValue(rp_timer));
      rdmaHw->SetAttribute("FastRecoveryTimes",
                           UintegerValue(fast_recovery_times));
      rdmaHw->SetAttribute("EwmaGain", DoubleValue(ewma_gain));
      rdmaHw->SetAttribute("RateAI", DataRateValue(DataRate(rate_ai)));
      rdmaHw->SetAttribute("RateHAI", DataRateValue(DataRate(rate_hai)));
      rdmaHw->SetAttribute("L2BackToZero", BooleanValue(l2_back_to_zero));
      rdmaHw->SetAttribute("L2ChunkSize", UintegerValue(l2_chunk_size));
      rdmaHw->SetAttribute("L2AckInterval", UintegerValue(l2_ack_interval));
      if (mix_lb_ratio > 0) {
        uint32_t mix_lb_mode = get_random_lb(mix_lb_ratio, 0, lb_mode);
        rdmaHw->SetAttribute("LbMode", UintegerValue(mix_lb_mode));
      } else {
        rdmaHw->SetAttribute("LbMode", UintegerValue(lb_mode));
      }
      Settings::lb_mode = lb_mode;
      rdmaHw->SetAttribute("CcMode", UintegerValue(cc_mode));
      rdmaHw->SetAttribute("RateDecreaseInterval",
                           DoubleValue(rate_decrease_interval));
      rdmaHw->SetAttribute("MinRate", DataRateValue(DataRate(min_rate)));
      rdmaHw->SetAttribute("Mtu", UintegerValue(packet_payload_size));
      rdmaHw->SetAttribute("MiThresh", UintegerValue(mi_thresh));
      rdmaHw->SetAttribute("VarWin", BooleanValue(var_win));
      rdmaHw->SetAttribute("HasWin", BooleanValue(has_win));
      rdmaHw->SetAttribute("OooAck", BooleanValue(ooo_ack));
      rdmaHw->SetAttribute("AckPsn", BooleanValue(ack_psn));
      rdmaHw->SetAttribute("FastReact", BooleanValue(fast_react));
      rdmaHw->SetAttribute("MultiRate", BooleanValue(multi_rate));
      rdmaHw->SetAttribute("SampleFeedback", BooleanValue(sample_feedback));
      rdmaHw->SetAttribute("TargetUtil", DoubleValue(u_target));
      rdmaHw->SetAttribute("RateBound", BooleanValue(rate_bound));
      rdmaHw->SetAttribute("DctcpRateAI",
                           DataRateValue(DataRate(dctcp_rate_ai)));
      rdmaHw->SetAttribute("GPUsPerServer", UintegerValue(gpus_per_server));
      rdmaHw->SetPintSmplThresh(pint_prob);
      rdmaHw->SetAttribute("TotalPauseTimes",
                           UintegerValue(nic_total_pause_time));
      rdmaHw->SetAttribute("MaxOOOSize", UintegerValue(max_ooo_size));                     
      rdmaHw->SetAttribute("UpdateFrequency", UintegerValue(aps_updateFreq));                     
      rdmaHw->SetAttribute("ApsIndMask", UintegerValue(aps_indMask));    
      rdmaHw->SetAttribute("FlowBender_T", DoubleValue(flowbender_ecn_t));    
      rdmaHw->SetAttribute("FlowBender_N", UintegerValue(flowbender_switch_n));  
      rdmaHw->SetAttribute("REPSBufferSize", UintegerValue(reps_bufferSize));  
      rdmaHw->SetAttribute("PSNPATH_K", UintegerValue(psn_path_k));  
      rdmaHw->SetAttribute("IOPSBufferSize", UintegerValue(iops_bufferSize));  
      rdmaHw->SetAttribute("ApsPathCredit", UintegerValue(aps_path_credit));
      rdmaHw->SetAttribute("TracedNode", UintegerValue(aps_selected_traced_node));
      rdmaHw->SetAttribute("EstimateWindowSize", UintegerValue(aps_estimate_window_size));
      rdmaHw->SetAttribute("RetransTimeOut", UintegerValue(retrans_time_out));

      Ptr<RdmaDriver> rdma = CreateObject<RdmaDriver>();
      Ptr<Node> node = n.Get(i);
      rdma->SetNode(node);
      rdma->SetRdmaHw(rdmaHw);

      node->AggregateObject(rdma);
      rdma->Init();
      rdma->TraceConnectWithoutContext(
          "QpComplete", MakeBoundCallback(qp_finish, fct_output));
      rdma->TraceConnectWithoutContext("SendComplete",MakeBoundCallback(send_finish,send_output));
      rdma->TraceConnectWithoutContext("OooBufferChange",
        MakeBoundCallback(&get_ooo_buf, ooo_buffer_output));
    }
  }
#endif

  if (ack_high_prio)
    RdmaEgressQueue::ack_q_idx = 0;
  else
    RdmaEgressQueue::ack_q_idx = 3;

  CalculateRoutes(n);
  SetRoutingEntries();

  maxRtt = maxBdp = 0;
  for (uint32_t i = 0; i < node_num; i++) {
    if (n.Get(i)->GetNodeType() != 0)
      continue;
    for (uint32_t j = 0; j < node_num; j++) {
      if (n.Get(j)->GetNodeType() != 0)
        continue;
      uint64_t delay = pairDelay[n.Get(i)][n.Get(j)];
      uint64_t txDelay = pairTxDelay[n.Get(i)][n.Get(j)];
      uint64_t rtt = delay * 2 + txDelay;
      #ifdef COMMON_RTT_LOG
        printf("rtt[%u][%u]=%lu ns, where delay*2=%lu, txDelay=%lu\n", i, j, rtt, delay * 2, txDelay);
      #endif
      uint64_t bw = pairBw[i][j];
      uint64_t bdp = rtt * bw / 1000000000 / 8;
      pairBdp[n.Get(i)][n.Get(j)] = bdp;
      // printf("Src: %u, Dst: %u, rtt: %lu, bw: %lu, BDP: %lu\n", i, j, rtt, bw, bdp);
      pairRtt[i][j] = rtt;
      if (bdp > maxBdp)
        maxBdp = bdp;
      if (rtt > maxRtt)
        maxRtt = rtt;
    }
  }
  printf("maxRtt=%lu maxBdp=%lu\n", maxRtt, maxBdp);

  /* Config ToR Switch */
  for (auto &pair : link_pairs) {
      Ptr<Node> probably_host = n.Get(pair.first);
      Ptr<Node> probably_switch = n.Get(pair.second);

      // host-switch link
      if (probably_host->GetNodeType() == 0 && probably_switch->GetNodeType() == 1) {
          Ptr<SwitchNode> sw = DynamicCast<SwitchNode>(probably_switch);
          sw->m_isToR = true;
          uint32_t hostIP = serverAddress[pair.first].Get();
          sw->m_isToR_hostIP.insert(hostIP);
          if (idxNodeToR.find(sw->GetId()) == idxNodeToR.end()) {
              idxNodeToR[sw->GetId()] = sw;
          };
      }
  }

  recordRoutingEntries();
  // printRoutingEntries();

  // /* config load balancer's switches using ToR-to-ToR routing */
  // if (lb_mode == 4) {  // Conga, Letflow, Conweave
  //     NS_LOG_INFO("Configuring Load Balancer's Switches");
  //     for (auto &pair : link_pairs) {
  //         Ptr<Node> probably_host = n.Get(pair.first);
  //         Ptr<Node> probably_switch = n.Get(pair.second);

  //         // host-switch link
  //         if (probably_host->GetNodeType() == 0 && probably_switch->GetNodeType() == 1) {
  //             Ptr<SwitchNode> sw = DynamicCast<SwitchNode>(probably_switch);
  //             uint32_t hostIP = serverAddress[pair.first].Get();
  //             Settings::hostIp2SwitchId[hostIP] = sw->GetId();  // hostIP -> connected switch's ID
  //             Settings::hostIp2SwitchIds[hostIP].insert(sw->GetId());  // hostIP -> connected switch's ID
  //         }
  //     }

  //     // Letflow: m_letflowRoutingTable
  //     for (auto i = nextHop.begin(); i != nextHop.end(); i++) {  // every node
  //         if (i->first->GetNodeType() == 1) {                    // switch
  //             Ptr<Node> nodeSrc = i->first;
  //             Ptr<SwitchNode> swSrc = DynamicCast<SwitchNode>(nodeSrc);  // switch
  //             uint32_t swSrcId = swSrc->GetId();

  //             if (swSrc->m_isToR) {
  //                 // printf("--- ToR Switch %d\n", swSrcId);

  //                 auto table1 = i->second;
  //                 for (auto j = table1.begin(); j != table1.end(); j++) {
  //                     Ptr<Node> dst = j->first;  // dst
  //                     uint32_t dstIP = Settings::hostId2IpMap[dst->GetId()];
  //                     uint32_t swDstId = Settings::hostIp2SwitchId[dstIP];  // Rx(dst)ToR

  //                     if (swSrcId == swDstId) {
  //                         continue;  // if in the same pod, then skip
  //                     }


  //                     // construct paths
  //                     uint64_t pathId;
  //                     uint8_t path_ports[8] = {0, 0, 0, 0, 0, 0, 0, 0};  // interface is always large than 0
  //                     vector<Ptr<Node>> nexts1 = j->second;
  //                     for (auto next1 : nexts1) {
  //                         uint32_t outPort1 = nbr2if[nodeSrc][next1].idx;
  //                         auto nexts2 = nextHop[next1][dst];
  //                         if (nexts2.size() == 1 && nexts2[0]->GetId() == swDstId) {
  //                             // this destination has 2-hop distance
  //                             uint32_t outPort2 = nbr2if[next1][nexts2[0]].idx;
  //                             // printf("[IntraPod-2hop] %d (%d)-> %d (%d) -> %d -> %d\n",
  //                             // nodeSrc->GetId(), outPort1, next1->GetId(), outPort2,
  //                             // nexts2[0]->GetId(), dst->GetId());
  //                             path_ports[0] = (uint8_t)outPort1;
  //                             path_ports[1] = (uint8_t)outPort2;
  //                             pathId = *((uint64_t *)path_ports);

  //                             if (lb_mode == 4) {
  //                                 swSrc->m_mmu->m_letflowRouting.m_letflowRoutingTable[swDstId]
  //                                     .insert(pathId);
  //                             }

  //                             continue;
  //                         }

  //                         for (auto next2 : nexts2) {
  //                             uint32_t outPort2 = nbr2if[next1][next2].idx;
  //                             auto nexts3 = nextHop[next2][dst];
  //                             if (nexts3.size() == 1 && nexts3[0]->GetId() == swDstId) {
  //                                 // this destination has 3-hop distance
  //                                 uint32_t outPort3 = nbr2if[next2][nexts3[0]].idx;
  //                                 // printf("[IntraPod-3hop] %d (%d)-> %d (%d) -> %d (%d) -> %d ->
  //                                 // %d\n", nodeSrc->GetId(), outPort1, next1->GetId(), outPort2,
  //                                 // next2->GetId(), outPort3, nexts3[0]->GetId(), dst->GetId());
  //                                 path_ports[0] = (uint8_t)outPort1;
  //                                 path_ports[1] = (uint8_t)outPort2;
  //                                 path_ports[2] = (uint8_t)outPort3;
  //                                 pathId = *((uint64_t *)path_ports);

  //                                 if (lb_mode == 4) {
  //                                     swSrc->m_mmu->m_letflowRouting
  //                                         .m_letflowRoutingTable[swDstId]
  //                                         .insert(pathId);
  //                                 }

  //                                 continue;
  //                             }

  //                             for (auto next3 : nexts3) {
  //                                 uint32_t outPort3 = nbr2if[next2][next3].idx;
  //                                 auto nexts4 = nextHop[next3][dst];
  //                                 if (nexts4.size() == 1 && nexts4[0]->GetId() == swDstId) {
  //                                     // this destination has 4-hop distance
  //                                     uint32_t outPort4 = nbr2if[next3][nexts4[0]].idx;
  //                                     // printf("[IntraPod-4hop] %d (%d)-> %d (%d) -> %d (%d) ->
  //                                     // %d (%d) -> %d -> %d\n", nodeSrc->GetId(), outPort1,
  //                                     // next1->GetId(), outPort2, next2->GetId(), outPort3,
  //                                     // next3->GetId(), outPort4, nexts4[0]->GetId(),
  //                                     // dst->GetId());
  //                                     path_ports[0] = (uint8_t)outPort1;
  //                                     path_ports[1] = (uint8_t)outPort2;
  //                                     path_ports[2] = (uint8_t)outPort3;
  //                                     path_ports[3] = (uint8_t)outPort4;
  //                                     pathId = *((uint64_t *)path_ports);

  //                                     if (lb_mode == 4) {
  //                                         swSrc->m_mmu->m_letflowRouting
  //                                             .m_letflowRoutingTable[swDstId]
  //                                             .insert(pathId);
  //                                     }

  //                                     continue;
  //                                 } 
                                  
  //                                 for (auto next4 : nexts4) {
  //                                   uint32_t outPort4 = nbr2if[next3][next4].idx;
  //                                   auto nexts5 = nextHop[next4][dst];
  //                                   if (nexts5.size() == 1 && nexts5[0]->GetId() == swDstId) {
  //                                       // this destination has 4-hop distance
  //                                       uint32_t outPort5 = nbr2if[next4][nexts5[0]].idx;
  //                                       // printf("[IntraPod-4hop] %d (%d)-> %d (%d) -> %d (%d) ->
  //                                       // %d (%d) -> %d -> %d\n", nodeSrc->GetId(), outPort1,
  //                                       // next1->GetId(), outPort2, next2->GetId(), outPort3,
  //                                       // next4->GetId(), outPort4, nexts5[0]->GetId(),
  //                                       // dst->GetId());
  //                                       path_ports[0] = (uint8_t)outPort1;
  //                                       path_ports[1] = (uint8_t)outPort2;
  //                                       path_ports[2] = (uint8_t)outPort3;
  //                                       path_ports[3] = (uint8_t)outPort4;
  //                                       path_ports[4] = (uint8_t)outPort5;
  //                                       pathId = *((uint64_t *)path_ports);

  //                                       if (lb_mode == 4) {
  //                                           swSrc->m_mmu->m_letflowRouting
  //                                               .m_letflowRoutingTable[swDstId]
  //                                               .insert(pathId);
  //                                       } 

  //                                       continue;

  //                                   } else {
  //                                         printf("Too large topology?\n");
  //                                         assert(false);
  //                                   }
  //                                 }
  //                             }
  //                         }
  //                     }
  //                 }
  //             }
  //         }
  //     }

  //     // Constant setup, and switchInfo
  //     for (auto i = nextHop.begin(); i != nextHop.end(); i++) {  // every node
  //         if (i->first->GetNodeType() == 1) {
  //             Ptr<Node> node = i->first;
  //             Ptr<SwitchNode> sw = DynamicCast<SwitchNode>(node);  // switch
  //             #ifdef SWITCH_INIT_INFO
  //               printf("[INFO:SWITCH] Switch ID:%u, ToR:%d\n", sw->GetId(), sw->m_isToR);
  //             #endif

  //             if (lb_mode == 4) {
  //                 sw->m_mmu->m_letflowRouting.SetConstants(letflow_agingTime,
  //                                                           letflow_flowletTimeout);
  //                 sw->m_mmu->m_letflowRouting.SetSwitchInfo(sw->m_isToR, sw->GetId());
  //             }

  //         }
  //     }

  // }

/* config load balancer's switches using ToR-to-ToR routing */
if (lb_mode == 4) {  // Conga, Letflow, Conweave
    NS_LOG_INFO("Configuring Load Balancer's Switches");

    /*
     * In the original implementation:
     *     hostIp2SwitchId[hostIP] = swId;
     *
     * This assumes that each host is connected to only one ToR.
     *
     * In dual-plane / dual-NIC topologies, one host may be connected to
     * multiple ToRs. Therefore, hostIp2SwitchId is changed to:
     *
     *     hostIP -> set<connected ToR IDs>
     */
    Settings::hostIp2SwitchId.clear();

    for (auto &pair : link_pairs) {
        Ptr<Node> nodeA = n.Get(pair.first);
        Ptr<Node> nodeB = n.Get(pair.second);

        Ptr<Node> probably_host = nullptr;
        Ptr<Node> probably_switch = nullptr;

        // host-switch link: host -> switch
        if (nodeA->GetNodeType() == 0 && nodeB->GetNodeType() == 1) {
            probably_host = nodeA;
            probably_switch = nodeB;
        }
        // host-switch link: switch -> host
        else if (nodeA->GetNodeType() == 1 && nodeB->GetNodeType() == 0) {
            probably_host = nodeB;
            probably_switch = nodeA;
        }
        else {
            continue;
        }

        Ptr<SwitchNode> sw = DynamicCast<SwitchNode>(probably_switch);
        NS_ASSERT_MSG(sw != nullptr, "Failed to cast node to SwitchNode");

        uint32_t hostIP = serverAddress[probably_host->GetId()].Get();

        /*
         * Key change:
         * A host IP may correspond to multiple connected ToRs.
         */
        Settings::hostIp2SwitchId[hostIP].insert(sw->GetId());

#ifdef SWITCH_INIT_INFO
        printf("[INFO:HOST-ToR] Host ID:%u, IP:%u, connected switch ID:%u\n",
               probably_host->GetId(), hostIP, sw->GetId());
#endif
    }

    /*
     * Letflow: m_letflowRoutingTable
     *
     * For each source ToR, construct candidate paths to each destination ToR.
     *
     * Original assumption:
     *     dstHost -> one dstToR
     *
     * New logic:
     *     dstHost -> multiple dstToRs
     *
     * Therefore, for each destination host, we enumerate all its connected
     * destination ToRs and insert paths separately:
     *
     *     m_letflowRoutingTable[dstToR].insert(pathId)
     */
    for (auto i = nextHop.begin(); i != nextHop.end(); i++) {  // every node
        if (i->first->GetNodeType() == 1) {                    // switch
            Ptr<Node> nodeSrc = i->first;
            Ptr<SwitchNode> swSrc = DynamicCast<SwitchNode>(nodeSrc);  // switch
            NS_ASSERT_MSG(swSrc != nullptr, "Failed to cast source node to SwitchNode");

            uint32_t swSrcId = swSrc->GetId();

            if (swSrc->m_isToR) {
                auto table1 = i->second;

                for (auto j = table1.begin(); j != table1.end(); j++) {
                    Ptr<Node> dst = j->first;  // dst host

                    uint32_t dstIP = Settings::hostId2IpMap[dst->GetId()];

                    auto hostIp2SwitchIdIt = Settings::hostIp2SwitchId.find(dstIP);
                    NS_ASSERT_MSG(hostIp2SwitchIdIt != Settings::hostIp2SwitchId.end(),
                                  "Cannot find connected ToR set for destination host IP");

                    const std::set<uint32_t> &swDstIds = hostIp2SwitchIdIt->second;
                    NS_ASSERT_MSG(!swDstIds.empty(),
                                  "Destination host has no connected ToR");

                    /*
                     * A destination host may be connected to multiple ToRs.
                     * For each possible destination ToR, construct ToR-to-ToR paths.
                     */
                    for (uint32_t swDstId : swDstIds) {
                        if (swSrcId == swDstId) {
                            continue;  // same ToR, skip inter-ToR routing
                        }

                        bool insertedPath = false;

                        vector<Ptr<Node>> nexts1 = j->second;

                        for (auto next1 : nexts1) {
                            uint32_t outPort1 = nbr2if[nodeSrc][next1].idx;
                            auto nexts2 = nextHop[next1][dst];

                            /*
                             * 2-hop path:
                             *
                             *     srcToR -> next1 -> dstToR -> dstHost
                             *
                             * Original code required:
                             *
                             *     nexts2.size() == 1 && nexts2[0]->GetId() == swDstId
                             *
                             * This is not valid in dual-plane topologies, because
                             * nexts2 may contain multiple destination ToRs.
                             *
                             * New logic:
                             *
                             *     if nexts2 contains swDstId, then it is a valid path.
                             */
                            Ptr<Node> dstTor2 = FindNodeById(nexts2, swDstId);

                            if (dstTor2 != nullptr) {
                                uint32_t outPort2 = nbr2if[next1][dstTor2].idx;

                                uint64_t pathId = EncodeLetflowPathId({
                                    outPort1,
                                    outPort2
                                });

                                swSrc->m_mmu->m_letflowRouting
                                    .m_letflowRoutingTable[swDstId]
                                    .insert(pathId);

                                insertedPath = true;

                                continue;
                            }

                            for (auto next2 : nexts2) {
                                uint32_t outPort2 = nbr2if[next1][next2].idx;
                                auto nexts3 = nextHop[next2][dst];

                                /*
                                 * 3-hop path:
                                 *
                                 *     srcToR -> next1 -> next2 -> dstToR -> dstHost
                                 */
                                Ptr<Node> dstTor3 = FindNodeById(nexts3, swDstId);

                                if (dstTor3 != nullptr) {
                                    uint32_t outPort3 = nbr2if[next2][dstTor3].idx;

                                    uint64_t pathId = EncodeLetflowPathId({
                                        outPort1,
                                        outPort2,
                                        outPort3
                                    });

                                    swSrc->m_mmu->m_letflowRouting
                                        .m_letflowRoutingTable[swDstId]
                                        .insert(pathId);

                                    insertedPath = true;

                                    continue;
                                }

                                for (auto next3 : nexts3) {
                                    uint32_t outPort3 = nbr2if[next2][next3].idx;
                                    auto nexts4 = nextHop[next3][dst];

                                    /*
                                     * 4-hop path:
                                     *
                                     *     srcToR -> next1 -> next2 -> next3
                                     *            -> dstToR -> dstHost
                                     */
                                    Ptr<Node> dstTor4 = FindNodeById(nexts4, swDstId);

                                    if (dstTor4 != nullptr) {
                                        uint32_t outPort4 = nbr2if[next3][dstTor4].idx;

                                        uint64_t pathId = EncodeLetflowPathId({
                                            outPort1,
                                            outPort2,
                                            outPort3,
                                            outPort4
                                        });

                                        swSrc->m_mmu->m_letflowRouting
                                            .m_letflowRoutingTable[swDstId]
                                            .insert(pathId);

                                        insertedPath = true;

                                        continue;
                                    }

                                    for (auto next4 : nexts4) {
                                        uint32_t outPort4 = nbr2if[next3][next4].idx;
                                        auto nexts5 = nextHop[next4][dst];

                                        /*
                                         * 5-hop path:
                                         *
                                         *     srcToR -> next1 -> next2 -> next3 -> next4
                                         *            -> dstToR -> dstHost
                                         */
                                        Ptr<Node> dstTor5 = FindNodeById(nexts5, swDstId);

                                        if (dstTor5 != nullptr) {
                                            uint32_t outPort5 = nbr2if[next4][dstTor5].idx;

                                            uint64_t pathId = EncodeLetflowPathId({
                                                outPort1,
                                                outPort2,
                                                outPort3,
                                                outPort4,
                                                outPort5
                                            });

                                            swSrc->m_mmu->m_letflowRouting
                                                .m_letflowRoutingTable[swDstId]
                                                .insert(pathId);

                                            insertedPath = true;

                                            continue;
                                        }
                                    }
                                }
                            }
                        }

#ifdef SWITCH_INIT_INFO
                        if (!insertedPath) {
                            printf("[WARN:LETFLOW-INIT] No path inserted, maybe different plane: srcToR=%u, dstToR=%u, dstHost=%u, dstIP=%u\n",
                                   swSrcId, swDstId, dst->GetId(), dstIP);
                        }
#endif
                    }
                }
            }
        }
    }

    /*
     * Constant setup, and switchInfo
     */
    for (auto i = nextHop.begin(); i != nextHop.end(); i++) {  // every node
        if (i->first->GetNodeType() == 1) {
            Ptr<Node> node = i->first;
            Ptr<SwitchNode> sw = DynamicCast<SwitchNode>(node);  // switch
            NS_ASSERT_MSG(sw != nullptr, "Failed to cast node to SwitchNode");

#ifdef SWITCH_INIT_INFO
            printf("[INFO:SWITCH] Switch ID:%u, ToR:%d\n",
                   sw->GetId(), sw->m_isToR);
#endif

            if (lb_mode == 4) {
                sw->m_mmu->m_letflowRouting.SetConstants(letflow_agingTime,
                                                          letflow_flowletTimeout);
                sw->m_mmu->m_letflowRouting.SetSwitchInfo(sw->m_isToR,
                                                           sw->GetId());
            }
        }
    }
}

  for (uint32_t i = 0; i < node_num; i++) {
    if (n.Get(i)->GetNodeType() == 1) { 
      Ptr<SwitchNode> sw = DynamicCast<SwitchNode>(n.Get(i));
      sw->SetAttribute("SwHashType", UintegerValue(hash_type));
      sw->SetAttribute("LbMode", UintegerValue(lb_mode));
      sw->SetAttribute("CcMode", UintegerValue(cc_mode));
      sw->SetAttribute("MaxRtt", UintegerValue(maxRtt));
      sw->SetAttribute("TimeInterval", UintegerValue(sw_sample_time_interval));
      sw->SetAttribute("PacketDropRate", DoubleValue(sw_packetDropRate));
    }
  }

  NodeContainer trace_nodes;
  for (uint32_t i = 0; i < trace_num; i++) {
    uint32_t nid;
    tracef >> nid;
    if (nid >= n.GetN()) {
      continue;
    }
    trace_nodes = NodeContainer(trace_nodes, n.Get(nid));
  }

  FILE *trace_output = fopen(trace_output_file.c_str(), "w");
  if (enable_trace)
    qbb.EnableTracing(trace_output, trace_nodes);

  {
    SimSetting sim_setting;
    for (auto i : nbr2if) {
      for (auto j : i.second) {
        uint16_t node = i.first->GetId();
        uint8_t intf = j.second.idx;
        uint64_t bps =
            DynamicCast<QbbNetDevice>(i.first->GetDevice(j.second.idx))
                ->GetDataRate()
                .GetBitRate();
        sim_setting.port_speed[node][intf] = bps;
      }
    }
    sim_setting.win = maxBdp;
    sim_setting.Serialize(trace_output);
  }

  NS_LOG_INFO("Create Applications.");

  Time interPacketInterval = Seconds(0.0000005 / 2);
  for (uint32_t i = 0; i < node_num; i++) {
    if (n.Get(i)->GetNodeType() == 0 || n.Get(i)->GetNodeType() == 2)
      for (uint32_t j = 0; j < node_num; j++) {
        if (n.Get(j)->GetNodeType() == 0 || n.Get(j)->GetNodeType() == 2)
          portNumber[i][j] = 10000; 
      }
  }
  flow_input.idx = 0;

  topof.close();
  tracef.close();
  switch_failuref.close();

  if (link_down_time > 0) {
    Simulator::Schedule(MicroSeconds(sim_start) + MicroSeconds(link_down_time),
                        &TakeDownLink, n, n.Get(link_down_A),
                        n.Get(link_down_B));
    printf("[Link_Down][%ld] Schedule DownLink between %u and %u at time %lu seconds\n", Simulator::Now().GetTimeStep(), link_down_A, link_down_B, 2 * 1000000000 + link_down_time * 1000);                  
  }
}
#endif
