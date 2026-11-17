#include "ns3/psn-path.h"
#include "ns3/rdma-hw.h"
#include "ns3/test.h"

using namespace ns3;

static void
IgnoreOooUpdate (Ptr<RdmaRxQueuePair>, uint32_t)
{
}

class PsnPathAlgorithmTest : public TestCase
{
public:
  PsnPathAlgorithmTest () : TestCase ("PSN-PATH mapping and continuity helpers") {}

private:
  void DoRun (void) override
  {
    NS_TEST_EXPECT_MSG_EQ (GetPsnFromSeq (7000, 1000), 7u, "seq to PSN");
    NS_TEST_EXPECT_MSG_EQ (GetLogicalPath (11, 4), 3u, "logical path mapping");

    uint32_t predecessor = 0;
    NS_TEST_EXPECT_MSG_EQ (
        GetSamePathPredecessor (11, 4, 3, predecessor), true, "valid predecessor");
    NS_TEST_EXPECT_MSG_EQ (predecessor, 7u, "same-path predecessor");
    NS_TEST_EXPECT_MSG_EQ (
        GetSamePathPredecessor (11, 4, 11, predecessor), false, "FPSN boundary");

    std::vector<PsnPathMappingState> mapping (4);
    mapping[3].offset = 4;
    NS_TEST_EXPECT_MSG_EQ (GetPsnPathSourcePort (7, 4, 10000, mapping),
                           10007,
                           "source port mapping");
    NS_TEST_EXPECT_MSG_EQ (ComputePathScore (5, 2, 0.5), 4.0, "path score");

    PsnPathTag sentTag;
    sentTag.SetK (4);
    sentTag.SetOffset (8);
    sentTag.SetFpsn (11);
    sentTag.SetFlowSport (10004);
    sentTag.SetProbe (true);
    Ptr<Packet> packet = Create<Packet> (1000);
    packet->AddPacketTag (sentTag);
    PsnPathTag receivedTag;
    NS_TEST_EXPECT_MSG_EQ (packet->PeekPacketTag (receivedTag), true, "tag present");
    NS_TEST_EXPECT_MSG_EQ (receivedTag.GetFpsn (), 11u, "tag FPSN");
    NS_TEST_EXPECT_MSG_EQ (receivedTag.IsProbe (), true, "tag probe flag");

    Ptr<RdmaHw> hw = CreateObject<RdmaHw> ();
    hw->m_mtu = 1000;
    hw->max_ooo_size = 64;
    hw->m_oooBufferChangeCallback = MakeCallback (&IgnoreOooUpdate);

    PsnPathTag baseTag;
    baseTag.SetK (4);
    baseTag.SetFpsn (3);
    Ptr<RdmaRxQueuePair> lossQp = CreateObject<RdmaRxQueuePair> ();
    lossQp->ReceiverNextExpectedSeq = 7000;
    PsnRxDecision loss = hw->ReceiverCheckSeqPsnPath (lossQp, 11, 1000, baseTag);
    bool samePathLoss = loss.result == PsnRxResult::SAME_PATH_LOSS;
    NS_TEST_EXPECT_MSG_EQ (samePathLoss, true, "same-path gap detected");
    NS_TEST_EXPECT_MSG_EQ (loss.nackPsn, 7u, "selective NACK PSN");

    PsnPathTag remapTag;
    remapTag.SetK (4);
    remapTag.SetFpsn (11);
    Ptr<RdmaRxQueuePair> remapQp = CreateObject<RdmaRxQueuePair> ();
    remapQp->ReceiverNextExpectedSeq = 7000;
    PsnRxDecision remap = hw->ReceiverCheckSeqPsnPath (remapQp, 11, 1000, remapTag);
    bool remapBoundary = remap.result == PsnRxResult::REMAP_FIRST_PACKET;
    NS_TEST_EXPECT_MSG_EQ (remapBoundary, true, "remap boundary suppresses false loss");
    NS_TEST_EXPECT_MSG_EQ (remap.sendNack, false, "no NACK across remap boundary");

    Ptr<RdmaQueuePair> txQp = CreateObject<RdmaQueuePair> (
        3, Ipv4Address ("10.0.99.1"), Ipv4Address ("10.0.227.1"), 10000, 100);
    txQp->mtu = 1000;
    txQp->fullMtu = 1000;
    txQp->inflight = 2000;
    txQp->CreateSendRecord (659000, 1000);
    txQp->CreateSendRecord (1008000, 1000);

    txQp->UpdatePsnPathNackInflight (659000, 660000);

    NS_TEST_EXPECT_MSG_EQ (txQp->tx_bitmap.count (659000),
                           0u,
                           "PSN-PATH NACK applies cumulative ACK information");
    NS_TEST_EXPECT_MSG_EQ (txQp->tx_bitmap.count (1008000),
                           1u,
                           "PSN-PATH NACK preserves the missing packet record");
    NS_TEST_EXPECT_MSG_EQ (txQp->send_times.size (),
                           1u,
                           "missing packet remains covered by RTO");
    NS_TEST_EXPECT_MSG_EQ (txQp->inflight,
                           1000u,
                           "only cumulatively acknowledged bytes leave inflight");
  }
};

class PsnPathTestSuite : public TestSuite
{
public:
  PsnPathTestSuite () : TestSuite ("psn-path", UNIT)
  {
    AddTestCase (new PsnPathAlgorithmTest, TestCase::QUICK);
  }
};

static PsnPathTestSuite g_psnPathTestSuite;
