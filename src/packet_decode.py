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
import argparse

# global constants
import waveConvertVars as wcv

# RF libraries and modules
from demod_rf import ook_flowgraph
from demod_rf import fsk_flowgraph

# protocol handling
import protocol_lib
from manual_protocol_def import manualProtocolAssign 

# waveconverter-specific GUI
from waveconverter_gui import * # NEED: no *
from waveconverterEngine import decodeBaseband

# for constructing the protocol database from scratch
from buildProtocolDatabase import buildProtocolDatabase

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
parser.add_argument("-d", "--db", help="build new database",
                    action="store_true")
args = parser.parse_args()

# assign args to variables
wcv.iqFileName = args.iq
if not args.baseband == None: # if not argument passed, used default
    wcv.waveformFileName = args.baseband
wcv.outFileName = args.output
try:
    wcv.samp_rate = args.samp_rate * 1.0 # ensure this is a float
except:
    wcv.samp_rate = 0.0
try:
    wcv.center_freq = args.center_freq * 1.0 # ensure this is a float
except:
    wcv.center_freq = 0.0
wcv.verbose = args.verbose
wcv.outputHex = args.hex_out
wcv.protocol_number = args.protocol
wcv.runWithGui = args.gui
wcv.buildNewDatabase = args.db
#wcv.argcHelp = args.help

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

# if we were passed the "build database" flag, then just do that and exit
if wcv.buildNewDatabase:
    print "Building new protocol database from manual entries..."
    buildProtocolDatabase()
    print "...database build complete."
    exit(0)

# based on command line, choose the protocol
# if the protocol number was not specified in the command line use
# manual assignment from manual_protocol_def.py
if wcv.protocol_number == -1:
    wcv.protocol = manualProtocolAssign()
    #wcv.protocol.saveProtocol()
# if the number passed is zero, then list the contents of the database and exit
elif wcv.protocol_number == 0:
    print "Printing stored protocol list"
    protocol_lib.listProtocols()
# do nothing
# fetch from database
else:
    print "attempting to retrieve protocol " + \
        str(wcv.protocol_number) + " from database"
    if wcv.verbose:
        wcv.protocol = protocol_lib.fetchProtocol(wcv.protocol_number)
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
            if wcv.protocol.modulation == wcv.MOD_OOK:
                flowgraphObject = ook_flowgraph(wcv.samp_rate, # samp_rate_in 
                                                wcv.basebandSampleRate, # rate_out 
                                                wcv.center_freq,
                                                wcv.protocol.frequency, # tune_freq
                                                wcv.protocol.channelWidth,
                                                wcv.protocol.transitionWidth,
                                                wcv.protocol.threshold,
                                                wcv.iqFileName, 
                                                wcv.waveformFileName) # temp file
            elif wcv.protocol.modulation == wcv.MOD_FSK:
                flowgraphObject = fsk_flowgraph(wcv.samp_rate, # samp_rate_in 
                                                wcv.basebandSampleRate, # rate_out 
                                                wcv.center_freq,
                                                wcv.protocol.frequency, # tune_freq
                                                wcv.protocol.channelWidth,
                                                wcv.protocol.transitionWidth,
                                                wcv.protocol.threshold,
                                                wcv.protocol.fskDeviation,
                                                wcv.iqFileName, 
                                                wcv.waveformFileName) # temp file
            else:
                print "Invalid modulation type selected" # NEED to put in status bar or pop-up
                exit(1)
            flowgraphObject.run()
            if wcv.verbose:
                print "flowgraph completed"
        except [[KeyboardInterrupt]]:
            pass

    # insert call to waveConverterEngine here and remove existing code
    wcv.payloadList = decodeBaseband(wcv.waveformFileName,
                                     wcv.basebandSampleRate,
                                     wcv.outFileName,
                                     wcv.protocol,
                                     wcv.outputHex)
    
    # add packet to string function calls with outFile write and pull outFileName from fn call above
    

else: # start up the GUI
    if __name__ == "__main__":
        main = TopWindow(wcv.protocol)
        Gtk.main()
  

print("Exiting")
exit(0)

