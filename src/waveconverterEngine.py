#############################################################################################3
########### copyright 2015 Factoria Labs
# This file contains  
#

# waveconverter decoding modules
import waveConvertVars as wcv
from breakWave import breakdownWaveform
from breakWave import breakdownWaveform2
from widthToBits import separatePackets
from widthToBits import decodePacket
#from widthToBits import printPacket
#from config import *
from protocol_lib import ProtocolDefinition

import io

def decodeBaseband(waveformFileName, basebandSampleRate, outFileName,
                   protocol, outputHex):

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
                decodePacket(protocol, packetWidths, decodedPacket, rawPacket)
                # print "Raw and Decoded Packets:"
                # print(rawPacket)
                # print(decodedPacket)
                packetList.append(decodedPacket[:])
                rawPacketList.append(rawPacket[:])
                i+=1
                #break # debug - only do first packet

            # print packets to file
            # print masterWidthList
            # print packetWidthsList

            # this function should only return the packets
            # hex conversion and file output should be in another
            # module and function; for now, we can output to a file and
            # then stream back into a display window
            # move this code to next FN
            """
            i=0
            for packet in packetList:
                outFile.write("Packet #" + str(i+1) + ": ")
                printPacket(outFile, packet, outputHex)
                i+=1
                
                # after we finish, close out files and exit
                
    # move this code to next FN
    outFile.close()
    """
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
            if (i % 8) == 0: # add a space between each byte
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
            if (i % 8) == 0:
                packetString += ' '

            # write each bit in ASCII
            if packet[i] == wcv.DATA_ZERO:
                packetString += '0'
            elif packet[i] == wcv.DATA_ONE:
                packetString += '1'
            else:
                packetString += 'FATAL ERROR\n'
                break

    packetString += '\n'
    return(packetString)

class basebandTx:
    txNum = 0
    timeStamp_us = 0.0 # in microseconds
    waveformData = []
    widthList = []
    preambleValid = False
    headerValid = False
    framingValid = False
    encodingValid = False
    crcValid = False
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
        
    def decodeTx(self, protocol):
        if wcv.verbose:
            print "decoding transmission #" + str(self.txNum)
                        
        # scan through waveform and get widths
        self.widthList = []
        breakdownWaveform2(protocol, self.waveformData, self.widthList)
        #print len(self.waveformData)
        #print self.waveformData
        #print self.widthList

        tempUnused = []
        decodePacket(protocol, self.widthList, self.fullBasebandData, tempUnused)
        #print "Decoded Packet # " + str(self.txNum)
        #print(self.fullBasebandData)
        
        # NEED preamble check
        # NEED encoding check
        # NEED CRC check
        # print(decodedPacket)
        
        # NEED break out paylod
        # NEED break out CRC
        # NEED check CRC
        # NEED break out ID
        # NEED break out Value1
        # NEED break out Value2
        
        self.binaryString = packetToString(self.fullBasebandData, 0)
        self.hexString = packetToString(self.fullBasebandData, 1)
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
