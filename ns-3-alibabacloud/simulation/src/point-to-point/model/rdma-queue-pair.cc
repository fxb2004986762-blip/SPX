#include <ns3/hash.h>
#include <ns3/uinteger.h>
#include <ns3/seq-ts-header.h>
#include <ns3/udp-header.h>
#include <ns3/ipv4-header.h>
#include <ns3/simulator.h>
#include <ns3/settings.h>
#include "ns3/ppp-header.h"
#include "rdma-queue-pair.h"
#include "point-to-point-utils.h"
#define TRACE ((sip.Get() >> 8) & 0xffff) == SRC && ((dip.Get() >> 8) & 0xffff) == DST
namespace ns3 {

/**************************
 * RdmaQueuePair
 *************************/
TypeId RdmaQueuePair::GetTypeId (void)
{
static TypeId tid = TypeId ("ns3::RdmaQueuePair")
		.SetParent<Object> ()
		;
	return tid;
}

// SR: for timeout
void RdmaQueuePair::RetransTimeout(void){
	NS_ASSERT(Simulator::Now() == rtx_timeout); // only handle timeout when current time reaches the scheduled timeout

	rtx_timeout_pending = false;
	Simulator::Cancel(m_retransEvent);

	// 从发送时间中找到最早发送的一个包
	auto first_entry = send_times.begin();
	if(first_entry == send_times.end()){
		#ifdef SR_SND_RT_LOG
			printf("[LOG:SR_SND_RT][%ld][%u]\tflow timeout but no send_time\n", Simulator::Now().GetTimeStep(), ((sip.Get() >> 8) & 0xffff));
		#endif
		RecalculateRTO();
		return;
	}
	auto seq = first_entry->second;
	auto send_record = tx_bitmap.find(seq);
	NS_ASSERT(send_record != tx_bitmap.end());
	uint32_t pkt_size = send_record->second.pkt_size;
	
	#ifdef SR_SND_RT_LOG
		printf("[LOG:SR_SND_RT][%ld][%u:%u]\tflow timeout happen, seq %u trigger RTO, snd_una:%ld, snd_nxt:%ld, rate:%ldbps\n", Simulator::Now().GetTimeStep(), ((sip.Get() >> 8) & 0xffff), ((dip.Get() >> 8) & 0xffff), seq, snd_una, snd_nxt, m_rate.GetBitRate());
	#endif

	// 与snd_una比较，如果seq < snd_una，说明这个包已经被ack了，但发送时间还没被删除(一般不会发生)，直接删除发送时间记录并返回
	if (seq < snd_una) {
		#ifdef SR_SND_RT_LOG
			printf("[LOG:SR_SND_RT][%ld][%u:%u]\tflow timeout but seq %ld < snd_una %ld, just delete send time record\n", Simulator::Now().GetTimeStep(), ((sip.Get() >> 8) & 0xffff), ((dip.Get() >> 8) & 0xffff), seq, snd_una);
		#endif
		DelFromSendTimes(send_record->second.send_time, seq);
		RecalculateRTO();
		return;
	}

	// 发送时间需要清除，因为要计算下一个重传时间，避免陷入死循环，tx_bitmap不清除，交给真正发生重传时删除
	DelFromSendTimes(send_record->second.send_time, seq);
	// tx_bitmap.erase(send_record);

	inflight = inflight > fullMtu ? inflight - fullMtu : 0; // update inflight

    // snd_nxt = snd_una;
	// while(!retransQueue.empty()){ // fresh retrans queue
	// 	retransQueue.erase(retransQueue.begin());
	// }
	if(retransQueue.find(seq) == retransQueue.end()){ // 未在重传队列，插入
		retransQueue[seq] = GetBytesLeftforSR(seq);
	}
	// m_win -= fullMtu; // 缩减发送窗口（可选）
	m_rdmaQpTriggerTransCb(this); // 触发传输
    timeoutNums++;
	// printf("[LOG:RT_NUM][%ld][%u] time out cnt is %u\n", Simulator::Now().GetTimeStep(), this->nic_id, timeoutNums);

	// PSN-PATH uses the normal RTO as the fallback for flow-tail and
	// remapping-boundary loss.  A timed-out probe is also a negative
	// DT-Switch result, so stop sending traffic to that candidate.
	if (Settings::lb_mode == 6 && psnPath.enabled && psnPath.packetSize != 0) {
		uint32_t psn = static_cast<uint32_t>(seq / psnPath.packetSize);
		uint32_t logicalPath = GetLogicalPath(psn, psnPath.k);
		auto packetState = psnPath.packetState.find(psn);
		if (packetState != psnPath.packetState.end() && packetState->second.probe) {
			PsnPathMappingState &mapping = psnPath.mapping[logicalPath];
			mapping.probing = false;
			mapping.candidateAckCnt = 0;
			mapping.packetsUntilProbe = mapping.probeStep;
		} else {
			psnPath.quality[logicalPath].nackCount++;
		}
	}

	// for aps
	if (Settings::lb_mode == 1) { // 启发式网络故障检测
		// printf("[REPS][%ld] Retransmission timeout, max_rtt %lu, base_rtt %lu\n", Simulator::Now().GetTimeStep(), aps.max_rtt, m_baseRtt);
		// 发生超时，如果 max_rtt < 阈值，认为是网络故障造成的丢包
		if (aps.max_rtt < m_baseRtt * 10) {
			#ifdef APS_FREEZING_INFO
			printf("[APS:Freezing][%ld] Retransmission timeout, max_rtt %lu is smaller than threshold %lu, enter freezing mode\n", Simulator::Now().GetTimeStep(), aps.max_rtt, (uint64_t)(m_baseRtt * 10));
			#endif			
			onFailureDetection();
		} else { // 反之认为是网络拥塞造成的丢包
			#ifdef APS_FREEZING_INFO
			printf("[APS:Freezing][%ld] Retransmission timeout, but max_rtt %lu is larger than threshold %lu, consider it as congestion\n", Simulator::Now().GetTimeStep(), aps.max_rtt, (uint64_t)(m_baseRtt * 10));
			#endif
		}
	}

	// for reps
	if (Settings::lb_mode == 5) { // 启发式网络故障检测
		// printf("[REPS][%ld] Retransmission timeout, max_rtt %lu, base_rtt %lu\n", Simulator::Now().GetTimeStep(), reps.max_rtt, m_baseRtt);
		// 发生超时，如果 max_rtt < 阈值，认为是网络故障造成的丢包
		if (reps.max_rtt < m_baseRtt * 10) {
			#ifdef APS_FREEZING_INFO
			printf("[REPS:Freezing][%ld] Retransmission timeout, max_rtt %lu is smaller than threshold %lu, enter freezing mode\n", Simulator::Now().GetTimeStep(), aps.max_rtt, (uint64_t)(m_baseRtt * 10));
			#endif				
			onFailureDetection();
		} else { // 反之认为是网络拥塞造成的丢包
			#ifdef REPS_FREEZING_INFO
			printf("[REPS:Freezing][%ld] Retransmission timeout, but max_rtt %lu is larger than threshold %lu, consider it as congestion\n", Simulator::Now().GetTimeStep(), reps.max_rtt, (uint64_t)(m_baseRtt * 10));
			#endif
		}
	}

	RecalculateRTO();

	/**
	 * TODO: 更新超时重传时间阈值，避免因为网络拥塞导致过度触发超时重传
	 */	

}

void RdmaQueuePair::ReScheduleTimeoutTimer(Time send_time){
	// ignore this function when initialing
	if (startTime.GetTimeStep() > 0 && Simulator::Now() >= startTime) {

		if(!rtx_timeout_pending) {
			// timer is not running - start it
			rtx_timeout_pending = true;
			rtx_timeout = send_time + m_retransTimeout;
			rto_send_time = send_time;

				if (rtx_timeout <= Simulator::Now()) {
					m_retransEvent = Simulator::Schedule(NanoSeconds(0), &RdmaQueuePair::RetransTimeout, this);
				} else {
					m_retransEvent = Simulator::Schedule(rtx_timeout - Simulator::Now(), &RdmaQueuePair::RetransTimeout, this);
				}
				#ifdef SR_SND_RT_LOG
				if(TRACE)
					printf("[LOG:SR_SND_RT][%ld][%u] schedule timeout at %ld, rto_send_time: %ld, RTO_event %u\n", Simulator::Now().GetTimeStep(), ((sip.Get() >> 8) & 0xffff), rtx_timeout.GetTimeStep(), rto_send_time.GetTimeStep(), m_retransEvent.GetUid());
				#endif
		} else {
			// timer is already running - check if we need to reschedule it
			if (send_time + m_retransTimeout < rtx_timeout) {
				// RTO needs to expire earlier than it is currently set - reschedule it
				Simulator::Cancel(m_retransEvent);
				rtx_timeout_pending = false;
				ReScheduleTimeoutTimer(send_time);
			}
		}
	} else return;
}

void RdmaQueuePair::RecalculateRTO() {
    // we're no longer waiting for the packet we set the timer for -
    // figure out what the timer should be now.
	if(m_retransEvent.IsRunning()){
		Simulator::Cancel(m_retransEvent);
		#ifdef SR_SND_RT_LOG
		if(TRACE)
			printf("[LOG:SR_SND_RT][%ld][%u] recalculate RTO, cancel RTO_event %u\n", Simulator::Now().GetTimeStep(), ((sip.Get() >> 8) & 0xffff), m_retransEvent.GetUid());
		#endif
	}
	rtx_timeout_pending = false; // timer is set to not pending
    if (send_times.empty()) {
        // nothing left that we're waiting for
		if(!IsFinished()){
			// fprintf(stdout,
			// 		"[RTO_BROKEN] now=%lu qp=(%u,%u,%u,%u) "
			// 		"unfinished but send_times empty: snd_una=%lu snd_nxt=%lu size=%lu "
			// 		"inflight=%lu tx_bitmap=%lu retransQueue=%lu\n",
			// 		Simulator::Now().GetTimeStep(),
			// 		m_src, m_dest, sport, dport,
			// 		snd_una, snd_nxt, m_size,
			// 		inflight,
			// 		tx_bitmap.size(),
			// 		retransQueue.size());
			// fflush(stdout);
            if (snd_nxt == snd_una && GetBytesLeft() > 0) {
                inflight = 0;
            }
		}
		#ifdef SR_SND_RT_LOG
		if(TRACE)
		printf("[LOG:SR_SND_RT][%ld][%u:%u]\tno send_time, maybe qp has finished\n", Simulator::Now().GetTimeStep(), ((sip.Get() >> 8) & 0xffff), ((dip.Get() >> 8) & 0xffff));
		#endif
        return;
    }
    auto earliest_send_time = send_times.begin()->first;
    ReScheduleTimeoutTimer(earliest_send_time);
}

uint32_t qp_ip_to_node_id(Ipv4Address ip) { return (ip.Get() >> 8) & 0xffff; }
void RdmaQueuePair::onFailureDetection(void){ // 超时，则进入freezing mode
	if (Settings::lb_mode == 1) {
		if (!aps.isFreezingMode && aps.exploreCnt == 0) {
			aps.isFreezingMode = true;
			aps.exitFreezingMode = Simulator::Now().GetTimeStep() + FREEZING_TIMEOUT;
			#ifdef APS_FREEZING_INFO
			if(TRACE) {
				printf("[APS:Freezing][%ld] Detect network failure, enter freezing mode, exit time is %ld, (From Send: SDSD) %u %u %u %u %lu\n", 
					Simulator::Now().GetTimeStep(), aps.exitFreezingMode,
				qp_ip_to_node_id(sip), qp_ip_to_node_id(dip), sport, dport, m_size);
			}
			#endif
		}
	} else if (Settings::lb_mode == 5) {
		if (!reps.isFreezingMode && reps.exploreCnt == 0) {
			reps.isFreezingMode = true;
			reps.exitFreezingMode = Simulator::Now().GetTimeStep() + FREEZING_TIMEOUT;
			#ifdef REPS_FREEZING_INFO
			if(TRACE) {
				printf("[REPS:Freezing][%ld] Detect network failure, enter freezing mode, exit time is %ld, (From Send: SDSD) %u %u %u %u %lu\n", 
					Simulator::Now().GetTimeStep(), reps.exitFreezingMode,
				qp_ip_to_node_id(sip), qp_ip_to_node_id(dip), sport, dport, m_size);
			}
			#endif
		}
	}
}

int RdmaQueuePair::DelFromSendTimes(Time send_time, uint64_t seq) {
    //cout << eventlist().now() << " flowid " << _flow.flow_id() << " _send_times.erase " << time << " for " << seq << endl;
    auto snd_seq_range = send_times.equal_range(send_time);
	if (snd_seq_range.first == snd_seq_range.second) {
		#ifdef SR_SND_LOG
		if(TRACE) {
			printf("[INFO:SR_SND][%ld] seq %u, send time %u, not found\n", Simulator::Now().GetTimeStep(), seq, send_time.GetTimeStep());
		}	
		#endif
		return 0;
	}
    auto snd_it = snd_seq_range.first;
    while (snd_it != snd_seq_range.second) {
        if (snd_it->second == seq) {
			#ifdef SR_SND_LOG
			if(TRACE) {
				printf("[INFO:SR_SND][%ld] Delete send_time, seq %u, send time %u\n", Simulator::Now().GetTimeStep(), snd_it->second, snd_it->first.GetTimeStep());
			}	
			#endif		
            send_times.erase(snd_it);
			return 1;
        } else {
            ++snd_it;
        }
    }
	#ifdef SR_SND_LOG
	if(TRACE) {
		printf("[INFO:SR_SND][%ld] Delete send_time failed, seq %u, send time %u, not found\n", Simulator::Now().GetTimeStep(), seq, send_time.GetTimeStep());
	}	
	#endif
	return 0; // not found
}

void RdmaQueuePair::CreateSendRecord(uint64_t seq, uint32_t pkt_payload_size) {
    // assert(full_pkt_size > 64);
    NS_ASSERT(tx_bitmap.find(seq) == tx_bitmap.end());
	#ifdef SR_SND_LOG
	if(TRACE) {
		printf("[INFO:SR_SND][%ld] Create Send Record seq %u\n", Simulator::Now().GetTimeStep(), seq);
	}
	#endif
    tx_bitmap.emplace(seq, RdmaQueuePair::SendRecord(pkt_payload_size, Simulator::Now()));
    send_times.emplace(Simulator::Now(), seq);
}
bool RdmaQueuePair::RemoveSendRecord(uint64_t seq) {
    auto it = tx_bitmap.find(seq);
    if (it == tx_bitmap.end()) {
        return false;
    }

    Time send_time = it->second.send_time;

    bool removed_from_send_times = DelFromSendTimes(send_time, seq);

    tx_bitmap.erase(it);

    if (removed_from_send_times) {
        inflight = inflight > fullMtu ? inflight - fullMtu : 0;
    }

    return removed_from_send_times;
}
void RdmaQueuePair::UpdateInflight(uint64_t old_snd_una,
                                   uint64_t epsn,
                                   uint64_t psn) {
    /*
     * 1. 先处理累计 ACK。
     * 只要 epsn 推进，就说明 [old_snd_una, epsn) 已经累计确认。
     * 这部分不能依赖 psn 是否存在。
     */
    if (epsn > old_snd_una) {
        for (uint64_t seq = old_snd_una; seq < epsn; seq += mtu) {
            RemoveSendRecord(seq);
        }
    }

    /*
     * 2. 再处理选择性确认 psn。
     * psn 可能是乱序 ACK 对应的实际数据包 seq。
     * 如果它已经在累计 ACK 阶段被删除，RemoveSendRecord 会安全返回 false。
     */
    RemoveSendRecord(psn);

    /*
     * 3. 强一致性修正。
     * 如果没有任何未确认发送记录，并且当前发送指针和确认指针一致，
     * inflight 必须为 0。
     */
    if (send_times.empty() && snd_nxt == snd_una) {
        if (inflight != 0) {
            fprintf(stdout,
                    "[ERROR:RTO_FIX] now=%lu qp=(%u,%u,%u,%u) "
                    "snd_una=%lu snd_nxt=%lu size=%lu old_inflight=%lu "
                    "tx_bitmap=%lu retransQueue=%lu\n",
                    Simulator::Now().GetTimeStep(),
                    m_src, m_dest, sport, dport,
                    snd_una, snd_nxt, m_size,
                    inflight,
                    tx_bitmap.size(),
                    retransQueue.size());
            fflush(stdout);
        }
        inflight = 0;
    }
}

void RdmaQueuePair::UpdatePsnPathNackInflight(uint64_t old_snd_una,
                                              uint64_t epsn) {
	/*
	 * A PSN-PATH NACK carries two different pieces of information:
	 *   - epsn cumulatively acknowledges [old_snd_una, epsn);
	 *   - the tagged PSN identifies a missing packet.
	 *
	 * The missing PSN must not go through UpdateInflight(), whose final
	 * RemoveSendRecord(psn) operation is intended for a selectively ACKed
	 * packet.  Handle only the cumulative part here so a SendRecord created
	 * synchronously by the NACK-triggered retransmission remains eligible for
	 * RTO recovery.
	 */
	if (epsn > old_snd_una) {
		for (uint64_t seq = old_snd_una; seq < epsn; seq += mtu) {
			RemoveSendRecord(seq);
		}
	}
}


RdmaQueuePair::RdmaQueuePair(uint16_t pg, Ipv4Address _sip, Ipv4Address _dip, uint16_t _sport, uint16_t _dport){
	startTime = Simulator::Now();
	sip = _sip;
	dip = _dip;
	sport = _sport;
	dport = _dport;
	m_size = 0;
	m_init_size = 0;
	m_src = -1;
	m_dest = -1;
	m_tag = -1;
	snd_nxt = snd_una = 0;
	m_pg = pg;
	m_ipid = 0;
	m_win = 0;
	m_baseRtt = 0;
	m_max_rate = 0;
	m_var_win = false;
	m_ooo_ack = false;
	m_rate = 0;
	m_nextAvail = Time(0);
	m_ttl = 64; //ttl for flow bender
	m_flow_bender_ecnCnt = 0;
	rr_cnt = 0;
	inflight = 0;
	fullMtu = 0;
	mlx.m_alpha = 1;
	mlx.m_alpha_cnp_arrived = false;
	mlx.m_first_cnp = true;
	mlx.m_decrease_cnp_arrived = false;
	mlx.m_rpTimeStage = 0;
	hp.m_lastUpdateSeq = 0;
	for (uint32_t i = 0; i < sizeof(hp.keep) / sizeof(hp.keep[0]); i++)
		hp.keep[i] = 0;
	hp.m_incStage = 0;
	hp.m_lastGap = 0;
	hp.u = 1;
	mprdma.m_maxCwnd = 0;
	mprdma.m_preCwnd = 0;
	for (uint32_t i = 0; i < IntHeader::maxHop; i++){
		hp.hopState[i].u = 1;
		hp.hopState[i].incStage = 0;
	}

	tmly.m_lastUpdateSeq = 0;
	tmly.m_incStage = 0;
	tmly.lastRtt = 0;
	tmly.rttDiff = 0;

	dctcp.m_lastUpdateSeq = 0;
	dctcp.m_caState = 0;
	dctcp.m_highSeq = 0;
	dctcp.m_alpha = 1;
	dctcp.m_ecnCnt = 0;
	dctcp.m_batchSizeOfAlpha = 0;

	hpccPint.m_lastUpdateSeq = 0;
	hpccPint.m_incStage = 0;
	// flowbender
	m_totalBytes = 0;
	m_markedBytes = 0;
	m_numCongestionRtt = 0;	
	m_rttTick = 0;

	// aps
	aps.m_lastUpdateSeq = 0;
	aps.m_freq = 0;
	aps.initIf2aps = false;
	aps.initCnt = false;
	aps.m_ifIndex = 0;
	aps.m_ifIndexAgg = 0;
	aps.m_nhop = 0; 
	aps.m_pathCnt = 0;
	aps.m_pathToRCnt = 1;
	aps.m_pathAggCnt = 1;
	// path score parameters
	aps.m_w.w_e = 0.33;
	aps.m_w.w_u = 0.33;
	aps.m_w.w_q = 0.33;
	aps.m_w.alpha = 0.9;

	// for timeout
	m_lastAckTime = startTime;
	timeoutNums = 0;
	gbnNums = 0;
	retransNums = 0;
	mtu = 0;
	m_retransEvent.Cancel();
	probePktCount = 0;
	selectPathPktCount = 0;
	rtx_timeout_pending = false;

	// statistics
	m_pktDropCnt = 0;
	m_cnp_number = 0;
}
void RdmaQueuePair::SetApsDefaultW(uint32_t apsIndMask) {
	if (apsIndMask > 7) {
		printf("ERROR: apsMask %u not supported\n", apsIndMask);
		NS_ASSERT(false);
	}	
	uint8_t ecn_mask = apsIndMask & 0x1;
	uint8_t qlen_mask = (apsIndMask >> 1) & 0x1;
	uint8_t util_mask = (apsIndMask >> 2) & 0x1;
	uint8_t total = ecn_mask + qlen_mask + util_mask;
	if (total == 1) {
		aps.m_w.w_e = ecn_mask == 1 ? 1.0 : 0.0;
		aps.m_w.w_q = qlen_mask == 1 ? 1.0 : 0.0;
		aps.m_w.w_u = util_mask == 1 ? 1.0 : 0.0;
	} else if (total == 2) {
		aps.m_w.w_e = ecn_mask == 1 ? 0.5 : 0.0;
		aps.m_w.w_q = qlen_mask == 1 ? 0.5 : 0.0;
		aps.m_w.w_u = util_mask == 1 ? 0.5 : 0.0;
	}
}
void RdmaQueuePair::ResetApsBuffer() {
    for (auto i = aps.ID2pathInfo.begin(); i != aps.ID2pathInfo.end(); i++) {
        i->second.credit = 0;
		i->second.m_avgNormalQlen = 0;
		i->second.m_avgUtil = 0;
    }
    aps.m_numberOfValidPath = 0;
	aps.pathID = 0;
	aps.pathEV = 0;
}
// reps
void RdmaQueuePair::ResetRepsBuffer() {
    for (int i = 0; i < reps.repsBuffer.size(); i++) {
        reps.repsBuffer[i].cachedEV = 0;
        reps.repsBuffer[i].isValid = false;
        reps.repsBuffer[i].switch_port = 0;
    }
    reps.head = 0;
	reps.numberOfValidEVs = 0;
}
void RdmaQueuePair::SetFlowType(uint32_t v) {
	m_flow_type = v;
}
void RdmaQueuePair::SetFlowId(int32_t v) {
    m_flow_id = v;
}
void RdmaQueuePair::SetSize(uint64_t size){
	m_size = size;
}

void RdmaQueuePair::SetSrc(uint32_t src){
	m_src = src;
}

void RdmaQueuePair::SetDest(uint32_t dest){
	m_dest = dest;
}

uint32_t RdmaQueuePair::GetSrc(){
	return m_src;
}

uint32_t RdmaQueuePair::GetDest(){
	return m_dest;
}

void RdmaQueuePair::SetTag(uint64_t tag){
	m_tag = tag;
}

uint64_t RdmaQueuePair::GetTag(){
	return m_tag;
}

void RdmaQueuePair::SetInitialSize(uint64_t size){
	m_init_size = size;
}

uint64_t RdmaQueuePair::GetInitialSize(){
	return m_init_size;
}

void RdmaQueuePair::SetWin(uint32_t win){
	m_win = win;
	// std::cout << "set win: " << m_win << std::endl;
}

void RdmaQueuePair::SetBaseRtt(uint64_t baseRtt){
	m_baseRtt = baseRtt;
}

void RdmaQueuePair::SetRetransTimeOut(uint32_t retransTimeOut){
	// SR: for timeout 
	// printf("RTO set to %u ns\n", retransTimeOut);
	m_retransTimeout = NanoSeconds(retransTimeOut); // time unit is ns
	// m_retransEvent = Simulator::Schedule(m_retransTimeout, &RdmaQueuePair::RetransTimeout, this);
}

void RdmaQueuePair::SetVarWin(bool v){
	m_var_win = v;
}

void RdmaQueuePair::SetOooAck(bool ooo_ack){
	m_ooo_ack = ooo_ack;
}

void RdmaQueuePair::SetAppNotifyCallback(Callback<void> notifyAppFinish){
	m_notifyAppFinish = notifyAppFinish;
}

void RdmaQueuePair::SetAppSentCallback(Callback<void> notifyAppSent){
	m_notifyAppSent = notifyAppSent;
}


uint64_t RdmaQueuePair::GetBytesLeft(){
	return m_size >= snd_nxt ? m_size - snd_nxt : 0;
}
uint64_t RdmaQueuePair::GetBytesLeftforSR(uint64_t m_seq){
	// for SR
	return m_size >= m_seq ? m_size - m_seq : 0;
}

uint32_t RdmaQueuePair::GetHash(void){
	union{
		struct {
			uint32_t sip, dip;
			uint16_t sport, dport;
		};
		char c[12];
	} buf;
	buf.sip = sip.Get();
	buf.dip = dip.Get();
	buf.sport = sport;
	buf.dport = dport;
	return Hash32(buf.c, 12);
}

bool RdmaQueuePair::Acknowledge(uint64_t ack){
    if (ack > snd_una) {
        snd_una = ack;
        if (snd_nxt < snd_una)
			snd_nxt = snd_una;
        return true;
    }
    return false;
}

uint64_t RdmaQueuePair::GetOnTheFly(){
	if (m_ooo_ack) 
		return inflight;
	else
		return snd_nxt - snd_una; // go-back-n
}

bool RdmaQueuePair::IsWinBound(){
	uint64_t w = GetWin();
	if (w != 0 && mprdma.m_maxCwnd > 0) { // mprdma
		if ( w > inflight ) {
			if(TRACE)
				printf("[MPRDMA:IsWinBound][%ld][%u] can send w %lu, inflight %lu [mtu+preCwnd %lu, inflight+mtu %lu]\n", Simulator::Now().GetTimeStep(), ((sip.Get() >> 8) & 0xffff), w, inflight, mtu + mprdma.m_preCwnd, inflight + mtu);
			return false; // using mtu for speculate sending
		}
		else {
			if(TRACE)
				printf("[MPRDMA:IsWinBound][%ld][%u] cannot send w %lu, inflight %lu [mtu+preCwnd %lu, inflight+mtu %lu]\n", Simulator::Now().GetTimeStep(), ((sip.Get() >> 8) & 0xffff), w, inflight, mtu + mprdma.m_preCwnd, inflight + mtu);
			return true; // is win bound, you can't send pkt
		}
	} 
	return w != 0 && GetOnTheFly() >= w; // other cc
}

uint64_t RdmaQueuePair::GetWin(){
	if (m_win == 0)
		return 0;
	uint64_t w;
	if (mprdma.m_maxCwnd > 0) { // mprdma win-based cc
		w = m_win;
	}else if (m_var_win){
		w = m_win * m_rate.GetBitRate() / m_max_rate.GetBitRate();
		if (w == 0)
			w = 1; // must > 0
	}else{
		w = m_win;
	}
	return w;
}

uint64_t RdmaQueuePair::HpGetCurWin(){
	if (m_win == 0)
		return 0;
	uint64_t w;
	if (m_var_win){
		w = m_win * hp.m_curRate.GetBitRate() / m_max_rate.GetBitRate();
		if (w == 0)
			w = 1; // must > 0
	}else{
		w = m_win;
	}
	return w;
}

bool RdmaQueuePair::IsFinished(){
	return snd_una >= m_size;
}

/*********************
 * RdmaRxQueuePair
 ********************/
TypeId RdmaRxQueuePair::GetTypeId (void)
{
	static TypeId tid = TypeId ("ns3::RdmaRxQueuePair")
		.SetParent<Object> ()
		;
	return tid;
}

RdmaRxQueuePair::RdmaRxQueuePair(){
	sip = dip = sport = dport = 0;
	m_ipid = 0;
	ReceiverNextExpectedSeq = 0;
	m_nackTimer = MicroSeconds(10);
	m_milestone_rx = 0;
	m_lastNACK = 0;
	ooo_bitmap_cnt = 0;
	ooo_win_max = 0;
	bitmap_overflow_cnt = 0;
	ack_timeout = 0;
}

uint32_t RdmaRxQueuePair::GetHash(void){
	union{
		struct {
			uint32_t sip, dip;
			uint16_t sport, dport;
		};
		char c[12];
	} buf;
	buf.sip = sip;
	buf.dip = dip;
	buf.sport = sport;
	buf.dport = dport;
	return Hash32(buf.c, 12);
}

/*********************
 * RdmaQueuePairGroup
 ********************/
TypeId RdmaQueuePairGroup::GetTypeId (void)
{
	static TypeId tid = TypeId ("ns3::RdmaQueuePairGroup")
		.SetParent<Object> ()
		;
	return tid;
}

RdmaQueuePairGroup::RdmaQueuePairGroup(void){
}

uint32_t RdmaQueuePairGroup::GetN(void){
	return m_qps.size();
}

Ptr<RdmaQueuePair> RdmaQueuePairGroup::Get(uint32_t idx){
	return m_qps[idx];
}

Ptr<RdmaQueuePair> RdmaQueuePairGroup::operator[](uint32_t idx){
	return m_qps[idx];
}

void RdmaQueuePairGroup::AddQp(Ptr<RdmaQueuePair> qp){
	m_qps.push_back(qp);
}

#if 0
void RdmaQueuePairGroup::AddRxQp(Ptr<RdmaRxQueuePair> rxQp){
	m_rxQps.push_back(rxQp);
}
#endif

void RdmaQueuePairGroup::Clear(void){
	m_qps.clear();
}

}
