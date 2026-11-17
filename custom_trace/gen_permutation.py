#!/usr/bin/env python

# Generate a permutation traffic matrix.
# python gen_pemutation.py <nodes> <conns> <flowsize> <extrastarttime>
# Parameters:
# <nodes>   number of nodes in the topology
# <conns>    number of active connections
# <flowsize>   size of the flows in bytes
# <extrastarttime>   How long in microseconds to space the start times over (start time will be random in between 0 and this time).  Can be a float.
# <randseed>   Seed for random number generator, or set to 0 for random seed
# e.g.: python3 gen_permutation.py permutation_128g_64M.txt 128 128 64000000 5 16

import os
import sys
from random import seed, shuffle
#print(sys.argv)
if len(sys.argv) != 7:
    print("Usage: python gen_pemutation.py <filename> <nodes> <conns> <flowsize> <extrastarttime> <randseed>")
    sys.exit()
filename = sys.argv[1]
nodes = int(sys.argv[2])
conns = int(sys.argv[3])
flowsize = int(sys.argv[4])
extrastarttime = float(sys.argv[5])
randseed = int(sys.argv[6])

""" print("Nodes: ", nodes)
print("Connections: ", conns)
print("Flowsize: ", flowsize, "bytes")
print("ExtraStartTime: ", extrastarttime, "us")
print("Random Seed ", randseed) """

f = open(filename, "w")
print(nodes, file=f)
# print("Connections", conns, file=f)

srcs = []
dsts = []
for n in range(nodes):
    srcs.append(n)
    dsts.append(n)
if randseed != 0:
    seed(randseed)

shuffle(srcs)
shuffle(dsts)
#print(srcs)
#print(dsts)

# eliminate any duplicates - a node should not send to itself
for n in range(nodes):
    if srcs[n] == dsts[n]:
        i = (n+1)%nodes
        #print("swapping", n, "and", i)
        tmp = dsts[n]
        dsts[n] = dsts[i]
        dsts[i] = tmp

#print(dsts)

for n in range(conns):
    out = str(srcs[n]) + " " + str(dsts[n]) + " 3 " + str(flowsize) + " " + "{0:.9f}".format(float(0.000000001 * extrastarttime * 1000)) + " 0" # us
    print(out, file=f)

f.close()
