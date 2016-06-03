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
from waveConvertVars import *
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
        if protocol.headerLevel != DATA_NULL:
            preambleWidthList.append(protocol.headerWidth)

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
            if (masterWidthList[i] > protocol.interPacketWidth):
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
        if not widthCheck(masterWidthList[start+i], preambleWidthList[i], protocol.unitError):
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
    dataStartIndex = checkValidPacket(protocol, packetWidths)

    # set loop index to the start of the data portion of the packet
    i = dataStartIndex

    # this should be tied to the interpacket width
    if (i % 2) == 0:
        currentLevel = DATA_ZERO
    else:
        currentLevel = DATA_ONE
 
    measurement = BAD_WIDTH

    # note: the decodedPacket list has been passed to this fn as an empty list
    if (protocol.encodingType == STD_MANCHESTER) or (protocol.encodingType == INV_MANCHESTER):
        # extract data
        while i < len(packetWidths):
            measurement = widthMeasure(packetWidths[i], protocol.unitWidth, protocol.unitError)
            if (measurement == UNIT_1X):
                rawPacket.append(currentLevel)
            elif (measurement == UNIT_2X):
                rawPacket.append(currentLevel)
                rawPacket.append(currentLevel)
            else:
                print("Bad level width")

            # flip level and increment index
            i = i + 1
            if (currentLevel == DATA_ZERO):
                currentLevel = DATA_ONE
            elif (currentLevel == DATA_ONE):
                currentLevel = DATA_ZERO
            else:
                print("Level isn't either one or zero")

        # remember that the last Manchester symbol will be swallowed
        rawPacket.append(DATA_ZERO)
        # now that we have raw bits, do the decoding
        #print rawPacket
        decodedPacket += manchesterDecode(rawPacket, protocol.encodingType) 
        # NEED code here for rev

    elif protocol.encodingType == PWM: # may want to kill this and decode from widths
        # the last symbol will have its zero time swallowed, so add it
        if widthCheck(packetWidths[-1], protocol.pwmZeroSymbol[0], protocol.unitError):
            packetWidths.append(protocol.pwmZeroSymbol[1]) # add a zero trail width
        elif widthCheck(packetWidths[-1], protocol.pwmOneSymbol[0], protocol.unitError):
            packetWidths.append(protocol.pwmOneSymbol[1]) # add a one trail width
        else:
            print("bad symbol encountered")

        # go through each width pair and determine long or short duty cycle
        while i < len(packetWidths)-1:
            if (widthCheck(packetWidths[i], protocol.pwmZeroSymbol[0], protocol.unitError) and \
                widthCheck(packetWidths[i+1], protocol.pwmZeroSymbol[1], protocol.unitError)):
                # we have a zero if both the high and low portions check out
                rawPacket.append(DATA_ZERO)
            elif widthCheck(packetWidths[i], protocol.pwmOneSymbol[0], protocol.unitError) and \
                widthCheck(packetWidths[i+1], protocol.pwmOneSymbol[1], protocol.unitError):
                # we have a zero if both the high and low portions check out
                rawPacket.append(DATA_ONE)
            else:
                print("bad symbol encountered")

            i+=2 # go to next pair of widths

        decodedPacket += rawPacket
        #print "raw length: " + str(len(rawPacket))
        #print rawPacket

    elif protocol.encodingType == NO_ENCODING:
        decodedPacket += rawPacket

    return(0)


#####################################
def widthCheck(width, expectedWidth, unitError):
    if (width >= expectedWidth * (1 - unitError)) and \
       (width <= expectedWidth * (1 + unitError)):
        return(True)
    else:
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
        return(UNIT_1X)
    elif (width >= minLong) and (width <= maxLong):
        return(UNIT_2X)
    else:
        print("Bad Level Width: " + str(width))
        return(BAD_WIDTH)
 

#####################################
# NEED: move this into a different section; want raw and decoded for display
def pwmDecode(encodedPacket):
    i=0
    packet = []

    # sometimes we miss trailing zeros because they look like inter-packet
    # levels; so we add the interpacket symbol to the end if necessary
    while (len(encodedPacket) % PWM_SYMBOL_SIZE) != 0:
        encodedPacket.append(INTERPACKET_SYMBOL)
        
    while i < (len(encodedPacket)+1):
        # each PWM symbol has been defined in terms of unit width
        if (encodedPacket[i:i+3] == PWM_ONE_SYMBOL):
            packet.append(DATA_ONE)
        elif (encodedPacket[i:i+3] == PWM_ZERO_SYMBOL):
            packet.append(DATA_ZERO)

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
        if encodingType == STD_MANCHESTER:
            packet.append(encodedPacket[i])
        elif encodingType == INV_MANCHESTER:
            packet.append(encodedPacket[i-1])
        i = i + 2 # move to next pair
    #print "i = " + str(i)
    #print len(packet)
    #print packet
    return packet


#####################################
# NEED: move this out of the current file
def printPacket(outFile, packet, optionFlag):

    if optionFlag == "x" or optionFlag == "-x": # output in hex
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
                if packet[j] == DATA_ZERO:
                    outFile.write('0')
                elif packet[j] == DATA_ONE:
                    outFile.write('1')
                else:
                    outFile.write("FATAL ERROR\n")

    else: # output in binary
        for i in range(len(packet)):
            # add a break at certain points
            if (i % 8) == 0:
                outFile.write(' ')

            # write each bit in ASCII
            if packet[i] == DATA_ZERO:
                outFile.write('0')
            elif packet[i] == DATA_ONE:
                outFile.write('1')
            else:
                outFile.write("FATAL ERROR\n")
                break

    outFile.write('\n')
    return(0)


#####################################
# NEED: move this into a different section; want raw and decoded for display
# NEED: store any error info in the packet object
def checkValidPacket(protocol, packetWidths):

    # check for sufficiently long low period preceding packet
    if packetWidths[0] < protocol.interPacketWidth:
        print "Bad interpacket timing"

    # check preamble
    i = 1
    while i < (len(packetWidths)-2):
        # check that high portion is valid
        # NEED to use a simple width check function, not measure
        # NEED to build measure off the width check function
        #measurement = widthMeasure(packetWidths[i], protocol.preambleSymbolHigh, protocol.unitError) 
        i += 1 
        #if measurement == BAD_WIDTH:
        if not widthCheck(packetWidths[i-1], protocol.preambleSymbolHigh, protocol.unitError):
            if protocol.headerLevel == DATA_NULL: # if there's no header, get out of loop
                print "finished preamble"
                i+=-2
                break

        # check that low portion is valid
        if not widthCheck(packetWidths[i], protocol.preambleSymbolHigh, protocol.unitError):
            print "finished preamble"
            break
        else:
            i += 1 

    # check number of preamble symbols
    preambleSymbolCount = int(i/2)
    if preambleSymbolCount in protocol.preambleSize :
        print "Got good preamble"
    else:
        print "Bad preamble length: " + str(preambleSymbolCount)

    # check header if there is one
    if protocol.headerLevel != DATA_NULL:
        if protocol.headerLevel == DATA_ZERO:
            if abs(packetWidths[i] - protocol.headerWidth) > protocol.headerWidth*protocol.unitError:
                print "Header length invalid: " + str(packetWidths[i])
            dataStartIndex = i + 1 # next length after header is where data starts
        elif protocol.headerLevel == DATA_ONE:
            if abs(packetWidths[i] - protocol.headerWidth) > protocol.headerWidth*protocol.unitError:
                print "Header length invalid: " + str(packetWidths[i])
            dataStartIndex = i + 1 # next length after header is where data starts
    else: 
        dataStartIndex = i # no header so don't increment

    #print "(inside fn) DataStartIndex = " + str(dataStartIndex)
    return (dataStartIndex)

    # check width of each data pulse
    # presently doing this in the main decode loop, could move here

    # check data size
    # presently doing this in the main decode loop, could move here

    return(0)

