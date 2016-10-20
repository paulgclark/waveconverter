# This file contains the python code that does a first pass over a raw
# input digital waveform. The output of this pass is an array of integers, 
# each defining the width of successive high and low states. The output
# feeds into a function that partitions the resulting array into packets.
#
# This file assumes that each bit of the bitstream is contained in a
# single byte, each with a value of either 0x00 or 0x01.
#
import sys
import io
import os
from collections import Counter
from protocol_lib import ProtocolDefinition
import waveConvertVars as wcv

from waveConvertVars import *
from config import *

#####################################
def bitProb(packetList, bitProbList):
    sumList = []
    packetBitCount = []
 
    # nested for loops
    for packet in packetList:
        for i in range(0, len(packet)):
            if i >= len(packetBitCount): # add item to list if necessary
                packetBitCount.append(0)
                sumList.append(0)
            packetBitCount[i] += 1
            sumList[i] += packet[i] # keep a running total of each index

    for i in range(0, len(sumList)):
        bitProbList.append(float(sumList[i])/float(packetBitCount[i]))

    return(0)


#####################################
# eliminate all packets from list that aren't of correct length
def pruneBadLengthPackets(packetList, computedPacketLength):
    # single for loop
    i=0
    while True:
        if len(packetList[i]) != computedPacketLength:
            del packetList[i]
        else:
            i+=1
        if (i >= len(packetList)):
            break
    return(0)


#####################################
def valueRange(packetList, lowAddr, highAddr, valList):
    # single for loop extracting values
    for packet in packetList:
        binaryString = ''.join(str(s) for s in packet[lowAddr:highAddr+1])
        valList.append(int(binaryString, 2))

    return(0)


#####################################
# NEED: pass back the entire list of values and frequency for analysis
def packetLengths(packetList, packetLengthList):
    # single for loop
    for packet in packetList:
        packetLengthList.append(len(packet))

    # determine most common length (not counting zero)
    lengthListNoZeros = packetLengthList[:] # copy list
    while 0 in lengthListNoZeros:
        lengthListNoZeros.remove(0)

    # find the most common length
    countedList = Counter(lengthListNoZeros)
    computedPacketLength, dummy = countedList.most_common(1)[0]
    return (computedPacketLength)

#####################################
def getIDs(packetList, lowAddr, highAddr):

    idList = []

    # get ID value for each packet and save as string to a new list  
    for packet in packetList:
        binaryString = ''.join(str(s) for s in packet[lowAddr:highAddr+1])
        idList.append(binaryString)

    # single for loop extracting values
    return(Counter(idList))

#####################################
def checkSum(packetList, lowAddr, highAddr, lowData, highData):

    checkSumPassList = []


    # compute checksum for each packet in the list and compare to defined field
    for packet in packetList:
        # get the integer value of the checksum from the binary packet values
        checkSum = 0
        i = highAddr-lowAddr
        for bit in packet[lowAddr:highAddr+1]:
            checkSum += 2**i*bit
            i -= 1

        # now compute the actual sum
        packetSum = sum(packet[lowData:highData+1])

        # checksum must be limited to number of bits available
        if packetSum % 2**(highAddr-lowAddr + 1) == checkSum:
            checkSumPassList.append(CRC_PASS)
        else:
            checkSumPassList.append(CRC_FAIL)

        #print "\nchecksum from packet:"
        #print checkSum
        #print "checksum mod 4:"
        #print packetSum % 2**(highAddr-lowAddr + 1)
        #print "checksum computed:"
        #print packetSum

    # single for loop extracting values
    return(checkSumPassList)

#####################################

# Compute an individual CRC
def checkCRC(protocol, crcBits, payload):
    
    crcValue = crcComputed(payload, protocol.crcPoly, protocol.crcBitOrder, 
                           protocol.crcInit, protocol.crcReverseOut,
                           protocol.crcFinalXor, protocol.crcPad, 
                           protocol.crcPadCount, protocol.crcPadVal)
    
    print "CRC Computed:"
    print crcValue
    
    if crcValue == crcBits:
        return(wcv.CRC_PASS)
    else:
        return(wcv.CRC_FAIL)

#####################################
def crcComputed(payload, crcPoly, inputBitOrder, initVal, reverseFinal,\
                finalXOR, padType, padCount, padVal):
# the payload and crcPoly are lists of integers, each valued either 1 or 0

    # pad the packet as instructed
    payloadPad = payload[:];
    if padType == wcv.CRC_PAD_ABS: # add fixed number of bits
        for i in range(padCount):
            payloadPad.append(padVal)
    elif padType == wcv.CRC_PAD_TO_EVEN:
        if padCount != 0:
            numBits = len(payload) % padCount # figure how many short of even
        else:
            numBits = len(payload)
        for i in range(numBits):
            payloadPad.append(padVal)

    # reflecting means reversing the bits within each byte
    # note, this will only work if the payload is a multiple of 8 long
    if inputBitOrder == wcv.CRC_REFLECT:
        payloadIn = payloadPad[:]
        i = 0
        while i <= len(payloadIn)-8:
            payloadByte = payloadIn[i:i+8]
            payloadIn[i:i+8] = payloadByte[::-1] # assign to reversed byte
            i += 8
    # reverse the payload if instructed
    elif inputBitOrder == wcv.CRC_REVERSE:
        payloadIn = payloadPad[::-1]
    # else process normally 
    else:
        payloadIn = payloadPad[:]

    # the working value of the computation is the payload input padded
    # by a number of bits equal to one less than the poly length
    # these bit positions allow for a remainder of the division
    for i in range(len(crcPoly) - 1):
        payloadIn.append(initVal) # CRCs can have different initial values

    #print "range i and j and len(payloadIn):"
    #print range(len(payload))
    #print range(len(crcPoly))
    #print len(payloadIn) #print payload
    #print payloadIn

    for i in range(len(payload)):
        if (payloadIn[i] == 1):
            for j in range(len(crcPoly)):
                payloadIn[i+j] = (payloadIn[i+j]+crcPoly[j]) % 2
        #print payloadIn

    # crc value is the remainder which is stored in the final bits 
    # of the computation
    crcRemainder = payloadIn[-(len(crcPoly)-1):]

    # final reversal of CRC bits
    if reverseFinal:
        crcOut = crcRemainder[::-1]
    else:
        crcOut = crcRemainder[:]

    # final XOR mask
    crcXOR = []
    for i in range(len(crcOut)):
        if ((crcOut[i]==1) ^ (finalXOR[i]==1)):
            crcXOR.append(1)
        else:
            crcXOR.append(0)

    return(crcXOR)


#####################################
# taking the CRC size from the address passed, this function will
# run through all the available CRC parameters and look for a set
# that will cause the packetlist to pass
# NEED: start using a CRC definition class and return that
# NEED: start using binary values instead of these lists
def bruteCRC(packetList, lowAddr, highAddr, lowData, highData):

    crcLen = highAddr-lowAddr+1

    # a bunch of nested loops that iterate through each CRC option
    crcPoly = []
    for i in range(crcLen+1): # poly is one more than crc
        crcPoly.append(1)

    i = -1
    while i < (2**len(crcPoly)): # go through each possibly polynomial
        i+=1
        # add one to the current polynomial string
        crcPoly = incrementList(crcPoly)
        for initVal in [0, 1]: # try both initial values
            for inputBitOrder in CRC_BIT_ORDER_OPTIONS: # both bit orders
                for reverseOut in [True, False]:
                    # setup XOR options
                    finalXOR = []
                    for j in range(crcLen):
                        finalXOR.append(1)
                    j = -1
                    while j < 2**len(finalXOR): # go through each XOR
                        j+=1
                        finalXOR = incrementList(finalXOR)
                        for padType in CRC_PAD_OPTIONS: # each pad possible
                            for padCount in CRC_PAD_COUNT_OPTIONS:
                                for padVal in [0, 1]:
                                    crcPassData = checkCRC(packetList,
                                                           lowAddr, highAddr,
                                                           lowData, highData,
                                                           crcPoly,
                                                           inputBitOrder,
                                                           initVal, reverseOut,
                                                           finalXOR, padType,
                                                           padCount, padVal)
                                    crcSuccess = CRC_PASS
                                    for passFail in crcPassData:
                                        if passFail == CRC_FAIL:
                                            crcSuccess = CRC_FAIL
                                            break
                                    # if we actually got a passing set
                                    # print the parameters that worked
                                    if crcSuccess == CRC_PASS:
                                        print "\nALL PACKETS PASSED FOR:"
                                        print "crcPoly:"
                                        print crcPoly
                                        print "inputBitOrder:"
                                        print inputBitOrder
                                        print "initVal:"
                                        print initVal
                                        print "reverseOut:"
                                        print reverseOut
                                        print "finalXOR:"
                                        print finalXOR
                                        print "padType:"
                                        print padType
                                        print "padCount:"
                                        print padCount
                                        print "padVal:"
                                        print padVal
                                    else:
                                        print "FAILED " + str(len(crcPassData) - sum(crcPassData)) + "/" + str(len(crcPassData))


##################################################################
# this is a kludge because I'm using lists of integers rather than
# simple binary values. This should go away when we move to binary
def incrementList(inputList):

    result = []
    carry = 1 # this is our initial +1

    # brute force increment logic
    for i in range(len(inputList)):
        result.append((inputList[i] + carry) % 2)
        if (inputList[i] + carry) == 2:
            carry = 1
        else:
            carry = 0
        
    return(result)
