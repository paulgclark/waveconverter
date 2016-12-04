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
def preambleSyncFound(protocol, masterWidthList, preambleWidthList, start, timingError, verbose):

    i = 0
    # for each width in the preamble
    while i < len(preambleWidthList):
        # if it matches the width in the packet
        if not widthCheck(masterWidthList[start+i], preambleWidthList[i], timingError, verbose):
            return False
        i+=1

    return True # if we haven't found a mismatch after going through all bits


#####################################
# takes the width data and checks that it is a legal packet, then extracts data
# NEED: error checking
# NEED: packet specs from input list
# NEED: check for even length so our zeros and ones don't get out of sync
# NEED: seeding the array with an initial zero should be parameterized
def decodePacket(protocol, packetWidths, decodedPacket, rawPacket, timingError, verbose):

    # check the packet's preamble, header, etc.
    encodingValid = True
    (dataStartIndex, interPacketValid, preambleValid, headerValid) = checkValidPacket(protocol, packetWidths, timingError, verbose)
    
    print "checkValidPacket Results:"
    print "    interPacketValid = " + str(interPacketValid)
    print "    preambleValid    = " + str(preambleValid)
    print "    headerValid      = " + str(headerValid)
    print "    dataStartIndex   = " + str(dataStartIndex)
    try:
        print "    starting width   = " + str(packetWidths[dataStartIndex])
    except:
        print "    starting width   = N/A"

    # if the preamble or header is broken, get out now
    if not preambleValid or not headerValid:
        encodingValid = False
        return(interPacketValid, preambleValid, headerValid, encodingValid)
    # set loop index to the start of the data portion of the packet
    i = dataStartIndex

    # this should be tied to the interpacket width or preamble sync event
    if (i % 2) == 0:
        currentLevel = wcv.DATA_ZERO
    else:
        currentLevel = wcv.DATA_ONE
 
    measurement = wcv.BAD_WIDTH

    # if we have a header, then it has swallowed up the low part of the first symbol, which we can now flag
    #if protocol.headerWidth_samp > 0:
    #    i = i - 1 # walk the index back
    #    headerSymbol = True
    #else:
    #    headerSymbol = False
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
                print("Error: Bad level width")
                encodingValid = False

            # flip level and increment index
            i = i + 1
            if (currentLevel == wcv.DATA_ZERO):
                currentLevel = wcv.DATA_ONE
            elif (currentLevel == wcv.DATA_ONE):
                currentLevel = wcv.DATA_ZERO
            else:
                print("Error: Level isn't either one or zero")
                encodingValid = False

        # remember that the last Manchester symbol will be swallowed
        rawPacket.append(wcv.DATA_ZERO)
        # now that we have raw bits, do the decoding
        #print rawPacket
        decodedPacket += manchesterDecode(rawPacket, protocol.encodingType) 
        # NEED code here for rev

    elif protocol.encodingType == wcv.PWM:
        # there are two major factors affecting PWM decoding:
        # - whether or not the payload was preceeded by a header
        # - whether the PWM symbol consists of a low level followed by high level or vice versa
        
        # in the first case, the starting symbol has a low period swallowed up by the header
        if protocol.headerWidth_samp > 0 and protocol.pwmSymbolOrder01:
            i = i - 1 # walk the index back
            headerSymbolSwallow = True
            trailingSymbolSwallow = False
        # in this case, the starting symbol is fin, but the last one is swallowed in the interpacket dead air
        elif protocol.headerWidth_samp > 0 and not protocol.pwmSymbolOrder01:
            headerSymbolSwallow = False
            trailingSymbolSwallow = True
        # in this case, both the leading and trailing symbols are intact
        elif protocol.headerWidth_samp <= 0 and protocol.pwmSymbolOrder01:
            headerSymbolSwallow = False
            trailingSymbolSwallow = False
        # this is an unlikely scenario, where the leading high part of the first payload symbol
        # is swallowed up by the last part of the preamble, the final symbol is also swallowed
        # NOT YET IMPLEMENTED
        else:
            pass
        
        # if we have the high period followed by the low, we need to swap the expected PWM widths
        if protocol.pwmSymbolOrder01:
            firstSymbolWidthZero = protocol.pwmZeroSymbol_samp[0]
            secondSymbolWidthZero = protocol.pwmZeroSymbol_samp[1]
            firstSymbolWidthOne = protocol.pwmOneSymbol_samp[0]
            secondSymbolWidthOne = protocol.pwmOneSymbol_samp[1]
        else:
            firstSymbolWidthZero = protocol.pwmZeroSymbol_samp[1]
            secondSymbolWidthZero = protocol.pwmZeroSymbol_samp[0]
            firstSymbolWidthOne = protocol.pwmOneSymbol_samp[1]
            secondSymbolWidthOne = protocol.pwmOneSymbol_samp[0]
            
        # the last symbol will have its zero time swallowed by the dead air that comes 
        # after the transmission, so add it
        if wcv.verbose:
            print "packetWidths: "
            print packetWidths
        #del packetWidths[-1] # this is the interpacket dead air NO LONGER TRUE: DELETE LINE
        # restore the final symbol width if necessary
        if trailingSymbolSwallow:
            if widthCheck(packetWidths[-1], firstSymbolWidthZero, wcv.timingError, verbose):
                packetWidths.append(secondSymbolWidthZero) # add a zero trail width
            elif widthCheck(packetWidths[-1], firstSymbolWidthOne, wcv.timingError, verbose):
                packetWidths.append(secondSymbolWidthOne) # add a one trail width
            else:
                print "bad symbol encountered at end of widths list"
                print "expected: " + str(firstSymbolWidthZero) + " or " + str(firstSymbolWidthOne) \
                      + ", got: " + str(packetWidths[-1])

        # go through each width pair and determine long or short duty cycle
        while i < len(packetWidths)-1:
            print "i = " + str(i)
            print "First half of symbol: " + str(packetWidths[i])
            print "Second half of symbol: " + str(packetWidths[i+1])
            if (headerSymbolSwallow or (widthCheck(packetWidths[i], firstSymbolWidthZero, wcv.timingError, verbose)) and \
                widthCheck(packetWidths[i+1], secondSymbolWidthZero, wcv.timingError, verbose)):
                # we have a zero if both the high and low portions check out
                rawPacket.append(wcv.DATA_ZERO)
            elif (headerSymbolSwallow or widthCheck(packetWidths[i], firstSymbolWidthOne, wcv.timingError, verbose)) and \
                widthCheck(packetWidths[i+1], secondSymbolWidthOne, wcv.timingError, verbose):
                # we have a zero if both the high and low portions check out
                rawPacket.append(wcv.DATA_ONE)
            else:
                # if this is the last half of the last bit in the transmission, then we're OK
                if len(rawPacket) == protocol.packetSize:
                    encodingValid = True
                else:
                    encodingValid = False
                    print "bad symbol encountered at index: " + str(i) + " out of max index: " + str(len(packetWidths))
                    print "expected: " + str(firstSymbolWidthZero) + " or: " + str(firstSymbolWidthOne) + ", got: " + str(packetWidths[i])
                    print "expected: " + str(secondSymbolWidthZero) + " or: " + str(secondSymbolWidthOne) + ", got: " + str(packetWidths[i+1])

            i += 2 # go to next pair of widths
            headerSymbolSwallow = False # only consider this the first time through

        decodedPacket += rawPacket # NEED to remove this
        #print "raw length: " + str(len(rawPacket))
        #print rawPacket

    elif protocol.encodingType == wcv.NO_ENCODING:
        decodedPacket += rawPacket

    if protocol.packetSize > 0 and len(decodedPacket) != protocol.packetSize:
        encodingValid = False

    return(interPacketValid, preambleValid, headerValid, encodingValid)


#####################################
def widthCheck(width, expectedWidth, unitError, verbose):
    try:
        if (width >= expectedWidth * (1 - unitError)) and \
           (width <= expectedWidth * (1 + unitError)):
            return(True)
        else:
            return(False)
    except:
        if verbose:
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
def checkValidPacket(protocol, packetWidths, timingError, verbose):
    
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
    if verbose:
        print "Framing List:"
        print framingList
        print "Input List:"
        print packetWidths
         
    # check this ideal framing list against the one passed into the fn
    if sequenceCompare(protocol, framingList, packetWidths, timingError, verbose):
        if verbose:
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
    if sequenceCompare(protocol, framingList, packetWidths, timingError, verbose):
        if verbose:
            print "Secondary preamble and header match transmission"
        return (len(framingList), True, True, True)
    
    # if we got this far, then nothing matched
    if verbose:
        print "Preamble and header match FAIL"
    return (len(framingList), False, False, False)

    
# this function checks all of the widths in two lists, returning True if they all 
# match withing the tolerance specified    
def sequenceCompare(protocol, idealTxList, realTxList, timingError, verbose):
    for i in range(1, len(idealTxList)): # skip the first timing, as the zero gets swallowed up by the inter-packet timing
        if verbose:
            print "i = " + str(i)
        try:
            if not widthCheck(realTxList[i], idealTxList[i], wcv.timingError, verbose):
                return(False)
        except:
            if verbose:
                print "NULL value encountered during sequence compare"
                print "len(realTxList): " + str(len(realTxList))
                print "len(idealTxList): " + str(len(idealTxList))
            return(False)    
    return True
