#ifndef SWITCH_NODE_H
#define SWITCH_NODE_H

#include <unordered_map>
#include <ns3/node.h>
#include "qbb-net-device.h"
#include "switch-mmu.h"
#include "pint.h"
#include "point-to-point-utils.h"
#include "ns3/random-variable-stream.h"


namespace ns3 {

class Packet;

class SwitchNode : public Node{
	static const uint32_t pCnt = 1025;	// Number of ports used
	static const uint32_t qCnt = 8;	// Number of queues/priorities used
	uint32_t m_ecmpSeed;
	std::unordered_map<uint32_t, std::vector<int> > m_rtTable; // map from ip address (u32) to possible ECMP port (index of dev)
	std::set<uint32_t> active_ports;	// record active ports in switch

	// monitor of PFC
	uint32_t m_bytes[pCnt][pCnt][qCnt]; // m_bytes[inDev][outDev][qidx] is the bytes from inDev enqueued for outDev at qidx
	
	uint64_t m_txBytes[pCnt]; // counter of tx bytes
	uint64_t m_last_txBytes[pCnt]; // counter of last time tx bytes
	uint64_t m_dt_txBytes[pCnt]; // delta tx bytes in the interval

	uint32_t m_lastPktSize[pCnt];
	uint64_t m_lastPktTs[pCnt]; // ns
	uint64_t m_last_sample_TS[pCnt]; // ns
	uint64_t TIME_INTERVAL; // ns
	uint64_t m_sample_time_interval[pCnt]; // ns
	bool config_test = true;
	bool m_isTor = false;
	bool m_isTorCached = false;
	double m_u[pCnt];

protected:
	bool m_ecnEnabled;
	uint32_t m_hashType; // 0: MurmurHash3(EcmpHash), 1: CRC32, 2: JenkinsHash, 3: SymHash
	uint32_t m_lbMode; // 0: ECMP, 1: APS, 2: RPS, 3: FlowBender, 4: LetFlow, 5: REPS, 6: PSN-PATH
	uint32_t m_ccMode;
	uint64_t m_maxRtt;
	uint64_t m_iterator;
	uint32_t m_failed = 0; // 0: normal, 1: failed (drop all packets)

	uint32_t m_ackHighPrio; // set high priority for ACK/NACK

private:
	int GetOutDev(Ptr<Packet>, CustomHeader &ch);
	void SendToDev(Ptr<Packet>p, CustomHeader &ch);
	static uint32_t EcmpHash(const uint8_t* key, size_t len, uint32_t seed);
	void CheckAndSendPfc(uint32_t inDev, uint32_t qIndex);
	void CheckAndSendResume(uint32_t inDev, uint32_t qIndex);
	/** Load Balancing */ 
	uint32_t DoHash(const uint8_t *key, size_t len, uint32_t seed, uint32_t nexthop_size);
	/* 0: ECMP */
	uint32_t DoLbECMP(Ptr<const Packet> p, CustomHeader &ch, const std::vector<int> &nexthops);
	/* 1: APS */
	uint32_t DoLbAPS(Ptr<const Packet> p, CustomHeader &ch, const std::vector<int> &nexthops);
	/* 2: RPS */
	uint32_t DoLbRPS(Ptr<const Packet> p, CustomHeader &ch, const std::vector<int> &nexthops);
	/* 3: FlowBender */
	uint32_t DoLbFlowBender(Ptr<const Packet> p, CustomHeader &ch, const std::vector<int> &nexthops);
	/* 4: LetFlow */
	uint32_t DoLbLetFlow(Ptr<Packet> p, CustomHeader &ch, const std::vector<int> &nexthops);
	/* 5: REPS */
	uint32_t DoLbReps(Ptr<const Packet> p, CustomHeader &ch, const std::vector<int> &nexthops);
	/* Legacy IOPS helper; mode 6 is PSN-PATH. */
	uint32_t DoLbIops(Ptr<const Packet> p, CustomHeader &ch, const std::vector<int> &nexthops);

	/**  switch pkt drop   */
    double m_packetDropRate = 0.0;
    Ptr<UniformRandomVariable> m_dropRandomVariable;
    // Only host-facing ports are stored here.
    std::unordered_set<uint32_t> m_downlinkPorts;	

public:
	Ptr<SwitchMmu> m_mmu;
    bool m_isToR;                                 // true if ToR switch
    std::unordered_set<uint32_t> m_isToR_hostIP;  // host's IP connected to this ToR
	// trace
	TracedCallback<int, CustomHeader &> m_traceFoward; // trace the forwarding of packets

	static TypeId GetTypeId (void);
	SwitchNode();
	void SetEcmpSeed(uint32_t seed);
	void AddTableEntry(Ipv4Address &dstAddr, uint32_t intf_idx);
	void ClearTable();
	bool SwitchReceiveFromDevice(Ptr<NetDevice> device, Ptr<Packet> packet, CustomHeader &ch);
	void SwitchNotifyDequeue(uint32_t ifIndex, uint32_t qIndex, Ptr<Packet> p);
	void SetSwitchFailed();
	void SetSwitchUp();
	void SwitchDropPacket();
	bool IsTorSwitch();
    void SetPacketDropRate(double dropRate);
    void AddDownlinkPort(uint32_t port);
    bool IsDownlinkPort(uint32_t port) const;

	// for approximate calc in PINT
	int logres_shift(int b, int l);
	int log2apprx(int x, int b, int m, int l); // given x of at most b bits, use most significant m bits of x, calc the result in l bits
	
	// for monitor
	uint64_t last_txBytes[pCnt]; // last sampling of the counter of tx bytes
	double last_bw[pCnt]; // last sampling of bandwidth
	uint64_t last_port_qlen[pCnt]; // last sampling of the port length
	uint32_t m_SwitchFailedPktDropCnt;
	uint32_t select_port[5][10];
	uint64_t mon_timer;
	#ifdef HASH_EGRESSPORT_OBSERVATION
	std::map<std::tuple<uint32_t, uint32_t, uint32_t, uint16_t, uint16_t>, uint64_t> packetCountMap;
	#endif
	
	/**
	 * outoput format:
	 * time, sw_id, port_id, q_id, qlen, port_len
	 */
	void PrintSwitchQlen(FILE* qlen_output);
	/**
	 * outoput format:
	 * time, sw_id, port_id, txBytes
	 */
	void PrintSwitchBw(FILE* bw_output, uint32_t bw_mon_interval);
	void PrintSwitchStatistic();
	#ifdef HASH_EGRESSPORT_OBSERVATION
	void PrintSwitchHASHload(FILE* hash_load_output, uint32_t hash_mon_interval);
	#endif
};

} /* namespace ns3 */

#endif /* SWITCH_NODE_H */
