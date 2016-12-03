# This file contains the python code that does a first pass over a raw
# input digital waveform. The output of this pass is an array of integers, 
# each defining the width of successive high and low states. The output
# feeds into a function that partitions the resulting array into packets.
#
# This file assumes that each bit of the bitstream is contained in a
# single byte, each with a value of either 0x00 or 0x01.
#
import sys # NEED
import io # NEED
import os # NEED
import waveConvertVars as wcv
#from protocol_lib import maxTransmissionSize
#from waveConvertVars import * # NEED
#from config import * # NEED

FALLING_EDGE = 0
RISING_EDGE = 1

#####################################
# reads through a file and produces list
def basebandFileToList(basebandFileName):
    basebandList = []
    # open file
    with io.open(basebandFileName, 'rb') as basebandFile:
        # read each byte and add to list
        try:
            byte = basebandFile.read(1)
            while byte != "":
                if byte == b'\x01':
                    basebandList.append(1)
                else:
                    basebandList.append(0)                    
                byte = basebandFile.read(1)
        finally:
            basebandFile.close()

    return basebandList

#####################################
# reads through the list representing the baseband data and divides it
# into smaller lists (one for each transmission), also cutting out dead time
def breakBaseband(basebandData, minTimeBetweenTx, glitchFilterCount, verbose):
    basebandTransmissionList = []
    newTx = []
    i = 0
    deadAirCount = 0
    currentStartIndex = 0
    consecutiveOnes = 0
    
    if verbose:
        print "Breaking baseband into individual transmissions..."
        #print "maxTxSize (samples): " + str(wcv.protocol.maxTransmissionSize())
    # run through file and find large swaths of dead air
    # two states:
    #   0) in the middle of dead air
    #   1) in the middle of a transmission
    IN_DEAD_AIR = 0
    IN_TX = 1
    state = IN_DEAD_AIR 
    while True:
        if state == IN_DEAD_AIR: # if we are in the middle of dead air
            # if we are at the end of the list, just quit
            if i >= len(basebandData):
                break
            # have we encountered a transmission?
            if (basebandData[i] == 1) and (consecutiveOnes > glitchFilterCount):
                if verbose:
                    print "Encountered TX at: " + str(i)
                state = IN_TX # move to signal found state
                deadAirCount = 0 # restart dead air counter
                currentStartIndex = i # current transmission starts now
            # if we have no transmission, just increment stuff
            else:
                deadAirCount += 1
        elif state == IN_TX:
            # if we are at the end of the list, append the current tx list and then quit
            if i >= len(basebandData):
                newTx = [0] * 100 + basebandData[currentStartIndex:i] # prepend zeros for nicer display
                basebandTransmissionList.append(newTx)
                break
            # have we encountered the end of a transmission?
            if deadAirCount > minTimeBetweenTx:
                newTx = [0] * 100 + basebandData[currentStartIndex:i] # prepend zeros for nicer display
                basebandTransmissionList.append(newTx)
                state = IN_DEAD_AIR
                if verbose:
                    print "Got Tx starting at:" + str(currentStartIndex) + " ending at index: " + str(i) + "length = " + str(len(newTx))
                    print "timestamp: " + str(len(basebandTransmissionList)/wcv.samp_rate)
            elif (basebandData[i] == 1) and (consecutiveOnes > glitchFilterCount):
                deadAirCount = 0
            else:
                deadAirCount += 1
        else:
            print "Error encountered while breaking down waveform"
            return(1)
        # regardless of state or transition, keep a count of the consecutive ones
        # and increment the index
        if basebandData[i] == 1:
            consecutiveOnes += 1
        else:
            consecutiveOnes = 0            
        i += 1

    if verbose:
        print "number of transmissions: " + str(len(basebandTransmissionList))
        
    return basebandTransmissionList

###########################################
# Used for extracting timing between edges given a file input
#####################################
# reads through a file, byte-by-byte until a 0x00 is followed by a 0x01
def timeToNextEdge(bitFile, edge):
    width=0

    if edge==RISING_EDGE: lastByte = b'\x00'
    else: lastByte = b'\x01'

    while True: 
        newByte = bitFile.peek(1)[:1] # look ahead at the next byte in buffer
        # if we come to EOF before a rising edge, pass on EOF
        if not newByte:
            return(wcv.END_OF_FILE)

        # if the value is not 0 or 1, exit immediately
        if (newByte != b'\x00') and (newByte != b'\x01'):
            print (bitFile.tell(), ': Illegal binary value : ', newByte, '\n');
            return(wcv.ILLEGAL_VALUE)

        # look for rising edge or a falling edge
        if ((edge==RISING_EDGE)and(lastByte==b'\x00')and(newByte==b'\x01')) or \
           ((edge==FALLING_EDGE)and(lastByte==b'\x01')and(newByte==b'\x00')):
            lastByte=bitFile.read(1) # advance file pointer
            #return(float(width)) # found it!
            return(width) # found it!
        else:
            width+=1;
            lastByte=bitFile.read(1) # advance file pointer


#####################################
# reads through a file, byte-by-byte until a 0x00 is followed by a 0x01
def timeToNextEdge2(waveformList, edge, i):
    width=0

    if edge==RISING_EDGE: lastByte = 0
    else: lastByte = 1

    #i=0
    while True: 
        # if we come to EOF before a rising edge, pass on EOF
        if i >= len(waveformList) - 1:
            return(wcv.END_OF_FILE, i)
        
        newByte = waveformList[i+1] 

        # if the value is not 0 or 1, exit immediately
        if (newByte != 0) and (newByte != 1):
            print (i, ': Illegal binary value : ', newByte, '\n');
            return(wcv.ILLEGAL_VALUE, i)

        # look for rising edge or a falling edge
        i+=1
        if ((edge==RISING_EDGE)and(lastByte==0)and(newByte==1)) or \
           ((edge==FALLING_EDGE)and(lastByte==1)and(newByte==0)):
            lastByte=waveformList[i] # advance list index
            return(width, i) # found it!
        else:
            width+=1;
            lastByte=waveformList[i] # advance file pointer


#####################################
# This function takes the sampled digital input and reduces it
# to a series of integers, each representing the width of
# the waveform's logic level before it transitions to the next
# NEED: Error checking? Maybe not
# NEED: If a period longer than the interpacket comes up, resync to IPSYMBOL
def breakdownWaveform(protocol, waveformFile, masterWidthList):

    if protocol.interPacketSymbol == wcv.DATA_ZERO:
        nextEdge = RISING_EDGE 
    elif protocol.interPacketSymbol == wcv.DATA_ONE:
        nextEdge = FALLING_EDGE 
    width = 0

    # run through file and catalog all transition widths
    #index = 0
    while True:
        # measure the number of samples to the next edge
        #(width, index) = timeToNextEdge2(waveformFile, nextEdge, index)
        width = timeToNextEdge(waveformFile, nextEdge)

# This should not be necessary; delete
        # if a width is longer than the packet separation width
        # assume we got messed up and resync
#        if width >= INTERPACKET_WIDTH:
            # resync by checking if we are at the correct INTERPACKET_SYMBOL
#            if INTERPACKET_SYMBOL == DATA_ZERO:
            

        # error checking
        if (width == wcv.END_OF_FILE):
            break
        elif (width == wcv.ILLEGAL_VALUE):
            return(wcv.ILLEGAL_VALUE)
        else:
            masterWidthList.append(width)

        if (nextEdge == RISING_EDGE):
            nextEdge = FALLING_EDGE
        else:
            nextEdge = RISING_EDGE

    #print("\n\n\nPre-glitch:")
    #print(masterWidthList)
    if protocol.glitchFilterCount > 0:
        glitchFilter(masterWidthList, wcv.glitchFilterCount) 
        # glitch filter behavior not part of protocol, but top level WC control
    #print("\n\n\nPost-glitch:")
    #print(masterWidthList)
    return(wcv.END_OF_FILE)

#####################################
# NOTE: This function is a slightly modified version of breakdownWaveform designed
# to be used on a single transmission rather than a string of transmissions. It should
# eventually replace the original and be renamed. 
#
# This function takes the sampled digital input and reduces it
# to a series of integers, each representing the width of
# the waveform's logic level before it transitions to the next
# NEED: Error checking? Maybe not
# NEED: If a period longer than the interpacket comes up, resync to IPSYMBOL
def breakdownWaveform2(protocol, waveformList, masterWidthList, glitchFilterCount):

    if protocol.interPacketSymbol == wcv.DATA_ZERO:
        nextEdge = RISING_EDGE 
    elif protocol.interPacketSymbol == wcv.DATA_ONE:
        nextEdge = FALLING_EDGE 
    width = 0

    # run through file and catalog all transition widths
    index = 0
    while True:
        # measure the number of samples to the next edge
        (width, index) = timeToNextEdge2(waveformList, nextEdge, index)

# This should not be necessary; delete
        # if a width is longer than the packet separation width
        # assume we got messed up and resync
#        if width >= INTERPACKET_WIDTH:
            # resync by checking if we are at the correct INTERPACKET_SYMBOL
#            if INTERPACKET_SYMBOL == DATA_ZERO:
            

        # error checking
        if (width == wcv.END_OF_FILE):
            break
        elif (width == wcv.ILLEGAL_VALUE):
            return(wcv.ILLEGAL_VALUE)
        else:
            masterWidthList.append(width)

        if (nextEdge == RISING_EDGE):
            nextEdge = FALLING_EDGE
        else:
            nextEdge = RISING_EDGE

    if glitchFilterCount > 0:
        # glitch filter behavior not part of protocol, but top level WC control from GUI or cmd line
        glitchFilter(masterWidthList, glitchFilterCount) 

    return(wcv.END_OF_FILE)

#####################################
def glitchFilter(masterWidthList, glitchMax):

    #print("start glitch filter")
    i = 0
    while True:
        # break out of loop if at end of list
        if (i >= (len(masterWidthList) - 3)):
            break

        # if there is a glitch, combine the next three widths
        if masterWidthList[i+1] <= glitchMax:
            newWidth = masterWidthList[i] + \
                       masterWidthList[i+1] + \
                       masterWidthList[i+2] 
            masterWidthList[i] = newWidth
            del masterWidthList[i+1:i+3]
        # if there's a glitch, don't increment, there may be another
        else:
            i += 1
            
    # this loop above will sometimes leave short widths at the end of the list
    if masterWidthList[-2] <= glitchMax:
        newWidth = masterWidthList[-3] + \
                   masterWidthList[-2] + \
                   masterWidthList[-1]
        del masterWidthList[-1]
        del masterWidthList[-1]
        del masterWidthList[-1]
        masterWidthList.append(newWidth)
        
    # if the final item is a glitch, delete it
    if masterWidthList[1] <= glitchMax:
        del masterWidthList[-1]
 
    return(0)
