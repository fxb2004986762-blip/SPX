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
#include "flow-type-tag.h"

namespace ns3 {

NS_OBJECT_ENSURE_REGISTERED (FlowTypeTag);

TypeId 
FlowTypeTag::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::FlowTypeTag")
    .SetParent<Tag> ()
    .AddConstructor<FlowTypeTag> ()
  ;
  return tid;
}
TypeId 
FlowTypeTag::GetInstanceTypeId (void) const
{
  return GetTypeId ();
}
uint32_t 
FlowTypeTag::GetSerializedSize (void) const
{
  return 4;
}
void 
FlowTypeTag::Serialize (TagBuffer buf) const
{
  buf.WriteU32 (m_flowType);
}
void 
FlowTypeTag::Deserialize (TagBuffer buf)
{
  m_flowType = buf.ReadU32 ();
}
void 
FlowTypeTag::Print (std::ostream &os) const
{
  os << "FlowType=" << m_flowType;
}
FlowTypeTag::FlowTypeTag ()
  : Tag () 
{
}

FlowTypeTag::FlowTypeTag (uint32_t type)
  : Tag (),
    m_flowType (type)
{
}

void
FlowTypeTag::SetFlowType (uint32_t type)
{
  m_flowType = type;
}
uint32_t
FlowTypeTag::GetFlowType (void) const
{
  return m_flowType;
}

// uint32_t 
// FlowTypeTag::AllocateFlowType (void)
// {
//   static uint32_t nextFlowType = 1;
//   uint32_t flowType = nextFlowType;
//   nextFlowId++;
//   return flowType;
// }

} // namespace ns3

