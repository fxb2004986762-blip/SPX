#include <ns3/simulator.h>
#include <ns3/simple-seq-ts-header.h>
#include <ns3/udp-header.h>
#include <ns3/ipv4-header.h>
#include "ns3/ppp-header.h"
#include "ns3/boolean.h"
#include "ns3/uinteger.h"
#include "ns3/double.h"
#include "ns3/data-rate.h"
#include "ns3/pointer.h"
#include "rdma-hw.h"
#include "ppp-header.h"
#include "qbb-header.h"
#include "cn-header.h"
#ifdef NS3_MTP
#include "ns3/mtp-interface.h"
#endif
#include <iostream>	// debug
#include "point-to-point-utils.h"
#include <cmath>
#include "ns3/flow-id-num-tag.h"
#include "flow-type-tag.h"
#include "flow-stat-tag.h"
#include "flow-info-tag.h"
#include "flow-custom-header-tag.h"
#include "psn-path.h"
#define TRACE (ip_to_node_id(qp->sip) == SRC && ip_to_node_id(qp->dip) == DST)
#define DST_TRACE (ip_to_node_id(rxQp->dip) == SRC && ip_to_node_id(rxQp->sip) == DST)
namespace ns3{

TypeId RdmaHw::GetTypeId (void)
{
	static TypeId tid = TypeId ("ns3::RdmaHw")
		.SetParent<Object> ()
		.AddAttribute("MinRate",
				"Minimum rate of a throttled flow",
				DataRateValue(DataRate("100Mb/s")),
				MakeDataRateAccessor(&RdmaHw::m_minRate),
				MakeDataRateChecker())
		.AddAttribute("Mtu",
				"Mtu.",
				UintegerValue(1000),
				MakeUintegerAccessor(&RdmaHw::m_mtu),
				MakeUintegerChecker<uint32_t>())
		.AddAttribute ("LbMode",
				"which mode of Load Balancing is running",
				UintegerValue(0),
				MakeUintegerAccessor(&RdmaHw::m_lb_mode),
				MakeUintegerChecker<uint32_t>())
		.AddAttribute ("CcMode",
				"which mode of DCQCN is running",
				UintegerValue(0),
				MakeUintegerAccessor(&RdmaHw::m_cc_mode),
				MakeUintegerChecker<uint32_t>())
		.AddAttribute("NACKGenerationInterval",
				"The NACK Generation interval",
				DoubleValue(50.0),
				MakeDoubleAccessor(&RdmaHw::m_nack_interval),
				MakeDoubleChecker<double>())
		.AddAttribute("L2ChunkSize",
				"Layer 2 chunk size. Disable chunk mode if equals to 0.",
				UintegerValue(0),
				MakeUintegerAccessor(&RdmaHw::m_chunk),
				MakeUintegerChecker<uint32_t>())
		.AddAttribute("L2AckInterval",
				"Layer 2 Ack intervals. Disable ack if equals to 0.",
				UintegerValue(0),
				MakeUintegerAccessor(&RdmaHw::m_ack_interval),
				MakeUintegerChecker<uint32_t>())
		.AddAttribute("L2BackToZero",
				"Layer 2 go back to zero transmission.",
				BooleanValue(false),
				MakeBooleanAccessor(&RdmaHw::m_backto0),
				MakeBooleanChecker())
		.AddAttribute("EwmaGain",
				"Control gain parameter which determines the level of rate decrease",
				DoubleValue(1.0 / 16),
				MakeDoubleAccessor(&RdmaHw::m_g),
				MakeDoubleChecker<double>())
		.AddAttribute ("RateOnFirstCnp",
				"the fraction of rate on first CNP",
				DoubleValue(1.0),
				MakeDoubleAccessor(&RdmaHw::m_rateOnFirstCNP),
				MakeDoubleChecker<double> ())
		.AddAttribute("ClampTargetRate",
				"Clamp target rate.",
				BooleanValue(false),
				MakeBooleanAccessor(&RdmaHw::m_EcnClampTgtRate),
				MakeBooleanChecker())
		.AddAttribute("RPTimer",
				"The rate increase timer at RP in microseconds",
				DoubleValue(1500.0),
				MakeDoubleAccessor(&RdmaHw::m_rpgTimeReset),
				MakeDoubleChecker<double>())
		.AddAttribute("RateDecreaseInterval",
				"The interval of rate decrease check",
				DoubleValue(4.0),
				MakeDoubleAccessor(&RdmaHw::m_rateDecreaseInterval),
				MakeDoubleChecker<double>())
		.AddAttribute("FastRecoveryTimes",
				"The rate increase timer at RP",
				UintegerValue(5),
				MakeUintegerAccessor(&RdmaHw::m_rpgThreshold),
				MakeUintegerChecker<uint32_t>())
		.AddAttribute("AlphaResumInterval",
				"The interval of resuming alpha",
				DoubleValue(55.0),
				MakeDoubleAccessor(&RdmaHw::m_alpha_resume_interval),
				MakeDoubleChecker<double>())
		.AddAttribute("RateAI",
				"Rate increment unit in AI period",
				DataRateValue(DataRate("5Mb/s")),
				MakeDataRateAccessor(&RdmaHw::m_rai),
				MakeDataRateChecker())
		.AddAttribute("RateHAI",
				"Rate increment unit in hyperactive AI period",
				DataRateValue(DataRate("50Mb/s")),
				MakeDataRateAccessor(&RdmaHw::m_rhai),
				MakeDataRateChecker())
		.AddAttribute("VarWin",
				"Use variable window size or not",
				BooleanValue(false),
				MakeBooleanAccessor(&RdmaHw::m_var_win),
				MakeBooleanChecker())
		.AddAttribute("OooAck",
				"Use out-of-order acknowledgment or not",
				BooleanValue(false),
				MakeBooleanAccessor(&RdmaHw::m_ooo_ack),
				MakeBooleanChecker())
		.AddAttribute("AckPsn",
				"Carry PSN in ACK or not",
				BooleanValue(false),
				MakeBooleanAccessor(&RdmaHw::m_ack_psn),
				MakeBooleanChecker())	
		.AddAttribute("HasWin",
				"Has window or not",
				BooleanValue(false),
				MakeBooleanAccessor(&RdmaHw::m_has_win),
				MakeBooleanChecker())							
		.AddAttribute("FastReact",
				"Fast React to congestion feedback",
				BooleanValue(true),
				MakeBooleanAccessor(&RdmaHw::m_fast_react),
				MakeBooleanChecker())
		.AddAttribute("MiThresh",
				"Threshold of number of consecutive AI before MI",
				UintegerValue(5),
				MakeUintegerAccessor(&RdmaHw::m_miThresh),
				MakeUintegerChecker<uint32_t>())
		.AddAttribute("TargetUtil",
				"The Target Utilization of the bottleneck bandwidth, by default 95%",
				DoubleValue(0.95),
				MakeDoubleAccessor(&RdmaHw::m_targetUtil),
				MakeDoubleChecker<double>())
		.AddAttribute("UtilHigh",
				"The upper bound of Target Utilization of the bottleneck bandwidth, by default 98%",
				DoubleValue(0.98),
				MakeDoubleAccessor(&RdmaHw::m_utilHigh),
				MakeDoubleChecker<double>())
		.AddAttribute("RateBound",
				"Bound packet sending by rate, for test only",
				BooleanValue(true),
				MakeBooleanAccessor(&RdmaHw::m_rateBound),
				MakeBooleanChecker())
		.AddAttribute("MultiRate",
				"Maintain multiple rates in HPCC",
				BooleanValue(true),
				MakeBooleanAccessor(&RdmaHw::m_multipleRate),
				MakeBooleanChecker())
		.AddAttribute("SampleFeedback",
				"Whether sample feedback or not",
				BooleanValue(false),
				MakeBooleanAccessor(&RdmaHw::m_sampleFeedback),
				MakeBooleanChecker())
		.AddAttribute("TimelyAlpha",
				"Alpha of TIMELY",
				DoubleValue(0.875),
				MakeDoubleAccessor(&RdmaHw::m_tmly_alpha),
				MakeDoubleChecker<double>())
		.AddAttribute("TimelyBeta",
				"Beta of TIMELY",
				DoubleValue(0.8),
				MakeDoubleAccessor(&RdmaHw::m_tmly_beta),
				MakeDoubleChecker<double>())
		.AddAttribute("TimelyTLow",
				"TLow of TIMELY (ns)",
				UintegerValue(50000),
				MakeUintegerAccessor(&RdmaHw::m_tmly_TLow),
				MakeUintegerChecker<uint64_t>())
		.AddAttribute("TimelyTHigh",
				"THigh of TIMELY (ns)",
				UintegerValue(500000),
				MakeUintegerAccessor(&RdmaHw::m_tmly_THigh),
				MakeUintegerChecker<uint64_t>())
		.AddAttribute("TimelyMinRtt",
				"MinRtt of TIMELY (ns)",
				UintegerValue(20000),
				MakeUintegerAccessor(&RdmaHw::m_tmly_minRtt),
				MakeUintegerChecker<uint64_t>())
		.AddAttribute("DctcpRateAI",
				"DCTCP's Rate increment unit in AI period",
				DataRateValue(DataRate("1000Mb/s")),
				MakeDataRateAccessor(&RdmaHw::m_dctcp_rai),
				MakeDataRateChecker())
		.AddAttribute("PintSmplThresh",
				"PINT's sampling threshold in rand()%65536",
				UintegerValue(65536),
				MakeUintegerAccessor(&RdmaHw::pint_smpl_thresh),
				MakeUintegerChecker<uint32_t>())
		.AddAttribute("GPUsPerServer",
				"the number of gpus in a server, used for routing",
				UintegerValue(1),
				MakeUintegerAccessor(&RdmaHw::m_gpus_per_server),
				MakeUintegerChecker<uint32_t>())	
		.AddAttribute("TotalPauseTimes",
				"The number of pause times to simulate PFC pause due to PCIe",
				UintegerValue(0),
				MakeUintegerAccessor(&RdmaHw::m_total_pause_times),
				MakeUintegerChecker<uint64_t>())
		.AddAttribute("NVLS_enable",
				"NVLS enable info",
				UintegerValue(0),
				MakeUintegerAccessor(&RdmaHw::nvls_enable),
				MakeUintegerChecker<uint32_t>())
		.AddAttribute("FlowBender_T",
				"FlowBender Threshold T",
				DoubleValue(0.05),
				MakeDoubleAccessor(&RdmaHw::m_flow_bender_T),
				MakeDoubleChecker<double>())
		.AddAttribute("FlowBender_N",
				"FlowBender Switch Path Threshold N",
				UintegerValue(0),
				MakeUintegerAccessor(&RdmaHw::m_flow_bender_N),
				MakeUintegerChecker<uint32_t>())								
		.AddAttribute("UpdateFrequency",
				"INT's update interval frequency",
				UintegerValue(1),
				MakeUintegerAccessor(&RdmaHw::m_updateFreq),
				MakeUintegerChecker<uint32_t>())
		.AddAttribute("ApsIndMask",
				"APS path evaluation indicator mask",
				UintegerValue(7),
				MakeUintegerAccessor(&RdmaHw::m_apsIndMask),
				MakeUintegerChecker<uint8_t>())
		.AddAttribute("ApsDefaultPortCnt",
				"APS default switch out port count",
				UintegerValue(8),
				MakeUintegerAccessor(&RdmaHw::m_apsDefaultPortCnt),
				MakeUintegerChecker<uint32_t>())	
		.AddAttribute("MaxOOOSize",
				"Max out of order packet buffer size",
				UintegerValue(0),
				MakeUintegerAccessor(&RdmaHw::max_ooo_size), 
				MakeUintegerChecker<uint32_t>())
		.AddAttribute("REPSBufferSize",
				"REPS buffer size for each QP",
				UintegerValue(8),
				MakeUintegerAccessor(&RdmaHw::REPS_BUFFER_SIZE),
				MakeUintegerChecker<uint32_t>())
		.AddAttribute("PSNPATH_K",
				"PSN-PATH multipath number K",
				UintegerValue(4),
				MakeUintegerAccessor(&RdmaHw::PSN_PATH_K),
				MakeUintegerChecker<uint32_t>())
		.AddAttribute("IOPSBufferSize",
				"IOPS buffer size for each QP",
				UintegerValue(8),
				MakeUintegerAccessor(&RdmaHw::IOPS_BUFFER_SIZE),
				MakeUintegerChecker<uint32_t>())
		.AddAttribute("ApsPathCredit",
				"APS path credit peak value",
				UintegerValue(1),
				MakeUintegerAccessor(&RdmaHw::CREDIT_SIZE),
				MakeUintegerChecker<uint32_t>())
		.AddAttribute("TracedNode",
				"Traced Node Id",
				UintegerValue(0),
				MakeUintegerAccessor(&RdmaHw::traced_node),
				MakeUintegerChecker<uint32_t>())	
		.AddAttribute("EstimateWindowSize",
				"Estimated window size",
				UintegerValue(3),
				MakeUintegerAccessor(&RdmaHw::m_esti_window),
				MakeUintegerChecker<uint32_t>())
		.AddAttribute("RetransTimeOut",
				"Retransmission Time Out",
				UintegerValue(100),
				MakeUintegerAccessor(&RdmaHw::m_retrans_time_out),
				MakeUintegerChecker<uint32_t>())													
		;
	return tid;
}

RdmaHw::RdmaHw(){
}

void RdmaHw::enable_nvls() {
	nvls_enable = 1;
}

void RdmaHw::disable_nvls() {
	nvls_enable = 0;
}

void RdmaHw::add_nvswitch(uint32_t nvswitch_id) {
	nvswitch_set.insert(nvswitch_id);
}

void RdmaHw::SetNode(Ptr<Node> node){
	m_node = node;
}
void RdmaHw::Setup(QpCompleteCallback cb,SendCompleteCallback send_cb){
	tx_bytes.resize(m_nic.size());
	last_tx_bytes.resize(m_nic.size());
	for (uint32_t i = 0; i < m_nic.size(); i++){
		tx_bytes[i] = 0;
		last_tx_bytes[i] = 0;
		Ptr<QbbNetDevice> dev = m_nic[i].dev;
		if (dev == NULL)
			continue;
		// share data with NIC
		dev->m_rdmaEQ->m_qpGrp = m_nic[i].qpGrp;
		// setup callback
		dev->m_rdmaReceiveCb = MakeCallback(&RdmaHw::Receive, this);
        dev->m_rdmaSentCb = MakeCallback(&RdmaHw::SendPacketComplete, this);
        dev->m_rdmaLinkDownCb = MakeCallback(&RdmaHw::SetLinkDown, this);
		dev->m_rdmaPktSent = MakeCallback(&RdmaHw::PktSent, this);
		dev->m_rdmaUpdateTxBytes = MakeCallback(&RdmaHw::UpdateTxBytes, this);
		// config NIC
		dev->m_rdmaEQ->m_rdmaGetNxtPkt = MakeCallback(&RdmaHw::GetNxtPacket, this);
	}
	// setup qp complete callback
	m_qpCompleteCallback = cb;
    m_sendCompleteCallback = send_cb;

	// initial random seed
	srand(0xb214);
}
uint32_t ip_to_node_id(Ipv4Address ip) { return (ip.Get() >> 8) & 0xffff; }
uint32_t ip_to_node_id(uint32_t ip) { return (ip >> 8) & 0xffff; }
uint32_t RdmaHw::GetNicIdxOfQp(Ptr<RdmaQueuePair> qp){
	uint32_t src = qp->m_src;
	uint32_t dst = qp->m_dest;
	if(src / m_gpus_per_server == dst / m_gpus_per_server || m_rtTable_nxthop_nvswitch.count(qp->dip.Get()) != 0){ // src and dst are in the same server, communicate through nvswitch
		auto &v = m_rtTable_nxthop_nvswitch[qp->dip.Get()];
		if (v.size() > 0){
			return v[qp->GetHash() % v.size()];
		}else{
			NS_ASSERT_MSG(false, "We assume at least one NIC is alive");
		}
	}else{ // src and dst don't in the same server, communicate through swicth
		auto &v = m_rtTable[qp->dip.Get()];
		if (v.size() > 0){
			return v[qp->GetHash() % v.size()];
		}else{
			NS_ASSERT_MSG(false, "We assume at least one NIC is alive");
		}
	}
}
uint64_t RdmaHw::GetQpKey(uint32_t dip, uint16_t sport, uint16_t pg){
	return ((uint64_t)dip << 32) | ((uint64_t)sport << 16) | (uint64_t)pg;
}
Ptr<RdmaQueuePair> RdmaHw::GetQp(uint32_t dip, uint16_t sport, uint16_t pg){
	uint64_t key = GetQpKey(dip, sport, pg);
	auto it = m_qpMap.find(key);
	if (it != m_qpMap.end())
		return it->second;
	return NULL;
}
void RdmaHw::AddQueuePair(uint32_t src, uint32_t dest, uint64_t tag, uint64_t size, uint16_t pg, Ipv4Address sip, Ipv4Address dip, uint16_t sport, uint16_t dport, uint32_t win, uint64_t baseRtt, int32_t flow_id, Callback<void> notifyAppFinish, Callback<void> notifyAppSent){
	// create qp
	Ptr<RdmaQueuePair> qp = CreateObject<RdmaQueuePair>(pg, sip, dip, sport, dport);
	qp->SetSrc(src);
	qp->SetDest(dest);
	qp->SetTag(tag);
	qp->SetSize(size);
	qp->SetInitialSize(size);
	if(m_has_win || m_cc_mode == 11) qp->SetWin(win); // mprdma or dcqcn+win
	else qp->SetWin(0);
	qp->SetBaseRtt(baseRtt);
	qp->SetVarWin(m_var_win);
	qp->SetOooAck(m_ooo_ack);
	qp->SetAppNotifyCallback(notifyAppFinish);
	qp->SetAppSentCallback(notifyAppSent);
    qp->SetFlowId(flow_id);
	qp->SetFlowType(m_lb_mode);
	qp->SetApsDefaultW(m_apsIndMask);
	// add qp
	uint32_t nic_idx = GetNicIdxOfQp(qp);
	qp->nic_id = nic_idx;
	#ifdef QP_INIT_INFO
	printf("[INFO:QP_INIT][%ld] nic_idx: %u, creating QP: (From Send: SDSD) %u %u %u %u, flow_id: %u, size: %u, baseRtt: %u, win %u\n", 
		Simulator::Now().GetTimeStep(), nic_idx, ip_to_node_id(sip), ip_to_node_id(dip), sport, dport, flow_id, (uint32_t)size, (uint32_t)baseRtt, win);
		fflush(stdout);
	#endif
		// std::cout << "src is: " << src << ", dst is: " << dest <<  ", nic_idx: " << nic_idx << ", and the m_nic size is: " << m_nic.size() << std::endl;
		// Assign the qp to specific qbbnetdevice
	m_nic[nic_idx].qpGrp->AddQp(qp);
	uint64_t key = GetQpKey(dip.Get(), sport, pg);
	m_qpMap[key] = qp;
	qp_cnp[key] = 0;
	last_qp_cnp[key] = 0;
	last_qp_rate[key] = 0;
	last_aps_selected[key].first = 0;
	last_aps_selected[key].second = 0;
	
	// SR: config NIC Notification Callback for each qp
	qp->m_rdmaQpTriggerTransCb = MakeCallback(&RdmaHw::TriggerTrans, this);
	qp->mtu = m_mtu;
	qp->m_cwnd = win / m_mtu;
	if (m_lb_mode == 6) {
		qp->psnPath.enabled = true;
		qp->psnPath.k = PSN_PATH_K;
		qp->psnPath.basePort = sport;
		qp->psnPath.packetSize = m_mtu;
		qp->psnPath.mapping.resize(qp->psnPath.k);
		qp->psnPath.quality.resize(qp->psnPath.k);
		for (uint32_t logicalPath = 0; logicalPath < qp->psnPath.k; ++logicalPath) {
			qp->psnPath.mapping[logicalPath].fpsn = logicalPath;
		}
		qp->psnPath.lastEvaluation = Simulator::Now();
	}
	
	// set init variables
	DataRate m_bps = m_nic[nic_idx].dev->GetDataRate();
	uint32_t RTO = baseRtt + 400000 * 4 * 8 / (m_bps.GetBitRate() / 1000000000);
	// printf("Calculate RTO, baseRtt %u, bit/s %u\n", baseRtt, m_bps.GetBitRate() / 1000000000);
	if (m_retrans_time_out != 0) RTO = m_retrans_time_out;
	qp->SetRetransTimeOut(RTO); // set retransmission timeout as baseRtt + 4 times of time to send a BDP size packet, which is a common setting in real RDMA NICs
	qp->m_rate = m_bps;
	qp->m_max_rate = m_bps;
	// cc
	if (m_cc_mode == 1){
		qp->mlx.m_targetRate = m_bps;
	}else if (m_cc_mode == 3){
		qp->hp.m_curRate = m_bps;
		if (m_multipleRate){
			for (uint32_t i = 0; i < IntHeader::maxHop; i++)
				qp->hp.hopState[i].Rc = m_bps;
		}
	}else if (m_cc_mode == 7){
		qp->tmly.m_curRate = m_bps;
	}else if (m_cc_mode == 10){
		qp->hpccPint.m_curRate = m_bps;
	}else if (m_cc_mode == 11){
		qp->mprdma.m_maxCwnd = 1.5 * win;
	}
	// lb
	if (m_lb_mode == 1) {
		qp->aps.exploreCnt = qp->m_cwnd;
	} else if (m_lb_mode == 5) {
		qp->reps.exploreCnt = qp->m_cwnd;
	}
	// NVLS settings
	if(nvls_enable == 1) qp->nvls_enable = 1;
	else qp->nvls_enable = 0;
	// Notify Nic
	m_nic[nic_idx].dev->NewQp(qp);
}

void RdmaHw::DeleteQueuePair(Ptr<RdmaQueuePair> qp){
	// remove qp from the m_qpMap
	uint64_t key = GetQpKey(qp->dip.Get(), qp->sport, qp->m_pg);
	m_qpMap.erase(key);
	qp_cnp.erase(key);
	last_qp_cnp.erase(key);
	last_qp_rate.erase(key);
}
// SR: for NIC Notification
void RdmaHw::TriggerTrans(Ptr<RdmaQueuePair> qp){
	// if (qp->m_src == 0 && qp->m_dest == 12) 
	// 	printf("[RETRANS][%ld] trigger retransmission for flow from 0 to 12, seq %u\n", Simulator::Now().GetTimeStep(), qp->snd_una);
	#ifdef SR_SND_RT_LOG
	if(TRACE)
		printf("[LOG:SR_SND_RT][%ld][%u]\tSender TriggerTrans, snd_una %u, snd_nxt %u, inflight %u\n", Simulator::Now().GetTimeStep(), this->m_node->GetId(), qp->snd_una, qp->snd_nxt, qp->inflight);
	#endif 
    uint32_t nic_idx = GetNicIdxOfQp(qp);
	Ptr<QbbNetDevice> dev = m_nic[nic_idx].dev;
	dev->TriggerTransmit();
}
Ptr<RdmaRxQueuePair> RdmaHw::GetRxQp(uint32_t sip, uint32_t dip, uint16_t sport, uint16_t dport, uint16_t pg, bool create){
    uint64_t key = ((uint64_t)dip << 32) | ((uint64_t)pg << 16) | (uint64_t)dport;
    #ifdef NS3_MTP
    MtpInterface::explicitCriticalSection cs;
    #endif
    auto it = m_rxQpMap.find(key);
    if (it != m_rxQpMap.end()){
        #ifdef NS3_MTP
        cs.ExitSection();
        #endif
        return it->second;
    }
    if (create){
        // create new rx qp
        Ptr<RdmaRxQueuePair> q = CreateObject<RdmaRxQueuePair>();
        // init the qp
        q->sip = sip;
        q->dip = dip;
        q->sport = sport;
        q->dport = dport;
        q->m_ecn_source.qIndex = pg;
        // store in map
        m_rxQpMap[key] = q;
        #ifdef NS3_MTP
        cs.ExitSection();
        #endif
        return q;
    }
    #ifdef NS3_MTP
    cs.ExitSection();
    #endif
    return NULL;
}
int RdmaHw::CreateRxQp(uint32_t sip, uint32_t dip, uint16_t sport, uint16_t dport, uint16_t pg){
	uint64_t key = ((uint64_t)dip << 32) | ((uint64_t)pg << 16) | (uint64_t)dport;
	auto it = m_rxQpMap.find(key);
	if (it != m_rxQpMap.end()){
		printf("[ERROR]: RxQp already exists!\n");
		return -1;
	}
	// create new rx qp
	Ptr<RdmaRxQueuePair> q = CreateObject<RdmaRxQueuePair>();
	// init the qp
	q->sip = sip;
	q->dip = dip;
	q->sport = sport;
	q->dport = dport;
	q->m_ecn_source.qIndex = pg;
	// store in map
	m_rxQpMap[key] = q;
	return key;
}
uint32_t RdmaHw::GetNicIdxOfRxQp(Ptr<RdmaRxQueuePair> q){
	// BUG就出现在这里了，首先要判断m_rtTable[q->dip]是否存在，若不存在就去判断m_rtTable_nxthop_nvswitch是否存在，如果都不存在，那么就输出错误
	// auto &v = m_rtTable[q->dip];

	if(m_rtTable.count(q->dip) != 0) {
		auto &v = m_rtTable[q->dip];
		if(v.size() > 0)
			return v[q->GetHash() % v.size()];
		else 
			NS_ASSERT_MSG(false, "We assume at least one NIC is alive");
	} else if(m_rtTable_nxthop_nvswitch.count(q->dip) != 0) {
		auto &v = m_rtTable_nxthop_nvswitch[q->dip];
		if(v.size() > 0)
			return v[q->GetHash() % v.size()];
		else 
			NS_ASSERT_MSG(false, "We assume at least one NIC is alive");
	} else {
		NS_ASSERT_MSG(false, "We assume at least one NIC is alive");
	}
	NS_ASSERT_MSG(false, "We assume at least one NIC is alive");
	
}
void RdmaHw::DeleteRxQp(uint32_t dip, uint16_t pg, uint16_t dport){
	uint64_t key = ((uint64_t)dip << 32) | ((uint64_t)pg << 16) | (uint64_t)dport;
	m_rxQpMap.erase(key);
}

int RdmaHw::SendPacketComplete(Ptr<Packet> p, CustomHeader &ch)
{
	uint16_t qIndex = ch.udp.pg;
	uint16_t port = ch.udp.sport;
	PsnPathTag psnPathTag;
	if (p->PeekPacketTag(psnPathTag)) {
		port = psnPathTag.GetFlowSport();
	}
	// uint32_t seq = ch.udp.seq;
	// uint8_t cnp = (ch.flags >> qbbHeader::FLAG_CNP) & 1;
	// int i;
	Ptr<RdmaQueuePair> qp = GetQp(ch.dip, port, qIndex);
	if (qp == NULL)
	{
		return 0;
	}
	uint32_t nic_idx = GetNicIdxOfQp(qp);
	Ptr<QbbNetDevice> dev = m_nic[nic_idx].dev;
	SendComplete(qp);
	return 0;
}

void RdmaHw::SendComplete(Ptr<RdmaQueuePair> qp)
{
	NS_ASSERT(!m_sendCompleteCallback.IsNull());

	m_sendCompleteCallback(qp);
}

int RdmaHw::ReceiveUdp(Ptr<Packet> p, CustomHeader &ch){
	uint8_t ecnbits = ch.GetIpv4EcnBits();
	
	uint32_t payload_size = p->GetSize() - ch.GetSerializedSize();
	PsnPathTag psnPathTag;
	bool isPsnPath = m_lb_mode == 6 && p->PeekPacketTag(psnPathTag);
	if (m_lb_mode == 6 && !isPsnPath) {
		printf("[ERROR:PSN_PATH] data packet %lu has no PSN-PATH metadata\n", ch.udp.seq);
		return 0;
	}
	uint16_t flowSport = isPsnPath ? psnPathTag.GetFlowSport() : ch.udp.sport;
	// TODO find corresponding rx queue pair
	Ptr<RdmaRxQueuePair> rxQp = GetRxQp(ch.dip, ch.sip, ch.udp.dport, flowSport, ch.udp.pg, false);
	if(rxQp == NULL) 
    {
		printf("[WARN][%ld][%u] ReceiveUdp: no rxqp, maybe tail packet ooo, (from Send: SDSD) %u %u %u %u\n", \
			Simulator::Now().GetTimeStep(), this->m_node->GetId(), ip_to_node_id(ch.sip), ip_to_node_id(ch.dip), ch.udp.sport, ch.udp.dport);
        return 0;
    }
	if (ecnbits != 0){
		rxQp->m_ecn_source.ecnbits |= ecnbits;
		rxQp->m_ecn_source.qfb++;
	}
	rxQp->m_ecn_source.total++;
	rxQp->m_milestone_rx = m_ack_interval;
	#ifdef SR_RCV_LOG
	if(DST_TRACE)
		printf("[LOG:SR_RCV][%ld][%u]\tReceive Udp ch.dip %08x ch.sip %08x seq %lu\n", Simulator::Now().GetTimeStep(), this->m_node->GetId(), ch.dip, ch.sip, ch.udp.seq);
	#endif
	int x;
	uint32_t nackSeq = ch.udp.seq;
	if (isPsnPath) {
		uint32_t psn = GetPsnFromSeq(ch.udp.seq, m_mtu);
		PsnRxDecision decision = ReceiverCheckSeqPsnPath(rxQp, psn, payload_size, psnPathTag);
		x = decision.sendNack ? 2 : 1;
		if (decision.sendNack) {
			nackSeq = decision.nackPsn * m_mtu;
		}
	} else {
		x = ReceiverCheckSeq(ch.udp.seq, rxQp, payload_size);
	}
	if (x == 1 || x == 2){ //generate ACK or NACK
		qbbHeader seqh;
		if(max_ooo_size != 0) // SR
		seqh.SetSeq(rxQp->ReceiverNextExpectedSeq);
		else seqh.SetSeq(x == 1 ? rxQp->ReceiverNextExpectedSeq : ch.udp.seq); // go-back-n
		seqh.SetPG(ch.udp.pg);
		seqh.SetSport(ch.udp.dport);
		seqh.SetDport(flowSport);
		seqh.SetIntHeader(ch.udp.ih);
		if (ecnbits) {
			seqh.SetCnp();
			#ifdef CNP_DEBUG
				printf("[DEBUG:CNP]\tGenerating CNP Packet\n");
			#endif
		}

		Ptr<Packet> newp = Create<Packet>(std::max(60-14-20-(int)seqh.GetSerializedSize(), 0));
		newp->AddHeader(seqh);

		Ipv4Header head;	// Prepare IPv4 header
		head.SetDestination(Ipv4Address(ch.sip));
		head.SetSource(Ipv4Address(ch.dip));
		head.SetProtocol(x == 1 ? 0xFC : 0xFD); //ack=0xFC nack=0xFD
		head.SetTtl(64);
		head.SetPayloadSize(newp->GetSize());
		head.SetIdentification(rxQp->m_ipid++);
		// GPU receives the packet and generate ACK with NVLS tag
		if(ch.m_tos == 4) head.SetTos(4);

		newp->AddHeader(head);
		AddHeader(newp, 0x800);	// Attach PPP header
		
		// add flow tag (for addition infomation)
		FlowInfoTag fit;
		if (p->PeekPacketTag(fit)) {
			newp->AddPacketTag(fit);
		}

		FlowTypeTag ftt;
		if (p->PeekPacketTag(ftt)) {
			newp->AddPacketTag(ftt);
		}		

		if (isPsnPath) {
			newp->AddPacketTag(psnPathTag);
		}
		
		// for sack like mechanism
		FlowCustomHeaderTag fcht;
		fcht.SetPsn(x == 2 && isPsnPath ? nackSeq : ch.udp.seq);
		newp->AddPacketTag(fcht);

		#ifdef SR_RCV_LOG
		if(DST_TRACE && x == 1)
			printf("[LOG:SR_RCV][%ld][%u]\tSend ACK seq %u ePSN %u\n", Simulator::Now().GetTimeStep(), this->m_node->GetId(), ch.udp.seq, rxQp->ReceiverNextExpectedSeq);
		else if (DST_TRACE && x == 2)
			printf("[LOG:SR_RCV][%ld][%u]\tSend NACK seq %u ePSN %u\n", Simulator::Now().GetTimeStep(), this->m_node->GetId(), ch.udp.seq, rxQp->ReceiverNextExpectedSeq);
		#endif		

		// uint32_t sip = ch.sip;
		// uint32_t sid = (sip >> 8) & 0xffff;
		uint32_t dip = ch.dip;
		uint32_t did = (dip >> 8) & 0xffff;
		// send
		uint32_t nic_idx = GetNicIdxOfRxQp(rxQp);
		m_nic[nic_idx].dev->RdmaEnqueueHighPrioQ(newp);
		// 发送给目标 NVSwitch 的报文
		if(did == m_node->GetId() && m_node->GetNodeType() == 2 && ch.m_tos == 4) m_nic[nic_idx].dev->SwitchAsHostSend();
		else m_nic[nic_idx].dev->TriggerTransmit();
	} else {
		printf("[INFO:RCV_UDP][%ld] Receive UDP from %u to %u, seq %u, but not generate ACK/NACK, maybe out of order or duplicate\n", Simulator::Now().GetTimeStep(), ip_to_node_id(ch.sip), ip_to_node_id(ch.dip), ch.udp.seq);
	}
	return 0;
}

int RdmaHw::ReceiveCnp(Ptr<Packet> p, CustomHeader &ch){
	// QCN on NIC
	// This is a Congestion signal
	// Then, extract data from the congestion packet.
	// We assume, without verify, the packet is destinated to me
	#ifdef CNP_DEBUG
		printf("[DEBUG:CNP]\tCNP received");
	#endif
	uint32_t qIndex = ch.cnp.qIndex;
	if (qIndex == 1){		//DCTCP
		return 0;
	}
	uint16_t udpport = ch.cnp.fid; // corresponds to the sport
	// uint8_t ecnbits = ch.cnp.ecnBits;
	// uint16_t qfb = ch.cnp.qfb;
	// uint16_t total = ch.cnp.total;

	// uint32_t i;
	// get qp
	Ptr<RdmaQueuePair> qp = GetQp(ch.sip, udpport, qIndex);
	if (qp == NULL)
		std::cout << "ERROR: QCN NIC cannot find the flow\n";
	// get nic
	uint32_t nic_idx = GetNicIdxOfQp(qp);
	Ptr<QbbNetDevice> dev = m_nic[nic_idx].dev;

	if (qp->m_rate == 0)			//lazy initialization	
	{
		qp->m_rate = dev->GetDataRate();
		if (m_cc_mode == 1){
			qp->mlx.m_targetRate = dev->GetDataRate();
		}else if (m_cc_mode == 3){
			qp->hp.m_curRate = dev->GetDataRate();
			if (m_multipleRate){
				for (uint32_t i = 0; i < IntHeader::maxHop; i++)
					qp->hp.hopState[i].Rc = dev->GetDataRate();
			}
		}else if (m_cc_mode == 7){
			qp->tmly.m_curRate = dev->GetDataRate();
		}else if (m_cc_mode == 10){
			qp->hpccPint.m_curRate = dev->GetDataRate();
		}
	}
	return 0;
}

int RdmaHw::ReceiveAck(Ptr<Packet> p, CustomHeader &ch){
	uint16_t qIndex = ch.ack.pg;
	uint16_t port = ch.ack.dport;
	uint64_t epsn = ch.ack.seq;
	uint64_t psn = epsn;
	uint8_t cnp = (ch.ack.flags >> qbbHeader::FLAG_CNP) & 1;
	bool tail_pkt_ack = false;

	if (m_ack_psn || m_lb_mode == 6) {
		FlowCustomHeaderTag fcht;
		if(p->PeekPacketTag(fcht)) {
			psn = fcht.GetPsn();
		} else {
			printf("[ERROR] Receive NACK but no PSN tag, maybe not generated by our SR implementation\n");
		}
	}

	// int i;
	Ptr<RdmaQueuePair> qp = GetQp(ch.sip, port, qIndex);
	if (qp == NULL){
		if (ch.l3Prot == 0xFC)
		printf("[WARN][%ld]: ReceiveACK no qp, seq %u, (From Send: SDSD) %u %u %u %u\n", Simulator::Now().GetTimeStep(), psn, ip_to_node_id(ch.dip), ip_to_node_id(ch.sip), ch.udp.dport, ch.udp.sport);
		else
		printf("[WARN][%ld]: ReceiveNACK no qp, seq %u, (From Send: SDSD) %u %u %u %u\n", Simulator::Now().GetTimeStep(), psn, ip_to_node_id(ch.dip), ip_to_node_id(ch.sip), ch.udp.dport, ch.udp.sport);
		return 0;
	}
	qp->m_lastAckTime = Simulator::Now();
	uint64_t last_snd_una = qp->snd_una;
	if (m_lb_mode == 6) {
		PsnPathTag psnPathTag;
		if (p->PeekPacketTag(psnPathTag)) {
			UpdatePsnPathFeedback(qp,
			                         GetPsnFromSeq(static_cast<uint32_t>(psn), m_mtu),
			                         ch.l3Prot == 0xFD,
			                         psnPathTag);
		} else {
			printf("[ERROR:PSN_PATH] ACK/NACK for seq %lu has no PSN-PATH metadata\n", psn);
		}
	}
	
	uint32_t nic_idx = GetNicIdxOfQp(qp);
	Ptr<QbbNetDevice> dev = m_nic[nic_idx].dev;
	if (m_ack_interval == 0)
		std::cout << "ERROR: shouldn't receive ack\n";
	else {
		// SR: reconstruct ACK & SACK machanism
		if(ch.l3Prot == 0xFC){ // ACK
			#ifdef SR_SND_LOG
			if(TRACE)
				printf("[LOG:SR_SND][%ld][%u]\tReceive ACK, seq: %lu, ePSN %u\n", Simulator::Now().GetTimeStep(), this->m_node->GetId(), psn, epsn);
			#endif
            if (!m_backto0){
				if (qp->Acknowledge(epsn)){
                    qp->m_retranstimes = 0;
				
				}else{
					// std::cout << "duplicate acks" << std::endl;;
				}
			}else {
				uint64_t goback_seq = epsn / m_chunk * m_chunk;
				if (qp->Acknowledge(goback_seq)){
                    qp->m_retranstimes = 0;

					// Simulator::Cancel(qp->m_retransEvent);
					// qp->ReScheduleTimeoutTimer();
				}else{

					// std::cout << "duplicate acks" << '\n';
				}
			}
			// if (qp->m_src == 0 && qp->m_dest == 12)
				// printf("[RCV_ACK][%ld] receive ACK from 12 to 0, seq %u, snd_una %u, m_size %u\n", Simulator::Now().GetTimeStep(), seq, qp->snd_una, qp->m_size);			
			if (qp->IsFinished()){
				tail_pkt_ack = true;
				QpComplete(qp);
				return 0;
			}
		}
		if(ch.l3Prot == 0xFD){ // NACK
			// if (qp->m_src == 0 && qp->m_dest == 12)
			// 	printf("[RCV_NACK][%ld] receive NACK from 12 to 0, seq %u, snd_una %u, m_size %u\n", Simulator::Now().GetTimeStep(), seq, qp->snd_una, qp->m_size);	

			#ifdef SR_SND_LOG
			if(TRACE)
				printf("[LOG:SR_SND][%ld][%u]\tReceive SACK, seq: %lu\n", Simulator::Now().GetTimeStep(), this->m_node->GetId(), psn);
			#endif
			#ifdef OOO_SR_INFO
				printf("[INFO:SR_INFO][%ld][%u]\tReceive SACK, seq: %lu from %u (dport:%u)\n", 
					Simulator::Now().GetTimeStep(), this->m_node->GetId(), psn, 
						ip_to_node_id(qp->dip), qp->sport);
			#endif 
			if (m_lb_mode == 6) {
				uint32_t missingPsn = GetPsnFromSeq(static_cast<uint32_t>(psn), m_mtu);
				HandlePsnPathNack(qp, missingPsn, missingPsn);
			} else if (max_ooo_size == 0) { // Go-Back-N
				RecoverQueue(qp);
				qp->gbnNums++;
			} else {
				qp->m_retranstimes++;
				// if(qp->m_retranstimes % 1000 == 1)
				// {
				if (qp->retransQueue.find(psn) == qp->retransQueue.end()) {
					qp->retransQueue[psn] = qp->GetBytesLeftforSR(psn);
					#ifdef SR_SND_LOG
					if(TRACE)
						printf("[LOG:SR_SND][%ld][%u]\tReceive SACK, seq: %lu, push it into retransQueue\n", Simulator::Now().GetTimeStep(), this->m_node->GetId(), psn);
					#endif					
				}
				// cnp = 1;
				// }
			}	
			
		}
	}
	
	
	
	// delete tx_bitmap record
	// handle bitmap
	auto i = qp->tx_bitmap.find(psn);
	if(i == qp->tx_bitmap.end()) {// 可能重传发了多次，前面的记录被覆盖，但是仍然inflight
		/** 潜在问题：
		 * RTO阈值低时，可坑没等ACK回到发送端，发送端就又超时重传
		 * 重传后，sendRecord 被重置，那么此时慢ACK到达后，参考的sendRecord显然是错误的
		 * 解决思路：
		 * 通过rtt判断是否是重传ACK，老旧的ACK只更新snd_una，不更新rtt、不删除bitmap，重传到达的ACK才更新rtt相关
		 */
		// if(!tail_pkt_ack)
			// printf("[WARN][%ld][%u:%u] Seq %u not found in tx_bitmap/retransQueue, maybe dup ack\n", Simulator::Now().GetTimeStep(), this->m_node->GetId(), ip_to_node_id(qp->dip.Get()), psn);
		// return -1;
	} else {
		FlowInfoTag fit;
		if (m_lb_mode == 1){
			NS_ASSERT(p->PeekPacketTag(fit));		
			qp->aps.raw_rtt = Simulator::Now().GetTimeStep() - i->second.send_time.GetTimeStep();
			if (qp->aps.raw_rtt > qp->aps.max_rtt) 
			qp->aps.max_rtt = qp->aps.raw_rtt;
			#ifdef APS_BITMAP_INFO
			if(TRACE)
			printf("[INFO:APS][%ld] ACK seq %u, from port %u, raw RTT: %lu, max RTT: %lu\n", 
				Simulator::Now().GetTimeStep(), psn, fit.GetSwitchPort(), qp->aps.raw_rtt, qp->aps.max_rtt);
			#endif		
		}
	
		if (m_lb_mode == 5){
			qp->reps.raw_rtt = Simulator::Now().GetTimeStep() - i->second.send_time.GetTimeStep();
			if (qp->reps.raw_rtt > qp->reps.max_rtt) 
			qp->reps.max_rtt = qp->reps.raw_rtt;
			#ifdef REPS_BITMAP_INFO
			if(TRACE)
			printf("[INFO:REPS][%ld] ACK seq %u, from port %u, raw RTT: %lu, max RTT: %lu\n", 
				Simulator::Now().GetTimeStep(), psn, fit.GetSwitchPort(), qp->reps.raw_rtt, qp->reps.max_rtt);
			#endif
		}
	}
		

	// reset RTO timer
	#ifdef SR_SND_LOG
	if(TRACE && !(m_lb_mode == 6 && i == qp->tx_bitmap.end()))
		printf("[LOG:SR_SND][%ld] Receive send_time %ld for seq %u, qp->rto_send_time %ld recalculate RTO\n", Simulator::Now().GetTimeStep(), i->second.send_time.GetTimeStep(), psn, qp->rto_send_time.GetTimeStep());
	#endif 
		
	if (m_lb_mode == 6 && ch.l3Prot == 0xFD) {
		// PSN-PATH NACK 中的 psn 是缺失包，不能按选择性 ACK 删除。
		// 重传可能已由 HandlePsnPathNack 同步触发，因此这里只清理累计确认区间。
		qp->UpdatePsnPathNackInflight(last_snd_una, epsn);
	} else {
		qp->UpdateInflight(last_snd_una, epsn, psn); // 删除乱序到达的 snd_una ~ seq 之间的发送时间记录以及本次接收ACK记录，并更新inflight
	}
	if (m_lb_mode == 6 && ch.l3Prot == 0xFC) {
		for (auto state = qp->psnPath.packetState.begin();
		     state != qp->psnPath.packetState.end();) {
			uint64_t stateSeq = static_cast<uint64_t>(state->first) * m_mtu;
			if (stateSeq < epsn || stateSeq == psn) {
				state = qp->psnPath.packetState.erase(state);
			} else {
				++state;
			}
		}
	}

	if(epsn > last_snd_una) {
		qp->RecalculateRTO(); // 累积ACK推进，就重新计算
	}


		
	// Load Balancing
	if (m_lb_mode == 1){ 
		HandleAckAps(qp, p, ch);
	} else if (m_lb_mode == 3){
		cnp_received_flow_bender(qp, cnp);
	} else if (m_lb_mode == 5){
		receiveRepsAck(qp, p, ch);
	}


	// handle cnp
	if (cnp){
		uint64_t key = GetQpKey(qp->dip.Get(), qp->sport, qp->m_pg);
		qp_cnp[key]++; // update for the number of cnp this qp has received
		qp->m_cnp_number++;
		if (m_cc_mode == 1 && m_rateBound){ // mlx version
			cnp_received_mlx(qp);
		} 

	}

	if (m_cc_mode == 3){
		HandleAckHp(qp, p, ch);
	}else if (m_cc_mode == 7){
		HandleAckTimely(qp, p, ch);
	}else if (m_cc_mode == 8){
		HandleAckDctcp(qp, p, ch);
	}else if (m_cc_mode == 10){
		HandleAckHpPint(qp, p, ch);
	}else if (m_cc_mode == 11){
		HandleAckMprdma(qp, p, ch);
	}
	// uint32_t sip = ch.sip;
	// uint32_t sid = (sip >> 8) & 0xffff;
	uint32_t dip = ch.dip;
	uint32_t did = (dip >> 8) & 0xffff;
	// ACK may advance the on-the-fly window, allowing more packets to send
	if(did == m_node->GetId() && m_node->GetNodeType() == 2) m_nic[nic_idx].dev->SwitchAsHostSend();
	else m_nic[nic_idx].dev->TriggerTransmit();
	//std:://cout << "ack triggere transmitted\n";
	return 0;
}

int RdmaHw::Receive(Ptr<Packet> p, CustomHeader &ch){
	if (ch.l3Prot == 0x11){ // UDP
		ReceiveUdp(p, ch);
	}else if (ch.l3Prot == 0xFF){ // CNP
		ReceiveCnp(p, ch);
	}else if (ch.l3Prot == 0xFD){ // NACK
		ReceiveAck(p, ch);
	}else if (ch.l3Prot == 0xFC){ // ACK
		ReceiveAck(p, ch);
	}
	return 0;
}

int RdmaHw::ReceiverCheckSeq(uint64_t seq, Ptr<RdmaRxQueuePair> q, uint32_t size){
	uint64_t expected = q->ReceiverNextExpectedSeq;
	if (seq == expected){
		// std::cout << "sip " << q->dip << " receive expected pkg \n";
        q->ReceiverNextExpectedSeq = expected + size;
        for(auto it = q->ooo_bitmap.begin(); it != q->ooo_bitmap.end();)
        {
            // std::cout << "seq:" << it->first << " size:" << it->second << " ";
            if(it->first == q->ReceiverNextExpectedSeq)
            {
				#ifdef OOO_SR_INFO
					printf("[INFO:OOO_SR][%ld]\tReceiverNode: %u, from %u (dport: %u), pkg %u in buffer\n", Simulator::Now().GetTimeStep(), this->m_node->GetId(), ip_to_node_id(Ipv4Address(q->dip)), q->dport, it->first);
				#endif
                q->ReceiverNextExpectedSeq += it->second;
                // std::cout << "earse seq: " << it->first << " size:" << it->second << std::endl;
                it = q->ooo_bitmap.erase(it);
				q->ooo_bitmap_cnt = q->ooo_bitmap_cnt == 0 ? 0 : q->ooo_bitmap_cnt - 1;
				m_oooBufferChangeCallback(q, q->ooo_bitmap_cnt);
				if (q->ooo_win_max < q->ooo_bitmap_cnt) q->ooo_win_max = q->ooo_bitmap_cnt;
            }else{
                break;
            }
        }
        
        // std::cout << std::endl;
        if (q->ReceiverNextExpectedSeq >= q->m_milestone_rx){
            q->m_milestone_rx += m_ack_interval;
            return 1; //Generate ACK
        }else if (q->ReceiverNextExpectedSeq % m_chunk == 0){
            return 1; //Generate ACK
        }else {
            std::cout << "delayed ack \n";
            return 5; // delayed ACK
        }
	}else if (seq > expected) {
		if ((seq-expected) % m_mtu != 0){ // tail packet out of order, drop
			printf("[ERROR:OOO][%ld][%u]\tReceiverNode: Modulo is not zero seq, seq %lu expected %lu, (From Send: SDSD)\n", 
				Simulator::Now().GetTimeStep(), this->m_node->GetId(), seq, expected, ip_to_node_id(q->dip), ip_to_node_id(q->sip), q->dport, q->sport);
            return 1;
		}else{
			#ifdef OOO_INFO
				printf("[INFO:OOO][%ld]\tReceiverNode: %u, receive ooo pkg from %u (dport: %u), expected %lu, but get seq %lu\n", 
					Simulator::Now().GetTimeStep(), this->m_node->GetId(), ip_to_node_id(Ipv4Address(q->dip)), q->dport, expected, seq);
			#endif			
			if (max_ooo_size != 0) { // SR
				uint32_t pkgIndex = (seq-expected) / m_mtu;
				if (pkgIndex <= max_ooo_size){
					if (q->ooo_bitmap[seq] == 0){
						q->ooo_bitmap[seq] = size;
						q->ooo_bitmap_cnt += 1;
						m_oooBufferChangeCallback(q, q->ooo_bitmap_cnt);
						if (q->ooo_win_max < q->ooo_bitmap_cnt) q->ooo_win_max = q->ooo_bitmap_cnt;
						#ifdef OOO_BUFF_INFO
							printf("[INFO:OOO_BUFF][%ld]\tReceiverNode: %u, pkg from %u (dport: %u), save %lu to buffer, expected %lu\n", 
								Simulator::Now().GetTimeStep(), this->m_node->GetId(), 
								ip_to_node_id(Ipv4Address(q->dip)), q->dport, seq, expected);
						#endif
					}
				}else{ // drop
					#ifdef OOO_WARN
						printf("[WARN:OOO][%ld]\tReceiverNode: %u, ooo pkg %u from %u (dport: %u), out of buffer, drop, expected %lu\n", 
							Simulator::Now().GetTimeStep(), this->m_node->GetId(), seq,
							ip_to_node_id(Ipv4Address(q->dip)), q->dport, expected);
						// printf("[WARN:OOO][%ld][%u]\tReceive: ooo pkg, out of buffer, drop\n", 
						// 	Simulator::Now().GetTimeStep(), this->m_node->GetId(),
						// 		ip_to_node_id(Ipv4Address(q->dip)), q->dport, seq, expected);
					#endif
					q->bitmap_overflow_cnt++;
					return 2;
				}
				return 1;
			} else { // Go-Back-N
				if (Simulator::Now() >= q->m_nackTimer || q->m_lastNACK != expected) { // new NACK， Go-Back-N的聚合逻辑
					q->m_nackTimer = Simulator::Now() + MicroSeconds(m_nack_interval);
					q->m_lastNACK = expected;
					return 2;
				} else {
					return 4; // skip NACK
				}
			}
		}
	}else{
		return 1; // duplicate pkg, but still send generate ack to send back fabric info
		// return 3; // duplicate pkg
	}
}

uint32_t
RdmaHw::SelectNextTxPsn(Ptr<RdmaQueuePair> qp, bool &isRetransmission)
{
	isRetransmission = !qp->retransQueue.empty();
	uint64_t seq = isRetransmission ? qp->retransQueue.begin()->first : qp->snd_nxt;
	return GetPsnFromSeq(static_cast<uint32_t>(seq), qp->psnPath.packetSize);
}

uint16_t
RdmaHw::ApplyPsnPathMapping(Ptr<RdmaQueuePair> qp,
	                         Ptr<Packet> packet,
	                         uint32_t psn,
	                         bool isRetransmission)
{
	NS_ASSERT_MSG(qp->psnPath.enabled && qp->psnPath.k != 0,
	              "PSN-PATH sender state is not initialized");
	uint32_t logicalPath = GetLogicalPath(psn, qp->psnPath.k);
	PsnPathMappingState &mapping = qp->psnPath.mapping[logicalPath];

	uint16_t offset = mapping.offset;
	uint32_t fpsn = mapping.fpsn;
	bool probe = false;
	auto original = qp->psnPath.packetState.find(psn);
	if (isRetransmission && original != qp->psnPath.packetState.end()) {
		// Keep the original continuity epoch, but route the retransmission over
		// the current (possibly remapped) healthy physical path.
		fpsn = original->second.fpsn;
	} else {
		offset = SelectProbeOrCurrentOffset(mapping);
		probe = mapping.probing && offset == mapping.candidateOffset;
		if (probe) {
			// An isolated DT-Switch probe is its own continuity epoch.
			fpsn = psn;
		} else if (mapping.currentNeedsBoundary) {
			// Do not compare the first current-path packet after a probe with
			// that probe, since they used different physical paths.
			mapping.fpsn = psn;
			mapping.currentNeedsBoundary = false;
			fpsn = psn;
		}
		qp->psnPath.packetState[psn] = PsnPathPacketState(offset, fpsn, probe);
	}

	uint32_t sourcePort = static_cast<uint32_t>(qp->psnPath.basePort)
	                      + logicalPath + offset;
	NS_ASSERT_MSG(sourcePort <= 65535, "PSN-PATH source port overflow");

	PsnPathTag tag;
	tag.SetK(qp->psnPath.k);
	tag.SetOffset(offset);
	tag.SetFpsn(fpsn);
	tag.SetFlowSport(qp->sport);
	tag.SetProbe(probe);
	packet->AddPacketTag(tag);
	return static_cast<uint16_t>(sourcePort);
}

PsnRxDecision
RdmaHw::ReceiverCheckSeqPsnPath(Ptr<RdmaRxQueuePair> qp,
	                             uint32_t psn,
	                             uint32_t packetSize,
	                             const PsnPathTag &tag)
{
	uint32_t k = tag.GetK();
	NS_ASSERT_MSG(k != 0 && packetSize != 0, "invalid PSN-PATH packet metadata");
	if (!qp->psnPath.enabled) {
		qp->psnPath.enabled = true;
		qp->psnPath.k = k;
		qp->psnPath.localFpsn.resize(k);
		for (uint32_t logicalPath = 0; logicalPath < k; ++logicalPath) {
			qp->psnPath.localFpsn[logicalPath] = logicalPath;
		}
	}
	NS_ASSERT_MSG(qp->psnPath.k == k, "PSN-PATH K changed within a QP");

	uint32_t expectedPsn = GetPsnFromSeq(
	    static_cast<uint32_t>(qp->ReceiverNextExpectedSeq), m_mtu);
	uint32_t logicalPath = GetLogicalPath(psn, k);
	uint32_t packetFpsn = tag.GetFpsn();
	uint32_t &localFpsn = qp->psnPath.localFpsn[logicalPath];

	if (psn < expectedPsn) {
		return PsnRxDecision(PsnRxResult::DUPLICATE);
	}

	bool newMapping = packetFpsn > localFpsn;
	if (newMapping) {
		localFpsn = packetFpsn;
	}

	uint32_t seq = psn * m_mtu;
	if (psn == expectedPsn) {
		qp->ReceiverNextExpectedSeq += packetSize;
		for (;;) {
			auto next = qp->ooo_bitmap.find(
			    static_cast<uint32_t>(qp->ReceiverNextExpectedSeq));
			if (next == qp->ooo_bitmap.end()) {
				break;
			}
			qp->ReceiverNextExpectedSeq += next->second;
			qp->ooo_bitmap.erase(next);
			qp->ooo_bitmap_cnt = qp->ooo_bitmap_cnt == 0 ? 0 : qp->ooo_bitmap_cnt - 1;
			m_oooBufferChangeCallback(qp, qp->ooo_bitmap_cnt);
		}
		return PsnRxDecision(PsnRxResult::IN_ORDER);
	}

	bool bitmapOverflow = false;
	if (qp->ooo_bitmap.find(seq) == qp->ooo_bitmap.end()) {
		uint32_t distance = psn - expectedPsn;
		if (max_ooo_size != 0 && distance > max_ooo_size) {
			qp->bitmap_overflow_cnt++;
			bitmapOverflow = true;
		} else {
			qp->ooo_bitmap[seq] = packetSize;
			qp->ooo_bitmap_cnt++;
			m_oooBufferChangeCallback(qp, qp->ooo_bitmap_cnt);
			if (qp->ooo_win_max < qp->ooo_bitmap_cnt) {
				qp->ooo_win_max = qp->ooo_bitmap_cnt;
			}
		}
	}
	if (bitmapOverflow) {
		// The packet was not retained, so it must not be selectively ACKed.
		return PsnRxDecision(PsnRxResult::SAME_PATH_LOSS, true, psn);
	}

	bool remapFirstPacket = newMapping || packetFpsn == psn;
	if (remapFirstPacket) {
		return PsnRxDecision(PsnRxResult::REMAP_FIRST_PACKET);
	}

	bool oldMapping = packetFpsn < localFpsn;
	uint32_t prevPsn = 0;
	if (!GetSamePathPredecessor(psn, k, packetFpsn, prevPsn)) {
		return PsnRxDecision(oldMapping ? PsnRxResult::OLD_MAPPING_PACKET
		                                : PsnRxResult::CROSS_PATH_OOO);
	}

	uint32_t prevSeq = prevPsn * m_mtu;
	bool predecessorReceived = prevSeq < qp->ReceiverNextExpectedSeq
	                           || qp->ooo_bitmap.find(prevSeq) != qp->ooo_bitmap.end();
	if (predecessorReceived) {
		return PsnRxDecision(oldMapping ? PsnRxResult::OLD_MAPPING_PACKET
		                                : PsnRxResult::CROSS_PATH_OOO);
	}
	return PsnRxDecision(PsnRxResult::SAME_PATH_LOSS, true, prevPsn);
}

void
RdmaHw::HandlePsnPathNack(Ptr<RdmaQueuePair> qp,
	                       uint32_t startPsn,
	                       uint32_t endPsn)
{
	for (uint32_t psn = startPsn; psn <= endPsn; ++psn) {
		uint64_t seq = static_cast<uint64_t>(psn) * qp->psnPath.packetSize;
		if (seq >= qp->m_size) {
			break;
		}
		if (qp->retransQueue.find(seq) == qp->retransQueue.end()) {
			qp->retransQueue[seq] = qp->GetBytesLeftforSR(seq);
		}
		if (psn == UINT32_MAX) {
			break;
		}
	}
	TriggerTrans(qp);
}

void
RdmaHw::UpdatePsnPathFeedback(Ptr<RdmaQueuePair> qp,
	                           uint32_t psn,
	                           bool isNack,
	                           const PsnPathTag &tag)
{
	uint32_t logicalPath = GetLogicalPath(psn, qp->psnPath.k);
	if (tag.IsProbe()) {
		if (isNack) {
			HandleProbeNack(qp, logicalPath);
		} else {
			HandleProbeAck(qp, logicalPath);
		}
	} else if (isNack) {
		qp->psnPath.quality[logicalPath].nackCount++;
	} else {
		qp->psnPath.quality[logicalPath].ackCount++;
	}

	if (Simulator::Now() - qp->psnPath.lastEvaluation
	    >= NanoSeconds(qp->m_baseRtt)) {
		EvaluatePsnPaths(qp);
	}
}

void
RdmaHw::EvaluatePsnPaths(Ptr<RdmaQueuePair> qp)
{
	const double beta = 1.0;
	const double exploreThreshold = 2.0;
	const double removeThreshold = 0.0;
	for (uint32_t logicalPath = 0; logicalPath < qp->psnPath.k; ++logicalPath) {
		PsnPathQuality &quality = qp->psnPath.quality[logicalPath];
		if (quality.ackCount == 0 && quality.nackCount == 0) {
			continue;
		}
		quality.score = ComputePathScore(quality.ackCount, quality.nackCount, beta);
		PsnPathMappingState &mapping = qp->psnPath.mapping[logicalPath];
		uint32_t candidate = static_cast<uint32_t>(mapping.offset) + qp->psnPath.k;
		if (static_cast<uint32_t>(qp->psnPath.basePort) + logicalPath + candidate > 65535) {
			candidate = 0;
		}
		if (quality.score < removeThreshold) {
			CommitPathRemap(qp, logicalPath, static_cast<uint16_t>(candidate));
		} else if (quality.score < exploreThreshold && !mapping.probing) {
			StartPathProbe(qp, logicalPath, static_cast<uint16_t>(candidate));
		}
		quality.ackCount = 0;
		quality.nackCount = 0;
	}
	qp->psnPath.lastEvaluation = Simulator::Now();
}

void
RdmaHw::StartPathProbe(Ptr<RdmaQueuePair> qp,
	                    uint32_t logicalPath,
	                    uint16_t candidateOffset)
{
	NS_ASSERT(logicalPath < qp->psnPath.mapping.size());
	PsnPathMappingState &mapping = qp->psnPath.mapping[logicalPath];
	if (candidateOffset == mapping.offset) {
		return;
	}
	mapping.probing = true;
	mapping.candidateOffset = candidateOffset;
	mapping.probeStep = 10;
	mapping.packetsUntilProbe = mapping.probeStep;
	mapping.candidateAckCnt = 0;
}

void
RdmaHw::HandleProbeAck(Ptr<RdmaQueuePair> qp, uint32_t logicalPath)
{
	PsnPathMappingState &mapping = qp->psnPath.mapping[logicalPath];
	if (!mapping.probing) {
		return;
	}
	mapping.candidateAckCnt++;
	if (mapping.candidateAckCnt >= mapping.probeStep) {
		mapping.candidateAckCnt = 0;
		if (mapping.probeStep > 1) {
			mapping.probeStep--;
		}
		mapping.packetsUntilProbe = mapping.probeStep;
		if (mapping.probeStep == 1) {
			CommitPathRemap(qp, logicalPath, mapping.candidateOffset);
		}
	}
}

void
RdmaHw::HandleProbeNack(Ptr<RdmaQueuePair> qp, uint32_t logicalPath)
{
	PsnPathMappingState &mapping = qp->psnPath.mapping[logicalPath];
	mapping.probing = false;
	mapping.candidateAckCnt = 0;
	mapping.packetsUntilProbe = mapping.probeStep;
}

void
RdmaHw::CommitPathRemap(Ptr<RdmaQueuePair> qp,
	                     uint32_t logicalPath,
	                     uint16_t newOffset)
{
	NS_ASSERT(logicalPath < qp->psnPath.mapping.size());
	PsnPathMappingState &mapping = qp->psnPath.mapping[logicalPath];
	mapping.offset = newOffset;
	mapping.active = true;
	mapping.probing = false;
	mapping.candidateAckCnt = 0;
	mapping.currentNeedsBoundary = false;

	uint32_t nextPsn = GetPsnFromSeq(static_cast<uint32_t>(qp->snd_nxt),
	                                 qp->psnPath.packetSize);
	uint32_t remainder = nextPsn % qp->psnPath.k;
	nextPsn += (logicalPath + qp->psnPath.k - remainder) % qp->psnPath.k;
	mapping.fpsn = nextPsn;
}

void RdmaHw::AddHeader (Ptr<Packet> p, uint16_t protocolNumber){
	PppHeader ppp;
	ppp.SetProtocol (EtherToPpp (protocolNumber));
	p->AddHeader (ppp);
}
uint16_t RdmaHw::EtherToPpp (uint16_t proto){
	switch(proto){
		case 0x0800: return 0x0021;   //IPv4
		case 0x86DD: return 0x0057;   //IPv6
		default: NS_ASSERT_MSG (false, "PPP Protocol number not defined!");
	}
	return 0;
}

void RdmaHw::RecoverQueue(Ptr<RdmaQueuePair> qp){
	#ifdef GBN_INFO
		printf("[INFO:GBN][%ld][%u]\tSender receive NACK from %u (sport:%u), Go Back to %u\n", Simulator::Now().GetTimeStep(),this->m_node->GetId() , ip_to_node_id(qp->dip), qp->sport, qp->snd_una);
	#endif
	qp->snd_nxt = qp->snd_una;
}

void RdmaHw::QpComplete(Ptr<RdmaQueuePair> qp){
	// if(qp->m_src == 0 && qp->m_dest == 12)
	// 	printf("[QP_COMPLETE][%ld] flow from 0 to 12 completes\n", Simulator::Now().GetTimeStep());
	NS_ASSERT(!m_qpCompleteCallback.IsNull());
	if (m_cc_mode == 1){
		Simulator::Cancel(qp->mlx.m_eventUpdateAlpha);
		Simulator::Cancel(qp->mlx.m_eventDecreaseRate);
		Simulator::Cancel(qp->mlx.m_rpTimer);
	}
	#ifdef APS_V2
	#ifdef APS_PATH_SWITCHID_INFO
	if (m_lb_mode == 1 && TRACE && qp->sport == 10000) { // print switchID of path
		for (auto it = qp->aps.pathID2switch.begin(); it != qp->aps.pathID2switch.end(); ++it) {
			int nhop = qp->aps.pathID2switch[it->first].size();
			vector<uint32_t> switchID = qp->aps.pathID2switch[it->first];
			if (nhop == 3) {
				printf("[INFO:APS_PATH_SWITCHID] src:dst %u:%u, pathID %u %u %u %u\n", 
					qp->m_src, qp->m_dest, it->first, switchID[0], switchID[1], switchID[2]);
			} else if (nhop == 5) {
				printf("[INFO:APS_PATH_SWITCHID] src:dst %u:%u, pathID %u %u %u %u %u %u\n", 
					qp->m_src, qp->m_dest, it->first, switchID[0], switchID[1], switchID[2], switchID[3], switchID[4]);
			}
			
		}
	}
	#endif
	#endif
	// SR: cancel timeout event
    Simulator::Cancel(qp->m_retransEvent);
	qp->snd_una = qp->m_size;
    while(!qp->retransQueue.empty())
    {
        qp->retransQueue.erase(qp->retransQueue.begin());
    }
    while(!qp->tx_bitmap.empty())
    {
        qp->tx_bitmap.erase(qp->tx_bitmap.begin());
    }
    while(!qp->send_times.empty())
    {
        qp->send_times.erase(qp->send_times.begin());
    }		
	// This callback will log info
	// It may also delete the rxQp on the receiver
	NS_ASSERT(!m_qpCompleteCallback.IsNull());
	m_qpCompleteCallback(qp);

	qp->m_notifyAppFinish();

	// delete the qp
	DeleteQueuePair(qp);
}

void RdmaHw::SetLinkDown(Ptr<QbbNetDevice> dev){
	printf("RdmaHw: node:%u a link down\n", m_node->GetId());
}

void RdmaHw::AddTableEntry(Ipv4Address &dstAddr, uint32_t intf_idx, bool is_nvswitch){
	uint32_t dip = dstAddr.Get();
	if(is_nvswitch == false)
		m_rtTable[dip].push_back(intf_idx);
	else {
		m_rtTable_nxthop_nvswitch[dip].push_back(intf_idx);
	}
}

void RdmaHw::ClearTable(){
	m_rtTable.clear();
	m_rtTable_nxthop_nvswitch.clear();
}

void RdmaHw::RedistributeQp(){
	// clear old qpGrp
	for (uint32_t i = 0; i < m_nic.size(); i++){
		if (m_nic[i].dev == NULL)
			continue;
		m_nic[i].qpGrp->Clear();
	}

	// redistribute qp
	for (auto &it : m_qpMap){
		Ptr<RdmaQueuePair> qp = it.second;
		uint32_t nic_idx = GetNicIdxOfQp(qp);
		m_nic[nic_idx].qpGrp->AddQp(qp);
		// Notify Nic
		m_nic[nic_idx].dev->ReassignedQp(qp);
	}
}

Ptr<Packet> RdmaHw::GetNxtPacket(Ptr<RdmaQueuePair> qp){
	uint64_t seqToSend;
	uint64_t payLoadSizeToSend;
	bool isRetransmission = false;

	// SR: reconstruct normalTrans & reTrans 
	if (qp->snd_nxt == qp->snd_una){
        seqToSend = qp->snd_nxt;
		payLoadSizeToSend = qp->GetBytesLeft();
		if (m_mtu < payLoadSizeToSend)
			payLoadSizeToSend = m_mtu;
		qp->snd_nxt += payLoadSizeToSend;
    
        // Simulator::Cancel(qp->m_retransEvent); // 只有snd_una == 0， 收到新的ACK才重置定时器，并采用Go-Back-N的形式超时重传
		// qp->ReScheduleTimeoutTimer();
    }else{
		if (!qp->retransQueue.empty()){ // retransmit
			if (qp->snd_nxt == qp->snd_una){
				// std::cout << "enter retrans mode via timeout.\n";
			}else{
				// std::cout << "enter retrans mode via SACK.\n";
			}
			uint64_t seqOfPkg = qp->retransQueue.begin()->first;
			qp->retransQueue.erase(qp->retransQueue.begin());
			// get an eligible pkg in retrans queue 
			while (seqOfPkg < qp->snd_una && !qp->retransQueue.empty()){
				seqOfPkg = qp->retransQueue.begin()->first;
				qp->retransQueue.erase(qp->retransQueue.begin());
			}
			if (seqOfPkg < qp->snd_una){ // no eligible pkt in retrans queue
				#ifdef SR_SND_RT_LOG
				if(TRACE)
					printf("[LOG:SR_SND_RT][%ld][%u]\tseqs in retrans queue are not eligible, send new pkg.\n", Simulator::Now().GetTimeStep(), this->m_node->GetId());
				#endif
				seqToSend = qp->snd_nxt;
				payLoadSizeToSend = qp->GetBytesLeft();
				if (m_mtu < payLoadSizeToSend)
					payLoadSizeToSend = m_mtu;
				qp->snd_nxt += payLoadSizeToSend;
			}else{ // retransmit valid pkt
				isRetransmission = true;
				#ifdef SR_SND_RT_LOG
				if(TRACE)
					printf("[LOG:SR_SND_RT][%ld][%u]\tsend one pkg in retrans queue, seq %u.\n", Simulator::Now().GetTimeStep(), this->m_node->GetId(), seqOfPkg);
				#endif
				seqToSend = seqOfPkg;
				qp->retransNums++;
				payLoadSizeToSend = qp->GetBytesLeftforSR(seqToSend);
				if (m_mtu < payLoadSizeToSend)
					payLoadSizeToSend = m_mtu;
			}
            // Simulator::Cancel(qp->m_retransEvent); // 超时重传用于兜底，而不是每个重传的包都重置定时器
		    // qp->ReScheduleTimeoutTimer();
		
        }else{ // transmit new pkgs
			seqToSend = qp->snd_nxt;
			payLoadSizeToSend = qp->GetBytesLeft();
			if (m_mtu < payLoadSizeToSend)
				payLoadSizeToSend = m_mtu;
			qp->snd_nxt += payLoadSizeToSend;
			
            // Simulator::Cancel(qp->m_retransEvent); // 发送新包不能重置计时器
		    // qp->ReScheduleTimeoutTimer();
		}
	}
	#ifdef SR_SND_LOG
		if(TRACE)
		printf("[LOG:SR_SND][%ld][%u]\tSend pkg %u with size %u, send_next %lu, send_unack %lu\n", \
			Simulator::Now().GetTimeStep(), this->m_node->GetId(), seqToSend, payLoadSizeToSend, qp->snd_nxt, qp->snd_una);
	#endif
	#ifdef OOO_SR_INFO
		if (seqToSend == 5000 && qp->sport == 10004 && ip_to_node_id(qp->dip) == 48)
			printf("\n");
		printf("[INFO:OOO_SR][%ld][%u]\tSender send seq %u, sport %u dst %u\n", Simulator::Now().GetTimeStep(), this->m_node->GetId(), seqToSend, qp->sport, ip_to_node_id(qp->dip));
	#endif	
	Ptr<Packet> p = Create<Packet> (payLoadSizeToSend);
	#ifdef GBN_INFO
		printf("[INFO:GBN][%ld][%u]\tSender send seq %u, sport %u dst %u\n", Simulator::Now().GetTimeStep(), this->m_node->GetId(), seqToSend, qp->sport, ip_to_node_id(qp->dip));
	#endif

	// aps: init phase, round robin on ifIndex
	if (m_lb_mode == 1){
		FlowInfoTag fit;
		NS_ASSERT(!p->PeekPacketTag(fit));

	#ifdef APS_OLD
		if (!qp->aps.initIf2aps){ // TODO: 增加有效路径计数器
			if (qp->aps.m_pathToRCnt == 1) {
				if (qp->aps.m_ifIndex != 0 && qp->aps.m_ifIndex % m_apsDefaultPortCnt == 0)
					qp->aps.m_ifIndexAgg++;
			} else { // nic has received the first INT ACK
				if (qp->aps.m_ifIndex != 0 && qp->aps.m_ifIndex % qp->aps.m_pathToRCnt == 0)
					qp->aps.m_ifIndexAgg++;
			}
			qp->aps.m_ifIndex++; 
			#ifdef APS_INIT_RRB_INFO
				printf("[INFO:APS_INIT_RRB][%ld]\tSenderNode: %u, Round Robin ToR_ifIndex:%u, Agg_ifIndex:%u\n", Simulator::Now().GetTimeStep(), this->m_node->GetId(), qp->aps.m_ifIndex, qp->aps.m_ifIndexAgg);
			#endif
		} 
	#elif defined(APS_V2)
		if (!qp->aps.isFreezingMode && (qp->aps.exploreCnt > 0 ||
			m_updateFreq == 0 ||
			 qp->aps.m_numberOfValidPath == 0)) { // no cached path or do not update
			#ifdef APS_PROBE_INFO
			if (TRACE) {
				printf("[INFO:APS_PROBE][%ld][%u:%u] Selelct from random path\n", 
					Simulator::Now().GetTimeStep(), m_node->GetId(), qp->sport);
			}
			#endif
			if (qp->aps.apsBuffer.empty()) { // 初始化
				#ifdef APS_PROBE_INFO 
				if (TRACE) {
					printf("[INFO:APS_PROBE][%ld][%u] start probe\n", Simulator::Now().GetTimeStep(), m_node->GetId());
				} 
				#endif
				qp->aps.apsBuffer.resize(REPS_BUFFER_SIZE);
			}			
			qp->aps.exploreCnt = qp->aps.exploreCnt > 0 ? qp->aps.exploreCnt - 1 : 0;
			qp->aps.pathEV = rand() % EVS_SIZE;
			qp->aps.pathID = 0; // do not use pathID
			fit.SetFlowInfo(qp->aps.pathEV);
			p->AddPacketTag(fit);				
			qp->probePktCount++;

		} else { // select from cached path
			qp->aps.pathEV = GetNextIfIndexAps(qp);
			fit.SetFlowInfo(qp->aps.pathEV);
			p->AddPacketTag(fit);			
			qp->selectPathPktCount++;
			#ifdef APS_PROBE_INFO
			if (TRACE) {
				printf("[INFO:APS_PROBE][%ld][%u:%u] using cache path %u\n", 
					Simulator::Now().GetTimeStep(), m_node->GetId(), qp->sport, qp->aps.pathEV);
			}
			#endif
		} 
	
	#endif
		#ifdef APS_INIT_DEBUG
			// printf("[DEBUG:APS_INIT][%ld]\tSenderNode: %u, send pkgs on ifIndex %u ifIndexAgg %u\n", Simulator::Now().GetTimeStep(), this->m_node->GetId(), qp->aps.m_ifIndex, qp->aps.m_ifIndexAgg);
		#endif
	}

	// add SimpleSeqTsHeader
	SimpleSeqTsHeader seqTs;
	seqTs.SetSeq (seqToSend);
	seqTs.SetPG (qp->m_pg);
    if (m_lb_mode == 1){
	#ifdef APS_OLD	
		seqTs.ih.hop[0].SetPathId(qp->aps.m_ifIndex); // set the first hop's ifIndex
		seqTs.ih.hop[1].SetPathId(qp->aps.m_ifIndexAgg); // set the second hop's ifIndexAgg
	#elif defined(APS_V2)
		seqTs.ih.hop[0].SetPathId(qp->aps.pathEV); // 本应当是 seqTs.ih.SetEV。暂时用该实现
	#endif
	}
	p->AddHeader (seqTs);
	// add udp header
	UdpHeader udpHeader;
	udpHeader.SetDestinationPort (qp->dport);
	uint16_t packetSourcePort = qp->sport;
	if (m_lb_mode == 6) {
		uint32_t psn = GetPsnFromSeq(static_cast<uint32_t>(seqToSend), m_mtu);
		packetSourcePort = ApplyPsnPathMapping(qp, p, psn, isRetransmission);
	}
	udpHeader.SetSourcePort (packetSourcePort);
	p->AddHeader (udpHeader);
	// add ipv4 header
	Ipv4Header ipHeader;
	ipHeader.SetSource (qp->sip);
	ipHeader.SetDestination (qp->dip);
	ipHeader.SetProtocol (0x11);
	ipHeader.SetPayloadSize (p->GetSize());
	if (m_lb_mode == 3)
		ipHeader.SetTtl (qp->m_ttl);
	else
		ipHeader.SetTtl (64);
	// nvls <-> ToS, ToS = 1 -> NVLS enable
	if(qp->nvls_enable == 1) ipHeader.SetTos (4);
	else ipHeader.SetTos (0);
	ipHeader.SetIdentification (qp->m_ipid);
	p->AddHeader(ipHeader);
	// add ppp header
	PppHeader ppp;
	ppp.SetProtocol (0x0021); // EtherToPpp(0x800), see point-to-point-net-device.cc
	p->AddHeader (ppp);

    // letflow: attach Stat Tag
	if (m_lb_mode == 4) {
		{
			FlowIDNUMTag fint;
			if (!p->PeekPacketTag(fint)) {
				fint.SetId(qp->m_flow_id);
				fint.SetFlowSize(qp->m_size);
				p->AddPacketTag(fint);
			}
			FlowStatTag fst;
			uint64_t size = qp->m_size;
			if (!p->PeekPacketTag(fst)) {
				if (size < m_mtu && qp->snd_nxt + payLoadSizeToSend >= qp->m_size) {
					fst.SetType(FlowStatTag::FLOW_START_AND_END);
				} else if (qp->snd_nxt + payLoadSizeToSend >= qp->m_size) {
					fst.SetType(FlowStatTag::FLOW_END);
				} else if (qp->snd_nxt == 0) {
					fst.SetType(FlowStatTag::FLOW_START);
				} else {
					fst.SetType(FlowStatTag::FLOW_NOTEND);
				}
				fst.setInitiatedTime(Simulator::Now().GetSeconds());
				p->AddPacketTag(fst);
			}
		}
	}

	// add lb_mode tag
	FlowTypeTag ftt;
	if (!p->PeekPacketTag(ftt)) {
		ftt.SetFlowType(m_lb_mode);
		p->AddPacketTag(ftt);
	}

	// rps: attch random EV Tag
	if (m_lb_mode == 2) {
		FlowInfoTag fit;
		if (!p->PeekPacketTag(fit)) {

			fit.SetFlowInfo(rand() % EVS_SIZE);

			p->AddPacketTag(fit);
			qp->probePktCount++;
		}

	}

	// reps: attach EV Tag
	if (m_lb_mode == 5) {
		FlowInfoTag fit;
		if (!p->PeekPacketTag(fit)) {

			if (qp->reps.exploreCnt > 0 || // 强制探索一个BDP
				qp->reps.repsBuffer.empty() || // 初始化
				(qp->reps.numberOfValidEVs == 0 && !qp->reps.isFreezingMode)) { // 网络拥塞，消耗完一个BDP仍然收不到有效EV，继续探索
					
					if (qp->reps.repsBuffer.empty()) { // 初始化
						#ifdef REPS_PROBE_INFO 
						if (TRACE) {
							printf("[INFO:REPS_PROBE][%ld][%u] start probe\n", Simulator::Now().GetTimeStep(), m_node->GetId());
						} 
						#endif
						qp->reps.repsBuffer.resize(REPS_BUFFER_SIZE);
					}
					uint32_t ev = rand() % EVS_SIZE; // 13340 21993 50587
					fit.SetFlowInfo(ev);
					fit.SetSwitchPort(0);
					// fit.SetFlowInfo(qp->rr_cnt++ % EVS_SIZE);
					qp->reps.exploreCnt = qp->reps.exploreCnt > 0 ? qp->reps.exploreCnt - 1 : 0;
					qp->probePktCount++;
					#ifdef REPS_PROBE_INFO 				
					if (TRACE) {
						printf("[INFO:REPS_PROBE][%ld][%u] random probe %u, exploreCnt: %u\n", Simulator::Now().GetTimeStep(), m_node->GetId(), ev, qp->reps.exploreCnt);
					}				
					#endif

			} else { // 存在有效EV
				uint32_t ev = getNextEV(qp);
				fit.SetFlowInfo(ev);
				fit.SetSwitchPort(0);
				#ifdef REPS_PROBE_INFO 				
				if (TRACE) {
					printf("[INFO:REPS_PROBE][%ld][%u] get from ev cache %u, exploreCnt: %u\t", Simulator::Now().GetTimeStep(), m_node->GetId(), ev, qp->reps.exploreCnt);
					for (int i = 0; i < REPS_BUFFER_SIZE; i++) {
						if (qp->reps.repsBuffer[i].isValid) {
							printf("%u(%u) ", qp->reps.repsBuffer[i].cachedEV, qp->reps.repsBuffer[i].switch_port);
						}
					}
					printf("\n");
				}
				#endif
				qp->selectPathPktCount++;
			}

			p->AddPacketTag(fit);
		}

	}
	
	// 插入新发送记录
	auto send_record = qp->tx_bitmap.find(seqToSend);
	if(send_record != qp->tx_bitmap.end()){
		if (m_lb_mode == 6 && isRetransmission) {
			// PSN-PATH NACK retransmission replaces one outstanding copy.
			// RemoveSendRecord keeps inflight unchanged when RTO already removed
			// the send-time entry, and otherwise prevents double accounting.
			qp->RemoveSendRecord(seqToSend);
		} else {
			qp->DelFromSendTimes(send_record->second.send_time, seqToSend);
			qp->tx_bitmap.erase(seqToSend);
		}
	} // 删除已经超时的旧记录，插入新记录
	qp->CreateSendRecord(seqToSend, payLoadSizeToSend);

	qp->m_ipid++;

	qp->ReScheduleTimeoutTimer(Simulator::Now()); // 每次发包检查更新定时器

	if (!qp->IsFinished() && !qp->send_times.empty()) {
		NS_ASSERT_MSG(qp->m_retransEvent.IsRunning() || qp->rtx_timeout_pending,
					"QP has outstanding packets but no RTO timer");
	}

	// if (qp->m_src == 0 && qp->m_dest == 12)
	// 	printf("[SEND_PKT][%ld] send packet from %u to %u, seq %lu\n" , Simulator::Now().GetTimeStep(), qp->m_src, qp->m_dest, seqToSend);

	if (p->GetSize() > qp->fullMtu) {
		qp->fullMtu = p->GetSize();
		#ifdef MPRDMA_INFO
		if(TRACE)
			printf("[MPRDMA:SET][%ld]\tUpdate minCwnd to %u\n", Simulator::Now().GetTimeStep(), qp->fullMtu);
		#endif
	}
	qp->inflight += qp->fullMtu;

	// return
	return p;
}

void RdmaHw::PktSent(Ptr<RdmaQueuePair> qp, Ptr<Packet> pkt, Time interframeGap){
	qp->lastPktSize = pkt->GetSize();
	UpdateNextAvail(qp, interframeGap, pkt->GetSize());
}

void RdmaHw::UpdateNextAvail(Ptr<RdmaQueuePair> qp, Time interframeGap, uint32_t pkt_size){
	Time sendingTime;
	if (m_rateBound)
		sendingTime = interframeGap + qp->m_rate.CalculateBytesTxTime(pkt_size);
	else
		sendingTime = interframeGap + qp->m_max_rate.CalculateBytesTxTime(pkt_size);
	qp->m_nextAvail = Simulator::Now() + sendingTime;
}

void RdmaHw::ChangeRate(Ptr<RdmaQueuePair> qp, DataRate new_rate){
	#if 1
	Time sendingTime = qp->m_rate.CalculateBytesTxTime(qp->lastPktSize);
	Time new_sendintTime = new_rate.CalculateBytesTxTime(qp->lastPktSize);
	qp->m_nextAvail = qp->m_nextAvail + new_sendintTime - sendingTime;
	// update nic's next avail event
	uint32_t nic_idx = GetNicIdxOfQp(qp);
	m_nic[nic_idx].dev->UpdateNextAvail(qp->m_nextAvail);
	#endif

	// change to new rate
	qp->m_rate = new_rate;
}
/**
 * when nic send a packet, update the bytes it has sent
*/
void RdmaHw::UpdateTxBytes(uint32_t port_id, uint64_t bytes){
	tx_bytes[port_id] += bytes;
}
/**
 * output format:
 * time, host_id, port_id, bandwidth
*/
void RdmaHw::PrintHostBW(FILE* bw_output, uint32_t bw_mon_interval){
	for(int i = 0; i < m_nic.size(); ++i){
		if(tx_bytes[i] == last_tx_bytes[i]){
			continue;
		}
		double bw = (tx_bytes[i] - last_tx_bytes[i]) * 8 * 1e6 / (bw_mon_interval); // bit/s
		bw = bw*1.0 / 1e9; // Gbps
		fprintf(bw_output, "%lu, %u, %u, %f\n", Simulator::Now().GetTimeStep(), m_node->GetId(), i, bw);
		fflush(bw_output);
		last_tx_bytes[i] = tx_bytes[i];
	}
}
/**
 * output format:
 * time, src, dst, sport, dport, size, rate
*/
void RdmaHw::PrintRxQpOoO(FILE* ooo_output){
	std::unordered_map<uint64_t, Ptr<RdmaRxQueuePair>>::iterator it = m_rxQpMap.begin();
	for(; it != m_rxQpMap.end(); it++){
		Ptr<RdmaRxQueuePair> RxQp = it->second;
		uint64_t key = it->first;
		if(RxQp->ooo_win_max == last_qp_ooo[key]){
			continue;
		}
		fprintf(ooo_output, "%ld %u %u %u %u %u\n", Simulator::Now().GetTimeStep(),
				ip_to_node_id(RxQp->dip), ip_to_node_id(RxQp->sip), RxQp->dport, RxQp->sport, RxQp->ooo_win_max);
		fflush(ooo_output);
		last_qp_ooo[key] = RxQp->ooo_win_max;
		RxQp->ooo_win_max = 0; // reset
	}
}
/**
 * output format:
 * time, src, dst, sport, dport, size, rate
*/
void RdmaHw::PrintQPRate(FILE* rate_output){
	std::unordered_map<uint64_t, Ptr<RdmaQueuePair>>::iterator it = m_qpMap.begin();
	for(; it != m_qpMap.end(); it++){
		Ptr<RdmaQueuePair> qp = it->second;
		uint64_t key = it->first;
		if(qp->m_rate.GetBitRate() == last_qp_rate[key]){
			continue;
		}
		fprintf(rate_output, "%lu, %u, %u, %u, %u, %lu, %lu\n", Simulator::Now().GetTimeStep(), qp->m_src, qp->m_dest, qp->sport, qp->dport, qp->m_size, qp->m_rate.GetBitRate());
		fflush(rate_output);
		last_qp_rate[key] = qp->m_rate.GetBitRate();
	}
}
/**
 * output format:
 * time, src, dst, sport, dport, size, cnp_number
*/
void RdmaHw::PrintQPCnpNumber(FILE* cnp_output){
	std::unordered_map<uint64_t, Ptr<RdmaQueuePair>>::iterator it = m_qpMap.begin();
	for(; it != m_qpMap.end(); it++){
		Ptr<RdmaQueuePair> qp = it->second;
		uint64_t key = it->first;
		if(qp_cnp[key] != last_qp_cnp[key]){
			fprintf(cnp_output, "%lu, %u, %u, %u, %u, %lu, %u\n", Simulator::Now().GetTimeStep(), qp->m_src, qp->m_dest, qp->sport, qp->dport, qp->m_size, qp_cnp[key]);
			fflush(cnp_output);
			last_qp_cnp[key] = qp_cnp[key];
		}
	}
}
/**
 * output format:
 * time, src, dst, pathID
*/
void RdmaHw::PrintPathSelected(FILE* aps_selected_output){
	std::unordered_map<uint64_t, Ptr<RdmaQueuePair>>::iterator it = m_qpMap.begin();
	for(; it != m_qpMap.end(); it++){
		Ptr<RdmaQueuePair> qp = it->second;
		uint64_t key = it->first;
		if (qp->aps.pathID == 0) {
			continue;
		}
		fprintf(aps_selected_output, "%lu %u %u %u\n", Simulator::Now().GetTimeStep(), qp->m_src, qp->m_dest, qp->aps.pathID);
		fflush(aps_selected_output);
	}
}
/**
 * output format:			
 * time, src, dst, sport, dport, tor_port, agg_port
*/
struct Interface {
  uint32_t idx;
  bool up;
  uint64_t delay;
  uint64_t bw;

  Interface() : idx(0), up(false) {}
};
void RdmaHw::PrintAPSSelected(FILE* aps_accuracy_output, 
	std::map<Ptr<Node>, std::map<Ptr<Node>, std::vector<std::pair<Ptr<Node>, uint32_t> >>> &Host, 
		std::map<Ptr<Node>, std::map<Ptr<Node>, std::vector<std::pair<Ptr<Node>, uint32_t> >>> &NetSwitch){
	std::unordered_map<uint64_t, Ptr<RdmaQueuePair>>::iterator it = m_qpMap.begin();
	for(; it != m_qpMap.end(); it++){
		Ptr<RdmaQueuePair> qp = it->second;
		uint64_t key = it->first;
		if(qp->aps.m_ifIndex == last_aps_selected[key].first && 
			qp->aps.m_ifIndexAgg == last_aps_selected[key].second){
			continue;
		}

		last_aps_selected[key].first == qp->aps.m_ifIndex;
		last_aps_selected[key].second == qp->aps.m_ifIndexAgg;

		Ptr<Node> src, dst, firstHop, nextHop;
		vector<uint32_t> hop;
		vector<uint32_t> port;
		int hopCnt = 0;
		// get the first ToR Switch
		for(auto i = Host.begin(); i != Host.end(); ++i)
			if(i->first->GetId() == qp->m_src) {
				auto table = i->second;
				for(auto j = table.begin(); j != table.end(); ++j){
					if(j->first->GetId() == qp->m_dest) {
						auto entries = j->second;
						firstHop = entries[0].first;
						break;
					}
				}
				break;
			}
		// #ifdef NS3_MTP
		// MtpInterface::explicitCriticalSection cs;
		// #endif		
		// [currentSrc][dstHost], pair<[nexthopNode], [overWhichPort]>
		src = firstHop;
		for(auto i = NetSwitch.begin(); i != NetSwitch.end();){
			if(src->GetNodeType() == 0) break;
			if(i->first->GetId() == src->GetId()) {
				auto table = i->second;
				for(auto j = table.begin(); j != table.end(); ++j){
					if(j->first->GetId() == qp->m_dest) {
						auto entries = j->second;
						uint32_t idx = 0;
						if(hopCnt == 0) {
							idx = qp->aps.m_ifIndex % entries.size();
						} else if(hopCnt == 1) {
							idx = qp->aps.m_ifIndexAgg % entries.size();
						}
						hopCnt++;
						hop.push_back(src->GetId());
						port.push_back(entries[idx].second);
						src = entries[idx].first;
						break;
					}
				}
				i = NetSwitch.begin();
			} else i++;
		}
		// for(auto i = NetSwitch.begin(); i != NetSwitch.end(); ++i) {

		// }
			
		if (hopCnt == 1) {
			fprintf(aps_accuracy_output, "%lu %u %u %u %u %u:%u\n", Simulator::Now().GetTimeStep(), 
				qp->m_src, qp->m_dest, qp->sport, qp->dport, hop[0], port[0]);
			fflush(aps_accuracy_output);
		} else if(hopCnt == 3) {
			fprintf(aps_accuracy_output, "%lu %u %u %u %u %u:%u %u:%u %u:%u\n", Simulator::Now().GetTimeStep(), 
				qp->m_src, qp->m_dest, qp->sport, qp->dport, hop[0], port[0], hop[1], port[1], hop[2], port[2]);
			fflush(aps_accuracy_output);	
		} else if(hopCnt == 5) {
			fprintf(aps_accuracy_output, "%lu %u %u %u %u %u:%u %u:%u %u:%u %u:%u %u:%u\n", Simulator::Now().GetTimeStep(), 
				qp->m_src, qp->m_dest, qp->sport, qp->dport, hop[0], port[0], hop[1], port[1], hop[2], port[2], hop[3], port[3], hop[4], port[4]);
			fflush(aps_accuracy_output);	
		} else {
			fprintf(aps_accuracy_output, "error hopCnt:%d\n", hopCnt);
			fflush(aps_accuracy_output);
		}

		// #ifdef NS3_MTP
		// cs.ExitSection();
		// #endif				


	}
}
#define PRINT_LOG 0
/******************************
 * Mellanox's version of DCQCN
 *****************************/
void RdmaHw::UpdateAlphaMlx(Ptr<RdmaQueuePair> q){
	#if PRINT_LOG
	//printf("%lu alpha update: %08x %08x %u %u %.6lf->", Simulator::Now().GetTimeStep(), q->sip.Get(), q->dip.Get(), q->sport, q->dport, q->mlx.m_alpha);
	#endif
	if (q->mlx.m_alpha_cnp_arrived){
		q->mlx.m_alpha = (1 - m_g)*q->mlx.m_alpha + m_g; 	//binary feedback
	}else {
		q->mlx.m_alpha = (1 - m_g)*q->mlx.m_alpha; 	//binary feedback
	}
	#if PRINT_LOG
	//printf("%.6lf\n", q->mlx.m_alpha);
	#endif
	q->mlx.m_alpha_cnp_arrived = false; // clear the CNP_arrived bit
	ScheduleUpdateAlphaMlx(q);
}
void RdmaHw::ScheduleUpdateAlphaMlx(Ptr<RdmaQueuePair> q){
	q->mlx.m_eventUpdateAlpha = Simulator::Schedule(MicroSeconds(m_alpha_resume_interval), &RdmaHw::UpdateAlphaMlx, this, q);
}

void RdmaHw::cnp_received_mlx(Ptr<RdmaQueuePair> q){
	q->mlx.m_alpha_cnp_arrived = true; // set CNP_arrived bit for alpha update
	q->mlx.m_decrease_cnp_arrived = true; // set CNP_arrived bit for rate decrease
	if (q->mlx.m_first_cnp){
		// init alpha
		q->mlx.m_alpha = 1;
		q->mlx.m_alpha_cnp_arrived = false;
		// schedule alpha update
		ScheduleUpdateAlphaMlx(q);
		// schedule rate decrease
		ScheduleDecreaseRateMlx(q, 1); // add 1 ns to make sure rate decrease is after alpha update
		// set rate on first CNP
		q->mlx.m_targetRate = q->m_rate = m_rateOnFirstCNP * q->m_rate;
		q->mlx.m_first_cnp = false;
	}
}


void RdmaHw::CheckRateDecreaseMlx(Ptr<RdmaQueuePair> q){
	ScheduleDecreaseRateMlx(q, 0);
	if (q->mlx.m_decrease_cnp_arrived){
		#if PRINT_LOG
		printf("%lu rate dec: %08x %08x %u %u (%0.3lf %.3lf)->", Simulator::Now().GetTimeStep(), q->sip.Get(), q->dip.Get(), q->sport, q->dport, q->mlx.m_targetRate.GetBitRate() * 1e-9, q->m_rate.GetBitRate() * 1e-9);
		#endif
		bool clamp = true;
		if (!m_EcnClampTgtRate){
			if (q->mlx.m_rpTimeStage == 0)
				clamp = false;
		}
		if (clamp)
			q->mlx.m_targetRate = q->m_rate;
		q->m_rate = std::max(m_minRate, q->m_rate * (1 - q->mlx.m_alpha / 2));
		// reset rate increase related things
		q->mlx.m_rpTimeStage = 0;
		q->mlx.m_decrease_cnp_arrived = false;
		Simulator::Cancel(q->mlx.m_rpTimer);
		q->mlx.m_rpTimer = Simulator::Schedule(MicroSeconds(m_rpgTimeReset), &RdmaHw::RateIncEventTimerMlx, this, q);
		#if PRINT_LOG
		printf("(%.3lf %.3lf)\n", q->mlx.m_targetRate.GetBitRate() * 1e-9, q->m_rate.GetBitRate() * 1e-9);
		#endif
	}
}
void RdmaHw::ScheduleDecreaseRateMlx(Ptr<RdmaQueuePair> q, uint32_t delta){
	q->mlx.m_eventDecreaseRate = Simulator::Schedule(MicroSeconds(m_rateDecreaseInterval) + NanoSeconds(delta), &RdmaHw::CheckRateDecreaseMlx, this, q);
}

void RdmaHw::RateIncEventTimerMlx(Ptr<RdmaQueuePair> q){
	q->mlx.m_rpTimer = Simulator::Schedule(MicroSeconds(m_rpgTimeReset), &RdmaHw::RateIncEventTimerMlx, this, q);
	RateIncEventMlx(q);
	q->mlx.m_rpTimeStage++;
}
void RdmaHw::RateIncEventMlx(Ptr<RdmaQueuePair> q){
	// check which increase phase: fast recovery, active increase, hyper increase
	if (q->mlx.m_rpTimeStage < m_rpgThreshold){ // fast recovery
		FastRecoveryMlx(q);
	}else if (q->mlx.m_rpTimeStage == m_rpgThreshold){ // active increase
		ActiveIncreaseMlx(q);
	}else { // hyper increase
		HyperIncreaseMlx(q);
	}
}

void RdmaHw::FastRecoveryMlx(Ptr<RdmaQueuePair> q){
	#if PRINT_LOG
	printf("%lu fast recovery: %08x %08x %u %u (%0.3lf %.3lf)->", Simulator::Now().GetTimeStep(), q->sip.Get(), q->dip.Get(), q->sport, q->dport, q->mlx.m_targetRate.GetBitRate() * 1e-9, q->m_rate.GetBitRate() * 1e-9);
	#endif
	q->m_rate = (q->m_rate / 2) + (q->mlx.m_targetRate / 2);
	#if PRINT_LOG
	printf("(%.3lf %.3lf)\n", q->mlx.m_targetRate.GetBitRate() * 1e-9, q->m_rate.GetBitRate() * 1e-9);
	#endif
}
void RdmaHw::ActiveIncreaseMlx(Ptr<RdmaQueuePair> q){
	#if PRINT_LOG
	printf("%lu active inc: %08x %08x %u %u (%0.3lf %.3lf)->", Simulator::Now().GetTimeStep(), q->sip.Get(), q->dip.Get(), q->sport, q->dport, q->mlx.m_targetRate.GetBitRate() * 1e-9, q->m_rate.GetBitRate() * 1e-9);
	#endif
	// get NIC
	uint32_t nic_idx = GetNicIdxOfQp(q);
	Ptr<QbbNetDevice> dev = m_nic[nic_idx].dev;
	// increate rate
	q->mlx.m_targetRate += m_rai;
	if (q->mlx.m_targetRate > dev->GetDataRate())
		q->mlx.m_targetRate = dev->GetDataRate();
	q->m_rate = (q->m_rate / 2) + (q->mlx.m_targetRate / 2);
	#if PRINT_LOG
	printf("(%.3lf %.3lf)\n", q->mlx.m_targetRate.GetBitRate() * 1e-9, q->m_rate.GetBitRate() * 1e-9);
	#endif
}
void RdmaHw::HyperIncreaseMlx(Ptr<RdmaQueuePair> q){
	#if PRINT_LOG
	printf("%lu hyper inc: %08x %08x %u %u (%0.3lf %.3lf)->", Simulator::Now().GetTimeStep(), q->sip.Get(), q->dip.Get(), q->sport, q->dport, q->mlx.m_targetRate.GetBitRate() * 1e-9, q->m_rate.GetBitRate() * 1e-9);
	#endif
	// get NIC
	uint32_t nic_idx = GetNicIdxOfQp(q);
	Ptr<QbbNetDevice> dev = m_nic[nic_idx].dev;
	// increate rate
	q->mlx.m_targetRate += m_rhai;
	if (q->mlx.m_targetRate > dev->GetDataRate())
		q->mlx.m_targetRate = dev->GetDataRate();
	q->m_rate = (q->m_rate / 2) + (q->mlx.m_targetRate / 2);
	#if PRINT_LOG
	printf("(%.3lf %.3lf)\n", q->mlx.m_targetRate.GetBitRate() * 1e-9, q->m_rate.GetBitRate() * 1e-9);
	#endif
}

/**
 * @brief Flow Bender receives a CNP packet and increases the TTL of the queue pair.
 */
void RdmaHw::cnp_received_flow_bender(Ptr<RdmaQueuePair> qp, uint32_t cnp){
	if (qp->m_rttTick == 0) {
		qp->m_rttTick = Simulator::Now().GetTimeStep() + qp->m_baseRtt;
	}
 	qp->m_totalBytes += m_mtu;
    if (cnp) qp->m_markedBytes += m_mtu;

	if (qp->m_rttTick <= Simulator::Now().GetTimeStep()) {
		double flow_bender_f = static_cast<double> (qp->m_markedBytes) / qp->m_totalBytes;
		if (flow_bender_f > m_flow_bender_T) {
			qp->m_numCongestionRtt ++; // continuous congestion
			if (qp->m_numCongestionRtt >= m_flow_bender_N) {
				#ifdef FLOWBENDER_INFO
					printf("[INFO:FLOWBENDER][%ld][%u]\tFlowBender: too much ECN from %u (sport: %u), seq %u switching path, m_ttl %u\n", 
						Simulator::Now().GetTimeStep(), this->m_node->GetId(), ip_to_node_id(qp->dip), qp->sport, qp->snd_nxt, qp->m_ttl);
				#endif			
				qp->m_numCongestionRtt = 0;
				(qp->m_ttl)++;

			}
		} else {
			qp->m_numCongestionRtt = 0;
		}
		qp->m_totalBytes = 0;
		qp->m_markedBytes = 0;
		qp->m_rttTick = Simulator::Now().GetTimeStep() + qp->m_baseRtt;
	}

}

/***********************
 * High Precision CC
 ***********************/
void RdmaHw::HandleAckHp(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch){
	uint64_t ack_seq = ch.ack.seq;
	// update rate
	if (ack_seq > qp->hp.m_lastUpdateSeq){ // if full RTT feedback is ready, do full update
		UpdateRateHp(qp, p, ch, false);
	}else{ // do fast react
		FastReactHp(qp, p, ch);
	}
}

void RdmaHw::UpdateRateHp(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch, bool fast_react){
	uint64_t next_seq = qp->snd_nxt;
	#if PRINT_LOG
	bool print = !fast_react || true;
	#endif
	if (qp->hp.m_lastUpdateSeq == 0){ // first RTT
		qp->hp.m_lastUpdateSeq = next_seq;
		// store INT
		IntHeader &ih = ch.ack.ih;
		NS_ASSERT(ih.nhop <= IntHeader::maxHop);
		for (uint32_t i = 0; i < ih.nhop; i++)
			qp->hp.hop[i] = ih.hop[i];
		#if PRINT_LOG
		if (print){
			printf("%lu %s %08x %08x %u %u [%u,%u,%u]", Simulator::Now().GetTimeStep(), fast_react? "fast" : "update", qp->sip.Get(), qp->dip.Get(), qp->sport, qp->dport, qp->hp.m_lastUpdateSeq, ch.ack.seq, next_seq);
			for (uint32_t i = 0; i < ih.nhop; i++)
				printf(" %u %lu %lu", ih.hop[i].GetQlen(), ih.hop[i].GetBytes(), ih.hop[i].GetTime());
			printf("\n");
		}
		#endif
	}else {
		// check packet INT
		IntHeader &ih = ch.ack.ih;
		if (ih.nhop <= IntHeader::maxHop){
			double max_c = 0;
			// bool inStable = false;
			#if PRINT_LOG
			if (print)
				printf("%lu %s %08x %08x %u %u [%u,%u,%u]", Simulator::Now().GetTimeStep(), fast_react? "fast" : "update", qp->sip.Get(), qp->dip.Get(), qp->sport, qp->dport, qp->hp.m_lastUpdateSeq, ch.ack.seq, next_seq);
			#endif
			// check each hop
			double U = 0;
			uint64_t dt = 0;
			bool updated[IntHeader::maxHop] = {false}, updated_any = false;
			NS_ASSERT(ih.nhop <= IntHeader::maxHop);
			for (uint32_t i = 0; i < ih.nhop; i++){
				if (m_sampleFeedback){
					if (ih.hop[i].GetQlen() == 0 && fast_react)
						continue;
				}
				updated[i] = updated_any = true;
				#if PRINT_LOG
				if (print)
					printf(" %u(%u) %lu(%lu) %lu(%lu)", ih.hop[i].GetQlen(), qp->hp.hop[i].GetQlen(), ih.hop[i].GetBytes(), qp->hp.hop[i].GetBytes(), ih.hop[i].GetTime(), qp->hp.hop[i].GetTime());
				#endif
				uint64_t tau = ih.hop[i].GetTimeDelta(qp->hp.hop[i]);;
				double duration = tau * 1e-9;
				double txRate = (ih.hop[i].GetBytesDelta(qp->hp.hop[i])) * 8 / duration;
				double u = txRate / ih.hop[i].GetLineRate() + (double)std::min(ih.hop[i].GetQlen(), qp->hp.hop[i].GetQlen()) * qp->m_max_rate.GetBitRate() / ih.hop[i].GetLineRate() /qp->m_win;
				#if PRINT_LOG
				if (print)
					printf(" %.3lf %.3lf", txRate, u);
				#endif
				if (!m_multipleRate){
					// for aggregate (single R)
					if (u > U){
						U = u;
						dt = tau;
					}
				}else {
					// for per hop (per hop R)
					if (tau > qp->m_baseRtt)
						tau = qp->m_baseRtt;
					qp->hp.hopState[i].u = (qp->hp.hopState[i].u * (qp->m_baseRtt - tau) + u * tau) / double(qp->m_baseRtt);
				}
				qp->hp.hop[i] = ih.hop[i];
			}

			DataRate new_rate;
			int32_t new_incStage;
			DataRate new_rate_per_hop[IntHeader::maxHop];
			int32_t new_incStage_per_hop[IntHeader::maxHop];
			if (!m_multipleRate){
				// for aggregate (single R)
				if (updated_any){
					if (dt > qp->m_baseRtt)
						dt = qp->m_baseRtt;
					qp->hp.u = (qp->hp.u * (qp->m_baseRtt - dt) + U * dt) / double(qp->m_baseRtt);
					max_c = qp->hp.u / m_targetUtil;

					if (max_c >= 1 || qp->hp.m_incStage >= m_miThresh){
						new_rate = qp->hp.m_curRate / max_c + m_rai;
						new_incStage = 0;
					}else{
						new_rate = qp->hp.m_curRate + m_rai;
						new_incStage = qp->hp.m_incStage+1;
					}
					if (new_rate < m_minRate)
						new_rate = m_minRate;
					if (new_rate > qp->m_max_rate)
						new_rate = qp->m_max_rate;
					#if PRINT_LOG
					if (print)
						printf(" u=%.6lf U=%.3lf dt=%u max_c=%.3lf", qp->hp.u, U, dt, max_c);
					#endif
					#if PRINT_LOG
					if (print)
						printf(" rate:%.3lf->%.3lf\n", qp->hp.m_curRate.GetBitRate()*1e-9, new_rate.GetBitRate()*1e-9);
					#endif
				}
			}else{
				// for per hop (per hop R)
				new_rate = qp->m_max_rate;
				for (uint32_t i = 0; i < ih.nhop; i++){
					if (updated[i]){
						double c = qp->hp.hopState[i].u / m_targetUtil;
						if (c >= 1 || qp->hp.hopState[i].incStage >= m_miThresh){
							new_rate_per_hop[i] = qp->hp.hopState[i].Rc / c + m_rai;
							new_incStage_per_hop[i] = 0;
						}else{
							new_rate_per_hop[i] = qp->hp.hopState[i].Rc + m_rai;
							new_incStage_per_hop[i] = qp->hp.hopState[i].incStage+1;
						}
						// bound rate
						if (new_rate_per_hop[i] < m_minRate)
							new_rate_per_hop[i] = m_minRate;
						if (new_rate_per_hop[i] > qp->m_max_rate)
							new_rate_per_hop[i] = qp->m_max_rate;
						// find min new_rate
						if (new_rate_per_hop[i] < new_rate)
							new_rate = new_rate_per_hop[i];
						#if PRINT_LOG
						if (print)
							printf(" [%u]u=%.6lf c=%.3lf", i, qp->hp.hopState[i].u, c);
						#endif
						#if PRINT_LOG
						if (print)
							printf(" %.3lf->%.3lf", qp->hp.hopState[i].Rc.GetBitRate()*1e-9, new_rate.GetBitRate()*1e-9);
						#endif
					}else{
						if (qp->hp.hopState[i].Rc < new_rate)
							new_rate = qp->hp.hopState[i].Rc;
					}
				}
				#if PRINT_LOG
				printf("\n");
				#endif
			}
			if (updated_any)
				ChangeRate(qp, new_rate);
			if (!fast_react){
				if (updated_any){
					qp->hp.m_curRate = new_rate;
					qp->hp.m_incStage = new_incStage;
				}
				if (m_multipleRate){
					// for per hop (per hop R)
					for (uint32_t i = 0; i < ih.nhop; i++){
						if (updated[i]){
							qp->hp.hopState[i].Rc = new_rate_per_hop[i];
							qp->hp.hopState[i].incStage = new_incStage_per_hop[i];
						}
					}
				}
			}
		}
		if (!fast_react){
			if (next_seq > qp->hp.m_lastUpdateSeq)
				qp->hp.m_lastUpdateSeq = next_seq; //+ rand() % 2 * m_mtu;
		}
	}
}

void RdmaHw::FastReactHp(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch){
	if (m_fast_react)
		UpdateRateHp(qp, p, ch, true);
}

/**********************
 * TIMELY
 *********************/
void RdmaHw::HandleAckTimely(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch){
	uint64_t ack_seq = ch.ack.seq;
	// update rate
	if (ack_seq > qp->tmly.m_lastUpdateSeq){ // if full RTT feedback is ready, do full update
		UpdateRateTimely(qp, p, ch, false);
	}else{ // do fast react
		FastReactTimely(qp, p, ch);
	}
}
void RdmaHw::UpdateRateTimely(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch, bool us){
	uint64_t next_seq = qp->snd_nxt;
	uint64_t rtt = Simulator::Now().GetTimeStep() - ch.ack.ih.ts;
	#if PRINT_LOG
		bool print = !us;
	#endif
	if (qp->tmly.m_lastUpdateSeq != 0){ // not first RTT
		int64_t new_rtt_diff = (int64_t)rtt - (int64_t)qp->tmly.lastRtt;
		double rtt_diff = (1 - m_tmly_alpha) * qp->tmly.rttDiff + m_tmly_alpha * new_rtt_diff;
		double gradient = rtt_diff / m_tmly_minRtt;
		bool inc = false;
		double c = 0;
		#if PRINT_LOG
		if (print)
			printf("%lu node:%u rtt:%lu rttDiff:%.0lf gradient:%.3lf rate:%.3lf", Simulator::Now().GetTimeStep(), m_node->GetId(), rtt, rtt_diff, gradient, qp->tmly.m_curRate.GetBitRate() * 1e-9);
		#endif
		if (rtt < m_tmly_TLow){
			inc = true;
		}else if (rtt > m_tmly_THigh){
			c = 1 - m_tmly_beta * (1 - (double)m_tmly_THigh / rtt);
			inc = false;
		}else if (gradient <= 0){
			inc = true;
		}else{
			c = 1 - m_tmly_beta * gradient;
			if (c < 0)
				c = 0;
			inc = false;
		}
		if (inc){
			if (qp->tmly.m_incStage < 5){
				qp->m_rate = qp->tmly.m_curRate + m_rai;
			}else{
				qp->m_rate = qp->tmly.m_curRate + m_rhai;
			}
			if (qp->m_rate > qp->m_max_rate)
				qp->m_rate = qp->m_max_rate;
			if (!us){
				qp->tmly.m_curRate = qp->m_rate;
				qp->tmly.m_incStage++;
				qp->tmly.rttDiff = rtt_diff;
			}
		}else{
			qp->m_rate = std::max(m_minRate, qp->tmly.m_curRate * c);
			if (!us){
				qp->tmly.m_curRate = qp->m_rate;
				qp->tmly.m_incStage = 0;
				qp->tmly.rttDiff = rtt_diff;
			}
		}
		#if PRINT_LOG
		if (print){
			printf(" %c %.3lf\n", inc? '^':'v', qp->m_rate.GetBitRate() * 1e-9);
		}
		#endif
	}
	if (!us && next_seq > qp->tmly.m_lastUpdateSeq){
		qp->tmly.m_lastUpdateSeq = next_seq;
		// update
		qp->tmly.lastRtt = rtt;
	}
}
void RdmaHw::FastReactTimely(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch){
}

/**********************
 * DCTCP
 *********************/
void RdmaHw::HandleAckDctcp(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch){
	uint64_t ack_seq = ch.ack.seq;
	uint8_t cnp = (ch.ack.flags >> qbbHeader::FLAG_CNP) & 1;
	bool new_batch = false;

	// update alpha
	qp->dctcp.m_ecnCnt += (cnp > 0);
	if (ack_seq > qp->dctcp.m_lastUpdateSeq){ // if full RTT feedback is ready, do alpha update
		#if PRINT_LOG
		printf("%lu %s %08x %08x %u %u [%u,%u,%u] %.3lf->", Simulator::Now().GetTimeStep(), "alpha", qp->sip.Get(), qp->dip.Get(), qp->sport, qp->dport, qp->dctcp.m_lastUpdateSeq, ch.ack.seq, qp->snd_nxt, qp->dctcp.m_alpha);
		#endif
		new_batch = true;
		if (qp->dctcp.m_lastUpdateSeq == 0){ // first RTT
			qp->dctcp.m_lastUpdateSeq = qp->snd_nxt;
			qp->dctcp.m_batchSizeOfAlpha = qp->snd_nxt / m_mtu + 1;
		}else {
			double frac = std::min(1.0, double(qp->dctcp.m_ecnCnt) / qp->dctcp.m_batchSizeOfAlpha);
			qp->dctcp.m_alpha = (1 - m_g) * qp->dctcp.m_alpha + m_g * frac;
			qp->dctcp.m_lastUpdateSeq = qp->snd_nxt;
			qp->dctcp.m_ecnCnt = 0;
			qp->dctcp.m_batchSizeOfAlpha = (qp->snd_nxt - ack_seq) / m_mtu + 1;
			#if PRINT_LOG
			printf("%.3lf F:%.3lf", qp->dctcp.m_alpha, frac);
			#endif
		}
		#if PRINT_LOG
		printf("\n");
		#endif
	}

	// check cwr exit
	if (qp->dctcp.m_caState == 1){
		if (ack_seq > qp->dctcp.m_highSeq)
			qp->dctcp.m_caState = 0;
	}

	// check if need to reduce rate: ECN and not in CWR
	if (cnp && qp->dctcp.m_caState == 0){
		#if PRINT_LOG
		printf("%lu %s %08x %08x %u %u %.3lf->", Simulator::Now().GetTimeStep(), "rate", qp->sip.Get(), qp->dip.Get(), qp->sport, qp->dport, qp->m_rate.GetBitRate()*1e-9);
		#endif
		qp->m_rate = std::max(m_minRate, qp->m_rate * (1 - qp->dctcp.m_alpha / 2));
		#if PRINT_LOG
		printf("%.3lf\n", qp->m_rate.GetBitRate() * 1e-9);
		#endif
		qp->dctcp.m_caState = 1;
		qp->dctcp.m_highSeq = qp->snd_nxt;
	}

	// additive inc
	if (qp->dctcp.m_caState == 0 && new_batch)
		qp->m_rate = std::min(qp->m_max_rate, qp->m_rate + m_dctcp_rai);
}

/*********************
 * HPCC-PINT
 ********************/
void RdmaHw::SetPintSmplThresh(double p){
       pint_smpl_thresh = (uint32_t)(65536 * p);
}
void RdmaHw::HandleAckHpPint(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch){
       uint64_t ack_seq = ch.ack.seq;
       if (rand() % 65536 >= pint_smpl_thresh)
               return;
       // update rate
       if (ack_seq > qp->hpccPint.m_lastUpdateSeq){ // if full RTT feedback is ready, do full update
               UpdateRateHpPint(qp, p, ch, false);
       }else{ // do fast react
               UpdateRateHpPint(qp, p, ch, true);
       }
}

void RdmaHw::UpdateRateHpPint(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch, bool fast_react){
       uint64_t next_seq = qp->snd_nxt;
       if (qp->hpccPint.m_lastUpdateSeq == 0){ // first RTT
               qp->hpccPint.m_lastUpdateSeq = next_seq;
       }else {
               // check packet INT
               IntHeader &ih = ch.ack.ih;
               double U = Pint::decode_u(ih.GetPower());

               DataRate new_rate;
               int32_t new_incStage;
               double max_c = U / m_targetUtil;

               if (max_c >= 1 || qp->hpccPint.m_incStage >= m_miThresh){
                       new_rate = qp->hpccPint.m_curRate / max_c + m_rai;
                       new_incStage = 0;
               }else{
                       new_rate = qp->hpccPint.m_curRate + m_rai;
                       new_incStage = qp->hpccPint.m_incStage+1;
               }
               if (new_rate < m_minRate)
                       new_rate = m_minRate;
               if (new_rate > qp->m_max_rate)
                       new_rate = qp->m_max_rate;
               ChangeRate(qp, new_rate);
               if (!fast_react){
                       qp->hpccPint.m_curRate = new_rate;
                       qp->hpccPint.m_incStage = new_incStage;
               }
               if (!fast_react){
                       if (next_seq > qp->hpccPint.m_lastUpdateSeq)
                               qp->hpccPint.m_lastUpdateSeq = next_seq; //+ rand() % 2 * m_mtu;
               }
       }
}
/*******************************
 * MPRDMA
 *******************************/
void RdmaHw::HandleAckMprdma(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch){
	uint8_t cnp = (ch.ack.flags >> qbbHeader::FLAG_CNP) & 1;
	uint64_t acked_pkt_size = qp->fullMtu;
	qp->mprdma.m_preCwnd = qp->m_win;
	if (ch.l3Prot == 0xFC) { // ACK
		if (cnp) {
			qp->m_win -= acked_pkt_size / 2;
			qp->m_win = std::max(qp->m_win, qp->fullMtu);
			#ifdef MPRDMA_INFO
			if(TRACE)
				printf("[MPRDMA:ACK][%ld] received ACK for %u bytes, ECN cwnd reduced to %u\n", Simulator::Now().GetTimeStep(), acked_pkt_size, qp->m_win);
			#endif
		} else {
			qp->m_win += acked_pkt_size * qp->fullMtu / qp->m_win;
			if (qp->m_win > qp->mprdma.m_maxCwnd)
				qp->m_win = qp->mprdma.m_maxCwnd;
			#ifdef MPRDMA_INFO
			if(TRACE)
				printf("[MPRDMA:ACK][%ld] received ACK for %u bytes, cwnd additive to %u\n", Simulator::Now().GetTimeStep(), acked_pkt_size, qp->m_win);
			#endif

		}
	} else if (ch.l3Prot == 0xFD) { // NACK
		qp->m_win -= acked_pkt_size;
		qp->m_win = std::max(qp->m_win, qp->fullMtu);
		#ifdef MPRDMA_INFO
		if(TRACE)
			printf("[MPRDMA:NACK][%ld] received NACK for %u bytes, cwnd reduced to %u\n", Simulator::Now().GetTimeStep(), acked_pkt_size, qp->m_win);
		#endif
	}
	return;
}

/*******************************
 * Adaptive Packet Spraying (APS)
 ******************************/
void RdmaHw::HandleAckAps(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch){
	if ((qp->aps.m_freq %= m_updateFreq) != 0) {
		qp->aps.m_freq++;
		return; // not time to update INT
	}
	qp->aps.m_freq++;
	#ifdef APS_OLD
	UpdateIntAps(qp, p, ch);
	#elif defined(APS_V2)
	UpdateIntApsv2(qp, p, ch);
	#endif
}
void RdmaHw::UpdateIntApsv2(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch){
	uint8_t cnp = (ch.ack.flags >> qbbHeader::FLAG_CNP) & 1;
	IntHeader &ih = ch.ack.ih;
	NS_ASSERT(ih.nhop <= IntHeader::maxHop);
	FlowInfoTag fit;
	NS_ASSERT(p->PeekPacketTag(fit));		
	if (ih.nhop == 0) { // nvlink, do not update aps info
		return;
	}
	if (cnp && !qp->aps.isFreezingMode && ((m_apsIndMask & 0b001) == 0b001)) return; // ECN, do not update aps info
	
	// check hop
	if (ih.nhop == 1) { // ToR nothing to do
		return; 
	} else if (ih.nhop == 3 || ih.nhop == 5) {
		// get pathEV and pathID
		uint16_t pathEV = ih.hop[0].GetPathId();
		uint16_t aggID = ih.hop[1].GetNodeId();
		uint16_t coreID = 0;
		if (ih.nhop == 5)
			coreID = ih.hop[2].GetNodeId();
		uint32_t pathID = GetPathIdKey(aggID, coreID);

		// update path Info
		if (qp->aps.ID2pathInfo.find(pathID) == qp->aps.ID2pathInfo.end()) { // new path, insert 
			RdmaQueuePair::PathInfo pathInfo;
			vector<uint32_t> switchID;
			for (int i = 0; i < ih.nhop; ++i) {
				pathInfo.hop[i] = ih.hop[i];
				switchID.push_back(ih.hop[i].GetNodeId());
			}
			pathInfo.pathID = pathID;
			pathInfo.credit = 0;
			qp->aps.pathID2switch[pathID] = switchID;
			qp->aps.ID2pathInfo[pathID] = pathInfo;
		} else { // cached path, update 
			// check each hop
			for (int i = 0; i < ih.nhop; ++i) {
				qp->aps.ID2pathInfo[pathID].hop[i] = ih.hop[i]; // update INT info
			}
		}

		// update pathInfo
		// qp->aps.ID2pathInfo[pathID].EVCache = pathEV; // update EV
		// if (qp->aps.m_numberOfValidPath >= REPS_BUFFER_SIZE) {
		// 	uint32_t old_path = qp->aps.apsBuffer[qp->aps.head];
		// 	while (qp->aps.ID2pathInfo[old_path].credit == 0) { // 找到一个老旧路径进行剔除，freezing mode也照常剔除
		// 		qp->aps.head = (qp->aps.head + 1) % REPS_BUFFER_SIZE;
		// 		old_path = qp->aps.apsBuffer[qp->aps.head];
		// 	}
		// 	qp->aps.ID2pathInfo[old_path].credit--; // evict a path with credit
		// 	qp->aps.m_numberOfValidPath--;
		// }

		// qp->aps.m_numberOfValidPath++;
		// qp->aps.ID2pathInfo[pathID].credit++;		
		
		
		qp->aps.ID2pathInfo[pathID].EVCache = pathEV; // update EV
		if (qp->aps.ID2pathInfo[pathID].credit > 0) { // update valid path count
			qp->aps.m_numberOfValidPath += CREDIT_SIZE - qp->aps.ID2pathInfo[pathID].credit;
		} else {
			qp->aps.m_numberOfValidPath += CREDIT_SIZE;
		}
		
		qp->aps.ID2pathInfo[pathID].credit = CREDIT_SIZE; // update credit, at most CREDIT_SIZE-1
		
		qp->aps.apsBuffer[qp->aps.head] = pathID;
		#ifdef APS_CACHED_PATH_INFO
		if (TRACE) {
			printf("[INFO:APS_CACHED_PATH][%ld][%u:%u:%u] cache pathid %u, head %u, apsBuffer: ", 
				Simulator::Now().GetTimeStep(), m_node->GetId(), ip_to_node_id(qp->dip), qp->sport, 
					pathID, qp->aps.head);
			for (int i = 0; i < REPS_BUFFER_SIZE; ++i) {
				printf("[%u]%u ", i, qp->aps.apsBuffer[i]);
			}
			printf("\n");
		}
		#endif
		qp->aps.head = (qp->aps.head + 1) % REPS_BUFFER_SIZE;


		double pathQlen = 0;
		double pathUtil = 0;
		for (int i = 0; i < ih.nhop; ++i) {
			double duration = ih.hop[i].GetTime() * 1e-9; // sec
			uint64_t lineRate = ih.hop[i].GetLineRate();
			double util = (ih.hop[i].GetBytes() * 8 / duration / lineRate);
			// pathUtil = pathUtil > util ? pathUtil : util;
			pathUtil += util;
			pathUtil = pathUtil / ih.nhop;

			pathQlen += ih.hop[i].GetQlen();

			qp->aps.ID2pathInfo[pathID].hop[i] = ih.hop[i]; // update INT info
		}

		qp->aps.ID2pathInfo[pathID].m_avgNormalQlen = pathQlen;
		qp->aps.ID2pathInfo[pathID].m_avgUtil = pathUtil;
		
		// update ordered score
		auto itQlen = qp->aps.pathID2itrQlen.find(pathID); // Qlen
		if (itQlen == qp->aps.pathID2itrQlen.end()) {
			auto it = qp->aps.orderedQlen.insert({pathQlen, pathID}).first; // insert new path
			qp->aps.pathID2itrQlen[pathID] = it;
		} else {
			qp->aps.orderedQlen.erase(itQlen->second);
			auto it = qp->aps.orderedQlen.insert({pathQlen, pathID}).first; // insert new path
			qp->aps.pathID2itrQlen[pathID] = it;
		}

		auto itUtil = qp->aps.pathID2itrUtil.find(pathID);
		if (itUtil == qp->aps.pathID2itrUtil.end()) {
			auto it = qp->aps.orderedUtil.insert({pathUtil, pathID}).first;
			qp->aps.pathID2itrUtil[pathID] = it;
		} else {
			qp->aps.orderedUtil.erase(itUtil->second);
			auto it = qp->aps.orderedUtil.insert({pathUtil, pathID}).first;
			qp->aps.pathID2itrUtil[pathID] = it;
		}

		#ifdef APS_CACHED_PATH_INFO
		if (TRACE) {
			printf("[INFO:APS_CACHED_PATH][%ld][%u:%u:%u] Receive ACK/NACK Cached Path %u , valid path %u, port %u\n", 
				Simulator::Now().GetTimeStep(), m_node->GetId(), ip_to_node_id(qp->dip), qp->sport, 
					pathID, qp->aps.m_numberOfValidPath, fit.GetSwitchPort());		
		}
		#endif
	} else { // error
		printf("[ERROR:APS][%ld][%u] INT hop number is %u, not support", 
			Simulator::Now().GetTimeStep(), m_node->GetId(), ih.nhop);
		return;
	}

	if(qp->aps.isFreezingMode && Simulator::Now().GetTimeStep() > qp->aps.exitFreezingMode) {
		#ifdef APS_FREEZING_INFO
		if(TRACE)
		printf("[INFO:APS_FREEZING][%ld][%u:%u:%u] Exit Freezing Mode, valid path %u\n", 
			Simulator::Now().GetTimeStep(), m_node->GetId(), ip_to_node_id(qp->dip), qp->sport, qp->aps.m_numberOfValidPath);
		#endif
		qp->aps.isFreezingMode = false;
		qp->ResetApsBuffer();
		qp->aps.exploreCnt = 2 * qp->m_cwnd;
	}


}
uint32_t RdmaHw::GetPathIdKey(uint16_t aggID, uint16_t coreID){
	uint32_t pathID = static_cast<uint32_t>(aggID);
	pathID = aggID << 16 | coreID;
	return pathID;
}
uint16_t RdmaHw::GetNextIfIndexAps(Ptr<RdmaQueuePair> qp){
	if(qp->aps.m_numberOfValidPath > 0 || qp->aps.isFreezingMode){
		if(qp->aps.isFreezingMode && qp->aps.m_numberOfValidPath == 0) { // freezing mode 从缓存路径中取credit
			qp->aps.m_numberOfValidPath += CREDIT_SIZE;
			qp->aps.ID2pathInfo[qp->aps.apsBuffer[qp->aps.head]].credit = CREDIT_SIZE;
			#ifdef APS_FREEZING_INFO
			if(TRACE)
			printf("[INFO:APS_FREEZING][%ld][%u:%u:%u] no credit, select from path buffer, pathid %u\n", 
				Simulator::Now().GetTimeStep(), m_node->GetId(), ip_to_node_id(qp->dip), qp->sport, qp->aps.apsBuffer[qp->aps.head]);
			#endif
			qp->aps.head = (qp->aps.head + 1) % REPS_BUFFER_SIZE;
		}		
		if ((m_apsIndMask & 0b110) == 0b110) { // util + qlen
			for (auto it = qp->aps.orderedUtil.begin(); it != qp->aps.orderedUtil.end(); ++it) { // find a least util path if util < 0.95

				if (qp->aps.ID2pathInfo[it->pathID].credit == 0) continue; // 在切入freezing状态的边界上，应当准入，但是还不能选到故障链路
				// calculate avg util
				double UtilThreshold = 0;
				if (m_esti_window > 0) {
					if (qp->aps.historyUtil.size() < m_esti_window) {
						qp->aps.historyUtil.push_back(qp->aps.ID2pathInfo[it->pathID].m_avgUtil);
						for (int i = 0; i < qp->aps.historyUtil.size(); i++) {
							UtilThreshold += qp->aps.historyUtil[i];
						}
						UtilThreshold /= qp->aps.historyUtil.size();
					} else if (qp->aps.historyUtil.size() == m_esti_window) {
						qp->aps.historyUtil.erase(qp->aps.historyUtil.begin());
						qp->aps.historyUtil.push_back(qp->aps.ID2pathInfo[it->pathID].m_avgUtil);
						for (int i = 0; i < m_esti_window; i++) {
							UtilThreshold += qp->aps.historyUtil[i];
						}
						UtilThreshold /= m_esti_window;
					} else {
						printf("[ERROR:APS] vector overflow\n");
					}
				} else UtilThreshold = 0.6;
				

				if (qp->aps.ID2pathInfo[it->pathID].m_avgUtil < UtilThreshold) {

					#ifdef APS_CACHED_PATH_INFO
					if (TRACE) {
						printf("[INFO:APS_CACHED_PATH][%ld][%u:%u:%u] Select from Cached Path %u based on Util, valid path %u\n", 
							Simulator::Now().GetTimeStep(), m_node->GetId(), ip_to_node_id(qp->dip), qp->sport, qp->aps.ID2pathInfo[it->pathID].pathID, qp->aps.m_numberOfValidPath);
						int rank = 0;
						for (auto itr = qp->aps.orderedUtil.begin(); itr != qp->aps.orderedUtil.end(); ++itr) {
							printf("[INFO:APS_CACHED_PATH_RANK][%ld][%u:%u:%u] Rank %u, PathID %u, Credit %u, Qlen %f, Util %f\n", 
								Simulator::Now().GetTimeStep(), m_node->GetId(), ip_to_node_id(qp->dip), qp->sport, rank, 
								qp->aps.ID2pathInfo[itr->pathID].pathID, qp->aps.ID2pathInfo[itr->pathID].credit, 
								qp->aps.ID2pathInfo[itr->pathID].m_avgNormalQlen, 
								qp->aps.ID2pathInfo[itr->pathID].m_avgUtil);
							rank++;
						}
					}
					#endif
					qp->aps.ID2pathInfo[it->pathID].credit = qp->aps.ID2pathInfo[it->pathID].credit > 0 ? qp->aps.ID2pathInfo[it->pathID].credit - 1 : 0;
					qp->aps.m_numberOfValidPath = qp->aps.m_numberOfValidPath > 0 ? qp->aps.m_numberOfValidPath - 1 : 0;
					qp->aps.pathID = it->pathID;
					return qp->aps.ID2pathInfo[it->pathID].EVCache;

				} else { // find a least qlen path
					for (auto itq = qp->aps.orderedQlen.begin(); itq != qp->aps.orderedQlen.end(); ++itq) { // find a lest Qlen path
						if (qp->aps.ID2pathInfo[itq->pathID].credit == 0) continue;

						#ifdef APS_CACHED_PATH_INFO
						if (TRACE) {
							printf("[INFO:APS_CACHED_PATH][%ld][%u:%u:%u] Select from Cached Path %u based on Util->Qlen, valid path %u\n", 
								Simulator::Now().GetTimeStep(), m_node->GetId(), ip_to_node_id(qp->dip), qp->sport, qp->aps.ID2pathInfo[itq->pathID].pathID, qp->aps.m_numberOfValidPath);
							int rank = 0;
							for (auto itr = qp->aps.orderedQlen.begin(); itr != qp->aps.orderedQlen.end(); ++itr) {
								printf("[INFO:APS_CACHED_PATH_RANK][%ld][%u:%u:%u] Rank %u, PathID %u, Credit %u, Qlen %f, Util %f\n", 
									Simulator::Now().GetTimeStep(), m_node->GetId(), ip_to_node_id(qp->dip), qp->sport, rank, 
									qp->aps.ID2pathInfo[itr->pathID].pathID, qp->aps.ID2pathInfo[itr->pathID].credit, 
									qp->aps.ID2pathInfo[itr->pathID].m_avgNormalQlen, 
									qp->aps.ID2pathInfo[itr->pathID].m_avgUtil);
								rank++;
							}
						}
						#endif
						qp->aps.ID2pathInfo[itq->pathID].credit = qp->aps.ID2pathInfo[itq->pathID].credit > 0 ? qp->aps.ID2pathInfo[itq->pathID].credit - 1 : 0;
						qp->aps.m_numberOfValidPath = qp->aps.m_numberOfValidPath > 0 ? qp->aps.m_numberOfValidPath - 1 : 0;
						qp->aps.pathID = itq->pathID;
						return qp->aps.ID2pathInfo[itq->pathID].EVCache;
					}
				}
			}

		} else if ((m_apsIndMask & 0b110) == 0b100) { // util
			for (auto it = qp->aps.orderedUtil.begin(); it != qp->aps.orderedUtil.end(); ++it) { // find a least util path
				if (qp->aps.ID2pathInfo[it->pathID].credit > 0) {

					#ifdef APS_CACHED_PATH_INFO
					if (TRACE) {
						printf("[INFO:APS_CACHED_PATH][%ld][%u:%u:%u] Select from Cached Path %u based on Util, valid path %u\n", 
							Simulator::Now().GetTimeStep(), m_node->GetId(), ip_to_node_id(qp->dip), qp->sport, qp->aps.ID2pathInfo[it->pathID].pathID, qp->aps.m_numberOfValidPath);
						int rank = 0;
						for (auto itr = qp->aps.orderedUtil.begin(); itr != qp->aps.orderedUtil.end(); ++itr) {
							printf("[INFO:APS_CACHED_PATH_RANK][%ld][%u:%u:%u] Rank %u, PathID %u, Credit %u, Qlen %f, Util %f\n", 
								Simulator::Now().GetTimeStep(), m_node->GetId(), ip_to_node_id(qp->dip), qp->sport, rank, 
								qp->aps.ID2pathInfo[itr->pathID].pathID, qp->aps.ID2pathInfo[itr->pathID].credit, 
								qp->aps.ID2pathInfo[itr->pathID].m_avgNormalQlen, 
								qp->aps.ID2pathInfo[itr->pathID].m_avgUtil);
							rank++;
						}
					}
					#endif
					if(!qp->aps.isFreezingMode) {
						qp->aps.ID2pathInfo[it->pathID].credit = qp->aps.ID2pathInfo[it->pathID].credit > 0 ? qp->aps.ID2pathInfo[it->pathID].credit - 1 : 0;
						qp->aps.m_numberOfValidPath = qp->aps.m_numberOfValidPath > 0 ? qp->aps.m_numberOfValidPath - 1 : 0;
						qp->aps.pathID = it->pathID;
					} else {
						qp->aps.ID2pathInfo[it->pathID].credit += 1;
						qp->aps.m_numberOfValidPath += 1;
						qp->aps.pathID = it->pathID;
					}
					return qp->aps.ID2pathInfo[it->pathID].EVCache;
				}
			}
		} else if ((m_apsIndMask & 0b110) == 0b010) { // qlen
			for (auto it = qp->aps.orderedQlen.begin(); it != qp->aps.orderedQlen.end(); ++it) { // find a lest Qlen path
				if (qp->aps.ID2pathInfo[it->pathID].credit > 0) {

					#ifdef APS_CACHED_PATH_INFO
					if (TRACE) {
						printf("[INFO:APS_CACHED_PATH][%ld][%u:%u:%u] Select from Cached Path %u based on Qlen, valid path %u\n", 
							Simulator::Now().GetTimeStep(), m_node->GetId(), ip_to_node_id(qp->dip), qp->sport, qp->aps.ID2pathInfo[it->pathID].pathID, qp->aps.m_numberOfValidPath);
						int rank = 0;
						for (auto itr = qp->aps.orderedQlen.begin(); itr != qp->aps.orderedQlen.end(); ++itr) {
							printf("[INFO:APS_CACHED_PATH_RANK][%ld][%u:%u:%u] Rank %u, PathID %u, Credit %u, Qlen %f, Util %f\n", 
								Simulator::Now().GetTimeStep(), m_node->GetId(), ip_to_node_id(qp->dip), qp->sport, rank, 
								qp->aps.ID2pathInfo[itr->pathID].pathID, qp->aps.ID2pathInfo[itr->pathID].credit, 
								qp->aps.ID2pathInfo[itr->pathID].m_avgNormalQlen, 
								qp->aps.ID2pathInfo[itr->pathID].m_avgUtil);
							rank++;
						}
					}

					#endif

					if(!qp->aps.isFreezingMode) {
						qp->aps.ID2pathInfo[it->pathID].credit = qp->aps.ID2pathInfo[it->pathID].credit > 0 ? qp->aps.ID2pathInfo[it->pathID].credit - 1 : 0;
						qp->aps.m_numberOfValidPath = qp->aps.m_numberOfValidPath > 0 ? qp->aps.m_numberOfValidPath - 1 : 0;
						qp->aps.pathID = it->pathID;

					} else {
						qp->aps.ID2pathInfo[it->pathID].credit += 1;
						qp->aps.m_numberOfValidPath += 1;
						qp->aps.pathID = it->pathID;
					}
					return qp->aps.ID2pathInfo[it->pathID].EVCache;
				}
			}
		} else if ((m_apsIndMask & 0b111) == 0b001) { // ecn based selection -> REPS
			
		}
		NS_ASSERT(qp->aps.m_numberOfValidPath > 0); // should not reach here
	} else { // no valid path 
		printf("[ERROR:APS_CACHE][%ld][%u] no valid cached path \n", Simulator::Now().GetTimeStep(), this->m_node->GetId());
		return 0;
	}
}

void RdmaHw::UpdateIntAps(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch){
	uint32_t next_seq = qp->snd_nxt;
	uint8_t cnp = (ch.ack.flags >> qbbHeader::FLAG_CNP) & 1;
	IntHeader &ih = ch.ack.ih;
	NS_ASSERT(ih.nhop <= IntHeader::maxHop);
	if (ih.nhop == 0) { // nvlink, do not update aps info
		return;
	}

	if (qp->aps.m_lastUpdateSeq == 0) { // first RTT
		qp->aps.m_lastUpdateSeq = next_seq;
		qp->aps.m_nhop = ih.nhop;

		// first RTT, get ToRCnt, add uninitialized m_pathToR2AggCnt items
		if (qp->aps.m_nhop == 1 || qp->aps.m_nhop == 3 || qp->aps.m_nhop == 5) {
			qp->aps.m_pathToRCnt = ih.hop[0].GetNodeId();
			for (uint32_t i = 0; i < qp->aps.m_pathToRCnt; i++)
				qp->aps.m_pathToR2AggCnt[i] = 0; // init ToR 2 Agg map
		} else {
			printf("[ERROR]: INT hop number is %u, not supported\n", ih.nhop);
			return;
		}

		#ifdef APS_INIT_INFO
			printf("[INFO:APS_INIT][%ld]\tGet the first ACK, ToRCnt:%u\n", Simulator::Now().GetTimeStep(), qp->aps.m_pathToRCnt);
		#endif
	} 
	
	// here can cal pidToR
	uint16_t pidToR = ih.hop[0].GetPathId() % qp->aps.m_pathToRCnt;


	// Get Agg switch out port cnt
	if (!qp->aps.initCnt && qp->aps.m_pathToR2AggCnt[pidToR] == 0) { // this ToR pid has not been init
		if (qp->aps.m_nhop == 1 || qp->aps.m_nhop == 3 || qp->aps.m_nhop == 5) {
			
			qp->aps.m_pathToR2AggCnt[pidToR] = 1; // ToR pid to Agg outPort number
			if (qp->aps.m_nhop == 5) {
				if (ih.hop[1].GetNodeId() == 0) {
					printf("ERROR: 5hop, but hop[1] out port cnt 0\n");
					return;
				}
				qp->aps.m_pathToR2AggCnt[pidToR] = ih.hop[1].GetNodeId(); // ToR pid to Agg outPort Cnt
				
			}

			qp->aps.m_pathCnt += qp->aps.m_pathToR2AggCnt[pidToR]; // add to path cnt

			// check whether all Agg init
			qp->aps.initCnt = true;
			for (auto &it : qp->aps.m_pathToR2AggCnt)
				if(it.second == 0) {
					qp->aps.initCnt = false;
					break;
				}

			if (qp->aps.m_pathCnt == 0) {
				printf("ERROR: INT first or Second hop nodeId is 0\n");
				return;
			}

		} else {
			printf("[ERROR:] INT hop number is %u, not supported\n", ih.nhop);
			return;
		}
	}

	// here can cal pidAgg
	uint16_t pidAgg = ih.hop[1].GetPathId() % qp->aps.m_pathToR2AggCnt[pidToR];


	//  increment init aps
	if (!qp->aps.initCnt) {
		for (uint32_t i = 0; i < qp->aps.m_pathCnt; i++){ 
			if (qp->aps.pidx2aps.find(i) != qp->aps.pidx2aps.end()) continue; // get the next not add aps
			RdmaQueuePair::ApsInfo tmp;
			qp->aps.pidx2aps[i] = tmp;
		}
	}


	// path decision
	if (!qp->aps.initIf2aps) { // initial phase 目标：pidx2aps 每个本地出端口序列号 赋值一个 IntHop；pid2pidx 本地出端口序列号 对应一个 交换机出端口序列号

		// add IntHop info from IntHeader
		uint16_t pathIdx; // = ih.hop[0].GetPathId() % qp->aps.m_pathCnt;
		for (pathIdx = 0; pathIdx < qp->aps.m_pathCnt; pathIdx++) {
			// update interface -> pathIdx mapping
			uint32_t pathId = GetPathIdKey(qp, pidToR, pidAgg);
			if (pathId == 0xffffffff) {
				printf("ERROR: no such nhop\n");
				return;
			}
			// get one uninitialized pathIdx
			if (qp->aps.pidx2aps[pathIdx].initAps || (qp->aps.pid2pidx.find(pathId) != qp->aps.pid2pidx.end())) continue;

			// init hop[i]
			for (uint32_t i = 0; i < qp->aps.m_nhop; i++)
				qp->aps.pidx2aps[pathIdx].hop[i] = ih.hop[i];
			qp->aps.pidx2aps[pathIdx].initAps = true;

			// init pid <-> pidx mapping
			qp->aps.pid2pidx[pathId] = pathIdx;	
			qp->aps.pidx2pid[pathIdx] = pathId;

			// init path score to 1
			qp->aps.pidx2pathScore[pathIdx] = 1;
			qp->aps.pathScore2pidx.insert({1, pathIdx});	

			#ifdef APS_INIT_INFO
				printf("[INFO:APS_INIT][%ld]\tInit PathIdx:%u, PathId:0x%08x(pidToR:%u pidAgg:%u) \n", Simulator::Now().GetTimeStep(),pathIdx, pathId, pidToR, pidAgg);
			#endif
			break;
		}

		// check whether all path have been initialized
		for (uint16_t i = 0; i < qp->aps.m_pathCnt; i++){
			if (!qp->aps.pidx2aps[i].initAps) break;
			if (i == qp->aps.m_pathCnt - 1 && qp->aps.initCnt) {
				qp->aps.initIf2aps = true; // all pathIdx have been initialized
				#ifdef APS_INIT_RRB_INFO
					printf("[INFO:APS_INIT_RRB][%ld]\tSenderNode: %u, APS finished all path init, path cnt %ld\n", Simulator::Now().GetTimeStep(), this->m_node->GetId(), qp->aps.pidx2aps.size());
				#endif
				#ifdef APS_INIT_DEBUG
					printf("[DEBUG:APS_INIT][%ld]\tAPS finished all path init, path cnt %ld\n", Simulator::Now().GetTimeStep(), qp->aps.pidx2aps.size());
				#endif
				#ifdef APS_INIT_INFO
					printf("[INFO:APS_INIT][%ld]\tFinish ToR outPort probe, all pathId got\n", Simulator::Now().GetTimeStep());
					for (uint32_t j = 0; j < qp->aps.m_pathCnt; j++) {
							printf("[INFO:APS_INIT][%ld]\tThere are PathIdx %u, PathId %08x \n", Simulator::Now().GetTimeStep(), j, qp->aps.pidx2pid[j]);
					}
				#endif

				break;
			}
		}

	} else { // compute aps info, and get the next optimal ifIndex
		double avgUtil = 0;
		double avgNormalQlen = 0;
		uint16_t pathIdx;
		uint32_t pathId = GetPathIdKey(qp, pidToR, pidAgg);
		if (pathId == 0xffffffff) {
			printf("ERROR: no such nhop\n");
			return;
		}

		pathIdx = qp->aps.pid2pidx[pathId];
			
		// check each hop
		for (uint32_t i = 0; i < ih.nhop; i++) {
			uint64_t tau = ih.hop[i].GetTimeDelta(qp->aps.pidx2aps[pathIdx].hop[i]);
			double duration = tau * 1e-9; // sec
			uint64_t lineRate = ih.hop[i].GetLineRate();
			avgUtil += ih.hop[i].GetBytesDelta(qp->aps.pidx2aps[pathIdx].hop[i]) * 8 / duration / lineRate; 

			#ifdef APS_DEBUG
				if (ih.hop[i].GetBytesDelta(qp->aps.pidx2aps[pathIdx].hop[i]) * 8 / duration / lineRate > 50)
					printf("[DEBUG:APS][%ld]\tBytesD too big, hop: %u qp: %llu, ih: %llu, PathId:%08x, pathIdx:%u\n", \
						Simulator::Now().GetTimeStep(), i, qp->aps.pidx2aps[pathIdx].hop[i].GetBytes(), ih.hop[i].GetBytes(), \
							pathId, pathIdx);
			#endif

			avgNormalQlen += ih.hop[i].GetQlen() / (lineRate * duration / 8); // avg normalize queue length

			qp->aps.pidx2aps[pathIdx].hop[i] = ih.hop[i]; // update aps info
		}
		avgUtil /= ih.nhop; // average bandwidth utilization
		avgNormalQlen /= ih.nhop; // average queue length

		qp->aps.pidx2aps[pathIdx].m_avgUtil = avgUtil; 
		qp->aps.pidx2aps[pathIdx].m_avgNormalQlen = avgNormalQlen;
		qp->aps.pidx2aps[pathIdx].ecn = cnp; // ECN

		#ifdef APS_DEBUG
			printf("[DEBUG:APS][%ld]\tSeq:%u PathId %08x PathIdx %d: avgNormalQlen: %f , avgUtil: %f, ecn: %d\n", \
				Simulator::Now().GetTimeStep(), ch.ack.seq, pathId, pathIdx, avgNormalQlen, avgUtil, cnp);
		#endif

		// get the next optimal switch ifIndex
		pathIdx = GetNextIfIndexAps(qp, pathIdx);
		pathId = qp->aps.pidx2pid[pathIdx];
		qp->aps.m_ifIndex = static_cast<uint16_t>(pathId >> 16);
		qp->aps.m_ifIndexAgg = static_cast<uint16_t>(pathId & 0xffff);
		

		#ifdef APS_SELECT_INFO
			printf("[INFO:APS_SELECT][%ld]\tSender Node %d, select next PathIdx: %u, PathId: %08x (pidToR:%u pidAgg:%u)\n", \
				Simulator::Now().GetTimeStep(), this->m_node->GetId(), pathIdx, pathId, qp->aps.m_ifIndex, qp->aps.m_ifIndexAgg);
		#endif
		
	}

	#ifdef APS_INT_PER_HOP_INFO
		uint16_t pathIdx;
		uint32_t pathId = GetPathIdKey(qp, pidToR, pidAgg);
		if (pathId == -1) {
			printf("ERROR: no such nhop\n");
			return;
		}
		pathIdx = qp->aps.pid2pidx[pathId];

		printf("[INFO:APS_INT_PER_HOP][%ld]\t Seq:%u PathId:%08x (pidToR:%u pidAgg:%u), PathIdx:%u\n",\
			Simulator::Now().GetTimeStep(), \
				ch.ack.seq, pathId, ih.hop[0].GetPathId() % qp->aps.m_pathToRCnt, ih.hop[1].GetPathId() % qp->aps.m_pathAggCnt, pathIdx);
			for (uint32_t i = 0; i < ih.nhop; i++)
				printf(" %lu, QL:%lu B:%llu T:%llu ECN:%u", i, ih.hop[i].GetQlen(), ih.hop[i].GetBytes(), ih.hop[i].GetTime(), cnp);
		printf("\n");
		fflush(stdout);
	#endif

}
uint32_t RdmaHw::GetPathIdKey(Ptr<RdmaQueuePair> qp, uint16_t pidToR, uint16_t pidAgg){
	uint32_t pathIdToR = static_cast<uint32_t>(pidToR);

	if (qp->aps.m_nhop == 1 || qp->aps.m_nhop == 3)
		return (pathIdToR << 16 | 0); // <ToR, 0> -> pathIdx
	else if (qp->aps.m_nhop == 5)
		return (pathIdToR << 16 | pidAgg); // <ToR, Agg> -> pathIdx
	else {
		return 0xffffffff;
	}
}

uint16_t RdmaHw::GetNextIfIndexAps(Ptr<RdmaQueuePair> qp, uint16_t pathIdx){
	// compute path Score
	double u = qp->aps.pidx2aps[pathIdx].m_avgUtil;
	double q = qp->aps.pidx2aps[pathIdx].m_avgNormalQlen;
	double e = qp->aps.pidx2aps[pathIdx].ecn;

	double score =  u * qp->aps.m_w.w_u + q * qp->aps.m_w.w_q + e * qp->aps.m_w.w_e;

	// update
	auto it = qp->aps.pidx2pathScore.find(pathIdx);
	for (auto &p2s : qp->aps.pidx2pathScore) {
		if (p2s.first != pathIdx) { // update other old path score, attenuation by 0.1
			qp->aps.pathScore2pidx.erase({p2s.second, p2s.first});
			p2s.second = p2s.second * qp->aps.m_w.alpha;
			qp->aps.pathScore2pidx.insert({p2s.second, p2s.first});
		} else { // 
			if (it != qp->aps.pidx2pathScore.end()) {
				double oldScore = it->second;
				qp->aps.pathScore2pidx.erase({oldScore, pathIdx});
			}
		}
	}
	
	qp->aps.pidx2pathScore[pathIdx] = score;
	qp->aps.pathScore2pidx.insert({score, pathIdx});	

	#ifdef APS_PATH_INFO
		printf("[INFO:APS_PATH][%ld]\tReceive PathIdx %u, util: %f, qlen: %f, ecn: %f, score: %f\n", Simulator::Now().GetTimeStep(), pathIdx, u, q, e, score);
		uint32_t rank = 0;
		for(auto &it : qp->aps.pathScore2pidx) {
			printf("[RANK%u][%u]\tordered map: pathIdx %u, score %f\n", rank++, this->m_node->GetId(), it.second, it.first);
		}
		printf("[SEND]\tSender Node %d, select next pathIdx: %u\n", this->m_node->GetId(), qp->aps.pathScore2pidx.begin()->second);
	#endif

	// get the optimal pathIdx, which with the lowest score
	return qp->aps.pathScore2pidx.begin()->second;


}
/*******************************
 * REPS
 ******************************/
void RdmaHw::receiveRepsAck(Ptr<RdmaQueuePair> qp, const Ptr<Packet> ack, CustomHeader &ch)
{
	uint8_t ecn = (ch.ack.flags >> qbbHeader::FLAG_CNP) & 1;
	FlowInfoTag fit;
	NS_ASSERT(ack->PeekPacketTag(fit));
	uint32_t ackEV = fit.GetFlowInfo();
	uint32_t ackPort = fit.GetSwitchPort();


    // ECN 信号则不学习 EV
    if (ecn) {
		#ifdef REPS_PROBE_INFO
		if (TRACE) {
			printf("[INFO:REPS_DROP][%ld][%u] ECN EV, drop it (Port %u) %u\n", Simulator::Now().GetTimeStep(), m_node->GetId(), ackPort, ackEV);
		}
		#endif
		return;
	}

    // 如果该 slot 本来 invalid，则有效数加一
    if (!qp->reps.repsBuffer[qp->reps.head].isValid) {
        qp->reps.numberOfValidEVs++;
		#ifdef REPS_PROBE_INFO
		if (TRACE) {
			printf("[INFO:REPS_PROBE][%ld][%u] receive EV, cache it (Port %u) %u\n", Simulator::Now().GetTimeStep(), m_node->GetId(), ackPort, ackEV);
		}
		#endif
    } else {
		uint32_t random_drop = rand() % 100;
		if (random_drop < 100) { 
			#ifdef REPS_PROBE_INFO
			if (TRACE) {
				printf("[INFO:REPS_PROBE][%ld][%u] receive EV, buffer full, override and cache new (Port %u) %u\n", Simulator::Now().GetTimeStep(), m_node->GetId(), ackPort, ackEV);
			}
			#endif
		} else {
			#ifdef REPS_PROBE_INFO
			if (TRACE) {
				printf("[INFO:REPS_PROBE][%ld][%u] receive EV, buffer full, but this time drop it (Port %u) %u\n", Simulator::Now().GetTimeStep(), m_node->GetId(), ackPort, ackEV);
			}
			#endif
			return;			
		}

	}

    // 写入 EV
    qp->reps.repsBuffer[qp->reps.head].cachedEV = ackEV;
	qp->reps.repsBuffer[qp->reps.head].switch_port = ackPort;
    qp->reps.repsBuffer[qp->reps.head].isValid = true;

    // qp->reps.head++
    qp->reps.head = (qp->reps.head + 1) % REPS_BUFFER_SIZE;

    // 退出 freezing mode
    if (qp->reps.isFreezingMode && Simulator::Now().GetTimeStep() > qp->reps.exitFreezingMode) {
		#ifdef REPS_FREEZING_INFO
		if(TRACE)
		printf("[REPS:Freezing][%ld][%u] Exit freezing mode\n", Simulator::Now().GetTimeStep(), m_node->GetId());
		#endif
        qp->reps.isFreezingMode = false;
		qp->ResetRepsBuffer(); // 退出 freezing mode 时清空 buffer，丢弃过期 EV
        qp->reps.exploreCnt = 1 * qp->m_cwnd; // 重新使用一个BDP探测路径
    }
}
 uint32_t RdmaHw::getNextEV(Ptr<RdmaQueuePair> qp){
    uint32_t offset;

    if (qp->reps.numberOfValidEVs > 0) { // 复用有效 EV
        // offset = (head - numberOfValidEVs) % size
        offset = (qp->reps.head - qp->reps.numberOfValidEVs) % REPS_BUFFER_SIZE;
        if (offset < 0) offset += REPS_BUFFER_SIZE;

        qp->reps.repsBuffer[offset].isValid = false;
        qp->reps.numberOfValidEVs--;
    }
    else { // 当前处于 freezing mode，保守起见，不随机选路，直接使用 head 指向的 slot
        offset = qp->reps.head;
        qp->reps.head = (qp->reps.head + 1) % REPS_BUFFER_SIZE;
		#ifdef REPS_FREEZING_INFO
		if(TRACE)
		printf("[REPS:Freezing][%ld][%u] Use frozen slot EV %u\n", Simulator::Now().GetTimeStep(), m_node->GetId(), qp->reps.repsBuffer[offset].cachedEV);
		#endif
    }

    return qp->reps.repsBuffer[offset].cachedEV;
}


/*******************************
 * INT-based Ordered Packet Spraying (IOPS)
 ******************************/
void RdmaHw::receiveIopsAck(Ptr<RdmaQueuePair> qp, const Ptr<Packet> ack, CustomHeader &ch)
{
	IntHeader &ih = ch.ack.ih;
	NS_ASSERT(ih.nhop <= IntHeader::maxHop);

	if (ih.nhop == 1 || ih.nhop == 3 || ih.nhop == 5) {
		qp->iops.m_nhop = ih.nhop;
	} else if (ih.nhop == 0){ // nvlink, do not update iops info
		return; 
	} else {
		printf("[ERROR]: INT hop number is %u, not supported\n", ih.nhop);
		return;
	}

	uint8_t ecn = (ch.ack.flags >> qbbHeader::FLAG_CNP) & 1;
	FlowInfoTag fit;
	NS_ASSERT(ack->PeekPacketTag(fit));
	uint32_t ackEV = fit.GetFlowInfo();

    // ECN 信号则不学习 EV
    if (ecn) return;

	// 2-packet 中的第一个数据包，缓存
	if (!qp->iops.receiveBundledEV) {
		qp->iops.receiveLastEV = ackEV;
		for (uint32_t i = 0; i < qp->iops.m_nhop; i++) {
			qp->iops.lastHop[i] = ih.hop[i];
		}
		qp->iops.receiveBundledEV = true;
		return;
	} else if (qp->iops.receiveLastEV != ackEV) {
		#ifdef IOPS_ACK_DEBUG
			printf("[DEBUG:IOPS_ACK][%ld][%u]: 2-packet bundling was broken, lastEV: %u, ackEV: %u\n", 
				Simulator::Now().GetTimeStep(), m_node->GetId(), qp->iops.receiveLastEV, ackEV);
		#endif
		// 新 EV，更新缓存
		qp->iops.receiveLastEV = ackEV;
		for (uint32_t i = 0; i < qp->iops.m_nhop; i++) {
			qp->iops.lastHop[i] = ih.hop[i];
		}
		qp->iops.receiveBundledEV = true;
		return;
	}
	#ifdef IOPS_ACK_DEBUG
	printf("[DEBUG:IOPS_ACK][%ld][%u]: 2-packet bundling was actived ackEV: %u\n", 
		Simulator::Now().GetTimeStep(), m_node->GetId(), ackEV);
	#endif

	// 2-packet 中的第二个数据包，进行激活(计算)和排序
	qp->iops.receiveBundledEV = false;
	
	double util = 0.0;
	double normalQlen = 0.0;
	for (uint32_t i = 0; i < qp->iops.m_nhop; i++) { // 计算平均 队列长度、链路利用率
		uint64_t tau = ih.hop[i].GetTimeDelta(qp->iops.lastHop[i]);
		double duration = tau * 1e-9; // sec
		uint64_t lineRate = ih.hop[i].GetLineRate();

		util += ih.hop[i].GetBytesDelta(qp->iops.lastHop[i]) * 8 / duration / lineRate; 
		normalQlen += ih.hop[i].GetQlen() / (lineRate * duration / 8); // avg normalize queue length
	}

	// for (uint32_t i = 0; i < qp->iops.m_nhop; i++) { // 计算峰值 队列长度、链路利用率
	// 	uint64_t tau = ih.hop[i].GetTimeDelta(qp->iops.lastHop[i]);
	// 	double duration = tau * 1e-9; // sec
	// 	uint64_t lineRate = ih.hop[i].GetLineRate();
	// 	double curUtil = ih.hop[i].GetBytesDelta(qp->iops.lastHop[i]) * 8 / duration / lineRate;
	// 	double curNormalQlen = ih.hop[i].GetQlen() / (lineRate * duration / 8); 

	// 	if(curUtil > util) util = curUtil;
	// 	if(curNormalQlen > normalQlen) normalQlen = curNormalQlen;
	// }	

	// 向 iopsBuffer 的 head 指向位置插入
    if (!qp->iops.iopsBuffer[qp->iops.head].isValid) { 
        qp->iops.numberOfValidEVs++;
    }
	
	// 写入 EV
    qp->iops.iopsBuffer[qp->iops.head].cachedEV = ackEV;
    qp->iops.iopsBuffer[qp->iops.head].isValid = true;
	qp->iops.iopsBuffer[qp->iops.head].m_util = util;
	qp->iops.iopsBuffer[qp->iops.head].m_normalQlen = normalQlen;

	// 在索引中重排序 优先按照队列长度排序；并更新head
	updateIndexByMetric(qp);

	#ifdef IOPS_CACHE_INFO
	// 按顺序打印 index 中有效缓存的分数
		printf("[INFO:IOPS_CACHE][%ld][%u]: IOPS Cache State: numberOfValidEVs: %u\n", 
			Simulator::Now().GetTimeStep(), m_node->GetId(), qp->iops.numberOfValidEVs);

		for (uint32_t i = 0; i < qp->iops.index.size(); i++) {
			uint32_t offset = qp->iops.index[i];
			if (qp->iops.iopsBuffer[offset].isValid) {
				printf("  Index %u: EV %u, util %.3lf, normalQlen %.3lf\n", 
					i, qp->iops.iopsBuffer[offset].cachedEV, 
					qp->iops.iopsBuffer[offset].m_util,
					qp->iops.iopsBuffer[offset].m_normalQlen);
			}
		}
		
	#endif


}

void RdmaHw::updateIndexByMetric(Ptr<RdmaQueuePair> qp) {

    // ======== 对 index 进行插入排序（仅对有效 item）========
    int n = qp->iops.index.size();                 // qp->iops.index 数组长度

    // i 从 1 开始，执行典型的插入排序
    for (int i = 1; i < n; ++i) {
        int key = qp->iops.index[i];               // key：本次要插入的位置的 vector 下标

        // 如果此 item 无效，则跳过排序，把它保持在末尾位置
        if (!qp->iops.iopsBuffer[key].isValid) continue;

        double key_metric = qp->iops.iopsBuffer[key].m_normalQlen;  // 当前元素的 metric

        int j = i - 1;                                 // 用 j 向前扫描已排序部分

        // 插入排序核心逻辑：
        // 只比较有效元素，且按照 metric 升序排序
        while (j >= 0) {

            // 如果 qp->iops.index[j] 对应的 item 无效，则跳过它
            if (!qp->iops.iopsBuffer[qp->iops.index[j]].isValid) {
                j--;                   // 无效项直接左移 j
                continue;
            }

            // 若已排序区元素的 metric <= 当前待插入 key 的 metric，则停止移动
            if (qp->iops.iopsBuffer[qp->iops.index[j]].m_normalQlen <= key_metric)
                break;

            // 否则需要把 qp->iops.index[j] 右移，为 key 腾位置
            qp->iops.index[j + 1] = qp->iops.index[j];
            j--;
        }

        // 将 key 插入到正确位置
        qp->iops.index[j + 1] = key;
    }

	// == head 指向替补位
	qp->iops.head = qp->iops.index[n - 1];

}


uint32_t RdmaHw::getCachedEV(Ptr<RdmaQueuePair> qp){
	uint32_t offset;

	for (uint32_t i = 0; i < qp->iops.index.size(); i++) {
		offset = qp->iops.index[i];
		if (qp->iops.iopsBuffer[offset].isValid) {
			break;
		}
		if ( i + 1 == qp->iops.index.size()) {
			printf("[ERROR]: IOPS index all invalid but numberOfValidEVs > 0\n");
			NS_ASSERT(false);
		}
	}

	qp->iops.iopsBuffer[offset].isValid = false;
	qp->iops.numberOfValidEVs--;


	return qp->iops.iopsBuffer[offset].cachedEV;
}



} /* namespace ns3 */
