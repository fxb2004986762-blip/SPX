/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
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
*/

#undef PGO_TRAINING
#define PATH_TO_PGO_CONFIG "path_to_pgo_config"

#include "astra-sim/system/AstraNetworkAPI.hh"
#include "astra-sim/system/Sys.hh"
#include "astra-sim/system/RecvPacketEventHadndlerData.hh"
#include "astra-sim/system/Common.hh"
#include "astra-sim/system/MockNcclLog.h"
#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/csma-module.h"
#include "ns3/internet-module.h"
#include "ns3/network-module.h"
#include "entry.h"
#include <execinfo.h>
#include <fstream>
#include <iostream>
#include <queue>
#include <stdio.h>
#include <string>
#include <thread>
#include <unistd.h>
#include <vector>

#ifdef NS3_MTP
#include "ns3/mtp-interface.h"
#endif
#ifdef NS3_MPI
#include "ns3/mpi-interface.h"
#include <mpi.h>
#endif

#define RESULT_PATH "./ncclFlowModel_"

using namespace ns3;
using namespace std;


void ReadFlowInput(){
	if (flow_input.idx < flow_num){
		flowf >> flow_input.src >> flow_input.dst >> flow_input.pg >> flow_input.maxPacketCount >> flow_input.start_time >> flow_input.tag;
        flow_input.dport = 100;
		NS_ASSERT(n.Get(flow_input.src)->GetNodeType() == 0 && n.Get(flow_input.dst)->GetNodeType() == 0);
	}
}
void ScheduleFlowInputs(){
    // printf("[ScheduleFlowInputs] time: %f, flow idx: %u\n", Simulator::Now().GetSeconds(), flow_input.idx);
    std::cout<< "[ScheduleFlowInputs] time: " << Simulator::Now().GetSeconds() << ", flow idx: " << flow_input.idx << std::endl;
    fflush(stdout);
	while (flow_input.idx < flow_num && Seconds(flow_input.start_time) == Simulator::Now()){
		uint32_t port = portNumber[flow_input.src][flow_input.dst]++; // get a new port number 
        bool nvls_on = false;

		RdmaClientHelper clientHelper(flow_input.pg, serverAddress[flow_input.src], serverAddress[flow_input.dst], 
            port, flow_input.dport, flow_input.maxPacketCount, has_win?(global_t==1?maxBdp:pairBdp[n.Get(flow_input.src)][n.Get(flow_input.dst)]):0, 
            global_t==1?maxRtt:pairRtt[flow_input.src][flow_input.dst], flow_input.tag, flow_input.src, flow_input.dst);
		// ApplicationContainer appCon = clientHelper.Install(n.Get(flow_input.src));

        clientHelper.SetAttribute("StatFlowID", IntegerValue(flow_input.idx));
        if(nvls_on) clientHelper.SetAttribute("NVLS_enable", UintegerValue (1));
        {
            #ifdef NS3_MTP
            MtpInterface::explicitCriticalSection cs;
            #endif
            gen_RxQp(flow_input.src, flow_input.dst, port, flow_input.dport, flow_input.pg, flow_input.maxPacketCount); // receiver gen RxQp in advance
            ApplicationContainer appCon = clientHelper.Install(n.Get(flow_input.src));
            appCon.Start(Time(0));

            #ifdef NS3_MTP
            cs.ExitSection();
            #endif
        }        

		// get the next flow input
		flow_input.idx++;
		ReadFlowInput();
	}

	// schedule the next time to run this function
	if (flow_input.idx < flow_num){
		Simulator::Schedule(Seconds(flow_input.start_time)-Simulator::Now(), ScheduleFlowInputs);
	}else { // no more flows, close the file
		flowf.close();
	}
}

struct user_param {
  int thread;
  string workload;
  string network_topo;
  string network_conf;
  user_param() {
    thread = 1;
    workload = "";
    network_topo = "";
    network_conf = "";
  };
  ~user_param(){};
};

static int user_param_prase(int argc,char * argv[],struct user_param* user_param){
  int opt;
  while ((opt = getopt(argc,argv,"ht:w:g:s:n:c:"))!=-1){
    switch (opt)
    {
    case 'h':
      /* code */
      std::cout<<"-t    number of threads,default 1"<<std::endl;
      std::cout<<"-w    workloads default none "<<std::endl;
      std::cout<<"-n    network topo"<<std::endl;
      std::cout<<"-c    network_conf"<<std::endl;
      return 1;
      break;
    case 't':
      user_param->thread = stoi(optarg);
      break;
    case 'w':
      user_param->workload = optarg;
      break;
    case 'n':
      user_param->network_topo = optarg;
      break;
    case 'c':
      user_param->network_conf = optarg;
      break;
    default:
      std::cerr<<"-h    help message"<<std::endl;
      return 1;
    }
  }
  return 0 ;
}

int main(int argc, char *argv[])
{
    struct user_param user_param;

    if(user_param_prase(argc,argv,&user_param)){
        return 0;
    }
    #ifdef NS3_MTP
    printf("ENABLE MTP with %d threads\n", user_param.thread);
    MtpInterface::Enable(user_param.thread);
    #endif
    
    main1(user_param.network_topo,user_param.network_conf);

    if (flow_num > 0) {
        // generate flows
        ReadFlowInput();
        Simulator::Schedule(Seconds(0), &ScheduleFlowInputs);
    }    

    schedule_monitor();

    // LogComponentEnable("OnOffApplication", LOG_LEVEL_INFO);
    // LogComponentEnable("PacketSink", LOG_LEVEL_INFO);
    LogComponentEnable("GENERIC_SIMULATION", LOG_LEVEL_INFO);

    
	//
	// Now, do the actual simulation.
	//
	std::cout << "third: Running Simulation.\n";
	fflush(stdout);
    std::cout << "simulator run " << std::endl;

    Simulator::Stop(Seconds(2000000000));
    Simulator::Run();
    Simulator::Destroy();
    
    #ifdef NS3_MPI
    MpiInterface::Disable ();
    #endif
    std::cout << "simulator end" << std::endl;
    return 0;

}