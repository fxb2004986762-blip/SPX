/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2023 NUS
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Authors: Chahwan Song <songch@comp.nus.edu.sg>
 */


#include "ns3/letflow-routing.h"

#include "assert.h"
#include "ns3/assert.h"
#include "ns3/event-id.h"
#include "ns3/ipv4-header.h"
#include "ns3/log.h"
#include "ns3/nstime.h"
#include "ns3/object.h"
#include "ns3/packet.h"
#include "ns3/settings.h"
#include "ns3/simulator.h"
#include "point-to-point-utils.h"

NS_LOG_COMPONENT_DEFINE("LetflowRouting");

namespace ns3 {

/*---- letflowTag-Tag -----*/

LetflowTag::LetflowTag() {}
LetflowTag::~LetflowTag() {}
TypeId LetflowTag::GetTypeId(void) {
    static TypeId tid = TypeId("ns3::LetflowTag")
                            .SetParent<Tag>()
                            .AddConstructor<LetflowTag>();
    return tid;
}
void LetflowTag::SetPathId(uint64_t pathId) {
    m_pathId = pathId;
}
uint64_t LetflowTag::GetPathId(void) const {
    return m_pathId;
}
void LetflowTag::SetHopCount(uint32_t hopCount) {
    m_hopCount = hopCount;
}
uint32_t LetflowTag::GetHopCount(void) const {
    return m_hopCount;
}
TypeId LetflowTag::GetInstanceTypeId(void) const {
    return GetTypeId();
}
uint32_t LetflowTag::GetSerializedSize(void) const {
    return sizeof(uint64_t) +
           sizeof(uint32_t);
}
void LetflowTag::Serialize(TagBuffer i) const {
    i.WriteU64(m_pathId);
    i.WriteU32(m_hopCount);
}
void LetflowTag::Deserialize(TagBuffer i) {
    m_pathId = i.ReadU64();
    m_hopCount = i.ReadU32();
}
void LetflowTag::Print(std::ostream& os) const {
    os << "m_pathId=" << m_pathId;
    os << ", m_hopCount=" << m_hopCount;
}

/*----- Letflow-Route ------*/
uint32_t LetflowRouting::nFlowletTimeout = 0;
LetflowRouting::LetflowRouting() {
    m_isToR = false;
    m_switch_id = (uint32_t)-1;

    // set constants
    m_flowletTimeout = Time(MicroSeconds(100));
    m_agingTime = Time(MilliSeconds(10));
}

// it defines flowlet's 64bit key (order does not matter)
uint64_t LetflowRouting::GetQpKey(uint32_t dip, uint16_t sport, uint16_t dport, uint16_t pg) {
    return ((uint64_t)dip << 32) | ((uint64_t)sport << 16) | (uint64_t)pg | (uint64_t)dport;
}

TypeId LetflowRouting::GetTypeId(void) {
    static TypeId tid = TypeId("ns3::LetflowRouting")
                            .SetParent<Object>()
                            .AddConstructor<LetflowRouting>();
    return tid;
}

void LetflowRouting::SetSwitchInfo(bool isToR, uint32_t switch_id) {
    m_isToR = isToR;
    m_switch_id = switch_id;
}
uint32_t ip_to_node_id_letflow(uint32_t ip) { return (ip >> 8) & 0xffff; }
/* LetflowRouting's main function */
uint32_t LetflowRouting::RouteInput(Ptr<Packet> p, CustomHeader ch) {
    // Packet arrival time
    Time now = Simulator::Now();

    // Turn on aging event scheduler if it is not running
    if (!m_agingEvent.IsRunning()) {
        NS_LOG_FUNCTION("Letflow routing restarts aging event scheduling:" << m_switch_id << now);
        m_agingEvent = Simulator::Schedule(m_agingTime, &LetflowRouting::AgingEvent, this);
    }

    // get LetflowTag from packet
    LetflowTag letflowTag;
    bool found = p->PeekPacketTag(letflowTag);

    // get srcToRId, dstToRId
    assert(Settings::hostIp2SwitchId.find(ch.sip) != Settings::hostIp2SwitchId.end());  // Misconfig of Settings::hostIp2SwitchId - sip"
    assert(Settings::hostIp2SwitchId.find(ch.dip) != Settings::hostIp2SwitchId.end());  // Misconfig of Settings::hostIp2SwitchId - dip"
    // uint32_t srcToRId = Settings::hostIp2SwitchId[ch.sip];
    uint32_t dstToRId = 0;
    auto srcToRIds = Settings::hostIp2SwitchId.find(ch.sip)->second;
    auto dstToRIds = Settings::hostIp2SwitchId.find(ch.dip)->second;

    for(uint32_t srcToR : srcToRIds) {
        for(uint32_t dstToR : dstToRIds){
            // it should be not in the same pod
            NS_ASSERT_MSG(srcToR != dstToR, "Should not be in the same pod");
            if (m_isToR && !found) {
                if (m_letflowRoutingTable.find(dstToR) != m_letflowRoutingTable.end())
                    dstToRId = dstToR;
                else continue;
            }
        }
    }
    
    // get QpKey to find flowlet
    NS_ASSERT_MSG(ch.l3Prot == 0x11, "Only supports UDP data packets");
    uint64_t qpkey = GetQpKey(ch.dip, ch.udp.sport, ch.udp.dport, ch.udp.pg);
    
    
    if (m_isToR) {     // ToR switch
        if (!found) {  // sender-side
            /*---- choosing outPort ----*/
            NS_ASSERT_MSG(dstToRId == 0, "dstToR not found!");
            struct Flowlet* flowlet = NULL;
            auto flowletItr = m_flowletTable.find(qpkey);
            uint64_t selectedPath;

            // 1) when flowlet already exists
            if (flowletItr != m_flowletTable.end()) {
                flowlet = flowletItr->second;
                NS_ASSERT_MSG(flowlet != NULL, "Impossible in normal cases - flowlet is not correctly registered");

                if (now - flowlet->_activeTime <= m_flowletTimeout) {  // no timeout
                    // update flowlet info
                    flowlet->_activeTime = now;
                    flowlet->_nPackets++;

                    // update/measure CE of this outPort and add letflowTag
                    selectedPath = flowlet->_PathId;
                    uint32_t outPort = GetOutPortFromPath(selectedPath, 0);  // sender switch is 0th hop
                    letflowTag.SetPathId(selectedPath);
                    letflowTag.SetHopCount(0);

                    p->AddPacketTag(letflowTag);
                    NS_LOG_FUNCTION("SenderToR"
                                    << m_switch_id
                                    << "Flowlet exists"
                                    << "Path/outPort" << selectedPath << outPort << now);
                    #ifdef LETFLOW_INFO
                        printf("[INFO:LETFLOW][%ld]\t ToR Switch: flowlet exists (%u %u %u %u) switch:outPort %u:%u\n", 
                            Simulator::Now().GetTimeStep(), ip_to_node_id_letflow(ch.sip), ip_to_node_id_letflow(ch.dip), ch.udp.sport, ch.udp.dport, m_switch_id, outPort);
                    #endif
                    return outPort;
                }

                /*---- Flowlet Timeout ----*/
                // NS_LOG_FUNCTION("Flowlet expires, calculate the new port");
                selectedPath = GetRandomPath(dstToRId);
                LetflowRouting::nFlowletTimeout++;

                // update flowlet info
                flowlet->_activatedTime = now;
                flowlet->_activeTime = now;
                flowlet->_nPackets++;
                flowlet->_PathId = selectedPath;

                // update/add letflowTag
                uint32_t outPort = GetOutPortFromPath(selectedPath, 0);
                letflowTag.SetPathId(selectedPath);
                letflowTag.SetHopCount(0);

                p->AddPacketTag(letflowTag);
                NS_LOG_FUNCTION("SenderToR"
                                << m_switch_id
                                << "Flowlet exists & Timeout"
                                << "Path/outPort" << selectedPath << outPort << now);
                #ifdef LETFLOW_INFO
                    printf("[INFO:LETFLOW][%ld]\t ToR Switch: flowlet exists (%u %u %u %u),  but timeout, new path switch:outPort %u:%u\n", 
                        Simulator::Now().GetTimeStep(), ip_to_node_id_letflow(ch.sip), ip_to_node_id_letflow(ch.dip), ch.udp.sport, ch.udp.dport, m_switch_id, outPort);
                #endif                                
                return GetOutPortFromPath(selectedPath, letflowTag.GetHopCount());
            }
            // 2) flowlet does not exist, e.g., first packet of flow
            selectedPath = GetRandomPath(dstToRId);
            struct Flowlet* newFlowlet = new Flowlet;
            newFlowlet->_activeTime = now;
            newFlowlet->_activatedTime = now;
            newFlowlet->_nPackets = 1;
            newFlowlet->_PathId = selectedPath;
            m_flowletTable[qpkey] = newFlowlet;

            // update/add letflowTag
            uint32_t outPort = GetOutPortFromPath(selectedPath, 0);
            letflowTag.SetPathId(selectedPath);
            letflowTag.SetHopCount(0);

            p->AddPacketTag(letflowTag);
            NS_LOG_FUNCTION("SenderToR"
                            << m_switch_id
                            << "Flowlet does not exist"
                            << "Path/outPort" << selectedPath << outPort << now);
            #ifdef LETFLOW_INFO
                printf("[INFO:LETFLOW][%ld]\t ToR Switch: flowlet does not exist (%u %u %u %u), new path switch:outPort %u:%u\n", 
                    Simulator::Now().GetTimeStep(), ip_to_node_id_letflow(ch.sip), ip_to_node_id_letflow(ch.dip), ch.udp.sport, ch.udp.dport, m_switch_id, outPort);
            #endif                                  
            return GetOutPortFromPath(selectedPath, letflowTag.GetHopCount());
        }
        /*---- receiver-side ----*/
        // remove letflowTag from header
        p->RemovePacketTag(letflowTag);
        NS_LOG_FUNCTION("ReceiverToR"
                        << m_switch_id
                        << "Path" << letflowTag.GetPathId() << now);
        return LETFLOW_NULL;
    } else {  // agg/core switch
        // extract letflowTag
        NS_ASSERT_MSG(found, "If not ToR (leaf), letflowTag should be found");
        // get/update hopCount
        uint32_t hopCount = letflowTag.GetHopCount() + 1;
        letflowTag.SetHopCount(hopCount);

        // get outPort
        uint32_t outPort = GetOutPortFromPath(letflowTag.GetPathId(), hopCount);
        
        // Re-serialize letflowTag
        LetflowTag temp_tag;
        p->RemovePacketTag(temp_tag);
        p->AddPacketTag(letflowTag);
        NS_LOG_FUNCTION("Agg/CoreSw"
                        << m_switch_id
                        << "Path/outPort" << letflowTag.GetPathId() << outPort << now);
        return outPort;
    }
    NS_ASSERT_MSG("false", "This should not be occured");
}

// random selection
uint64_t LetflowRouting::GetRandomPath(uint32_t dstToRId) {
    auto pathItr = m_letflowRoutingTable.find(dstToRId);
    assert(pathItr != m_letflowRoutingTable.end());  // Cannot find dstToRId from ToLeafTable

    auto innerPathItr = pathItr->second.begin();
    std::advance(innerPathItr, rand() % pathItr->second.size());
    return *innerPathItr;
}

uint32_t LetflowRouting::GetOutPortFromPath(const uint32_t& path, const uint32_t& hopCount) {
    return ((uint8_t*)&path)[hopCount];
}

void LetflowRouting::SetOutPortToPath(uint32_t& path, const uint32_t& hopCount, const uint32_t& outPort) {
    ((uint8_t*)&path)[hopCount] = outPort;
}

void LetflowRouting::SetConstants(Time agingTime, Time flowletTimeout) {
    m_agingTime = agingTime;
    m_flowletTimeout = flowletTimeout;
    #ifdef LETFLOW_DEBUG
        m_agingTime = MicroSeconds(50);
        m_flowletTimeout = NanoSeconds(500);
    #endif    
}

void LetflowRouting::DoDispose() {
    for (auto i : m_flowletTable) {
        delete (i.second);
    }
    m_agingEvent.Cancel();
}

void LetflowRouting::AgingEvent() {
    /**
     * @brief This function is just to keep the flowlet table small as possible, to reduce memory overhead.
     */
    NS_LOG_FUNCTION(Simulator::Now());
    auto now = Simulator::Now();
    auto itr = m_flowletTable.begin();
    while (itr != m_flowletTable.end()) {
        if (now - ((itr->second)->_activeTime) > m_agingTime) {
            uint64_t qpkey = itr->first;
            uint32_t dport = static_cast<uint32_t>(qpkey & 0xffff) - 3; // subtract pg
            uint32_t sport = static_cast<uint32_t>((qpkey >> 16) & 0xffff);
            uint32_t dst = static_cast<uint32_t>(qpkey >> 32); 
            #ifdef LETFLOW_INFO
                printf("[INFO:LETFLOW][%ld]\t ToR switch %u, aging: delete flowlet (dst sport dport %u %u %u)\n", 
                    Simulator::Now().GetTimeStep(), m_switch_id, 
                    ip_to_node_id_letflow(dst), 
                    sport, dport);
            #endif               
            itr = m_flowletTable.erase(itr);
        } else {
            ++itr;
        }
    }
    m_agingEvent = Simulator::Schedule(m_agingTime, &LetflowRouting::AgingEvent, this);
}

}  // namespace ns3