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
from waveConvertVars import * # NEED
from config import * # NEED

#class edgeEnum(Enum):
FALLING_EDGE = 0
RISING_EDGE = 1

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
            return(END_OF_FILE)

        # if the value is not 0 or 1, exit immediately
        if (newByte != b'\x00') and (newByte != b'\x01'):
            print (bitFile.tell(), ': Illegal binary value : ', newByte, '\n');
            return(ILLEGAL_VALUE)

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
# This function takes the sampled digital input and reduces it
# to a series of integers, each representing the width of
# the waveform's logic level before it transitions to the next
# NEED: Error checking? Maybe not
# NEED: If a period longer than the interpacket comes up, resync to IPSYMBOL
def breakdownWaveform(protocol, waveformFile, masterWidthList):

    if protocol.interPacketSymbol == DATA_ZERO:
        nextEdge = RISING_EDGE 
    elif protocol.interPacketSymbol == DATA_ONE:
        nextEdge = FALLING_EDGE 
    width = 0

    # run through file and catalog all transition widths
    while True:
        # measure the number of samples to the next edge
        width = timeToNextEdge(waveformFile, nextEdge)

# This should not be necessary; delete
        # if a width is longer than the packet separation width
        # assume we got messed up and resync
#        if width >= INTERPACKET_WIDTH:
            # resync by checking if we are at the correct INTERPACKET_SYMBOL
#            if INTERPACKET_SYMBOL == DATA_ZERO:
            

        # error checking
        if (width == END_OF_FILE):
            break
        elif (width == ILLEGAL_VALUE):
            return(ILLEGAL_VALUE)
        else:
            masterWidthList.append(width)

        if (nextEdge == RISING_EDGE):
            nextEdge = FALLING_EDGE
        else:
            nextEdge = RISING_EDGE

    #print("\n\n\nPre-glitch:")
    #print(masterWidthList)
    if protocol.glitchFilterCount > 0:
        glitchFilter(masterWidthList, protocol.glitchFilterCount)
    #print("\n\n\nPost-glitch:")
    #print(masterWidthList)
    return(END_OF_FILE)

#####################################
def glitchFilter(masterWidthList, glitchMax):

    #print("start glitch filter")
    i = 0
    while True:
        #print("i=" + str(i) + ":")
        #print(masterWidthList)
        # break out of loop if at end of list
        if (i >= (len(masterWidthList) - 3)):
            break
        #print(i) 
        #print(len(masterWidthList)) 

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
    #print("end glitch filter") 
    return(0)
