# this is gdb script
set breakpoint pending on
# set scheduler-locking on

### SimAI front-end
## MockNcclGroup.cc
# MockNcclGroup()
# break MockNcclGroup.cc:49

## third.cc
# ReadFlowInput()
# break third.cc:55

# ScheduleFlowInputs()
# break third.cc:62
# break third.cc:77

# main()
# break third.cc:161

# gen_local_ring()
# break MockNcclGroup.cc:229 if type == 1

# genAllReduceRingFlowModels()
# break MockNcclGroup.cc:1094

# getFlowModels()
# break MockNcclGroup.cc:297 if rank == 18
# break MockNcclGroup.cc:326 if rank == 18
# break MockNcclGroup.cc:335 if rank == 18
# break MockNcclGroup.cc:329 if rank == 18


## Sys.cc
# ~Sys()
# break Sys.cc:46

# Sys()
# break Sys.cc:300

# try_register_event()
# break Sys.cc:try_register_event

# call_events()
# break Sys.cc:1693

# generate_collective_phase()
# break Sys.cc:1192 if id == 18
# break Sys.cc:1199 if id == 18

# proceed_to_next_vnet_baseline()
# break Sys.cc:1721 if id == 18

# notify_stream_added()
# break Sys.cc:948 if sys->id == 18


## RingTopology.cc


## StreamBaseline.cc
# break StreamBaseline.cc:31

# call()
# break StreamBaseline.cc:42


## NcclTreeFlowModel.cc
# run()
# break NcclTreeFlowModel.cc:235
# break NcclTreeFlowModel.cc:254 

# init_recv_ready()
# break NcclTreeFlowModel.cc:298 
# break NcclTreeFlowModel.cc:324
# break NcclTreeFlowModel.cc:327

# recv_ready()
# break NcclTreeFlowModel.cc:334

# insert_packets()
# break NcclTreeFlowModel.cc:102
# display *zero_latency_packets
# display *non_zero_latency_packets
# display toggle

# ready()
# break NcclTreeFlowModel.cc:516
# break NcclTreeFlowModel.cc:551


## PacketBundle.cc
# break PacketBundle.cc:78 


## AstraSimNetwork.cc
# sim_finish()
# break AstraSimNetwork.cc:78

# break AstraSimNetwork.cc:330


## entry.h
# main1()
# break entry.h:109
# break entry.h:400


## common.h
# ReadConf()
# break common.h:475
# break common.h:888
# break common.h:972

# SetupNetwork()
# break common.h:1473


### SimAI Backend ns3
## rdma-client.cc
# StartApplication()
# break rdma-client.cc:133

## rdma-hw.cc
# UpdateNextAvail()
# break rdma-hw.cc:1155 if hopCnt == 2
# break rdma-hw.cc:1131 if firstHop->GetId() == 12 
# break rdma-hw.cc:2095

# GetNxtPacket()
# break rdma-hw.cc:947
# break rdma-hw.cc:909 if this->m_node->GetId() == 8

# GetNextIfIndexAps()
# break rdma-hw.cc:1801
# break rdma-hw.cc:2005

# ReceiverCheckSeq()
# break rdma-hw.cc:726

# AddQueuePair()
# break rmda-hw.cc:348

# ReceiveAck()
break rdma-hw.cc:692


## rdma-queue-pair.cc
# ReScheduleTimeoutTimer()
# break rdma-queue-pair.cc:40


## switch-node.cc
# DoLbLetFlow()
# break switch-node.cc:168

# GetOutDev()
# break switch-node.cc:231

# SwitchNotifyDequeue()
# break switch-node.cc:475


## letflow-routing.cc
# RouteInput()
# break letflow-routing.cc:143


## qbb-net-device.cc
# SwitchDequeueAndTransmit()
# break qbb-net-device.cc:755

# DequeueAndTransmit()
# break qbb-net-device.cc:320


## qbb-channel.cc
# TransmitStart()
# break qbb-channel.cc:108 if txTime.GetTimeStep() == 1

### Debug exit
# break _exit
# break exit_group
# info stack

run

