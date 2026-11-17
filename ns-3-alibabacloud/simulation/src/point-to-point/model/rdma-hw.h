#ifndef RDMA_HW_H
#define RDMA_HW_H

#include <ns3/rdma.h>
#include <ns3/rdma-queue-pair.h>
#include <ns3/node.h>
#include <ns3/custom-header.h>
#include "qbb-net-device.h"
#include <unordered_map>
#include <set>
#include "pint.h"
#include <random>

namespace ns3 {

struct RdmaInterfaceMgr{
	// The QbbDevice dev contains many qps in qpGrp
	Ptr<QbbNetDevice> dev;
	Ptr<RdmaQueuePairGroup> qpGrp;

	RdmaInterfaceMgr() : dev(NULL), qpGrp(NULL) {}
	RdmaInterfaceMgr(Ptr<QbbNetDevice> _dev){
		dev = _dev;
	}
};

class RdmaHw : public Object {
public:

	static TypeId GetTypeId (void);
	RdmaHw();

	Ptr<Node> m_node;
	DataRate m_minRate;		//< Min sending rate
	uint32_t m_mtu;
	uint32_t m_cc_mode;
	uint32_t m_lb_mode; // 0: ECMP, 1: APS, 2: RPS, 3: FlowBender, 4: LetFlow, 5: REPS, 6: PSN-PATH
	double m_nack_interval;
	uint32_t m_chunk;
	uint32_t m_ack_interval;
	uint32_t max_ooo_size; // SR: reorder window size
	bool m_backto0;
	bool m_var_win, m_ooo_ack, m_fast_react;
	bool m_rateBound;
	bool m_ack_psn; // whether to carry PSN in ACK
	bool m_has_win;
	uint32_t m_total_pause_times; 
	uint32_t m_paused_times;
	uint32_t m_retrans_time_out;
	std::vector<RdmaInterfaceMgr> m_nic; // list of running nic controlled by this RdmaHw
	std::unordered_map<uint64_t, Ptr<RdmaQueuePair> > m_qpMap; // mapping from uint64_t to qp
	std::unordered_map<uint64_t, Ptr<RdmaRxQueuePair> > m_rxQpMap; // mapping from uint64_t to rx qp
	std::unordered_map<uint32_t, std::vector<int> > m_rtTable; // map from ip address (u32) to possible ECMP port (index of dev)
	std::unordered_map<uint32_t, std::vector<int> > m_rtTable_nxthop_nvswitch; // map from ip address (u32) to possible ECMP port (index of dev) connected to nvswitch
	uint32_t m_gpus_per_server; // uesed for routing; if src and dst in the same server, then communicate by nvswitch.
	uint32_t nvls_enable;
	std::set<uint32_t> nvswitch_set;

	// qp complete callback
	typedef Callback<void, Ptr<RdmaQueuePair> > QpCompleteCallback;
	QpCompleteCallback m_qpCompleteCallback;
    typedef Callback<void, Ptr<RdmaQueuePair> > SendCompleteCallback;
    SendCompleteCallback m_sendCompleteCallback;

    // for monitor
	uint32_t traced_node; // the node id of the node that is being monitored
	std::vector<uint64_t> tx_bytes; // <port_id, tx_bytes>
	std::unordered_map<uint64_t, uint32_t> qp_cnp; // key of qp ---> received cnp number
	std::vector<uint64_t> last_tx_bytes; // last sampling value <port_id, tx_bytes>
	std::unordered_map<uint64_t, uint32_t> last_qp_cnp; // last sampling value key of qp ---> received cnp number
	std::unordered_map<uint64_t, uint64_t> last_qp_rate; // last sampling value key of qp ---> sending rate
	std::unordered_map<uint64_t, uint64_t> last_qp_ooo; // last sampling value key of qp ---> sending rate
	std::unordered_map<uint64_t, std::pair<uint16_t, uint16_t>> last_aps_selected;
	void UpdateTxBytes(uint32_t port_id, uint64_t bytes);
	void PrintHostBW(FILE* bw_output, uint32_t bw_mon_interval);
	void PrintQPRate(FILE* rate_output);
	void PrintRxQpOoO(FILE* ooo_output);
	void PrintQPCnpNumber(FILE* cnp_output);
	void PrintPathSelected(FILE* aps_selected_output);
	void PrintAPSSelected(FILE* aps_accuracy_output, 
		std::map<Ptr<Node>, std::map<Ptr<Node>, std::vector<std::pair<Ptr<Node>, uint32_t> >>> &Host, 
			std::map<Ptr<Node>, std::map<Ptr<Node>, std::vector<std::pair<Ptr<Node>, uint32_t> >>> &NetSwitch);

	// nvls
	void enable_nvls();
	void disable_nvls();
	void add_nvswitch(uint32_t nvswitch_id);

	void SetNode(Ptr<Node> node);
	void Setup(QpCompleteCallback cb,SendCompleteCallback send_cb); // setup shared data and callbacks with the QbbNetDevice
	static uint64_t GetQpKey(uint32_t dip, uint16_t sport, uint16_t pg); // get the lookup key for m_qpMap
	Ptr<RdmaQueuePair> GetQp(uint32_t dip, uint16_t sport, uint16_t pg); // get the qp
	uint32_t GetNicIdxOfQp(Ptr<RdmaQueuePair> qp); // get the NIC index of the qp
	void AddQueuePair(uint32_t src, uint32_t dest, uint64_t tag, uint64_t size, uint16_t pg, Ipv4Address _sip, Ipv4Address _dip, uint16_t _sport, uint16_t _dport, uint32_t win, uint64_t baseRtt, int32_t flow_id, Callback<void> notifyAppFinish, Callback<void> notifyAppSent); // add a new qp (new send)
	void DeleteQueuePair(Ptr<RdmaQueuePair> qp);

	Ptr<RdmaRxQueuePair> GetRxQp(uint32_t sip, uint32_t dip, uint16_t sport, uint16_t dport, uint16_t pg, bool create); // get a rxQp
	uint32_t GetNicIdxOfRxQp(Ptr<RdmaRxQueuePair> q); // get the NIC index of the rxQp
	void DeleteRxQp(uint32_t dip, uint16_t pg, uint16_t dport);
	void TriggerTrans(Ptr<RdmaQueuePair> qp);

	int CreateRxQp(uint32_t sip, uint32_t dip, uint16_t sport, uint16_t dport, uint16_t pg);
	int ReceiveUdp(Ptr<Packet> p, CustomHeader &ch);
	int ReceiveCnp(Ptr<Packet> p, CustomHeader &ch);
	int ReceiveAck(Ptr<Packet> p, CustomHeader &ch); // handle both ACK and NACK
	int Receive(Ptr<Packet> p, CustomHeader &ch); // callback function that the QbbNetDevice should use when receive packets. Only NIC can call this function. And do not call this upon PFC

	void PCIePause(uint32_t nic_idx, uint32_t qIndex);
	void PCIeResume(uint32_t nic_idx, uint32_t qIndex);
	void EnablePause();
	bool enable_pcie_pause; 

	void CheckandSendQCN(Ptr<RdmaRxQueuePair> q);
	int ReceiverCheckSeq(uint64_t seq, Ptr<RdmaRxQueuePair> q, uint32_t size);
	void AddHeader (Ptr<Packet> p, uint16_t protocolNumber);
	static uint16_t EtherToPpp (uint16_t protocol);

	void RecoverQueue(Ptr<RdmaQueuePair> qp);
	void QpComplete(Ptr<RdmaQueuePair> qp);
	void SetLinkDown(Ptr<QbbNetDevice> dev);

    int SendPacketComplete(Ptr<Packet> p, CustomHeader &ch);
    void SendComplete(Ptr<RdmaQueuePair> qp);

    // call this function after the NIC is setup
	void AddTableEntry(Ipv4Address &dstAddr, uint32_t intf_idx, bool is_nvswitch);
	void ClearTable();
	void RedistributeQp();

	Ptr<Packet> GetNxtPacket(Ptr<RdmaQueuePair> qp); // get next packet to send, inc snd_nxt

	/*******************************
	 * PSN-PATH (lb_mode = 6)
	 ******************************/
	uint32_t SelectNextTxPsn(Ptr<RdmaQueuePair> qp, bool &isRetransmission);
	uint16_t ApplyPsnPathMapping(Ptr<RdmaQueuePair> qp,
	                                   Ptr<Packet> packet,
	                                   uint32_t psn,
	                                   bool isRetransmission);
	PsnRxDecision ReceiverCheckSeqPsnPath(Ptr<RdmaRxQueuePair> qp,
	                                           uint32_t psn,
	                                           uint32_t packetSize,
	                                           const PsnPathTag &tag);
	void HandlePsnPathNack(Ptr<RdmaQueuePair> qp,
	                           uint32_t startPsn,
	                           uint32_t endPsn);
	void UpdatePsnPathFeedback(Ptr<RdmaQueuePair> qp,
	                                uint32_t psn,
	                                bool isNack,
	                                const PsnPathTag &tag);
	void EvaluatePsnPaths(Ptr<RdmaQueuePair> qp);
	void StartPathProbe(Ptr<RdmaQueuePair> qp,
	                        uint32_t logicalPath,
	                        uint16_t candidateOffset);
	void HandleProbeAck(Ptr<RdmaQueuePair> qp, uint32_t logicalPath);
	void HandleProbeNack(Ptr<RdmaQueuePair> qp, uint32_t logicalPath);
	void CommitPathRemap(Ptr<RdmaQueuePair> qp,
	                         uint32_t logicalPath,
	                         uint16_t newOffset);
	void PktSent(Ptr<RdmaQueuePair> qp, Ptr<Packet> pkt, Time interframeGap);
	void UpdateNextAvail(Ptr<RdmaQueuePair> qp, Time interframeGap, uint32_t pkt_size);
	void ChangeRate(Ptr<RdmaQueuePair> qp, DataRate new_rate);
	/******************************
	 * Mellanox's version of DCQCN
	 *****************************/
	double m_g; //feedback weight
	double m_rateOnFirstCNP; // the fraction of line rate to set on first CNP
	bool m_EcnClampTgtRate;
	double m_rpgTimeReset;
	double m_rateDecreaseInterval;
	uint32_t m_rpgThreshold;
	double m_alpha_resume_interval;
	DataRate m_rai;		//< Rate of additive increase
	DataRate m_rhai;		//< Rate of hyper-additive increase

	// the Mellanox's version of alpha update:
	// every fixed time slot, update alpha.
	void UpdateAlphaMlx(Ptr<RdmaQueuePair> q);
	void ScheduleUpdateAlphaMlx(Ptr<RdmaQueuePair> q);

	// Mellanox's version of CNP receive
	void cnp_received_mlx(Ptr<RdmaQueuePair> q);

	// Mellanox's version of rate decrease
	// It checks every m_rateDecreaseInterval if CNP arrived (m_decrease_cnp_arrived).
	// If so, decrease rate, and reset all rate increase related things
	void CheckRateDecreaseMlx(Ptr<RdmaQueuePair> q);
	void ScheduleDecreaseRateMlx(Ptr<RdmaQueuePair> q, uint32_t delta);

	// Mellanox's version of rate increase
	void RateIncEventTimerMlx(Ptr<RdmaQueuePair> q);
	void RateIncEventMlx(Ptr<RdmaQueuePair> q);
	void FastRecoveryMlx(Ptr<RdmaQueuePair> q);
	void ActiveIncreaseMlx(Ptr<RdmaQueuePair> q);
	void HyperIncreaseMlx(Ptr<RdmaQueuePair> q);

	/***********************
	 * High Precision CC
	 ***********************/
	double m_targetUtil;
	double m_utilHigh;
	uint32_t m_miThresh;
	bool m_multipleRate;
	bool m_sampleFeedback; // only react to feedback every RTT, or qlen > 0
	void HandleAckHp(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch);
	void UpdateRateHp(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch, bool fast_react);
	void UpdateRateHpTest(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch, bool fast_react);
	void FastReactHp(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch);
	void HandleAckMprdma(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch);
	
	/**********************
	 * TIMELY
	 *********************/
	double m_tmly_alpha, m_tmly_beta;
	uint64_t m_tmly_TLow, m_tmly_THigh, m_tmly_minRtt;
	void HandleAckTimely(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch);
	void UpdateRateTimely(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch, bool us);
	void FastReactTimely(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch);

	/**********************
	 * DCTCP
	 *********************/
	DataRate m_dctcp_rai;
	void HandleAckDctcp(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch);

	/*********************
	 * HPCC-PINT
	 ********************/
	uint32_t pint_smpl_thresh;
	void SetPintSmplThresh(double p);
	void HandleAckHpPint(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch);
	void UpdateRateHpPint(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch, bool fast_react);

	/*********************
	 * Flow Bender ECN check
	 ********************/
	std::unordered_map<uint32_t, std::vector<int> > m_flow_bender_table; // map from ip address (u32) to possible ECMP port (index of dev) connected to flow bender
	void cnp_received_flow_bender(Ptr<RdmaQueuePair> qp, uint32_t cnp);
	double m_flow_bender_T;
	uint32_t m_flow_bender_N;

	/*******************************
	 * Adaptive Packet Spraying (APS)
	 ******************************/
	uint32_t m_updateFreq; // frequency of INT update
	uint8_t m_apsIndMask; // 3 bit mask for INT indicator, 001:ecn, 010:qlen, 100:util, ..., 111:all
	uint32_t m_apsDefaultPortCnt; // default number of switch out ports counts
	uint32_t CREDIT_SIZE;
	uint32_t m_esti_window; // estimated window size in packets
	void HandleAckAps(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch);
	void UpdateIntAps(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch);
	void UpdateIntApsv2(Ptr<RdmaQueuePair> qp, Ptr<Packet> p, CustomHeader &ch);
	uint32_t GetPathIdKey(Ptr<RdmaQueuePair> qp, uint16_t pidToR, uint16_t pidAgg);
	uint32_t GetPathIdKey(uint16_t aggID, uint16_t coreID);
	uint16_t GetNextIfIndexAps(Ptr<RdmaQueuePair> qp, uint16_t pathId);
	uint16_t GetNextIfIndexAps(Ptr<RdmaQueuePair> qp);
	// monitor
	Callback<void, Ptr<RdmaRxQueuePair>, uint32_t> m_oooBufferChangeCallback;

	/*******************************
	 * REPS
	 ******************************/
	uint32_t REPS_BUFFER_SIZE;
	static const uint32_t EVS_SIZE = 65536;
	static const uint32_t NUM_PKTS_BDP = 306;        // 伪代码中的 NUM_PKTS_BDP
												// now() 单位需要与此一致
	uint32_t getNextEV(Ptr<RdmaQueuePair> qp);
	void receiveRepsAck(Ptr<RdmaQueuePair> qp, const Ptr<Packet> p, CustomHeader &ch);

	/*******************************
	 * INT-based Ordered Packet Spraying (IOPS)
	 ******************************/
	uint32_t IOPS_BUFFER_SIZE;
	void receiveIopsAck(Ptr<RdmaQueuePair> qp, const Ptr<Packet> ack, CustomHeader &ch);
	uint32_t getCachedEV(Ptr<RdmaQueuePair> qp);
	void updateIndexByMetric(Ptr<RdmaQueuePair> qp);

	/*******************************
	 * PSN-PATH
	 ******************************/	
	uint32_t PSN_PATH_K;

};

} /* namespace ns3 */

#endif /* RDMA_HW_H */
