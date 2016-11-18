# This file contains the python code that does a first pass over a raw
# input digital waveform. The output of this pass is an array of integers, 
# each defining the width of successive high and low states. The output
# feeds into a function that partitions the resulting array into packets.
#
# This file assumes that each bit of the bitstream is contained in a
# single byte, each with a value of either 0x00 or 0x01.
#
#import sys
#import io
#import os
import waveConvertVars as wcv
from config import *

# NEED: parameterize these values
#MIN_SHORT = protocol.unitWidth * (1 - UNIT_ERROR)
#MAX_SHORT = protocol.unitWidth * (1 + UNIT_ERROR)
#MIN_LONG = 2 * protocol.unitWidth * (1 - UNIT_ERROR)
#MAX_LONG = 2 * protocol.unitWidth * (1 + UNIT_ERROR)

# MIN_PRE_HIGH = protocol.preambleSymbolHigh * (1 - protocol.unitError)
# MAX_PRE_HIGH = protocol.preambleSymbolHigh * (1 + protocol.unitError)
# MIN_PRE_LOW = protocol.preambleSymbolLow * (1 - protocol.unitError)
# MAX_PRE_LOW = protocol.preambleSymbolLow * (1 + protocol.unitError)


#####################################
# looks for low levels of sufficient width to be packet dividers
# NEED: cover the case where interpacket level is high
# NEED: add error codes
# NEED: can we do everything with preamble sync? elim the interpacket width?
def separatePackets(protocol, masterWidthList, packetWidthsList):
    i = 0
    newPacket = []
    packetStartIndexList = []

    if protocol.preambleSync: # interpacket width is too short to use to div packets
        # build the shortest legal preamble
        preambleWidthList = []
        for i in range(min(protocol.preamble_size)):
            preambleWidthList.append(protocol.preambleSymbolLow)
            preambleWidthList.append(protocol.preambleSymbolHigh)
        del preambleWidthList[0] # first zero width swallowed by interpacket
        # now add the header if there is one
        if protocol.headerLevel != wcv.DATA_NULL:
            preambleWidthList.append(protocol.headerWidth_samp)

        # scan through width list and find a match; record each packet start
        i = 0
        while i < (len(masterWidthList) - len(preambleWidthList)):
            if preambleSyncFound(protocol, masterWidthList, preambleWidthList, i):
                packetStartIndexList.append(i)
                i+=min(protocol.preambleSize)
            i+=1
        # appending the final index makes packet assembly easier
        packetStartIndexList.append(len(masterWidthList)-1)

        # now split up the list based on the start indices
        for i in range(len(packetStartIndexList)-1):
            startIndex = packetStartIndexList[i] - 1 # get the interpacket before
            stopIndex = packetStartIndexList[i+1] - 1 # stop before next
            newPacket = masterWidthList[startIndex:stopIndex]
            packetWidthsList.append(newPacket[:])


    else: # scan through widths and find large ones that separate packets
        while i < (len(masterWidthList)-2): 

            # first look at the width of the zero pulse
            if (masterWidthList[i] > protocol.interPacketWidth_samp):
                packetWidthsList.append(newPacket[:])
                newPacket = []

            newPacket.append(masterWidthList[i])
            newPacket.append(masterWidthList[i+1])

            i = i + 2
 
        # this method sticks a null packet on the front
        del packetWidthsList[0]
    #print packetWidthsList

    return(1)


#####################################
# This function checks the next series of widths (starting from start)
# to see if a preamble has been reached
def preambleSyncFound(protocol, masterWidthList, preambleWidthList, start):

    i = 0
    # for each width in the preamble
    while i < len(preambleWidthList):
        # if it matches the width in the packet
        if not widthCheck(masterWidthList[start+i], preambleWidthList[i], wcv.timingError):
            return False
        i+=1

    return True # if we haven't found a mismatch after going through all bits


#####################################
# takes the width data and checks that it is a legal packet, then extracts data
# NEED: error checking
# NEED: packet specs from input list
# NEED: check for even length so our zeros and ones don't get out of sync
# NEED: seeding the array with an initial zero should be parameterized
def decodePacket(protocol, packetWidths, decodedPacket, rawPacket):

    # check the packet's preamble, header, etc.
    encodingValid = True
    (dataStartIndex, interPacketValid, preambleValid, headerValid) = checkValidPacket(protocol, packetWidths)

    # set loop index to the start of the data portion of the packet
    i = dataStartIndex

    # this should be tied to the interpacket width or preamble sync event
    if (i % 2) == 0:
        currentLevel = wcv.DATA_ZERO
    else:
        currentLevel = wcv.DATA_ONE
 
    measurement = wcv.BAD_WIDTH

    # note: the decodedPacket list has been passed to this fn as an empty list
    if (protocol.encodingType == wcv.STD_MANCHESTER) or (protocol.encodingType == wcv.INV_MANCHESTER):
        # extract data
        while i < len(packetWidths):
            measurement = widthMeasure(packetWidths[i], protocol.unitWidth_samp, wcv.timingError)
            if (measurement == wcv.UNIT_1X):
                rawPacket.append(currentLevel)
            elif (measurement == wcv.UNIT_2X):
                rawPacket.append(currentLevel)
                rawPacket.append(currentLevel)
            else:
                print("Bad level width")
                encodingValid = False

            # flip level and increment index
            i = i + 1
            if (currentLevel == wcv.DATA_ZERO):
                currentLevel = wcv.DATA_ONE
            elif (currentLevel == wcv.DATA_ONE):
                currentLevel = wcv.DATA_ZERO
            else:
                print("Level isn't either one or zero")
                encodingValid = False

        # remember that the last Manchester symbol will be swallowed
        rawPacket.append(wcv.DATA_ZERO)
        # now that we have raw bits, do the decoding
        #print rawPacket
        decodedPacket += manchesterDecode(rawPacket, protocol.encodingType) 
        # NEED code here for rev

    elif protocol.encodingType == wcv.PWM: # may want to kill this and decode from widths
        # the last symbol will have its zero time swallowed by the dead air that comes 
        # after the transmission, so add it
        del packetWidths[-1] # this is the interpacket dead air
        if widthCheck(packetWidths[-1], protocol.pwmZeroSymbol_samp[0], wcv.timingError):
            packetWidths.append(protocol.pwmZeroSymbol_samp[1]) # add a zero trail width
        elif widthCheck(packetWidths[-1], protocol.pwmOneSymbol_samp[0], wcv.timingError):
            packetWidths.append(protocol.pwmOneSymbol_samp[1]) # add a one trail width
        else:
            print "bad symbol encountered at end of widths list"
            print "expected: " + str(protocol.pwmZeroSymbol_samp[0]) + ", got: " + str(packetWidths[-1])
            encodingValid = False

        # go through each width pair and determine long or short duty cycle
        while i < len(packetWidths)-1:
            if (widthCheck(packetWidths[i], protocol.pwmZeroSymbol_samp[0], wcv.timingError) and \
                widthCheck(packetWidths[i+1], protocol.pwmZeroSymbol_samp[1], wcv.timingError)):
                # we have a zero if both the high and low portions check out
                rawPacket.append(wcv.DATA_ZERO)
            elif widthCheck(packetWidths[i], protocol.pwmOneSymbol_samp[0], wcv.timingError) and \
                widthCheck(packetWidths[i+1], protocol.pwmOneSymbol_samp[1], wcv.timingError):
                # we have a zero if both the high and low portions check out
                rawPacket.append(wcv.DATA_ONE)
            else:
                print "bad symbol encountered at index: " + str(i)
                print "expected: " + str(protocol.pwmZeroSymbol_samp[0]) + " or: " + str(protocol.pwmOneSymbol_samp[0]) + ", got: " + str(packetWidths[i])
                print "expected: " + str(protocol.pwmZeroSymbol_samp[1]) + " or: " + str(protocol.pwmOneSymbol_samp[1]) + ", got: " + str(packetWidths[i+1])
                # if this is the last half of the last bit in the transmission, then we're OK
                if len(rawPacket) == protocol.packetSize:
                    print "last bit in transmission, so it's OK"
                    encodingValid = True
                else:
                    encodingValid = False

            i+=2 # go to next pair of widths

        decodedPacket += rawPacket
        #print "raw length: " + str(len(rawPacket))
        #print rawPacket

    elif protocol.encodingType == wcv.NO_ENCODING:
        decodedPacket += rawPacket

    return(interPacketValid, preambleValid, headerValid, encodingValid)


#####################################
def widthCheck(width, expectedWidth, unitError):
    try:
        if (width >= expectedWidth * (1 - unitError)) and \
           (width <= expectedWidth * (1 + unitError)):
            return(True)
        else:
            return(False)
    except:
        if wcv.verbose:
            print "Encountered NULL value in width check"
        return(False)

#####################################
# This function checks the width passed and compares it to the unit width for this protocol. If
# the width is equal to one unit width (plus or minus the unit error margin), a value is returned
# denoting one unit of width. If it is equal to two units (plus or minus error), this is also
# returned. In all other cases, a bad width is flagged.
def widthMeasure(width, unitWidth, unitError):

    minShort = unitWidth * (1 - unitError)
    maxShort = unitWidth * (1 + unitError)
    minLong = 2 * unitWidth * (1 - unitError)
    maxLong = 2 * unitWidth * (1 + unitError)

    if (width >= minShort) and (width <= maxShort):
        return(wcv.UNIT_1X)
    elif (width >= minLong) and (width <= maxLong):
        return(wcv.UNIT_2X)
    else:
        print("Bad Level Width: " + str(width))
        return(wcv.BAD_WIDTH)
 

#####################################
# NEED: move this into a different section; want raw and decoded for display
def pwmDecode(encodedPacket):
    i=0
    packet = []

    # sometimes we miss trailing zeros because they look like inter-packet
    # levels; so we add the interpacket symbol to the end if necessary
    while (len(encodedPacket) % PWM_SYMBOL_SIZE) != 0: # NEED to fix this function
        encodedPacket.append(INTERPACKET_SYMBOL)
        
    while i < (len(encodedPacket)+1):
        # each PWM symbol has been defined in terms of unit width
        if (encodedPacket[i:i+3] == PWM_ONE_SYMBOL):
            packet.append(wcv.DATA_ONE)
        elif (encodedPacket[i:i+3] == PWM_ZERO_SYMBOL):
            packet.append(wcv.DATA_ZERO)

        # move to next PWM symbol
        i = i + 3
    return packet


#####################################
# NEED: move this into a different section; want raw and decoded for display
def manchesterDecode(encodedPacket, encodingType):
    i=1
    packet = []

    while i < len(encodedPacket):
        # check that encoding is intact; paired bits cannot be the same
        if encodedPacket[i] == encodedPacket[i-1]:
            print "Manchester decode fail: fallen out of sync"
            return (packet)
        
        # now just take the second bit of the pair (assuming IEEE 802.3)
        if encodingType == wcv.STD_MANCHESTER:
            packet.append(encodedPacket[i])
        elif encodingType == wcv.INV_MANCHESTER:
            packet.append(encodedPacket[i-1])
        i = i + 2 # move to next pair
    #print "i = " + str(i)
    #print len(packet)
    #print packet
    return packet


#####################################
# NEED: move this out of the current file
def printPacket(outFile, packet, outputHex):

    if outputHex: # output in hex
        i = 0
        while i < len(packet)-3:
            hexVal = packet[i]*8 + packet[i+1]*4 + packet[i+2]*2 + packet[i+3]
            outFile.write(hex(hexVal)[-1:]) 
            i+=4
            if (i % 8) == 0: # add a space between each byte
                outFile.write(' ')
            
        if (len(packet) % 4 != 0): # have to display the leftover
            outFile.write(' + b')
            for j in range(i, len(packet)):
                if packet[j] == wcv.DATA_ZERO:
                    outFile.write('0')
                elif packet[j] == wcv.DATA_ONE:
                    outFile.write('1')
                else:
                    outFile.write("FATAL ERROR\n")

    else: # output in binary
        for i in range(len(packet)):
            # add a break at certain points
            if (i % 8) == 0:
                outFile.write(' ')

            # write each bit in ASCII
            if packet[i] == wcv.DATA_ZERO:
                outFile.write('0')
            elif packet[i] == wcv.DATA_ONE:
                outFile.write('1')
            else:
                outFile.write("FATAL ERROR\n")
                break

    outFile.write('\n')
    return(0)

#####################################
# Rewritten version of original function to check inter-tx width, preamble and header
# This version generates a list of the ideal expected timing widths based on the 
# protocol given. A second function then executes the comparison with the actual
# waveform's list of widths. 
def checkValidPacket(protocol, packetWidths):
    
    # build ideal timing list
    framingList = []
    # add the preamble
    for n in range(0, protocol.preambleSize[0]):
        framingList.append(protocol.preambleSymbolLow_samp)
        framingList.append(protocol.preambleSymbolHigh_samp)
        
    # add the header
    if protocol.headerWidth >= 0:
        framingList.append(protocol.headerWidth_samp)

    # debug only
    print "Framing List:"
    print framingList
    print "Input List:"
    print packetWidths
         
    # check this ideal framing list against the one passed into the fn
    if sequenceCompare(protocol, framingList, packetWidths):
        if wcv.verbose:
            print "Primary preamble and header match transmission"
        return (len(framingList), True, True, True)
    
    # add the preamble
    for i in range(0, protocol.preambleSize[1]):
        framingList.append(protocol.preambleSymbolLow_samp)
        framingList.append(protocol.preambleSymbolHigh_samp)
        
    # add the header
    if protocol.headerWidth >= 0:
        framingList.append(protocol.headerWidth_samp)
        
    # check this ideal framing list against the one passed into the fn
    if sequenceCompare(protocol, framingList, packetWidths):
        if wcv.verbose:
            print "Secondary preamble and header match transmission"
        return (len(framingList), True, True, True)
    
    # if we got this far, then nothing matched
    if wcv.verbose:
        print "Preamble and header match FAIL"
    return (len(framingList), False, False, False)

    
# this function checks all of the widths in two lists, returning True if they all 
# match withing the tolerance specified    
def sequenceCompare(protocol, idealTxList, realTxList):
    for i in range(1, len(idealTxList)): # skip the first timing, as the zero gets swallowed up by the inter-packet timing
        print "i = " + str(i)
        try:
            if not widthCheck(realTxList[i], idealTxList[i], wcv.timingError):
                return(False)
        except:
            if wcv.verbose:
                print "NULL value encountered during sequence compare"
                print "len(realTxList): " + str(len(realTxList))
                print "len(idealTxList): " + str(len(idealTxList))
            return(False)    
    return True

