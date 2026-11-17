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
#ifndef FLOW_TYPE_TAG_H
#define FLOW_TYPE_TAG_H

#include "ns3/tag.h"

namespace ns3 {

class FlowTypeTag : public Tag
{
public:
  static TypeId GetTypeId (void);
  virtual TypeId GetInstanceTypeId (void) const;
  virtual uint32_t GetSerializedSize (void) const;
  virtual void Serialize (TagBuffer buf) const;
  virtual void Deserialize (TagBuffer buf);
  virtual void Print (std::ostream &os) const;
  FlowTypeTag ();
  FlowTypeTag (uint32_t flowType);
  void SetFlowType (uint32_t flowType);
  uint32_t GetFlowType (void) const;
//   static uint32_t AllocateFlowType (void);
private:
  uint32_t m_flowType; // 0:ECMP 1:APS 2:RPS 3:FlowBender 4:LetFlow
};

} // namespace ns3

#endif /* FLOW_TYPE_TAG_H */
