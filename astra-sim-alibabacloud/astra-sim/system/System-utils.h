// This file contains utils for System modules
/******************************************************************************/

#ifndef __SYSTEM_UTILS_H__
#define __SYSTEM_UTILS_H__

#include <fstream>
#include <string>
#include <iomanip>
#include <iostream>
#include <unordered_set>

#define RESET "\033[0m"
#define BLACK "\033[30m"  /* Black */
#define RED "\033[31m"    /* Red */
#define GREEN "\033[32m"  /* Green */
#define YELLOW "\033[33m" /* Yellow */
#define BLUE "\033[34m"   /* Blue */
#define PURPLE "\033[35m" /* Purple */
#define CYAN "\033[36m"   /* Cyan */
#define WHITE "\033[37m"  /* White */

#define U_NORMAL (std::cout << RESET)
#define U_INFO (std::cout << GREEN)
#define U_WARN (std::cout << YELLOW)
#define U_ERROR (std::cout << RED)
#define U_DEBUG (std::cout << CYAN)
#define U_END (std::endl)
#define U_REND "\033[0m" << std::endl

using namespace std;

/* Log file path*/
inline std::string debug_log_file = "/home/dell/sjw/lb/simulator/output/simulation/debug.log";
inline FILE *debug_log = fopen(debug_log_file.c_str(), "w");


#define W_LOG(msg)                                \
    do {     \
        std::string _tmp_msg = msg;                                                         \
        fprintf(debug_log, "%s\n", _tmp_msg.c_str());                                             \
        fflush(debug_log);                                          \
    } while (0)

/*** astra-sim/system Log/Debug define ***/
/* MockNcclGroup.cc */
// log
// #define NCCL_GROUP_LOG
// #define NCCL_GEN_RINGFLOW_LOG



#endif