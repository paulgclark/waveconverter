#!/usr/bin/env python
# This file contains the top level code for extracting binary packet
# data from an input digital waveform. It opens the file, does a first
# pass over the waveform to extract the timing between all rising and
# falling edges, divides the waveform into packets, validates the legality
# of the packet and finally extracts the data from each packet.
#
# This file assumes that each bit of the bitstream is contained in a
# single byte, each with a value of either 0x00 or 0x01.
#
# standard Python libraries
import sys
import io
import os
import argparse

# global constants
from waveConvertVars import *

# waveconverter decoding modules
from breakWave import breakdownWaveform
from widthToBits import separatePackets
from widthToBits import decodePacket
from widthToBits import printPacket
from config import *

# RF libraries and modules
from demod_rf import *
from gnuradio import gr

# protocol handling
from protocol_lib import *
from manual_protocol_def import *
from protocol_lib import *

# waveconverter-specific GUI
from waveconverter_gui import *
#from gi.repository import Gtk # note gtk+3 uses Gtk, not gtk

#####################################
# preset some command line args
protocol_number = -1 # denotes no protocol given via command line

# handling command line arguments using argparse
parser = argparse.ArgumentParser("Process input baseband waveforms OR I-Q data files and convert to output binary data")
parser.add_argument("-q", "--iq", help="input i-q data file name")
parser.add_argument("-b", "--baseband", help="input digital baseband file name")
parser.add_argument("-o", "--output", help="output file name")
parser.add_argument("-s", "--samp_rate", help="sample rate", type=int)
parser.add_argument("-c", "--center_freq", help="center frequency (Hz)",
                    type=int)
parser.add_argument("-p", "--protocol", help="protocol for decode (listed by number, enter 0 for list)", 
                    type=int)
parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
parser.add_argument("-x", "--hex_out", help="output data in hex format",
                    action="store_true")
parser.add_argument("-g", "--gui", help="brings up graphical interface",
                    action="store_true")
args = parser.parse_args()

# assign args to variables
iqFileName = args.iq
waveformFileName = args.baseband
outFileName = args.output
samp_rate = args.samp_rate
center_freq = args.center_freq
verbose = args.verbose
outputHex = args.hex_out
protocol_number = args.protocol
runWithGui = args.gui

if verbose:      
    print 'ARGV           :', sys.argv[1:]  
    print 'VERBOSE        :', verbose
    print 'IQ FILE        :', iqFileName
    print 'BASEBAND FILE  :', waveformFileName
    print 'OUTPUT         :', outFileName
    print 'PROTOCOL       :', protocol_number
    print 'SAMPLE RATE    :', samp_rate
    print 'CENTER_FREQ    :', center_freq
    print 'OUTPUT_HEX     :', outputHex
    print 'RUN WITH GUI   :', runWithGui

"""
## temp code for test
tempProtocol = ProtocolDefinition(11)
tempProtocol.name = "temp name"
tempProtocol.frequency = 94.7
tempProtocol2 = ProtocolDefinition(13)
tempProtocol2.name = "temp name 2"
tempProtocol2.crcPoly = 105.2
tempProtocol.printProtocolMinimal()

# upload these to the database
protocolSession.add(tempProtocol)
protocolSession.add(tempProtocol2)
protocolSession.commit()
## temp code for test
"""

# based on command line, choose the protocol
# if the protocol number was not specified in the command line use
# manual assignment from manual_protocol_def.py
if protocol_number == -1:
    protocol = manualProtocolAssign()
    protocol.saveProtocol()
# if the number passed is zero, then list the contents of the database and exit
elif protocol_number == 0:
    print "Printing stored protocol list"
    listProtocols()
# fetch from database
else:
    print "attempting to retrieve protocol " + str(protocol_number) + " from database"
    protocol = fetchProtocol(protocol_number)
    protocol.printProtocolFull()

#exit()

# if we were not given the GUI flag, run through in command line mode
if not runWithGui:

    # if we were given an I-Q file, then we need to demodulate it first to obtain the
    # digital baseband waveform (need future modifications if multiple waveforms are
    # contained in the same I-Q file)
    if iqFileName:
        #if __name__ == '__main__':
        # since we have an I-Q input file, we will generate the baseband waveform and
        # temporarily place it in the following file
        waveformFileName = "../output_files/temp.dig"
        basebandSampleRate = 400000 # will use a sample rate of 400kHz for the extracted baseband 
        try:
            if verbose:
                print "Running Demodulation Flowgraph"
                flowgraphObject = ook_flowgraph(samp_rate, # samp_rate_in 
                                                basebandSampleRate, # samp_rate_out 
                                                center_freq, # center_freq
                                                314938000, # tune_freq
                                                40000, # channel_width
                                                4000,  # transition_width
                                                0.3,   # threshold
                                                iqFileName, # iq_filename 
                                                waveformFileName) # temp dig_out_filename
                flowgraphObject.run()
        except [[KeyboardInterrupt]]:
            pass

    # begin decoding baseband waveform
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
            i=0
            for packet in packetList:
                outFile.write("Packet #" + str(i+1) + ": ") 
                printPacket(outFile, packet, outputHex)
                i+=1
    
else: # start up the GUI
    if __name__ == "__main__":
        main = TopWindow(protocol_number, protocol)
        Gtk.main()
  
# after we finish, close out files and exit
outFile.close()
waveformFile.close()
print("Exiting")
exit(0)

