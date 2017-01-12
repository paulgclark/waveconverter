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


def computeStats(txList, protocol, showAllTx):
    bitProbList = []
    
    # if directed, create txList copy that removes all bad transmissions
    if not showAllTx:
        txList2 = []
        for tx in txList:
            if tx.txValid:
                txList2.append(tx)
    else:
        txList2 = txList

    # compute the probability of each bit being equal to 1
    # first figure out the longest transmission length
    maxTxLen = 0
    for iTx in txList2:
        if len(iTx.fullBasebandData) > maxTxLen:
            maxTxLen = len(iTx.fullBasebandData)

    i=0
    while i < maxTxLen:
        sumOfBits = 0
        totalBits = 0
        for iTx in txList2:
            try:
                sumOfBits += iTx.fullBasebandData[i]
                totalBits += 1
            except:
                totalBits = totalBits
        try:
            bitProbList.append(100.0*sumOfBits/totalBits)
        except:
            bitProbList.append(-1.0) # if no bits at this address, use -1
        i+=1
        
    # get ID value for each packet and save as string to a new list  
    idList = []
    for iTx in txList2:
        binaryString = ''.join(str(s) for s in iTx.fullBasebandData[protocol.idAddrLow:protocol.idAddrHigh+1])
        idList.append(binaryString)
    idListCounter = Counter(idList)
    

    # build ranges of values    
    # need to trap for bad indices
    value1List = []
    value2List = []
    value3List = []
    for iTx in txList2:
        # if any of the transmissions are too short to include the value bit range, skip
        if protocol.val1AddrLow < len(iTx.fullBasebandData) or protocol.val1AddrHigh < iTx.fullBasebandData:
            # get bits that comprise the value
            bitList = iTx.fullBasebandData[protocol.val1AddrLow:protocol.val1AddrHigh+1]
            # convert bits to number
            value = 0
            for bit in bitList:
                value = (value << 1) | bit
            # add to list
            value1List.append(int(value))
            
        # repeat for value 2
        if protocol.val2AddrLow < len(iTx.fullBasebandData) or protocol.val2AddrHigh < iTx.fullBasebandData:
            # get bits that comprise the value
            bitList = iTx.fullBasebandData[protocol.val2AddrLow:protocol.val2AddrHigh+1]
            # convert bits to number
            value = 0
            for bit in bitList:
                value = (value << 1) | bit
            # add to list
            value2List.append(int(value))

        # repeat for value 3
        if protocol.val3AddrLow < len(iTx.fullBasebandData) or protocol.val3AddrHigh < iTx.fullBasebandData:
            # get bits that comprise the value
            bitList = iTx.fullBasebandData[protocol.val3AddrLow:protocol.val3AddrHigh+1]
            # convert bits to number
            value = 0
            for bit in bitList:
                value = (value << 1) | bit
            # add to list
            value3List.append(int(value))
            
    return (bitProbList, idListCounter, value1List, value2List, value3List)


def buildStatStrings(bitProbList, idListCounter, value1List, value2List, value3List, outputHex):

    # build string for display of bit probabilities, one per line
    bitProbString = "Bit: Probability %\n"
    i=0
    for bitProb in bitProbList:
        bitProbString += '{:3d}'.format(i) + ": " + '{:6.2f}'.format(bitProb) + "\n"
        i+=1

    # build string showing frequency of each ID value
    idStatString = "Count ID\n" # NEED: make the whitespace match the length of the IDs
    for (idVal, idCount) in idListCounter.most_common():
        if outputHex:
            try:
                hexString = '%0*X' % ((len(idVal) + 3) // 4, int(idVal, 2))
                idStatString += '{:5d}'.format(idCount) + "  " + hexString + "\n"
                #idStatString += '{:5d}'.format(idCount) + "  " + hex(int(idVal, 2)) + "\n"
            except:
                idStatString += '{:5d}'.format(idCount) + "  " + "N/A" + "\n"
        else:
            idStatString += '{:5d}'.format(idCount) + "  " + idVal + "\n"

    # build string of values
    if value1List == []:
        valuesString = "Value 1: Undefined\n\n"
    elif value1List[0] == -1:
        valuesString = "Value 1: Illegal Values\n\n"
    else:
        valuesString = "Value 1:\n"
        valuesString += "  Average:  " + str(sum(value1List)/len(value1List)) + "\n" 
        valuesString += "  Low Val:  " + str(min(value1List)) + "\n"
        valuesString += "  High Val: " + str(max(value1List)) + "\n\n"
        
    # repeat for value #2
    if value2List == []:
        valuesString += "Value 2: Undefined\n\n"
    elif value2List[0] == -1:
        valuesString += "Value 2: Illegal Values\n\n"
    else:
        valuesString += "Value 2:\n"
        valuesString += "  Average:  " + str(sum(value2List)/len(value2List)) + "\n" 
        valuesString += "  Low Val:  " + str(min(value2List)) + "\n"
        valuesString += "  High Val: " + str(max(value2List)) + "\n\n"

    # repeat for value #3
    if value3List == []:
        valuesString += "Value 3: Undefined\n\n"
    elif value3List[0] == -1:
        valuesString += "Value 3: Illegal Values\n\n"
    else:
        valuesString += "Value 3:\n"
        valuesString += "  Average:  " + str(sum(value3List)/len(value3List)) + "\n" 
        valuesString += "  Low Val:  " + str(min(value3List)) + "\n"
        valuesString += "  High Val: " + str(max(value3List)) + "\n\n"

    return (bitProbString, idStatString, valuesString)
    

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
        return True
    else:
        return False

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
