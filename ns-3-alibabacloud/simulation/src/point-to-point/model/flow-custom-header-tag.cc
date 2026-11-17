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
#include "flow-custom-header-tag.h"

namespace ns3 {

NS_OBJECT_ENSURE_REGISTERED (FlowCustomHeaderTag);

TypeId 
FlowCustomHeaderTag::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::FlowCustomHeaderTag")
    .SetParent<Tag> ()
    .AddConstructor<FlowCustomHeaderTag> ()
  ;
  return tid;
}
TypeId 
FlowCustomHeaderTag::GetInstanceTypeId (void) const
{
  return GetTypeId ();
}
uint32_t 
FlowCustomHeaderTag::GetSerializedSize (void) const
{
  return 8;
}
void 
FlowCustomHeaderTag::Serialize (TagBuffer buf) const
{
  buf.WriteU32 (m_psn);
}
void 
FlowCustomHeaderTag::Deserialize (TagBuffer buf)
{
  m_psn = buf.ReadU32 ();
}
void 
FlowCustomHeaderTag::Print (std::ostream &os) const
{
  os << "Psn=" << m_psn;
}
FlowCustomHeaderTag::FlowCustomHeaderTag ()
  : Tag () 
{
}

FlowCustomHeaderTag::FlowCustomHeaderTag (uint32_t psn)
  : Tag (),
    m_psn (psn)
{
}

void
FlowCustomHeaderTag::SetPsn (uint32_t psn)
{
  m_psn = psn;
}
uint32_t
FlowCustomHeaderTag::GetPsn (void) const
{
  return m_psn;
}

}
// namespace ns3

