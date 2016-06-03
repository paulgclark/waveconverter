#!/usr/bin/env python
# This file contains the top level code for analyzing the previously
# captured packets. These will be read from a text file generated
# by packet_decode.py. 
#
# This file assumes that each packet is prepended by "Packet <num>:"
# followed by the packet in binary ('0' and '1' characters) with spaces
# every 8 bits. Incomplete or blank packets may be in the files.
#
import sys
import io
import os
from statEngine import bitProb
from statEngine import valueRange
from statEngine import packetLengths
from statEngine import pruneBadLengthPackets
from statEngine import getIDs
from statEngine import checkCRC
from statEngine import checkSum
from statEngine import bruteCRC

from waveConvertVars import *
from config import *

#####################################
def readPacketsFromFile(packetFile, packetList):
    # read all the lines into a list
    lines = packetFile.readlines()
    intList = []
   
    # strip out leading text and whitespace
    for line in lines:
        line = line.split(":")[1] # take only what's after the colon
        line = ''.join(line.split()) # remove whitespace

        # convert characters to integers
        intList = []
        for ch in line:
           intList.append(int(ch))
        # add list of ints to packet list
        packetList.append(intList[:])

    return(0)


#####################################
def printStatsToFile(outFile, bitProbList, uniqueIDList, valList, crcPassList):
    # top level stats
    outFile.write("Top Level Stats:\n")
    outFile.write("    TBD\n")
    outFile.write("\n")

    # probability for each bit
    outFile.write("Probabilities of being 1'b1 by bit:\n")
    for i in range(0, len(bitProbList)):
        outFile.write("Bit " + str(i) + ": " + str(bitProbList[i]) + "\n")
    outFile.write("\n")

    # IDs determined and frequency
    outFile.write("frequency: ID\n")
    #print(uniqueIDList)
    #print(uniqueIDList.most_common())
    for (ID, frequency) in uniqueIDList.most_common():
        outFile.write(str(frequency) + "\t" + ID + "\n")

    # value range for specified region
    outFile.write("\n")
    outFile.write("Measured Data:")
    outFile.write("Max Value: " + str(max(valList)) + "\n")
    outFile.write("Min Value: " + str(min(valList)) + "\n")

    # CRC Results
    outFile.write("\n")
    outFile.write("CRC Outcomes:\n")
    for i in range(0, len(crcPassList)):
        outFile.write("Bit " + str(i) + ": ")
        if crcPassList[i] == CRC_PASS:
            outFile.write("PASS\n")
        elif crcPassList[i] == CRC_FAIL:
            outFile.write("FAIL\n")
        else:
            outFile.write("N/A\n")
 
    # simple checksum results
    outFile.write("\n")
    outFile.write("Checksum Outcomes:\n")
    for i in range(0, len(checkSumPassList)):
        outFile.write("Bit " + str(i) + ": ")
        if checkSumPassList[i] == CRC_PASS:
            outFile.write("PASS\n")
        elif checkSumPassList[i] == CRC_FAIL:
            outFile.write("FAIL\n")
        else:
            outFile.write("N/A\n")
 
 
    return(0)


#packetFileName = "digital_sig_lib/out_full.txt"
#outFileName = "./stat.txt"
if len(sys.argv) != 3:
    print "    Usage: python packet_stat.py <input file> <output file>"
    exit(0)
else:
    packetFileName = sys.argv[1]
    outFileName = sys.argv[2]


##################################### main
packetList = [] # list of decoded packets
bitProbList = [] # for each bit, probability of being a 1
valList = [] # list of binary values delimited by input addresses
packetLengthList = [] # list of the lengths of all packets
uniqueIDList = [] # unique values for a defined subset of the protocol
computedPacketLength = 0

# open input file for read access in binary mode
with io.open(packetFileName, 'rb') as packetFile: 
    readPacketsFromFile(packetFile, packetList)
# open output file for write access
outFile = open(outFileName, 'w')

# generate the three types of stats we want
computedPacketLength = packetLengths(packetList, packetLengthList)
pruneBadLengthPackets(packetList, computedPacketLength)
bitProb(packetList, bitProbList)
valueRange(packetList, VAL_ADDR_LOW, VAL_ADDR_HIGH, valList)
uniqueIDList = getIDs(packetList, ID_ADDR_LOW, ID_ADDR_HIGH)
crcPassList = []
crcPassList = checkCRC(packetList, CRC_LOW, CRC_HIGH, CRC_DATA_LOW, CRC_DATA_HIGH, CRC_POLY, \
                       CRC_BIT_ORDER, CRC_INIT, CRC_REVERSE_OUT, CRC_FINAL_XOR, \
                       CRC_PAD, CRC_PAD_COUNT, CRC_PAD_VAL)
#bruteCRC(packetList, CRC_LOW, CRC_HIGH, CRC_DATA_LOW, CRC_DATA_HIGH)
checkSumPassList = checkSum(packetList, CRC_LOW, CRC_HIGH, CRC_DATA_LOW, CRC_DATA_HIGH)
#print("Length = " + str(computedPacketLength))
#print uniqueIDList
#print bitProbList
#print valList

printStatsToFile(outFile, bitProbList, uniqueIDList, valList, crcPassList)

# could then display these in clever ways, but that will wait
# bitProbList could have astericks representing 10% each
# - ID CRC values if they are close to 50%
# - ID subsets that have same bits (scan through them)
# value range could be plotted
# packetLength optimal size could be highlighted
# look into bruteforce-crc on github for CRC breakdown

# after we finish, close out files and exit
outFile.close()
packetFile.close()
exit(0)

