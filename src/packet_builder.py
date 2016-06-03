#!/usr/bin/env python
# This file contains the top level code for generating packet files.
# These files are then used by a gnuradio flowgraph to modulate and
# then transmit the RF waveform.
#
# The file format is simply byte data equal to zero or one at the 
# data rate intended. This data rate is contained in the filename itself
# for ease of use in gnuradio.
#
import sys
import io
import os
from subprocess import call
from statEngine import crcComputed
import random

from config import *

#####################################
def readPacketsFromFile(packetFile, packetList):
    # read all the lines into a list
    lines = packetFile.readlines()
    intList = []
   
    # strip out leading text and whitespace
    for line in lines:
        line = line.split(":")[1] # take only what's after the colon
        line = ''.join(line.split()) # remove whitespace

        # convert characters to integers
        intList = []
        for ch in line:
           intList.append(int(ch))
        # add list of ints to packet list
        packetList.append(intList[:])

    return(0)


#####################################
def populateLevel(outFile, level, sampleCount):

    for i in range(sampleCount):
        if level == 1:
            outFile.write(b'\x01')
        else:
            outFile.write(b'\x00')

#####################################
def printPacketsToFile(outFile, packetList):
    
    for packet in packetList:
        populateLevel(outFile, INTERPACKET_SYMBOL, 100*INTERPACKET_WIDTH)

        for i in range(3): # send each packet 3 times
            # first add the interpacket period;
            populateLevel(outFile, INTERPACKET_SYMBOL, 10*INTERPACKET_WIDTH)

            # add preamble
            if (len(PREAMBLE_SIZE) == 1) or i==0: # for the first packet, send the long preamble
                for preambleCount in range(PREAMBLE_SIZE[0]):
                    populateLevel(outFile, 0, PREAMBLE_SYMBOL_LOW)
                    populateLevel(outFile, 1, PREAMBLE_SYMBOL_HIGH)
            else: # for all others, send the short one
                    for preambleCount in range(PREAMBLE_SIZE[1]):
                        populateLevel(outFile, 0, PREAMBLE_SYMBOL_LOW)
                        populateLevel(outFile, 1, PREAMBLE_SYMBOL_HIGH)

            # add header
            populateLevel(outFile, HEADER_LEVEL, HEADER_WIDTH-UNIT_WIDTH)

            # encode the packet data
            manchesterPacket = []
            if ENCODING == STD_MANCHESTER:
                for bit in packet:
                    if bit == 1: # encode rising edge (low->high)
                        manchesterPacket.append(0)
                        manchesterPacket.append(1)
                    else:        # encode falling edge (high->low)
                        manchesterPacket.append(1)
                        manchesterPacket.append(0)

                # output the encoded data to the file
                for bit in manchesterPacket:
                    populateLevel(outFile, bit, UNIT_WIDTH)

            # handle PWM encoding
            elif ENCODING == PWM:
                for bit in packet:
                    if bit == 1: # append PWM=1 symbol
                        populateLevel(outFile, 1, PWM_ONE_SYMBOL[0])
                        populateLevel(outFile, 0, PWM_ONE_SYMBOL[1])
                    else:
                        populateLevel(outFile, 1, PWM_ZERO_SYMBOL[0])
                        populateLevel(outFile, 0, PWM_ZERO_SYMBOL[1])
    
    # finish back end of packets with another gap        
    populateLevel(outFile, INTERPACKET_SYMBOL, 100*INTERPACKET_WIDTH)

    return(0)


#packetFileName = "digital_sig_lib/out_full.txt"
#outFileName = "./stat.txt"
if len(sys.argv) < 3:
    print "    Usage: python packet_builder.py <input file> <output file>"
    print "           <optional> -s -b"
    print "           s: single shot mode, transmit packets then exit"
    print "           b: brute force mode, gen&tx new packets until Ctl-C"
    exit(0)
else:
    packetFileName = sys.argv[1]
    outFileName = sys.argv[2]
    if sys.argv > 3:
        option = sys.argv[3]


##################################### main
#sampleRate = 200000 # this is the target sample rate for gnuradio
#baudRate = 1333 # not used presently; taking all timing from config.py

# grcc creates the block with bad permissions; this fixes it
call(["touch", "top_block.py"])
call(["chmod", "+x", "top_block.py"])

# for single-shot mode, we need an input packet file
packetList = [] # empty list of packets
if option == "-s":
    # open input file for read access in binary mode
    with io.open(packetFileName, 'rb') as packetFile: 
        readPacketsFromFile(packetFile, packetList)

packetCount = 0
while True: # loop until user terminates
    # open output file for binary write access; do this each iteration
    outFile = open(outFileName, 'wb')

    try:
        if option == "-b": # brute force
            packetList = []
            packet = []

            # bit 0 is always zero
            packet.append(0)

            # generate random, non-repeating packet data 
            # (this is hardcoded for the Volvo)
            # bits 1-32 are random
            #randomInteger = randint(0, 0xffffffff)
            randomInteger = int(random.getrandbits(32))
            for i in range(32):
                packet.append(randomInteger % 2)
                randomInteger = randomInteger/2

            # bits 33-64 is a fixed ID
            iD = [1,0,0,1, 1,1,1,0,  1,1,0,1, 0,1,1,0,\
                  0,1,1,1, 0,1,1,1,  1,1,1,1, 1,1,1,1]
            packet = packet + iD

            # bit 65 is always 1
            packet.append(1)

            # bits 66 and 67 are the CRC
            crcVal = crcComputed(packet[1:32], CRC_POLY, CRC_BIT_ORDER,\
                                 CRC_INIT, CRC_REVERSE_OUT, CRC_FINAL_XOR,\
                                 CRC_PAD, CRC_PAD_COUNT, CRC_PAD_VAL)
            packet = packet + crcVal

            # bits 68 and 69 are random
            packet.append(random.randint(0,1))
            packet.append(random.randint(0,1))

            # bit 70 is zero; manchester artifact
            packet.append(0)

            # packet list of one item
            print packet
            packetList.append(packet)
            print "# of packets in list: " + str(len(packetList))


        # now output the packets to a file for handoff to gnuradio 
        # NEED: replace this with a named pipe to save disk access
        printPacketsToFile(outFile, packetList)

        # call gnuradio to transmit the file
        call(["grcc", "-d", ".", "--execute", "ook_tx_cmd_line.grc"])

        if option == "-s": # single-shot mode, just break out of loop
            print "Packets From Input File: Transmission Complete"
            break
        else:
            packetCount += 1
            # print "PacketCount: " + str(PacketCount)

    except KeyboardInterrupt:
        print "User Interrupt Detected. Exiting."
        print "  transmitted " + str(packetCount) + " packets"
        break


outFile.close()
packetFile.close()
exit(0)

