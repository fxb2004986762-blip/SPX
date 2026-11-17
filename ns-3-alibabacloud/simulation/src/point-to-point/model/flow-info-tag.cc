/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2008 INRIA
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
 * Author: Mathieu Lacage <mathieu.lacage@sophia.inria.fr>
 */
#include "flow-info-tag.h"

namespace ns3 {

NS_OBJECT_ENSURE_REGISTERED (FlowInfoTag);

TypeId 
FlowInfoTag::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::FlowInfoTag")
    .SetParent<Tag> ()
    .AddConstructor<FlowInfoTag> ()
  ;
  return tid;
}
TypeId 
FlowInfoTag::GetInstanceTypeId (void) const
{
  return GetTypeId ();
}
uint32_t 
FlowInfoTag::GetSerializedSize (void) const
{
  return 8;
}
void 
FlowInfoTag::Serialize (TagBuffer buf) const
{
  buf.WriteU32 (m_flowInfo);
  buf.WriteU32 (m_switch_port);
}
void 
FlowInfoTag::Deserialize (TagBuffer buf)
{
  m_flowInfo = buf.ReadU32 ();
  m_switch_port = buf.ReadU32 ();
}
void 
FlowInfoTag::Print (std::ostream &os) const
{
  os << "FlowInfo=" << m_flowInfo << ", SwitchPort=" << m_switch_port;
}
FlowInfoTag::FlowInfoTag ()
  : Tag () 
{
}

FlowInfoTag::FlowInfoTag (uint32_t info)
  : Tag (),
    m_flowInfo (info)
{
}

FlowInfoTag::FlowInfoTag (uint32_t info, uint32_t switchPort)
  : Tag (),
    m_flowInfo (info),
    m_switch_port (switchPort)
{
}

void
FlowInfoTag::SetFlowInfo (uint32_t info)
{
  m_flowInfo = info;
}
uint32_t
FlowInfoTag::GetFlowInfo (void) const
{
  return m_flowInfo;
}
void
FlowInfoTag::SetSwitchPort (uint32_t switchPort)
{
  m_switch_port = switchPort;

}
uint32_t
FlowInfoTag::GetSwitchPort (void) const
{
  return m_switch_port;
}
}
// namespace ns3

