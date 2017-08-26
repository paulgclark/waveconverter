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
from iqFileArgParse import iqFileObject
from iqFileArgParse import fileNameTextToFloat

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
# get needed functions from engine modules
from waveconverterEngine import demodIQFile
from waveconverterEngine import buildTxList
from waveconverterEngine import decodeAllTx
from statEngine import computeStats
from statEngine import buildStatStrings
        

# for constructing the protocol database from scratch
from buildProtocolDatabase import buildProtocolDatabase
from waveConvertVars import waveformFileName

#####################################
# preset some command line args
protocol_number = -1 # denotes no protocol given via command line

# handling command line arguments using argparse
parser = argparse.ArgumentParser("Process input baseband waveforms OR I-Q data files and convert to output binary data")
parser.add_argument("-q", "--iq", help="input i-q data file name")
parser.add_argument("-b", "--baseband", help="digital baseband input file name")
parser.add_argument("-n", "--bb_save", help="save baseband to file", action="store_true")
parser.add_argument("-o", "--output", help="output file name")
parser.add_argument("-s", "--samp_rate", help="sample rate (Hz), minimum of 100,000Hz", type=int)
parser.add_argument("-y", "--bb_samp_rate", help="baseband sample rate (Hz), minimum of 100,000Hz", type=int)
parser.add_argument("-c", "--center_freq", help="center frequency in Hz",type=int)
parser.add_argument("-p", "--protocol", help="protocol for decode - listed by number, enter 0 for list", type=int)
parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
parser.add_argument("-x", "--hex_out", help="output data in hex format", action="store_true")
parser.add_argument("-z", "--hide_bad", help="hide bad transmissions from output", action="store_true")
parser.add_argument("-i", "--glitch_count", help="glitch filter in 10us samples", type=int)
parser.add_argument("-f", "--freq", help="frequency of target in Hz", type=int)
parser.add_argument("-u", "--squelch", help="FSK squelch level in negative dB", type=int)
parser.add_argument("-l", "--threshold", help="threshold value", type=float)
parser.add_argument("-t", "--time_between_tx", help="min time between tx in us", type=int)
parser.add_argument("-e", "--timing_error", help="max allowable timing error percentage", type=int)
parser.add_argument("-g", "--gui", help="brings up graphical interface", action="store_true")
parser.add_argument("-d", "--db", help="build new database", action="store_true")
parser.add_argument("-r", "--export_protocol", help="export specified protocol to a text file", type=int)
parser.add_argument("-j", "--import_protocol", help="import specified protocol from the specified text file")
args = parser.parse_args()

# assign args to variables
if not args.import_protocol is None: # first check if we are importing a protocol
    inFileName = args.import_protocol
    try:
        inFile = file(inFileName, "r")
        protocolString = inFile.read()
    except:
        print "Trouble reading input text file {}, exiting...".format(inFileName)
        exit(1)
    protocol_lib.createProtocolFromText(protocolString)
    print "Protocol import complete."
    exit(0)
        
    
wcv.outFileName = args.output
if not args.export_protocol is None:
    wcv.protocol_number = args.export_protocol
    try:
        wcv.protocol = protocol_lib.fetchProtocol(wcv.protocol_number)
    except:
        print "Protocol {} does not exist, please supply valid protocol ID for export".format(wcv.protocol_number)
        exit(1)
    try:
        outFile = file(wcv.outFileName, "w")
        outFile.write(wcv.protocol.fullProtocolString())
        outFile.close()
    except:
        print "Error exporting protocol to file: {} \nPlease check if supplied file is writeable".format(wcv.outFileName)
        exit(1)
    print "Protocol {} exported successfully to {}".format(wcv.protocol_number, wcv.outFileName)
    exit(0)

try:
    wcv.runWithGui = args.gui
except:
    wcv.runWithGui = False
if args.baseband: # if not argument passed, use default
    wcv.waveformFileName = args.baseband

if args.iq:
    wcv.iqFileName = args.iq
    # try to parse the file name to see if if contains the iq parameters
    wcv.inputFileObject = iqFileObject(fileName =  wcv.iqFileName)
    try:
        wcv.center_freq = wcv.inputFileObject.centerFreq
        wcv.samp_rate = wcv.inputFileObject.sampRate
    # since the parameters weren't there, they must be supplied from other args
    except:
        wcv.center_freq = -1
        wcv.samp_rate = -1

# can't run from command line without input file
elif not wcv.runWithGui:
    if (args.protocol != 0) and not args.db and len(wcv.waveformFileName) <= 0: # these commands do not require an IQ file
        print "Fatal Error: No IQ file provided"
        exit(0)

if args.samp_rate > 0:
    wcv.samp_rate = args.samp_rate * 1.0 # ensure this is a float
# can't run from command line without sample rate
elif (wcv.samp_rate < 0) and not wcv.runWithGui:
    print "Fatal Error: No sample rate given (or less than zero)"
    exit(0)

if args.center_freq > 0:
    wcv.center_freq = args.center_freq * 1.0 # ensure this is a float
# can't run from command line without sample rate
elif (wcv.center_freq < 0) and not wcv.runWithGui:
    print "Fatal Error: No center frequency given (or less than zero)"
    exit(0)

# default baseband sample rate already set in wcv, but override if cmd line value
if args.bb_samp_rate > 0:
    wcv.basebandSampleRate = args.bb_samp_rate * 1.0

if args.protocol is None:
    wcv.protocol_number = -1    
else:
    wcv.protocol_number = args.protocol

try:
    wcv.verbose = args.verbose
except:
    wcv.verbose = False
try:
    wcv.outputHex = args.hex_out
except:
    wcv.outputHex = False
try:    
    wcv.buildNewDatabase = args.db
except:
    wcv.buildNewDatabase = False
try:
    wcv.glitchFilterCount = int(args.glitch_count)
except:
    wcv.glitchFilterCount = 2
try:
    wcv.saveBasebandToFile = bool(args.bb_save)
    if not wcv.saveBasebandToFile:
        wcv.bbOutFileName = "" # signal to flowgraph not to output a bb file by not giving it a name
    else:
        wcv.bbOutFileName = wcv.iqFileName + ".bb"
except:
    wcv.saveBasebandToFile = False
    wcv.bbOutFileName = "" # signal to flowgraph not to output a bb file by not giving it a name
try:
    wcv.showAllTx = not bool(args.hide_bad)
except:
    wcv.showAllTx = True
try:
    wcv.timeBetweenTx = args.time_between_tx
except:
    wcv.timeBetweenTx = -1 # allow protocol to supply value
try:
    wcv.frequency = args.freq * 1.0
except:
    wcv.frequency = -1.0 # allow protocol to supply value
try:
    wcv.squelch = args.squelch * -1.0
except:
    wcv.squelch = -1.0 # allow protocol to supply value    
try:
    wcv.timingError = args.timing_error / 100.0
except:
    wcv.timingError = 0.2
try:
    wcv.threshold = args.threshold * 1.0
except:
    wcv.threshold = -1.0 # allow protocol to supply value

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
    print 'TIMING ERROR   :', wcv.timingError
    print 'TIME BTW TX    :', wcv.timeBetweenTx
    print 'TUNE FREQ      :', wcv.frequency
    print 'SQUELCH        :', wcv.squelch
    print 'GLITCH FILT    :', wcv.glitchFilterCount
    print 'SHOW ALL       :', wcv.showAllTx
    print 'THRESHOLD      :', wcv.threshold

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
    exit(0)
# do nothing
# fetch from database
else:
    if wcv.verbose:
        print "attempting to retrieve protocol " + str(wcv.protocol_number) + " from database"
    wcv.protocol = protocol_lib.fetchProtocol(wcv.protocol_number)
    if wcv.verbose:
        print "successfully retrieved protocol"
    if wcv.verbose:
        print wcv.protocol.fullProtocolString()


# if we were not given the GUI flag, run through in command line mode
if not wcv.runWithGui:
    
    # if we were given an I-Q file, then we need to demodulate it first to 
    # obtain the digital baseband waveform (need future modifications if 
    # multiple waveforms are contained in the same I-Q file)
    basebandData = []
    if wcv.iqFileName:
        # decide whether to use protocol values or command line overrides
        if wcv.frequency < 0:
            wcv.frequency = wcv.protocol.frequency
        if wcv.threshold < 0:
            wcv.threshold = wcv.protocol.threshold
        if wcv.squelch == -1.0:
            wcv.squelch = wcv.protocol.fskSquelchLeveldB
            
        # need to get baseband sample rate from protocol
        wcv.basebandSampleRate = wcv.protocol.bb_samp_rate
        
        # since we have an I-Q input file, we will generate the baseband waveform
        basebandData = demodIQFile(verbose = wcv.verbose,
                                   modulationType = wcv.protocol.modulation,
                                   iqSampleRate = wcv.samp_rate,
                                   basebandSampleRate = wcv.protocol.bb_samp_rate,
                                   centerFreq = wcv.center_freq,
                                   frequency = wcv.frequency,
                                   channelWidth = wcv.protocol.channelWidth,
                                   transitionWidth = wcv.protocol.transitionWidth,
                                   threshold = wcv.threshold,
                                   fskDeviation = wcv.protocol.fskDeviation,
                                   fskSquelch = wcv.squelch,
                                   frequencyHopList = wcv.protocol.frequencyHopList,
                                   iqFileName = wcv.iqFileName,
                                   waveformFileName = wcv.bbOutFileName)

    # if we didn't have an iq file, then we'll use the supplied baseband file to get the BB data
    elif len(wcv.waveformFileName) > 0:
        try:
            print "Opening baseband file"
            from breakWave import basebandFileToList
            basebandData = basebandFileToList(wcv.waveformFileName)
        except:
            print "Error opening baseband file. Exiting..."
            exit(1)
        
    # decide whether to use protocol values or command line overrides
    if wcv.timeBetweenTx < 0:
        wcv.timeBetweenTx = wcv.protocol.interPacketWidth
    timeBetweenTx_samp = wcv.timeBetweenTx * wcv.basebandSampleRate / 1000000
    
    # split transmissions
    txList = buildTxList(basebandData = basebandData,
                         basebandSampleRate =  wcv.basebandSampleRate,
                         interTxTiming = timeBetweenTx_samp,
                         glitchFilterCount = wcv.glitchFilterCount,
                         interTxLevel = wcv.protocol.interPacketSymbol,
                         verbose = wcv.verbose)

    if wcv.verbose:       
        print "Number of transmissions broken down: " + str(len(txList))
        for tx in txList:
            print "tx waveform list length: " + str(len(tx.waveformData)) 

    # decode
    (txList, decodeOutputString) = decodeAllTx(protocol = wcv.protocol, 
                                               txList = txList,
                                               outputHex = wcv.outputHex,
                                               timingError = wcv.timingError,
                                               glitchFilterCount = wcv.glitchFilterCount,
                                               verbose = wcv.verbose,
                                               showAllTx = wcv.showAllTx)
        
    # compute stats
    (bitProbList, idListMaster, valListMaster, payloadLenList) = computeStats(txList = txList,
                                                                              protocol = wcv.protocol, 
                                                                              showAllTx = wcv.showAllTx)
    # compute stat string
    (bitProbString, idStatString, valuesString) = buildStatStrings(bitProbList, 
                                                                   idListMaster, 
                                                                   valListMaster, 
                                                                   payloadLenList, 
                                                                   wcv.outputHex)
    
    # output strings to stdio
    print "Raw Transmission Data:"
    print decodeOutputString
    print "End Raw Transmission Data"
    print bitProbString
    print idStatString
    print valuesString
    

else: # start up the GUI
    if __name__ == "__main__":
        main = TopWindow(wcv.protocol)
        Gtk.main()
  
if wcv.verbose:
    print("Exiting")
exit(0)

