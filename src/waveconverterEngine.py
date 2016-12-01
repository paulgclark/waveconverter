#############################################################################################3
########### copyright 2015 Factoria Labs
# This file contains  
#

# waveconverter decoding modules
import waveConvertVars as wcv
#from breakWave import breakdownWaveform
from breakWave import breakdownWaveform2
from widthToBits import separatePackets
from widthToBits import decodePacket
from statEngine import checkCRC
#from widthToBits import printPacket
#from config import *
from protocol_lib import ProtocolDefinition

import io

def decodeBaseband(waveformFileName, basebandSampleRate, outFileName,
                   protocol, outputHex, verbose):

    masterWidthList = [] # contains the widths for the entire file
    packetWidthsList = [] # list of packet width lists
    packetList = [] # list of decoded packets
    rawPacketList = [] # list of pre-decoded packets

    # open input file for read access in binary mode
    with io.open(waveformFileName, 'rb') as waveformFile:

        # open output file for write access
        outFile = open(outFileName, 'w')

        # scan through waveform and get widths
        if (breakdownWaveform(protocol, waveformFile, masterWidthList) == wcv.END_OF_FILE):

            # separate master list into list of packets
            separatePackets(protocol, masterWidthList, packetWidthsList)

            # decode each packet and add it to the list
            i=0
            for packetWidths in packetWidthsList:
                # print("Packet #" + str(i+1) + ": ")
                # print(packetWidths)
                decodedPacket = [] # move out of loop to main vars?
                rawPacket = [] # move out of loop to main vars?
                decodePacket(protocol, packetWidths, decodedPacket, rawPacket, verbose)
                # print "Raw and Decoded Packets:"
                # print(rawPacket)
                # print(decodedPacket)
                packetList.append(decodedPacket[:])
                rawPacketList.append(rawPacket[:])
                i+=1
                #break # debug - only do first packet

    waveformFile.close()

    return packetList

# this function takes the list of decoded packets and produces a
# string consisting of each packet formatted according to the user's
# direction
def packetsToFormattedString(packetList, protocol, outputHex):
    outputString = ""
    i=0
    for packet in packetList:
        outputString += ("Transmission #" + str(i+1) + ":")
        # align printout based on packet number
        if (i + 1) < 10:
            outputString += " "
        if (i + 1) < 100:
            outputString += " "
        outputString += packetToString(packet, outputHex)
        i+=1
    return(outputString)
        
        
def packetToString(packet, outputHex):

    packetString = ""
    if outputHex: # output in hex
        i = 0
        while i < len(packet)-3:
            hexVal = packet[i]*8 + packet[i+1]*4 + packet[i+2]*2 + packet[i+3]
            packetString += str(hex(hexVal)[-1:]) 
            i+=4
            if (i % 8) == 0 and i != 0: # add a space between each byte
                packetString += ' '
            
        if (len(packet) % 4 != 0): # have to display the leftover
            packetString += ' + b'
            for j in range(i, len(packet)):
                if packet[j] == wcv.DATA_ZERO:
                    packetString += '0'
                elif packet[j] == wcv.DATA_ONE:
                    packetString += '1'
                else:
                    packetString += 'FATAL ERROR\n'

    else: # output in binary
        for i in range(len(packet)):
            # add a break at certain points
            if (i % 8) == 0 and i != 0:
                packetString += ' '

            # write each bit in ASCII
            if packet[i] == wcv.DATA_ZERO:
                packetString += '0'
            elif packet[i] == wcv.DATA_ONE:
                packetString += '1'
            else:
                packetString += 'FATAL ERROR\n'
                break

    return(packetString)

class basebandTx:
    txNum = 0
    timeStamp_us = 0.0 # in microseconds
    waveformData = []
    widthList = []
    interPacketTimingValid = False
    preambleValid = False
    headerValid = False
    framingValid = False
    encodingValid = False
    crcValid = False
    txValid = False
    fullBasebandData = []
    payloadData = []
    crcBits = []
    id = []
    value1 = 0
    value2 = 0
    binaryString = ""
    hexString = ""
    
    def __init__(self, txNum, timeStampIn, waveformDataIn):
        self.txNum = txNum
        self.timeStamp = timeStampIn
        self.waveformData = waveformDataIn
        self.fullBasebandData = []
        
    def decodeTx(self, protocol, glitchFilterCount, timingError, verbose):
        if verbose:
            print "decoding transmission #" + str(self.txNum)
                        
        # scan through waveform and get widths
        self.widthList = []
        breakdownWaveform2(protocol, self.waveformData, self.widthList, glitchFilterCount)
        #print len(self.waveformData)
        #print self.waveformData
        #print self.widthList

        tempUnused = []
        self.fullBasebandData = []     # dump any info from previous decoding attempt
        (self.interPacketTimingValid, self.preambleValid, 
         self.headerValid, self.encodingValid) = \
            decodePacket(protocol, self.widthList, self.fullBasebandData, tempUnused, timingError, verbose)
        
        self.framingValid = self.interPacketTimingValid & \
                            self.preambleValid & \
                            self.headerValid

        # NEED: add protocol check to ensure bits are legal
        self.crcBits = self.fullBasebandData[protocol.crcLow:protocol.crcHigh+1]
        self.payloadData = self.fullBasebandData[protocol.crcDataLow:protocol.crcDataHigh+1]
        if verbose:
            print "crcbits and payload"
            print self.crcBits
            print self.payloadData
        
        if len(protocol.crcPoly) == 0: # if no CRC given, then assume valid
            self.crcValid = True
        else:
            self.crcValid = checkCRC(protocol, self.crcBits, self.payloadData)

        if self.framingValid and self.encodingValid and self.crcValid and (len(self.fullBasebandData) == protocol.packetSize):
            self.txValid = True
            
        # NEED break out ID
        # NEED break out Value1
        # NEED break out Value2
        
        self.binaryString = packetToString(self.fullBasebandData, 0)
        self.hexString = packetToString(self.fullBasebandData, 1)
        if verbose:
            print "data size: " + str(len(self.fullBasebandData))
        #print self.binaryString
        
    def display(self):
        print "Displaying Transmission Object " + str(self.txNum)
        print "Time Stamp (us): " + str(self.timeStamp_us)
        print "Waveform Size (samples): " + str(len(self.waveformData))
        print "Preamble Valid: " + str(self.preambleValid)
        print "Header Valid: " + str(self.headerValid)
        print "Framing Valid: " + str(self.framingValid)
        print "Encoding Valid: " + str(self.encodingValid)
        print "CRC Valid: " + str(self.crcValid)
        print "Widths List:"
        print self.widthList
        print "Full baseband data:"
        print self.fullBasebandData
        print "Payload Data:"
        print self.payloadData
        print "CRC String:"
        print self.crcBits
        print "ID:"
        print self.id
        print "Value 1: " + str(self.value1)
        print "Value 2: " + str(self.value2)
        print "Binary String: " + self.binaryString
        print "Hex String: " + self.hexString


from demod_rf import ook_flowgraph
from demod_rf import fsk_flowgraph
def demodIQFile(verbose, modulationType, iqSampleRate, basebandSampleRate, centerFreq, frequency,
                channelWidth, transitionWidth, threshold, iqFileName, waveformFileName, fskDeviation):
    # create flowgraph object and execute flowgraph
        try:
            if verbose:
                print "Running Demodulation Flowgraph"
            if modulationType == wcv.MOD_OOK:
                flowgraphObject = ook_flowgraph(iqSampleRate, # rate_in
                                                basebandSampleRate, # rate_out
                                                centerFreq,
                                                frequency, 
                                                channelWidth,
                                                transitionWidth,
                                                threshold,
                                                iqFileName,
                                                waveformFileName) # temp digfile
                flowgraphObject.run()
            elif modulationType == wcv.MOD_FSK:
                flowgraphObject = fsk_flowgraph(iqSampleRate, # samp_rate_in 
                                                basebandSampleRate, # rate_out 
                                                centerFreq,
                                                frequency, # tune_freq
                                                channelWidth,
                                                transitionWidth,
                                                threshold,
                                                fskDeviation,
                                                iqFileName, 
                                                waveformFileName) # temp file
                flowgraphObject.run()
            else:
                print "Invalid modulation type selected" # NEED to put in status bar or pop-up
            
        except [[KeyboardInterrupt]]:
            pass
        
        if verbose:
            print "Flowgraph completed"

        # get the message queue object used in the flowgraph          
        queue = flowgraphObject.sink_queue
        
        # now run through each message in the queue, and pull out each 
        # byte from each message
        basebandList = []
        for n in xrange(queue.count()):
            messageSPtr = queue.delete_head() # get and remove the front-most message
            messageString = messageSPtr.to_string() # convert message to a string
            # for each character in the string, determine if binary 1 or 0 and append
            for m in xrange(len(messageString)):
                if messageString[m] == b'\x00':
                    basebandList.append(0)
                elif messageString[m] == b'\x01':
                    basebandList.append(1)
                else:
                    basebandList.append(messageString)
                    print "Fatal Error: flowgraph output baseband value not equal to 1 or 0"
                    print "n = " + str(n)
                    exit(1)
        return basebandList

# this function takes the binary baseband data and breaks it into individual
# transmissions, assigning each to a Tx Object along with a timestamp
from breakWave import breakBaseband
def buildTxList(basebandData, basebandSampleRate, interTxTiming, glitchFilterCount, verbose):
    
    basebandDataByTx = breakBaseband(basebandData, interTxTiming, glitchFilterCount, verbose)
    runningSampleCount = 0
    txList = []

    # build a list of transmission objects with timestamp
    for iTx in basebandDataByTx:
        timeStamp_us = 1000000.0 * runningSampleCount/basebandSampleRate
        runningSampleCount += len(iTx)
        txList.append(basebandTx(len(txList), timeStamp_us, iTx))

    return txList

def decodeAllTx(protocol, txList, outputHex, timingError, glitchFilterCount, verbose):

    # call decode engine for each transmission
    formatString = '{:>6}   {}\n'
    decodeOutputString = formatString.format("TX Num", "Payload") # need to start over after each decode attempt
    i = 0
    for iTx in txList:
        if i == len(txList):
            iTx.display()
        else:
            iTx.decodeTx(protocol, timingError, glitchFilterCount, verbose)
        if outputHex:
            decodeOutputString += formatString.format(str(i+1), iTx.hexString)
        else:
            decodeOutputString += formatString.format(str(i+1), iTx.binaryString)
        i+=1

    return (txList, decodeOutputString)