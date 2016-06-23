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
import sys # NEED: remove?
import io # NEED: remove?
import os # NEED: remove?
import argparse

# waveconverter decoding modules: NEED: remove when engine code separated
from breakWave import breakdownWaveform
from widthToBits import separatePackets
from widthToBits import decodePacket
from widthToBits import printPacket
from config import * # NEED: what do we need from the *; delete as config no longer used?

# RF libraries and modules
from demod_rf import * # NEED: remove
from gnuradio import gr # NEED: remove

# protocol handling
from protocol_lib import * # NEED: no *
from manual_protocol_def import * # NEED: no * 
from protocol_lib import * # NEED: no *

# waveconverter-specific GUI
from waveconverter_gui import * # NEED: no *
from waveconverterEngine import decodeBaseband

# global constants
import waveConvertVars as wcv


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
wcv.iqFileName = args.iq
if not args.baseband == None: # if not argument passed, used default
    wcv.waveformFileName = args.baseband
wcv.outFileName = args.output
wcv.samp_rate = args.samp_rate
wcv.center_freq = args.center_freq
wcv.verbose = args.verbose
wcv.outputHex = args.hex_out
wcv.protocol_number = args.protocol
wcv.runWithGui = args.gui

if wcv.verbose:      
    print 'ARGV           :', sys.argv[1:]  
    print 'VERBOSE        :', wcv.verbose
    print 'IQ FILE        :', wcv.iqFileName
    print 'BASEBAND FILE  :', wcv.waveformFileName
    print 'OUTPUT         :', wcv.outFileName
    print 'PROTOCOL       :', wcv.protocol_number
    print 'SAMPLE RATE    :', wcv.samp_rate
    print 'CENTER_FREQ    :', wcv.center_freq
    print 'OUTPUT_HEX     :', wcv.outputHex
    print 'RUN WITH GUI   :', wcv.runWithGui

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
if wcv.protocol_number == -1:
    wcv.protocol = manualProtocolAssign()
    wcv.protocol.saveProtocol()
# if the number passed is zero, then list the contents of the database and exit
elif wcv.protocol_number == 0:
    print "Printing stored protocol list"
    listProtocols()
# do nothing
# fetch from database
else:
    print "attempting to retrieve protocol " + \
        str(wcv.protocol_number) + " from database"
    if wcv.verbose:
        wcv.protocol = fetchProtocol(wcv.protocol_number)
        wcv.protocol.printProtocolFull()

#exit()

# if we were not given the GUI flag, run through in command line mode
if not wcv.runWithGui:
    
    # NEED: pull checking code into flowgraph method and simplify this block

    # if we were given an I-Q file, then we need to demodulate it first to 
    # obtain the digital baseband waveform (need future modifications if 
    # multiple waveforms are contained in the same I-Q file)
    if wcv.iqFileName:
        #if __name__ == '__main__':
        # since we have an I-Q input file, we will generate the baseband 
        # waveform and temporarily place it in the following file
        try:
            if wcv.verbose:
                print "Running Demodulation Flowgraph"
                print wcv.iqFileName
                print wcv.waveformFileName
            flowgraphObject = ook_flowgraph(wcv.samp_rate, # samp_rate_in 
                                            wcv.basebandSampleRate, # rate_out 
                                            wcv.center_freq, # center_freq
                                            314938000, # tune_freq
                                            20000, # channel_width
                                            1000,  # transition_width
                                            0.3,   # threshold
                                            wcv.iqFileName, # iq_filename 
                                            wcv.waveformFileName) # temp file
            flowgraphObject.run()
            if wcv.verbose:
                print "flowgraph completed"
        except [[KeyboardInterrupt]]:
            pass

    # insert call to waveConverterEngine here and remove existing code
    # packetList = decodeBaseband(wcv.waveformFileName,
    #                             wcv.basebandSampRate,
    #                             wcv.outFileName,
    #                             wcv.protocol,
    #                             wcv.outputHex)
    
    decodeBaseband(wcv.waveformFileName, wcv.basebandSampleRate, wcv.outFileName,
                   wcv.protocol, wcv.outputHex)

    """
    # begin decoding baseband waveform
    if wcv.verbose:
        print "begining decode process"
    masterWidthList = [] # contains the widths for the entire file
    packetWidthsList = [] # list of packet width lists
    packetList = [] # list of decoded packets
    rawPacketList = [] # list of pre-decoded packets

    # open input file for read access in binary mode
    with io.open(wcv.waveformFileName, 'rb') as waveformFile: 

        # open output file for write access
        outFile = open(wcv.outFileName, 'w')

        # scan through waveform and get widths
        print waveformFile
        if (breakdownWaveform(wcv.protocol, waveformFile, masterWidthList) == END_OF_FILE):

            print masterWidthList
            
            # separate master list into list of packets
            separatePackets(wcv.protocol, masterWidthList, packetWidthsList)

            # decode each packet and add it to the list
            i=0
            for packetWidths in packetWidthsList:
                # print("Packet #" + str(i+1) + ": ") 
                # print(packetWidths)
                decodedPacket = [] # move out of loop to main vars?
                rawPacket = [] # move out of loop to main vars?
                decodePacket(wcv.protocol, packetWidths, decodedPacket, rawPacket)
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
                """ 
    
else: # start up the GUI
    if __name__ == "__main__":
        main = TopWindow(protocol_number, protocol)
        Gtk.main()
  

print("Exiting")
exit(0)

