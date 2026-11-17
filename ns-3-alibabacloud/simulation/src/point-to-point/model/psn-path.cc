#include "psn-path.h"

#include "ns3/assert.h"

namespace ns3 {

NS_OBJECT_ENSURE_REGISTERED (PsnPathTag);

PsnPathMappingState::PsnPathMappingState ()
    : offset (0),
      fpsn (0),
      active (true),
      probing (false),
      candidateOffset (0),
      probeStep (10),
      packetsUntilProbe (10),
      candidateAckCnt (0),
      currentNeedsBoundary (false)
{
}

PsnPathQuality::PsnPathQuality ()
    : ackCount (0), nackCount (0), score (0.0)
{
}

TypeId
PsnPathTag::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::PsnPathTag")
                          .SetParent<Tag> ()
                          .AddConstructor<PsnPathTag> ();
  return tid;
}

TypeId
PsnPathTag::GetInstanceTypeId (void) const
{
  return GetTypeId ();
}

uint32_t
PsnPathTag::GetSerializedSize (void) const
{
  return 13;
}

void
PsnPathTag::Serialize (TagBuffer buf) const
{
  buf.WriteU32 (m_k);
  buf.WriteU16 (m_offset);
  buf.WriteU32 (m_fpsn);
  buf.WriteU16 (m_flowSport);
  buf.WriteU8 (m_probe);
}

void
PsnPathTag::Deserialize (TagBuffer buf)
{
  m_k = buf.ReadU32 ();
  m_offset = buf.ReadU16 ();
  m_fpsn = buf.ReadU32 ();
  m_flowSport = buf.ReadU16 ();
  m_probe = buf.ReadU8 ();
}

void
PsnPathTag::Print (std::ostream &os) const
{
  os << "K=" << m_k << ", offset=" << m_offset << ", FPSN=" << m_fpsn
     << ", flowSport=" << m_flowSport << ", probe=" << unsigned (m_probe);
}

PsnPathTag::PsnPathTag ()
    : m_k (0), m_offset (0), m_fpsn (0), m_flowSport (0), m_probe (0)
{
}

void PsnPathTag::SetK (uint32_t k) { m_k = k; }
uint32_t PsnPathTag::GetK (void) const { return m_k; }
void PsnPathTag::SetOffset (uint16_t offset) { m_offset = offset; }
uint16_t PsnPathTag::GetOffset (void) const { return m_offset; }
void PsnPathTag::SetFpsn (uint32_t fpsn) { m_fpsn = fpsn; }
uint32_t PsnPathTag::GetFpsn (void) const { return m_fpsn; }
void PsnPathTag::SetFlowSport (uint16_t sport) { m_flowSport = sport; }
uint16_t PsnPathTag::GetFlowSport (void) const { return m_flowSport; }
void PsnPathTag::SetProbe (bool probe) { m_probe = probe ? 1 : 0; }
bool PsnPathTag::IsProbe (void) const { return m_probe != 0; }

PsnRxDecision::PsnRxDecision (PsnRxResult value, bool nack, uint32_t missing)
    : result (value), sendNack (nack), nackPsn (missing)
{
}

uint32_t
GetPsnFromSeq (uint32_t seq, uint32_t packetSize)
{
  NS_ASSERT_MSG (packetSize != 0, "PSN-PATH packet size must be non-zero");
  return seq / packetSize;
}

uint32_t
GetLogicalPath (uint32_t psn, uint32_t k)
{
  NS_ASSERT_MSG (k != 0, "PSN-PATH logical path count must be non-zero");
  return psn % k;
}

bool
GetSamePathPredecessor (uint32_t psn,
                        uint32_t k,
                        uint32_t fpsn,
                        uint32_t &prevPsn)
{
  if (k == 0 || psn == fpsn || psn < k || psn - k < fpsn)
    {
      return false;
    }
  prevPsn = psn - k;
  return true;
}

uint16_t
GetPsnPathSourcePort (uint32_t psn,
                      uint32_t k,
                      uint16_t basePort,
                      const std::vector<PsnPathMappingState> &mapping)
{
  uint32_t logicalPath = GetLogicalPath (psn, k);
  NS_ASSERT_MSG (logicalPath < mapping.size (), "PSN-PATH mapping is incomplete");
  uint32_t port = static_cast<uint32_t> (basePort) + logicalPath
                  + mapping[logicalPath].offset;
  NS_ASSERT_MSG (port <= 65535, "PSN-PATH source port overflow");
  return static_cast<uint16_t> (port);
}

double
ComputePathScore (uint64_t ackCount, uint64_t nackCount, double beta)
{
  return static_cast<double> (ackCount) - beta * static_cast<double> (nackCount);
}

uint16_t
SelectProbeOrCurrentOffset (PsnPathMappingState &state)
{
  if (!state.probing)
    {
      return state.offset;
    }
  if (state.packetsUntilProbe == 0)
    {
      state.packetsUntilProbe = state.probeStep;
      state.currentNeedsBoundary = true;
      return state.candidateOffset;
    }
  --state.packetsUntilProbe;
  return state.offset;
}

} // namespace ns3
