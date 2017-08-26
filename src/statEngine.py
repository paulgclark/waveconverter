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
from collections import deque
from protocol_lib import ProtocolDefinition
import waveConvertVars as wcv
import itertools
import crc_custom
import bit_list_utilities as blu

from waveConvertVars import *
from config import *

# check if there are any statistical plugins
try:
    import waveconverter_plugin_00 as wcp00
    plugin_00 = True
    print "Plugin Detected"
except:
    plugin_00 = False


# if we were able to import a plugin, then this function calls the 
# highest priority plugin installed and executes the code contained 
# therein; otherwise it exits immediately
def plugin_stats_stdout(txList, protocol, showAllTx):
    if plugin_00:
        wcp00.run_plugin(txList, protocol, showAllTx)
                
    
# computes the bit probabilities, the ID frequencies and the 
# analog value ranges
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
    idListMaster = []
    for idAddr in protocol.idAddr:
        idList = []
        idAddrLow = idAddr[0]
        idAddrHigh = idAddr[1]
        for iTx in txList2:
            binaryString = ''.join(str(s) for s in iTx.fullBasebandData[idAddrLow:idAddrHigh+1])
            idList.append(binaryString)
        idListCounter = Counter(idList)
        idListMaster.append(idListCounter)

    # build ranges of values    
    # need to trap for bad indices
    valListMaster = []
    for valAddr in protocol.valAddr:
        valList = []
        valAddrLow = valAddr[0]
        valAddrHigh = valAddr[1]
        for iTx in txList2:
            # if any of the transmissions are too short to include the value bit range, skip
            if valAddrLow < len(iTx.fullBasebandData) or valAddrHigh < iTx.fullBasebandData:
                # get bits that comprise the value
                bitList = iTx.fullBasebandData[valAddrLow:valAddrHigh+1]
                # convert bits to number
                value = 0
                for bit in bitList:
                    value = (value << 1) | bit
                # add to list
                valList.append(int(value))
        valListMaster.append(valList)
        
    # get all of the payload lengths and put them in a list
    payloadLenList = []
    for iTx in txList:
        payloadLenList.append(len(iTx.fullBasebandData))

    return (bitProbList, idListMaster, valListMaster, payloadLenList)


def buildStatStrings(bitProbList, idListMaster, valListMaster, payloadLenList, outputHex):

    # build string for display of bit probabilities, one per line
    bitProbString = "Bit: Probability %\n"
    i=0
    for bitProb in bitProbList:
        bitProbString += '{:3d}'.format(i) + ": " + '{:6.2f}'.format(bitProb) + "\n"
        i+=1

    # for each ID definition
    idStatString = ""
    for i, idListCounter in enumerate(idListMaster):
        # build string showing frequency of each ID value
        idStatString += "Count for ID " + str(i+1) + "\n" # NEED: make the whitespace match the length of the IDs
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

    # for each value definition
    valuesString = ""
    for i, valList in enumerate(valListMaster):
        # build string of values
        if valList == []:
            valuesString += "Value " + str(i+1) + ": Undefined\n\n"
        elif valList[0] == -1:
            valuesString += "Value " + str(i+1) + ": Illegal Values\n\n"
        else:
            valuesString += "Value " + str(i+1) + ":\n"
            valuesString += "  Average:  " + str(sum(valList)/len(valList)) + "\n" 
            valuesString += "  Low Val:  " + str(min(valList)) + "\n"
            valuesString += "  High Val: " + str(max(valList)) + "\n\n"
        
    # report count of payload lengths
    valuesString += "Payload Lengths:\n"
    payloadLenCounter = Counter(payloadLenList)
    for (lenVal, lenCount) in payloadLenCounter.most_common():
        valuesString += '{:5d}'.format(lenCount) + "  " + str(lenVal) + "\n"
    valuesString += "\n"
    
    # now list all the bits that had variation
    valuesString += "Variable Bits:\n"
    #valCount = 0
    for i, bit in enumerate(bitProbList):
        if bit < 100.0 and bit > 0.0:
            valuesString += str(i) + "\n"
        #    valCount += 1
        #if valCount > 4:
        #    valuesString += "\n"
        #    valCount = 0
            
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

#########################################
# Check all CRCs for a given transmission
def checkCRC(protocol, fullData):
    
    # if there are no CRC polynomial defined, then say that it passed
    if len(protocol.crcPoly) == 0:
        return True
    
    crcPass = True
    for crcAddr, crcData in zip(protocol.crcAddr, protocol.crcData):
        # only check if there's a CRC of greater than zero length
        if crcAddr[1] >= crcAddr[0]:
            # the crc field must be the same size as they poly-1
            if (crcAddr[1] - crcAddr[0] + 1) != (len(protocol.crcPoly)-1):
                crcPass = False
                break
            # also fail if any address is out of range
            elif max(crcAddr + crcData) >= len(fullData):
                crcPass = False
                break
            # else get on with the CRC
            else:
                crcObserved = fullData[crcAddr[0] : crcAddr[1]+1]
                payload = fullData[crcData[0] : crcData[1]+1]
                crcValue = crc_custom.crcCompute(payload=payload, 
                                                 crcPoly=protocol.crcPoly, 
                                                 inputBitOrder=protocol.crcBitOrder, 
                                                 initVal=protocol.crcInit, 
                                                 reverseFinal=protocol.crcReverseOut,
                                                 finalXOR=protocol.crcFinalXor, 
                                                 padType=protocol.crcPad, 
                                                 padCount=protocol.crcPadCount, 
                                                 padVal=protocol.crcPadVal)
                if crcValue != crcObserved:
                    crcPass = False
                    break
                
    return crcPass

#########################################
# Check all arithmetic checksums (ACS) for a given transmission
def checkACS(protocol, fullData):
    acsPass = True
    for acsAddr, acsData, acsInitSum in \
        zip(protocol.acsAddr, protocol.acsData, protocol.acsInitSum):
        # only check if there's a ACS field of greater than zero length
        if acsAddr[1] >= acsAddr[0]:
            # the acs field must be the same size as the acs length
            if (acsAddr[1] - acsAddr[0] + 1) != protocol.acsLength:
                acsPass = False
                break
            # also fail if any address is out of range
            elif max(acsAddr + acsData) >= len(fullData):
                acsPass = False
                break
            # else get on with the ACS check
            else:
                acsObserved = blu.bitsToDec(fullData[acsAddr[0] : acsAddr[1]+1])
                payload = fullData[acsData[0] : acsData[1]+1]
                acsValue = crc_custom.checksumCompute(dataList=fullData, 
                                                      dataStart=acsData[0], 
                                                      dataStop=acsData[1], 
                                                      dataInvert = protocol.acsInvertData, 
                                                      dataReverse = False, 
                                                      numOutputBits = protocol.acsLength, 
                                                      initSum=acsInitSum)

                if acsValue != acsObserved:
                    acsPass = False
                    break                         
    return acsPass
"""
#####################################
# the payload, crcPoly and the finalXOR are lists of integers, 
# each valued either 1 or 0
def crcComputed(payload, crcPoly, inputBitOrder, initVal, reverseFinal,\
                finalXOR, padType, padCount, padVal):
    
    if False:
        print "payload: ",
        print payload
        print "crcPoly: ",
        print crcPoly
        print "inputBitOrder: " + str(inputBitOrder)
        print "initVal: " + str(initVal)
        print "reverseFinal: " + str(reverseFinal)
        print "finalXOR: ",
        print finalXOR
        print "padType: " + str(padType)
        print "padCount: " + str(padCount)
        print "padVal: " + str(padVal)

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
"""

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

"""
        # add display of width list info to GUI
        # for now, just print to stdout
        # first create a big list of all the widths:
        allWidthsList = []
        for iTx in wcv.txList:
            allWidthsList += iTx.widthList
        
        # build a Counter list    
        widthCount = Counter(allWidthsList)
        
        # get a python dictionary containing all the widths and their corresponding frequency in order of most common
        orderedWidthDict = {}
        for n in range(len(widthCount)):
            newWidth = widthCount.most_common()[n][0]
            newWidthCount = widthCount.most_common()[n][1]
            #print "n={}\twidth={}\tcount={}".format(n, newWidth, newWidthCount)
            mergedVal = False
            # go through all the widths in the current list and check whether the new one is within the timing tolerance
            for (widthVal, countVal) in orderedWidthDict.items():
                if widthVal != 0:
                    #print "Timing error with {}: {}".format(widthVal, abs(1.0*newWidth - widthVal)/widthVal)
                    if (abs(1.0*newWidth - widthVal)/widthVal) <= wcv.timingError:
                        orderedWidthDict[widthVal] += newWidthCount
                        mergedVal = True
                        break
            if not mergedVal:
                orderedWidthDict[newWidth] = newWidthCount
            #print orderedWidthDict

        if wcv.verbose:
            print "Merged list of frequencies:"            
            print orderedWidthDict
        
            print "Top N values:"
            from collections import OrderedDict
            from operator import itemgetter
            #od = OrderedDict(sorted(orderedWidthDict.items(), key=itemgetter(1)))
            od = sorted(orderedWidthDict.iteritems(), key=itemgetter(1), reverse=True)
            print od
            for width, count in od:
                print "  {}: {}".format(width, count)
"""