#ifndef PSN_PATH_H
#define PSN_PATH_H

#include "ns3/tag.h"

#include <cstdint>
#include <vector>

namespace ns3 {

/** Per-logical-path sender mapping used by PSN-PATH. */
struct PsnPathMappingState
{
  uint16_t offset;
  uint32_t fpsn;
  bool active;

  bool probing;
  uint16_t candidateOffset;
  uint32_t probeStep;
  uint32_t packetsUntilProbe;
  uint32_t candidateAckCnt;
  bool currentNeedsBoundary;

  PsnPathMappingState ();
};

struct PsnPathQuality
{
  uint64_t ackCount;
  uint64_t nackCount;
  double score;

  PsnPathQuality ();
};

/**
 * Metadata carried by PSN-PATH data packets and echoed by ACK/NACK packets.
 * flowSport is the immutable QP source port; the UDP source port itself is
 * allowed to change for path selection.
 */
class PsnPathTag : public Tag
{
public:
  static TypeId GetTypeId (void);
  TypeId GetInstanceTypeId (void) const override;
  uint32_t GetSerializedSize (void) const override;
  void Serialize (TagBuffer buf) const override;
  void Deserialize (TagBuffer buf) override;
  void Print (std::ostream &os) const override;

  PsnPathTag ();

  void SetK (uint32_t k);
  uint32_t GetK (void) const;
  void SetOffset (uint16_t offset);
  uint16_t GetOffset (void) const;
  void SetFpsn (uint32_t fpsn);
  uint32_t GetFpsn (void) const;
  void SetFlowSport (uint16_t sport);
  uint16_t GetFlowSport (void) const;
  void SetProbe (bool probe);
  bool IsProbe (void) const;

private:
  uint32_t m_k;
  uint16_t m_offset;
  uint32_t m_fpsn;
  uint16_t m_flowSport;
  uint8_t m_probe;
};

enum class PsnRxResult
{
  IN_ORDER,
  CROSS_PATH_OOO,
  SAME_PATH_LOSS,
  REMAP_FIRST_PACKET,
  OLD_MAPPING_PACKET,
  DUPLICATE
};

struct PsnRxDecision
{
  PsnRxResult result;
  bool sendNack;
  uint32_t nackPsn;

  PsnRxDecision (PsnRxResult value = PsnRxResult::IN_ORDER,
                 bool nack = false,
                 uint32_t missing = 0);
};

uint32_t GetPsnFromSeq (uint32_t seq, uint32_t packetSize);
uint32_t GetLogicalPath (uint32_t psn, uint32_t k);
bool GetSamePathPredecessor (uint32_t psn,
                             uint32_t k,
                             uint32_t fpsn,
                             uint32_t &prevPsn);
uint16_t GetPsnPathSourcePort (
    uint32_t psn,
    uint32_t k,
    uint16_t basePort,
    const std::vector<PsnPathMappingState> &mapping);
double ComputePathScore (uint64_t ackCount, uint64_t nackCount, double beta);
uint16_t SelectProbeOrCurrentOffset (PsnPathMappingState &state);

} // namespace ns3

#endif /* PSN_PATH_H */
