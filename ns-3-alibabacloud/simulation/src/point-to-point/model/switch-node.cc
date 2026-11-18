#include "ns3/ipv4.h"
#include "ns3/packet.h"
#include "ns3/ipv4-header.h"
#include "ns3/pause-header.h"
#include "ns3/flow-id-tag.h"
#include "ns3/boolean.h"
#include "ns3/uinteger.h"
#include "ns3/double.h"
#include "switch-node.h"
#include "qbb-net-device.h"
#include "ppp-header.h"
#include "ns3/int-header.h"
#include "ns3/simulator.h"
#include <cmath>
#include <random>
#include "point-to-point-utils.h"
#include "ns3/letflow-routing.h"
#include "assert.h"
#include "switch-hash.h"
#include "flow-type-tag.h"
#include "flow-info-tag.h"
#include "flow-custom-header-tag.h"
// #define TRACE (((ch.sip >> 8) & 0xffff) == SRC && ((ch.dip >> 8) & 0xffff) == DST) || (((ch.sip >> 8) & 0xffff) == DST && ((ch.dip >> 8) & 0xffff) == SRC)
#define TRACE (((ch.sip >> 8) & 0xffff) == SRC && ((ch.dip >> 8) & 0xffff) == DST)

namespace ns3 {

TypeId SwitchNode::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::SwitchNode")
    .SetParent<Node> ()
    .AddConstructor<SwitchNode> ()
	.AddAttribute("EcnEnabled",
			"Enable ECN marking.",
			BooleanValue(false),
			MakeBooleanAccessor(&SwitchNode::m_ecnEnabled),
			MakeBooleanChecker())
	.AddAttribute("LbMode",
			"LB mode.",
			UintegerValue(0),
			MakeUintegerAccessor(&SwitchNode::m_lbMode),
			MakeUintegerChecker<uint32_t>())	
	.AddAttribute("SwHashType",
			"Switch Hash Type.",
			UintegerValue(0),
			MakeUintegerAccessor(&SwitchNode::m_hashType),
			MakeUintegerChecker<uint32_t>())							
	.AddAttribute("CcMode",
			"CC mode.",
			UintegerValue(0),
			MakeUintegerAccessor(&SwitchNode::m_ccMode),
			MakeUintegerChecker<uint32_t>())
	.AddAttribute("AckHighPrio",
			"Set high priority for ACK/NACK or not",
			UintegerValue(0),
			MakeUintegerAccessor(&SwitchNode::m_ackHighPrio),
			MakeUintegerChecker<uint32_t>())
	.AddAttribute("MaxRtt",
			"Max Rtt of the network",
			UintegerValue(9000),
			MakeUintegerAccessor(&SwitchNode::m_maxRtt),
			MakeUintegerChecker<uint32_t>())
	.AddTraceSource("SwitchForward",
			"Trace the forwarding of packets",
			MakeTraceSourceAccessor(&SwitchNode::m_traceFoward),
			"ns3::SwitchNode::SwitchForward")
	.AddAttribute("TimeInterval",
			"Sample interval of txBytes",
			UintegerValue(1000),
			MakeUintegerAccessor(&SwitchNode::TIME_INTERVAL),
			MakeUintegerChecker<uint64_t>())
	.AddAttribute("PacketDropRate",
			"Switch Packet Drop Rate on dstToR",
			DoubleValue(0.0),
			MakeDoubleAccessor(&SwitchNode::m_packetDropRate),
			MakeDoubleChecker<double>())
  ;
  return tid;
}
SwitchNode::SwitchNode(){
	m_ecmpSeed = m_id;
	m_node_type = 1;
	m_mmu = CreateObject<SwitchMmu>();
	m_isToR = false;
	// switch pkt drop
    m_dropRandomVariable = CreateObject<UniformRandomVariable>();	

	for (uint32_t i = 0; i < pCnt; i++)
		for (uint32_t j = 0; j < pCnt; j++)
			for (uint32_t k = 0; k < qCnt; k++)
				m_bytes[i][j][k] = 0;
	for (uint32_t i = 0; i < pCnt; i++){
		m_txBytes[i] = 0;	
		m_last_txBytes[i] = 0;
		m_dt_txBytes[i] = 0;
		m_last_sample_TS[i] = 0;
		m_sample_time_interval[i] = 1000;
	}
	for (uint32_t i = 0; i < pCnt; i++)
		m_lastPktSize[i] = m_lastPktTs[i] = 0;
	for (uint32_t i = 0; i < pCnt; i++)
		m_u[i] = 0;
	for (uint32_t i = 0; i < pCnt; i++){
		last_txBytes[i] = 0;
		last_port_qlen[i] = 0;
		last_bw[i] = 0;
	}
	
	// for monitor
	for (uint32_t i = 1; i <= 8; i++){
		for (uint32_t j = 0; j < 4; j++)
		select_port[j][i] = 0;
	}
	mon_timer = 0;

	// RPS initial
	unsigned int rps_seed = 0xb214 + this->GetId();
	std::mt19937 gen(rps_seed);
	std::uniform_int_distribution<size_t> dist(0, 256);
	m_iterator = dist(gen);
	m_SwitchFailedPktDropCnt = 0;
}
// switch pkt drop
void
SwitchNode::SetPacketDropRate(double dropRate)
{
    NS_ASSERT_MSG(dropRate >= 0.0 && dropRate <= 1.0,
                  "Packet drop rate must be in [0, 1]");

    m_packetDropRate = dropRate;
}

void
SwitchNode::AddDownlinkPort(uint32_t port)
{
    m_downlinkPorts.insert(port);
}

bool
SwitchNode::IsDownlinkPort(uint32_t port) const
{
    return m_downlinkPorts.find(port) != m_downlinkPorts.end();
}
// letflow
bool SwitchNode::IsTorSwitch()
{
    if (m_isTorCached) {
        return m_isTor;
    }

    m_isTor = false;

    for (uint32_t i = 0; i < GetNDevices(); ++i) {
        Ptr<NetDevice> dev = GetDevice(i);
        if (dev == 0) {
            continue;
        }

        Ptr<Channel> ch = dev->GetChannel();
        if (ch == 0) {
            continue;
        }

        for (uint32_t j = 0; j < ch->GetNDevices(); ++j) {
            Ptr<NetDevice> peerDev = ch->GetDevice(j);
            if (peerDev == 0) {
                continue;
            }

            Ptr<Node> peerNode = peerDev->GetNode();
            if (peerNode == 0 || peerNode == this) {
                continue;
            }
            // Ptr<SwitchNode> peerSwitch = DynamicCast<SwitchNode>(peerNode);

            // 只要邻居不是 SwitchNode，就说明当前交换机直连 Host/Server
            if (peerNode->GetNodeType() == 0) {
				// printf("Node %u is a ToR switch, directly connected to host %u\n", GetId(), peerNode->GetId());
                m_isTor = true;
                m_isTorCached = true;
                return true;
            }
        }
    }

    m_isTorCached = true;
    return false;
}
uint32_t SwitchNode::DoHash(const uint8_t *key, size_t len, uint32_t seed, uint32_t nexthop_size){
	uint32_t idx = 0;
	switch (m_hashType) {
		case 0:
			idx = EcmpHash(key, len, seed) % nexthop_size; break; // MurmurHash3
		case 1:
			idx = Crc32Hash(key, len) % nexthop_size; break; // CRC32 hash
		case 2:
			idx = JenkinsHash(key, len) % nexthop_size; break; // Jenkins hash
		case 3:
			idx = SymHash(key, len, IsTorSwitch() ? 0x243f6a88u : 0x85a308d3u) % nexthop_size; break; // SymHash
		default:
			printf("[ERROR]: Unsupported hash type %u\n", m_hashType);
			assert(false);
	}
	return idx;
}
// Load Balancing: 0-ECMP, 1-APS, 2-RPS, 3-FlowBender, 4-LetFlow
/* 0: ECMP */
uint32_t SwitchNode::DoLbECMP(Ptr<const Packet> p, CustomHeader &ch, const std::vector<int> &nexthops){
	
	union {
		uint8_t u8[4+4+2+2];
		uint32_t u32[3];
	} buf;
	buf.u32[0] = ch.sip;
	buf.u32[1] = ch.dip;
	if (ch.l3Prot == 0x6)
		buf.u32[2] = ch.tcp.sport | ((uint32_t)ch.tcp.dport << 16);
	else if (ch.l3Prot == 0x11)
		buf.u32[2] = ch.udp.sport | ((uint32_t)ch.udp.dport << 16);
	else if (ch.l3Prot == 0xFC || ch.l3Prot == 0xFD)
		buf.u32[2] = ch.ack.sport | ((uint32_t)ch.ack.dport << 16);

	return DoHash(buf.u8, 12, m_ecmpSeed, nexthops.size());
}
/* 1: APS */
uint32_t SwitchNode::DoLbAPS(Ptr<const Packet> p, CustomHeader &ch, const std::vector<int> &nexthops){
	uint32_t idx = 0;
	// APS: first hop, second hop port selection is directed by sender
	#ifdef APS_OLD
	if (ch.l3Prot == 0x11) { // udp packet
		bool isFirstHop = ch.udp.ih.nhop == 0 ? true : false; // the first hop
		bool isSecondHop = ch.udp.ih.nhop == 1 ? true : false; // the second hop
		if (isFirstHop) idx = ch.udp.ih.hop[0].GetPathId() % nexthops.size(); // use the ToR interface index in INT header to select the next hop
		else if (isSecondHop) idx = ch.udp.ih.hop[1].GetPathId() % nexthops.size(); // use the Agg interface index in INT header to select the next hop
		else idx = DoLbECMP(p, ch, nexthops);
	}
	#elif defined(APS_V2)
	uint32_t ev = 0;
	if (ch.l3Prot == 0x11) { // udp packet
		ev = ch.udp.ih.hop[0].GetPathId();
		#ifdef SWITCH_OPORT_LOG
	
		if(TRACE)
			if(m_id == SRC_SW || m_id == SRC_AGG_SW) printf("[LOG:SWITCH_OPORT][%ld][%u] Udp pkt seq %u hash, ev %u\n", Simulator::Now().GetTimeStep(), m_id, ch.udp.seq, ev);
		#endif		
	} else if (ch.l3Prot == 0xFC || ch.l3Prot == 0xFD) {
		ev = ch.ack.ih.hop[0].GetPathId();
		#ifdef SWITCH_OPORT_LOG
		FlowCustomHeaderTag fcht;
		NS_ASSERT(p->PeekPacketTag(fcht));			
		if(TRACE)
			if(m_id == DST_SW) printf("[LOG:SWITCH_OPORT][%ld][%u] Control pkt seq %u, ePSN %u hash, ev %u\n", Simulator::Now().GetTimeStep(), m_id, fcht.GetPsn(), ch.ack.seq, ev);
		#endif
	}
		
		union {
			uint8_t u8[4+4+2+2];
			uint32_t u32[3];
		} buf;
		buf.u32[0] = ch.sip;
		buf.u32[1] = ch.dip;
		if (ch.l3Prot == 0x6)
			buf.u32[2] = ch.tcp.sport | ((uint32_t)ch.tcp.dport << 16);
		else if (ch.l3Prot == 0x11)
			buf.u32[2] = ev | ((uint32_t)ch.udp.dport << 16); // udp packet using REPS
		else if (ch.l3Prot == 0xFC || ch.l3Prot == 0xFD)
			buf.u32[2] = ch.ack.sport | ((uint32_t)ev << 16);

		idx = DoHash(buf.u8, 12, m_ecmpSeed, nexthops.size()); // hash
	#endif
	// else idx = DoLbECMP(p, ch, nexthops); // 包都已经是乱序到达了，ACK乱不乱有意义吗
	return idx;
}
/* 2: RPS */
uint32_t SwitchNode::DoLbRPS(Ptr<const Packet> p, CustomHeader &ch, const std::vector<int> &nexthops){
	uint32_t idx = 0;
	// Randomly select a next hop, fix the seed for bug

	// static int iterator = 0;
	idx = m_iterator % nexthops.size();
	m_iterator += 1 % nexthops.size();
	return idx;
}
/* 3: FlowBender */
uint32_t SwitchNode::DoLbFlowBender(Ptr<const Packet> p, CustomHeader &ch, const std::vector<int> &nexthops){
	uint32_t idx = 0;

	union {
		uint8_t u8[4+4+2+2];
		uint32_t u32[3];
	} buf;
	buf.u32[0] = ch.sip;
	buf.u32[1] = ch.dip;
	if (ch.l3Prot == 0x6)
		buf.u32[2] = ch.tcp.sport | ((uint32_t)ch.tcp.dport << 16);
	else if (ch.l3Prot == 0x11)
		buf.u32[2] = ch.udp.sport | ((uint32_t)ch.udp.dport << 16);
	else if (ch.l3Prot == 0xFC || ch.l3Prot == 0xFD)
		buf.u32[2] = ch.ack.sport | ((uint32_t)ch.ack.dport << 16);

	PppHeader ppp;
	Ipv4Header head;
	Ptr<Packet> p2 = p->Copy();
	p2->RemoveHeader(ppp);
	p2->PeekHeader(head);
	idx = FlowBenderHash(buf.u8, 12, m_ecmpSeed, head.GetTtl()) % nexthops.size(); // FlowBender hash
	return idx;
}
/* 4: LetFlow */
uint32_t SwitchNode::DoLbLetFlow(Ptr<Packet> p, CustomHeader &ch, const std::vector<int> &nexthops){
	uint32_t idx = 0;
    if (m_isToR && nexthops.size() == 1) {
        if (m_isToR_hostIP.find(ch.sip) != m_isToR_hostIP.end() &&
            m_isToR_hostIP.find(ch.dip) != m_isToR_hostIP.end()) {
            return nexthops[0];  // intra-pod traffic, return the first interface
        }
    }

    /* ONLY called for inter-Pod traffic */
    idx = m_mmu->m_letflowRouting.RouteInput(p, ch);
    if (idx == LETFLOW_NULL) {
        assert(nexthops.size() == 1);  // Receiver's TOR has only one interface to receiver-server
        idx = nexthops[0];         // has only one option, return the first interface
    }
    assert(std::find(nexthops.begin(), nexthops.end(), idx) !=
           nexthops.end());  // Result of Letflow cannot be found in nexthops
	m_traceFoward(idx, ch);

	/* switch pkt drop */
	if (IsDownlinkPort(idx))
	{
		// Only inject loss to data packets.
		if (ch.l3Prot == 0x11)
		{
			double randValue = m_dropRandomVariable->GetValue(0.0, 1.0);

			if (randValue < m_packetDropRate)
			{
				return -1;
			}
		}
	}	
    return idx;
}
/* 5: REPS */
uint32_t SwitchNode::DoLbReps(Ptr<const Packet> p, CustomHeader &ch, const std::vector<int> &nexthops){
	uint32_t idx = 0;

	// get EV from tag
	FlowInfoTag fit;
	p->PeekPacketTag(fit);
	uint32_t ev = fit.GetFlowInfo();	

	union {
		uint8_t u8[4+4+2+2];
		uint32_t u32[3];
	} buf;
	buf.u32[0] = ch.sip;
	buf.u32[1] = ch.dip;
	if (ch.l3Prot == 0x6)
		buf.u32[2] = ch.tcp.sport | ((uint32_t)ch.tcp.dport << 16);
	else if (ch.l3Prot == 0x11)
		buf.u32[2] = ev | ((uint32_t)ch.udp.dport << 16); // udp packet using REPS
	else if (ch.l3Prot == 0xFC || ch.l3Prot == 0xFD)
		buf.u32[2] = ch.ack.sport | ((uint32_t)ev << 16);


	idx = DoHash(buf.u8, 12, m_ecmpSeed, nexthops.size()); // ECMP hash
	return idx;
}
/* Legacy IOPS hash helper (mode 6 is now PSN-PATH and uses DoLbECMP). */
uint32_t SwitchNode::DoLbIops(Ptr<const Packet> p, CustomHeader &ch, const std::vector<int> &nexthops){
	uint32_t idx = 0;

	// get EV from tag
	FlowInfoTag fit;
	p->PeekPacketTag(fit);
	uint32_t ev = fit.GetFlowInfo();	

	union {
		uint8_t u8[4+4+2+2];
		uint32_t u32[3];
	} buf;
	buf.u32[0] = ch.sip;
	buf.u32[1] = ch.dip;
	if (ch.l3Prot == 0x6)
		buf.u32[2] = ch.tcp.sport | ((uint32_t)ch.tcp.dport << 16);
	else if (ch.l3Prot == 0x11)
		buf.u32[2] = ev | ((uint32_t)ch.udp.dport << 16); // udp packet using IOPS
	else if (ch.l3Prot == 0xFC || ch.l3Prot == 0xFD)
		buf.u32[2] = ev | ((uint32_t)ch.ack.dport << 16);

	idx = DoHash(buf.u8, 12, m_ecmpSeed, nexthops.size()); // hash
	return idx;
}
uint32_t ip_to_node_id_switch(Ipv4Address ip) { return (ip.Get() >> 8) & 0xffff; }
int SwitchNode::GetOutDev(Ptr<Packet> p, CustomHeader &ch){
	if (m_failed) return -1; // if the switch is failed, drop all packets

	// look up entries
	auto entry = m_rtTable.find(ch.dip);

	// no matching entry
	if (entry == m_rtTable.end())
		return -1;

	// entry found
	const auto &nexthops = entry->second; // auto &nexthops = entry->second; 

	// pick one next hop based LB mode
	#ifdef SWITCH_DROP_DEBUG
		#ifdef SIWTCH_DROP_TRACE_DEBUG
		if (ch.udp.seq == 5000 && ip_to_node_id_switch(Ipv4Address(ch.sip)) == 46 && ch.udp.sport == 10004) 
			printf("[DEBUG:SWITCH_DROP][%ld][%u]\tTracing pkt %u (SDSD) %u %u %u %u\n", 
				Simulator::Now().GetTimeStep(), this->m_id, ch.udp.seq, ip_to_node_id_switch(Ipv4Address(ch.sip)), ip_to_node_id_switch(Ipv4Address(ch.dip)), 
					ch.udp.sport, ch.udp.dport);
		#endif
					
		if(config_test && this->m_id == 203 && ch.l3Prot != 0xFC && ch.l3Prot != 0xFD && (ch.udp.seq == 2000 && ip_to_node_id_switch(Ipv4Address(ch.sip)) == 46 && ch.udp.sport == 10004))
		{
			if(ch.udp.seq == 2000) config_test = false;
			printf("[DEBUG:SWITCH_DROP][%ld][%u]\tSwitch Drop Pkg %u (SDSD) %u %u %u %u\n", 
				Simulator::Now().GetTimeStep(), this->m_id, ch.udp.seq, ip_to_node_id_switch(Ipv4Address(ch.sip)), ip_to_node_id_switch(Ipv4Address(ch.dip)), 
					ch.udp.sport, ch.udp.dport);
			return -1;
		}
	#endif
	

	uint32_t idx = 0;
	FlowTypeTag ftt;
	p->PeekPacketTag(ftt);
	uint32_t flow_lbMode = ftt.GetFlowType();

    bool control_pkt = (ch.l3Prot == 0xFF || ch.l3Prot == 0xFE);
    if (flow_lbMode == 0 || control_pkt) {  // control packet (ACK, NACK, PFC, QCN)
        idx = DoLbECMP(p, ch, nexthops);     // ECMP routing path decision (4-tuple)
    } else {
		switch (flow_lbMode) {
			case 1:
				idx = DoLbAPS(p, ch, nexthops); break;
			case 2:
				idx = DoLbRPS(p, ch, nexthops); break;
				//idx = DoLbReps(p, ch, nexthops); break;
			case 3:
				idx = DoLbFlowBender(p, ch, nexthops); break;
			case 4:
				if (ch.l3Prot != 0x11) {
					idx = DoLbECMP(p, ch, nexthops); // LetFlow is only for UDP packets, other packets use ECMP
					break;					
				} else{
        			return DoLbLetFlow(p, ch, nexthops);
				}
			case 5:
				idx = DoLbReps(p, ch, nexthops); break;
			case 6:
				// PSN-PATH selects a physical path by changing the UDP source
				// port; switches only need their normal ECMP hash.
				idx = DoLbECMP(p, ch, nexthops); break;
			default:
				printf("[ERROR]: Unknown load balancing mode %u\n", flow_lbMode);
				assert(false);
		}
	}


	int outPort = nexthops[idx];
	/* switch pkt drop module */
	if (IsDownlinkPort(outPort))
	{
		// Only inject loss to data packets.
		if (ch.l3Prot == 0x11)
		{
			double randValue = m_dropRandomVariable->GetValue(0.0, 1.0);
			if (randValue < m_packetDropRate)
			{
				#ifdef SWITCH_DROP_LOG
					if (TRACE){
						printf("[SW_DROP_LOG][%ld] pkt random drop happended(drop rate:%.3f %), dst:0\n", Simulator::Now().GetTimeStep(), m_packetDropRate * 100);
					}
				#endif
				return -1;
			}
		}
	}

	m_traceFoward(outPort, ch);

	#ifdef SWITCH_OPORT_LOG
		
		// ToR Switch udp packet
		if(TRACE){
			if ((ch.l3Prot == 0x11) && (m_id == SRC_SW || m_id == SRC_AGG_SW)) printf("[LOG:SWITCH_OPORT][%ld]\tSwitchNode:%d udp seq %u select outport %u\n", Simulator::Now().GetTimeStep(), this->m_id, ch.udp.seq, outPort);
			else if ((ch.l3Prot == 0xFC || ch.l3Prot == 0xFD) && (m_id == SRC_SW || m_id == SRC_AGG_SW)) {
				FlowCustomHeaderTag fcht;
				NS_ASSERT(p->PeekPacketTag(fcht));	
				printf("[LOG:SWITCH_OPORT][%ld]\tSwitchNode:%d control seq %u, ePSN %u, selcet outport %u\n", Simulator::Now().GetTimeStep(), this->m_id, fcht.GetPsn(), ch.udp.seq, outPort);
			}

		}
	#endif

	#ifdef SWITCH_PORT_SELECT
	if (!control_pkt && m_id == SRC_SW && ((ip_to_node_id_switch(Ipv4Address(ch.sip))) == 0 || (ip_to_node_id_switch(Ipv4Address(ch.sip))) == 1 || (ip_to_node_id_switch(Ipv4Address(ch.sip))) == 2 || (ip_to_node_id_switch(Ipv4Address(ch.sip))) == 3)) {
		select_port[ip_to_node_id_switch(Ipv4Address(ch.sip))][outPort] += 1;
		FlowInfoTag fit;
		p->PeekPacketTag(fit);
		p->RemovePacketTag(fit);
		fit.SetSwitchPort(outPort);
		p->AddPacketTag(fit);
		if (Simulator::Now().GetTimeStep() > mon_timer) {
			for (uint32_t j = 0; j < 4; j++){
				printf("[%ld] Node %u:\n", Simulator::Now().GetTimeStep(), j);
				for (uint32_t i = 5; i <= 8; i++)
					printf(" p(%u): %u", i, select_port[j][i]);
				printf("\n");
			}	
			printf("\n");	
			mon_timer = Simulator::Now().GetTimeStep() + MicroSeconds(50).GetTimeStep();
		}


	}
	#endif
	return outPort;
}

void SwitchNode::SetSwitchFailed(){
	m_failed = 1;
	printf("[Switch_Failed][%ld] Switch %u FAILED\n", Simulator::Now().GetTimeStep(), m_id);
}
void SwitchNode::SetSwitchUp(){
	m_failed = 0;
	printf("[Switch_Failed][%ld] Switch %u UP\n", Simulator::Now().GetTimeStep(), m_id);
}

void SwitchNode::SwitchDropPacket(){
	m_SwitchFailedPktDropCnt++;
}

void SwitchNode::CheckAndSendPfc(uint32_t inDev, uint32_t qIndex){
	Ptr<QbbNetDevice> device = DynamicCast<QbbNetDevice>(m_devices[inDev]);
	if (m_mmu->CheckShouldPause(inDev, qIndex)){
		device->SendPfc(qIndex, 0);
		m_mmu->SetPause(inDev, qIndex);

	}
}
void SwitchNode::CheckAndSendResume(uint32_t inDev, uint32_t qIndex){
	Ptr<QbbNetDevice> device = DynamicCast<QbbNetDevice>(m_devices[inDev]);
	if (m_mmu->CheckShouldResume(inDev, qIndex)){
		device->SendPfc(qIndex, 1);
		m_mmu->SetResume(inDev, qIndex);
	}
}

void SwitchNode::SendToDev(Ptr<Packet>p, CustomHeader &ch){
	int idx = GetOutDev(p, ch);
	if (idx >= 0){
		NS_ASSERT_MSG(m_devices[idx]->IsLinkUp(), "The routing table look up should return link that is up");

		// determine the qIndex
		uint32_t qIndex;
		if (ch.l3Prot == 0xFF || ch.l3Prot == 0xFE || (m_ackHighPrio && (ch.l3Prot == 0xFD || ch.l3Prot == 0xFC))){  //QCN or PFC or NACK, go highest priority
			qIndex = 0;
		}else{
			qIndex = (ch.l3Prot == 0x06 ? 1 : ch.udp.pg); // if TCP, put to queue 1
		}
		// std::cout << "qIndex is: " << qIndex << std::endl;

		// admission control
		FlowIdTag t;
		p->PeekPacketTag(t);
		uint32_t inDev = t.GetFlowId();
		if (qIndex != 0){ //not highest priority
			if (m_mmu->CheckIngressAdmission(inDev, qIndex, p->GetSize()) && m_mmu->CheckEgressAdmission(idx, qIndex, p->GetSize())){			// Admission control
				m_mmu->UpdateIngressAdmission(inDev, qIndex, p->GetSize());
				m_mmu->UpdateEgressAdmission(idx, qIndex, p->GetSize());
			}else{

				return; // Drop
			}
			CheckAndSendPfc(inDev, qIndex);
		}
		m_bytes[inDev][idx][qIndex] += p->GetSize();
		// #ifdef HASH_EGRESSPORT_OBSERVATION
		// m_txBytes[idx] += p->GetSize();
		// packetCountMap[std::make_tuple(idx, ch.sip, ch.dip, ch.udp.sport, ch.udp.dport)] += p->GetSize();
		// #endif
		m_devices[idx]->SwitchSend(qIndex, p, ch);
	}else
	{
		SwitchDropPacket(); // statistics
		return; // Drop
	}
}

uint32_t SwitchNode::EcmpHash(const uint8_t* key, size_t len, uint32_t seed) {
	
  return MurmurHash3(key, len, seed);
}
void SwitchNode::SetEcmpSeed(uint32_t seed){
	m_ecmpSeed = seed;
}

void SwitchNode::AddTableEntry(Ipv4Address &dstAddr, uint32_t intf_idx){
	uint32_t dip = dstAddr.Get();
	m_rtTable[dip].push_back(intf_idx);
}

void SwitchNode::ClearTable(){
	m_rtTable.clear();
}

// This function can only be called in switch mode
bool SwitchNode::SwitchReceiveFromDevice(Ptr<NetDevice> device, Ptr<Packet> packet, CustomHeader &ch){
	SendToDev(packet, ch);
	return true;
}

void SwitchNode::SwitchNotifyDequeue(uint32_t ifIndex, uint32_t qIndex, Ptr<Packet> p){
	FlowIdTag t;
	p->PeekPacketTag(t);
	if (qIndex != 0){
		uint32_t inDev = t.GetFlowId();
		m_mmu->RemoveFromIngressAdmission(inDev, qIndex, p->GetSize());
		m_mmu->RemoveFromEgressAdmission(ifIndex, qIndex, p->GetSize());
		m_bytes[inDev][ifIndex][qIndex] -= p->GetSize();
		if (m_ecnEnabled){
			bool egressCongested = m_mmu->ShouldSendCN(ifIndex, qIndex);
			#ifdef SWITCH_ECN_DEBUG
				static uint64_t timeTh = 500;
				if (Simulator::Now().GetTimeStep() > timeTh) {
					egressCongested = true;
					timeTh += 500;
				}	
			#endif
			if (egressCongested){
				PppHeader ppp;
				Ipv4Header h;
				p->RemoveHeader(ppp);
				p->RemoveHeader(h);
				h.SetEcn((Ipv4Header::EcnType)0x03);
				p->AddHeader(h);
				p->AddHeader(ppp);
				#ifdef SWITCH_ECN_LOG
				if (m_id == SRC_SW)
					printf("[LOG:SWITCH_ECN][%ld]\t SwitchNode:%d\tMark ECN\n", Simulator::Now().GetTimeStep(), this->m_id);
				#endif 
			}
		}
		//CheckAndSendPfc(inDev, qIndex);
		CheckAndSendResume(inDev, qIndex);
	}
	if (1){
		uint8_t* buf = p->GetBuffer();
		FlowTypeTag ftt;
		p->PeekPacketTag(ftt);
		uint32_t flow_lbMode = ftt.GetFlowType();		
		if (buf[PppHeader::GetStaticSize() + 9] == 0x11){ // udp packet
			IntHeader *ih = (IntHeader*)&buf[PppHeader::GetStaticSize() + 20 + 8 + 10]; // ppp, ip, udp, SeqTs
			Ptr<QbbNetDevice> dev = DynamicCast<QbbNetDevice>(m_devices[ifIndex]);
			if (m_ccMode == 3 || flow_lbMode == 1){ // HPCC or APS encapsulate IntHop
				if (flow_lbMode == 1) { // APS
					#ifdef APS_OLD
					if (ih->nhop == 0 || ih->nhop == 1) {// the first/second hop
						// look up entries
						CustomHeader ch(CustomHeader::L2_Header | CustomHeader::L3_Header);
						p->PeekHeader(ch);

						uint32_t dip = ch.dip;

						auto entry = m_rtTable.find(dip);
						// no matching entry
						if (entry == m_rtTable.end()) {
							printf("INT Error: no routing entry found for dst %d \n ", dip);
							return;
						}
						uint32_t ifCnt = entry->second.size();

						ih->PushHop((uint32_t)(ifCnt), Simulator::Now().GetTimeStep(), m_txBytes[ifIndex], dev->GetQueue()->GetNBytesTotal(), dev->GetDataRate().GetBitRate());
					}
					else ih->PushHop(m_id, Simulator::Now().GetTimeStep(), m_txBytes[ifIndex], dev->GetQueue()->GetNBytesTotal(), dev->GetDataRate().GetBitRate());
					#elif defined(APS_V2)
						ih->PushHop(m_id, m_sample_time_interval[ifIndex],
							m_dt_txBytes[ifIndex], dev->GetQueue()->GetNBytesTotal(), dev->GetDataRate().GetBitRate());
					#endif
				}
				else ih->PushHop(Simulator::Now().GetTimeStep(), m_txBytes[ifIndex], dev->GetQueue()->GetNBytesTotal(), dev->GetDataRate().GetBitRate());
			}else if (m_ccMode == 10){ // HPCC-PINT
				uint64_t t = Simulator::Now().GetTimeStep();
				uint64_t dt = t - m_lastPktTs[ifIndex];
				if (dt > m_maxRtt)
					dt = m_maxRtt;
				uint64_t B = dev->GetDataRate().GetBitRate() / 8; //Bps
				uint64_t qlen = dev->GetQueue()->GetNBytesTotal();
				double newU;

				/**************************
				 * approximate calc
				 *************************/
				int b = 20, m = 16, l = 20; // see log2apprx's paremeters
				int sft = logres_shift(b,l);
				double fct = 1<<sft; // (multiplication factor corresponding to sft)
				double log_T = log2(m_maxRtt)*fct; // log2(T)*fct
				double log_B = log2(B)*fct; // log2(B)*fct
				double log_1e9 = log2(1e9)*fct; // log2(1e9)*fct
				double qterm = 0;
				double byteTerm = 0;
				double uTerm = 0;
				if ((qlen >> 8) > 0){
					int log_dt = log2apprx(dt, b, m, l); // ~log2(dt)*fct
					int log_qlen = log2apprx(qlen >> 8, b, m, l); // ~log2(qlen / 256)*fct
					qterm = pow(2, (
								log_dt + log_qlen + log_1e9 - log_B - 2*log_T
								)/fct
							) * 256;
					// 2^((log2(dt)*fct+log2(qlen/256)*fct+log2(1e9)*fct-log2(B)*fct-2*log2(T)*fct)/fct)*256 ~= dt*qlen*1e9/(B*T^2)
				}
				if (m_lastPktSize[ifIndex] > 0){
					int byte = m_lastPktSize[ifIndex];
					int log_byte = log2apprx(byte, b, m, l);
					byteTerm = pow(2, (
								log_byte + log_1e9 - log_B - log_T
								)/fct
							);
					// 2^((log2(byte)*fct+log2(1e9)*fct-log2(B)*fct-log2(T)*fct)/fct) ~= byte*1e9 / (B*T)
				}
				if (m_maxRtt > dt && m_u[ifIndex] > 0){
					int log_T_dt = log2apprx(m_maxRtt - dt, b, m, l); // ~log2(T-dt)*fct
					int log_u = log2apprx(int(round(m_u[ifIndex] * 8192)), b, m, l); // ~log2(u*512)*fct
					uTerm = pow(2, (
								log_T_dt + log_u - log_T
								)/fct
							) / 8192;
					// 2^((log2(T-dt)*fct+log2(u*512)*fct-log2(T)*fct)/fct)/512 = (T-dt)*u/T
				}
				newU = qterm+byteTerm+uTerm;

				#if 0
				/**************************
				 * accurate calc
				 *************************/
				double weight_ewma = double(dt) / m_maxRtt;
				double u;
				if (m_lastPktSize[ifIndex] == 0)
					u = 0;
				else{
					double txRate = m_lastPktSize[ifIndex] / double(dt); // B/ns
					u = (qlen / m_maxRtt + txRate) * 1e9 / B;
				}
				newU = m_u[ifIndex] * (1 - weight_ewma) + u * weight_ewma;
				printf(" %lf\n", newU);
				#endif

				/************************
				 * update PINT header
				 ***********************/
				uint16_t power = Pint::encode_u(newU);
				if (power > ih->GetPower())
					ih->SetPower(power);

				m_u[ifIndex] = newU;
			}
		}
	}
	if(DynamicCast<QbbNetDevice>(m_devices[ifIndex])->m_linkFailed) m_txBytes[ifIndex] += 0;
	else
	m_txBytes[ifIndex] += p->GetSize();
	#ifdef APS_V2
	if (m_last_sample_TS[ifIndex] == 0){
		m_last_sample_TS[ifIndex] = Simulator::Now().GetTimeStep();
		m_last_txBytes[ifIndex] = m_txBytes[ifIndex];
	} else if (Simulator::Now().GetTimeStep() - m_last_sample_TS[ifIndex] >= TIME_INTERVAL){
		// get delta time and txBytes
		m_sample_time_interval[ifIndex] = Simulator::Now().GetTimeStep() - m_last_sample_TS[ifIndex];
		m_dt_txBytes[ifIndex] = m_txBytes[ifIndex] - m_last_txBytes[ifIndex];

		m_last_sample_TS[ifIndex] = Simulator::Now().GetTimeStep();
		m_last_txBytes[ifIndex] = m_txBytes[ifIndex];
	}
	#endif
	#ifdef HASH_EGRESSPORT_OBSERVATION
	CustomHeader ch(CustomHeader::L2_Header | CustomHeader::L3_Header | CustomHeader::L4_Header);
	ch.getInt = 1; // parse INT header
	p->PeekHeader(ch);
	packetCountMap[std::make_tuple(ifIndex, ch.sip, ch.dip, ch.udp.sport, ch.udp.dport)] += p->GetSize();
	#endif
	m_lastPktSize[ifIndex] = p->GetSize();
	m_lastPktTs[ifIndex] = Simulator::Now().GetTimeStep();
}

int SwitchNode::logres_shift(int b, int l){
	static int data[] = {0,0,1,2,2,3,3,3,3,4,4,4,4,4,4,4,4,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5};
	return l - data[b];
}

int SwitchNode::log2apprx(int x, int b, int m, int l){
	int x0 = x;
	int msb = int(log2(x)) + 1;
	if (msb > m){
		x = (x >> (msb - m) << (msb - m));
		#if 0
		x += + (1 << (msb - m - 1));
		#else
		int mask = (1 << (msb-m)) - 1;
		if ((x0 & mask) > (rand() & mask))
			x += 1<<(msb-m);
		#endif
	}
	return int(log2(x) * (1<<logres_shift(b, l)));
}

// for monitor
/**
 * outoput format:
 * time, sw_id, port_id, q_id, qlen, port_len
*/
void SwitchNode::PrintSwitchQlen(FILE* qlen_output){
	uint32_t n_dev = this->GetNDevices();
	for(uint32_t i = 1; i < n_dev; ++i){
		uint64_t port_len = 0;
		for(uint32_t j=0; j < qCnt; ++j){
			port_len += m_mmu->egress_bytes[i][j];
		}
		if(port_len == last_port_qlen[i]){
			continue;
		}
		for(uint32_t j=0; j < qCnt; ++j){
			fprintf(qlen_output, "%lu, %u, %u, %u, %lu, %lu\n", Simulator::Now().GetTimeStep(), m_id, i, j, m_mmu->egress_bytes[i][j], port_len);
			fflush(qlen_output);
		}
		last_port_qlen[i] = port_len;
	}		
}

/**
 * outoput format:
 * time, sw_id, port_id, bandwidth
*/
void SwitchNode::PrintSwitchBw(FILE* bw_output, uint32_t bw_mon_interval){
	uint32_t n_dev = this->GetNDevices();
	for(uint32_t i = 1; i < n_dev; ++i){
		if(last_txBytes[i] == m_txBytes[i] && last_bw[i] == 0.0){
			continue;
		}
		double bw = (m_txBytes[i] - last_txBytes[i]) * 8 * 1e6 / bw_mon_interval; // bit/s
		bw = bw*1.0 / 1e9; // Gbps
		fprintf(bw_output, "%lu, %u, %u, %f\n", Simulator::Now().GetTimeStep(), m_id, i, bw);
		fflush(bw_output);
		last_txBytes[i] = m_txBytes[i];
		last_bw[i] = bw;
	}	
}

// 打印交换机各个端口单独丢包数量
void SwitchNode::PrintSwitchStatistic(){
	uint32_t n_interfaces = m_devices.size();
	for(uint32_t i = 1; i < n_interfaces; ++i){
		Ptr<QbbNetDevice> device = DynamicCast<QbbNetDevice>(m_devices[i]);
		if (device->m_linkFailedPktDropCnt > 0)
			printf("%u:%u\t", i, device->m_linkFailedPktDropCnt);
		else continue;
	}	
	printf("\n");
}

#ifdef HASH_EGRESSPORT_OBSERVATION
void SwitchNode::PrintSwitchHASHload(FILE* hash_load_output, uint32_t hash_mon_interval){
	uint32_t n_dev = this->GetNDevices();
	for(uint32_t i = 1; i < n_dev; ++i){
		if(last_txBytes[i] == m_txBytes[i] && last_bw[i] == 0.0){
			continue;
		}
		for (const auto& [key, count] : packetCountMap) {
        	auto [field1, field2, field3, port1, port2] = key;
        
        	fprintf(hash_load_output, "%ld, %u, %u, %u, %u, %u, %u, %lu\n", 
                	Simulator::Now().GetTimeStep(), m_id, field1, (field2 >> 8) & 0xffff,  (field3 >> 8) & 0xffff, port1, port2, count);
			fflush(hash_load_output);
    	}
		
		last_txBytes[i] = m_txBytes[i];
		packetCountMap.clear();
	}	
}
#endif

} /* namespace ns3 */
