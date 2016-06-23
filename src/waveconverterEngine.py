#############################################################################################3
########### copyright 2015 Factoria Labs
# This file contains  
#

# waveconverter decoding modules
from breakWave import breakdownWaveform
from widthToBits import separatePackets
from widthToBits import decodePacket
from widthToBits import printPacket
from config import *
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
        if (breakdownWaveform(protocol, waveformFile, masterWidthList) == END_OF_FILE):

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
            i=0
            for packet in packetList:
                outFile.write("Packet #" + str(i+1) + ": ")
                printPacket(outFile, packet, outputHex)
                i+=1
                
                # after we finish, close out files and exit
    outFile.close()
    waveformFile.close()
