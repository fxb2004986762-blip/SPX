#ifndef RDMA_QUEUE_PAIR_H
#define RDMA_QUEUE_PAIR_H

#include <ns3/object.h>
#include <ns3/packet.h>
#include <ns3/ipv4-address.h>
#include <ns3/data-rate.h>
#include <ns3/event-id.h>
#include <ns3/custom-header.h>
#include <ns3/int-header.h>
#include "psn-path.h"
#include <vector>
#include <unordered_map>
#include <set>
#include <queue>
#include <map>

namespace ns3 {

struct PsnPathPacketState
{
	uint16_t offset;
	uint32_t fpsn;
	bool probe;

	PsnPathPacketState(uint16_t pathOffset = 0,
	                   uint32_t firstPsn = 0,
	                   bool isProbe = false)
		: offset(pathOffset), fpsn(firstPsn), probe(isProbe) {}
};

struct PsnPathTxState
{
	bool enabled;
	uint32_t k;
	uint16_t basePort;
	uint32_t packetSize;
	std::vector<PsnPathMappingState> mapping;
	std::vector<PsnPathQuality> quality;
	std::map<uint32_t, PsnPathPacketState> packetState;
	Time lastEvaluation;

	PsnPathTxState()
		: enabled(false), k(4), basePort(0), packetSize(0), lastEvaluation(0) {}
};

struct PsnPathRxState
{
	bool enabled;
	uint32_t k;
	std::vector<uint32_t> localFpsn;

	PsnPathRxState() : enabled(false), k(0) {}
};

class RdmaQueuePair : public Object {
public:
	Time startTime;
	Ipv4Address sip, dip;
	uint16_t sport, dport;
	uint64_t m_size, m_init_size, m_tag;
	uint32_t m_src, m_dest;
	uint64_t snd_nxt, snd_una; // next seq to send, the highest unacked seq
	uint16_t m_pg;
	uint16_t m_ipid;
	uint32_t m_win; // bound of on-the-fly packets
	uint64_t m_baseRtt; // base RTT of this qp
	DataRate m_max_rate; // max rate
	bool m_var_win; // variable window size
	bool m_ooo_ack; // support out-of-order ack
	Time m_nextAvail;	//< Soonest time of next send
	uint32_t wp; // current window of packets
	uint32_t lastPktSize;
	Callback<void> m_notifyAppFinish;
	Callback<void> m_notifyAppSent;
    int32_t m_flow_id;
	uint32_t m_flow_type;
	uint64_t rr_cnt; // round robin counter

	// for monitor
	uint64_t m_cnp_number;

	// SR: reorder window size
	uint64_t last_una;

	/******************************
	 * runtime states
	 *****************************/
	// Congestion control states
	uint32_t nvls_enable;
	DataRate m_rate;	//< Current rate
	struct {
		DataRate m_targetRate;	//< Target rate
		EventId m_eventUpdateAlpha;
		double m_alpha;
		bool m_alpha_cnp_arrived; // indicate if CNP arrived in the last slot
		bool m_first_cnp; // indicate if the current CNP is the first CNP
		EventId m_eventDecreaseRate;
		bool m_decrease_cnp_arrived; // indicate if CNP arrived in the last slot
		uint32_t m_rpTimeStage;
		EventId m_rpTimer;
	} mlx;
	struct {
		uint64_t m_lastUpdateSeq;
		DataRate m_curRate;
		IntHop hop[IntHeader::maxHop];
		uint32_t keep[IntHeader::maxHop];
		uint32_t m_incStage;
		double m_lastGap;
		double u;
		struct {
			double u;
			DataRate Rc;
			uint32_t incStage;
		}hopState[IntHeader::maxHop];
	} hp;
	struct{
		uint64_t m_lastUpdateSeq;
		DataRate m_curRate;
		uint32_t m_incStage;
		uint64_t lastRtt;
		double rttDiff;
	} tmly;
	struct{
		uint64_t m_lastUpdateSeq;
		uint32_t m_caState;
		uint64_t m_highSeq; // when to exit cwr
		double m_alpha;
		uint32_t m_ecnCnt;
		uint32_t m_batchSizeOfAlpha;
	} dctcp;
	struct{
		uint64_t m_lastUpdateSeq;
		DataRate m_curRate;
		uint32_t m_incStage;
	}hpccPint;
	struct{
		uint64_t m_maxCwnd;
		uint64_t m_preCwnd; // cwnd when last update happens
	}mprdma;	
	// Load balancing states
	// PSN-PATH (lb_mode = 6)
	PsnPathTxState psnPath;

	// flowbender
	uint32_t m_totalBytes;
	uint32_t m_markedBytes;
	uint32_t m_numCongestionRtt;
	uint64_t m_rttTick;

	// aps
	struct ApsInfo{
		bool initAps = false;
		IntHop hop[IntHeader::maxHop];
		double m_avgUtil; // average utilization
		double m_avgNormalQlen; // average queue length
		uint8_t ecn;
	};
	struct PathInfo{
		uint32_t pathID;
		IntHop hop[IntHeader::maxHop];
		uint16_t EVCache;
		uint32_t credit;
		double m_avgNormalQlen; // average queue length
		double m_avgUtil; // average utilization
	};
	struct Score{
		double m_score; // avgNormalQlen or avgUtil
		uint32_t pathID;
	};
	struct Cmp {
		bool operator()(Score const &a, Score const &b) const {
			if (a.m_score != b.m_score)
				return a.m_score < b.m_score;   // 按分数升序
			return a.pathID < b.pathID;         // ID 保证严格弱序
   		}	
	};
	struct BufferEntry{
		bool isValid = false;
		uint32_t cachedEV = 0;
		uint32_t switch_port = 0;
	};
	struct SendRecord{
		SendRecord(uint64_t _pkt_size, Time _send_time): pkt_size(_pkt_size), send_time(_send_time) {};
		uint64_t pkt_size;
		Time send_time;
	};
	struct {
		// aps-v2
		uint32_t m_numberOfValidPath = 0;
		uint16_t pathEV = 0; // path random entropy value
		uint32_t pathID = 0; // path ID 
		uint64_t max_rtt = 0; 
		uint64_t raw_rtt = 0;
		bool isFreezingMode = false;
		uint64_t exitFreezingMode = 0;
		uint32_t exploreCnt = 0;
		std::vector<uint32_t> apsBuffer;
		uint32_t head = 0;
		std::unordered_map<uint32_t, PathInfo> ID2pathInfo;
		std::set<Score, Cmp> orderedQlen; // ordered set
		std::unordered_map<uint32_t, std::set<Score>::iterator> pathID2itrQlen;
		std::set<Score, Cmp> orderedUtil; // ordered set
		std::unordered_map<uint32_t, std::set<Score>::iterator> pathID2itrUtil;
		std::unordered_map<uint32_t, std::vector<uint32_t>> pathID2switch; // store switch ID in path
		std::vector<double> historyUtil;


		// aps
		uint32_t m_lastUpdateSeq;
		std::unordered_map<uint16_t, ApsInfo> pidx2aps; // pathIdx -> ApsInfo
		std::unordered_map<uint32_t, uint16_t> pid2pidx; // pathId<pidToR, pidAgg> -> pathIdx
		std::unordered_map<uint16_t, uint32_t> pidx2pid; // pathIdx -> pathId<pidToR, pidAgg>
		std::set<std::pair<double, uint16_t>> pathScore2pidx; // <pathScore, pathId> set
		std::unordered_map<uint16_t, double> pidx2pathScore; // pathId -> pathScore
		std::unordered_map<uint16_t, uint8_t> pidx2validCnt; // pathIdx -> valid cnt
		bool initIf2aps; // whether all ToR ifIndex has been added to if2aps
		bool initCnt; // whether all switch ifIndex cnt has been got
		uint16_t m_ifIndex; // selected ToR interface index for next packet
		uint16_t m_ifIndexAgg; // selected Agg interface index for next packet
		uint16_t m_nhop; // number of hops
		uint32_t m_pathCnt; // number of Path
		std::unordered_map<uint16_t, uint32_t> m_pathToR2AggCnt; // ToR ifCnt：m_pathToR2AggCnt.size(), Agg ifCnt: m_pathToR2AggCnt[i]
		uint32_t m_pathToRCnt; // number of ToR outPort interfaces
		uint32_t m_pathAggCnt; // number of Agg outPort interfaces
		uint32_t m_freq; // frequency of INT update
		struct {
			double w_u, w_q, w_e;
			double alpha;
		}m_w;
	}aps;
	void ResetApsBuffer();

	// flowBender
	uint8_t m_ttl;
	uint32_t m_flow_bender_ecnCnt;

	// REPS
	struct {
		
		std::vector<BufferEntry> repsBuffer;
		uint32_t head = 0;
		uint32_t numberOfValidEVs = 0;
		bool isFreezingMode = false;
		uint32_t exploreCnt = 0;
		uint64_t exitFreezingMode = 0;

		uint64_t max_rtt = 0;
		uint64_t raw_rtt = 0;

	}reps;
	static const uint32_t FREEZING_TIMEOUT = 100000;  // 假设 100us（需要你根据论文设置）	
	void ResetRepsBuffer();


	// IOPS
	struct iopsBufferEntry{
		uint32_t cachedEV = 0;
		bool isValid = false;
		// IntHop hop[IntHeader::maxHop];
		double m_util; // average utilization
		double m_normalQlen; // average queue length
	};
	struct {
		std::vector<iopsBufferEntry> iopsBuffer;
		std::vector<uint32_t> index;

		IntHop lastHop[IntHeader::maxHop]; // cached waiting for next packet to activate
		uint32_t m_nhop = 0;

		uint32_t exploreCnt = 0; // 1 * BDP pkt number
		uint32_t numberOfValidEVs = 0;
		uint32_t head = 0;

		uint32_t sendLastEV = 0;
		uint32_t receiveLastEV = 0;
		bool sendBundledEV = false;
		bool receiveBundledEV = false;

	}iops;


	/***********
	 * methods
	 **********/
	static TypeId GetTypeId (void);
	RdmaQueuePair(uint16_t pg, Ipv4Address _sip, Ipv4Address _dip, uint16_t _sport, uint16_t _dport);
	void SetSize(uint64_t size);
	void SetWin(uint32_t win);
	void SetBaseRtt(uint64_t baseRtt);
	void SetRetransTimeOut(uint32_t retransTimeOut);
	void SetVarWin(bool v);
	void SetOooAck(bool ooo_ack);
	void SetAppNotifyCallback(Callback<void> notifyAppFinish);
	void SetAppSentCallback(Callback<void> notifyAppSent);
	void SetFlowId(int32_t v);
	void SetFlowType(uint32_t v);
	void SetApsDefaultW(uint32_t apsIndMask);

	uint64_t GetBytesLeft();
	uint64_t GetBytesLeftforSR(uint64_t m_seq);	
	uint64_t GetInitialSize();
	uint32_t GetSrc();
	uint32_t GetDest();
	uint64_t GetTag();
	void SetTag(uint64_t tag);void SetSrc(uint32_t src);void SetDest(uint32_t dest);void SetInitialSize(uint64_t size);
	uint32_t GetHash(void);
	bool Acknowledge(uint64_t ack);
	uint64_t GetOnTheFly();
	bool IsWinBound();
	uint64_t GetWin(); // window size calculated from m_rate
	bool IsFinished();
	uint64_t HpGetCurWin(); // window size calculated from hp.m_curRate, used by HPCC	
	
	// SR: for timeout
	uint32_t nic_id;
	typedef Callback<void, Ptr<RdmaQueuePair> > RdmaQpTriggerTransCb;
	RdmaQpTriggerTransCb m_rdmaQpTriggerTransCb;
	EventId 	m_retransEvent;
	Time		m_lastAckTime;
	Time 		m_retransTimeout;
	
	// RTO
    void RetransTimeout(void);
	void ReScheduleTimeoutTimer(Time send_time);
	void onFailureDetection(void); // 从网络反馈到故障，则进入freezing mode
	int DelFromSendTimes(Time send_time, uint64_t seq);
	bool RemoveSendRecord(uint64_t seq);
	void CreateSendRecord(uint64_t seq, uint32_t pkt_payload_size);
	void RecalculateRTO();
	void UpdateInflight(uint64_t old_snd_una, uint64_t seq, uint64_t psn);
	void UpdatePsnPathNackInflight(uint64_t old_snd_una, uint64_t epsn);
	uint32_t timeoutNums;
	uint32_t gbnNums;
	uint32_t retransNums;
	uint32_t probePktCount;
	uint32_t selectPathPktCount;	
	uint64_t inflight; // inflight bytes
	uint32_t fullMtu;
	uint32_t m_cwnd;
	uint32_t mtu;
	std::map<uint64_t, uint32_t> retransQueue;
	std::multimap<Time, uint64_t> send_times; // send time -> seq
	std::map<uint64_t, SendRecord> tx_bitmap; // seq -> SendRecord
	bool rtx_timeout_pending;
	Time rto_send_time;
	Time rtx_timeout;
    uint32_t m_retranstimes = 0;

	// Statistics
	uint32_t m_pktDropCnt;
};

class RdmaRxQueuePair : public Object { // Rx side queue pair
public:
	struct ECNAccount{
		uint16_t qIndex;
		uint8_t ecnbits;
		uint16_t qfb;
		uint16_t total;

		ECNAccount() { memset(this, 0, sizeof(ECNAccount));}
	};
	ECNAccount m_ecn_source;
	uint32_t sip, dip;
	uint16_t sport, dport;
	uint16_t m_ipid;
	uint64_t ReceiverNextExpectedSeq;
	Time m_nackTimer;
	int32_t m_milestone_rx;
	uint32_t m_lastNACK;
	EventId QcnTimerEvent; // if destroy this rxQp, remember to cancel this timer
    int32_t m_flow_id;

	// SR: reorder queue
    std::map<uint32_t,uint32_t> ooo_bitmap;
	uint32_t ooo_bitmap_cnt;
	uint32_t ooo_win_max;
	uint32_t bitmap_overflow_cnt;	
	uint64_t ack_timeout;

	// PSN-PATH per-QP receiver mapping boundaries.
	PsnPathRxState psnPath;

	static TypeId GetTypeId (void);
	RdmaRxQueuePair();
	uint32_t GetHash(void);
};

class RdmaQueuePairGroup : public Object {
public:
	std::vector<Ptr<RdmaQueuePair> > m_qps;
	//std::vector<Ptr<RdmaRxQueuePair> > m_rxQps;

	static TypeId GetTypeId (void);
	RdmaQueuePairGroup(void);
	uint32_t GetN(void);
	Ptr<RdmaQueuePair> Get(uint32_t idx);
	Ptr<RdmaQueuePair> operator[](uint32_t idx);
	void AddQp(Ptr<RdmaQueuePair> qp);
	//void AddRxQp(Ptr<RdmaRxQueuePair> rxQp);
	void Clear(void);
};

}

#endif /* RDMA_QUEUE_PAIR_H */
