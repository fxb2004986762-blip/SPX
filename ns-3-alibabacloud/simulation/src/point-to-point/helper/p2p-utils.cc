#ifndef __P2P_UTILS_H__
#define __P2P_UTILS_H__
#include <cstdlib>
#include <climits>
#include <random>
using namespace std;


/* Utils */
static mt19937 random_engine;

void srand(unsigned seed)
{
    random_engine = mt19937(seed);
    // printf("[RANDOM_SEED] srand with seed: %u\n", seed);
}

int rand()
{
    return random_engine() & INT_MAX;
}

void srandom(unsigned seed)
{
    srand(seed);
}

long random()
{
    return rand();
}
#endif
