# This file is used to manually set up a new protocol definition. This 
# can be saved to the library or simply used and discarded.
from protocol_lib import ProtocolDefinition
from waveConvertVars import *

def manualProtocolAssign():
    protocol = ProtocolDefinition()
    protocol.name = "Temporary Protocol"
    protocol.protocolID = TEMP_PROTOCOL # this value reserved for current, unsaved protocol
    
    # ONLY EDIT THIS SECTION BELOW
    protocol.frequency = 315000000
    protocol.modulation = MOD_OOK
    protocol.fskDeviation = 0
    protocol.interPacketWidth = 1000
    protocol.interPacketSymbol = DATA_ZERO
    protocol.unitWidth = 90
    protocol.unitError = 0.2
    protocol.packetSize = 67
    protocol.preambleSync = False
    protocol.preambleSymbolHigh = 100
    protocol.preambleSymbolLow = 200
    protocol.preambleSize = [10]
    protocol.headerLevel = DATA_ZERO
    protocol.headerWidth = 960
    protocol.encodingType = PWM
    protocol.pwmOneSymbol = [90, 490]
    protocol.pwmZeroSymbol = [180, 400]
    protocol.pwmSymbolSize = sum(protocol.pwmOneSymbol)
    protocol.glitchFilterCount = 4
    protocol.idAddrLow = 66
    protocol.idAddrHigh = 67
    protocol.valAddrLow = 24
    protocol.valAddrHigh = 31
    protocol.crcLow = 65
    protocol.crcHigh = 66
    protocol.crcDataLow = 0
    protocol.crcDataHigh = 31
    protocol.crcPoly = [1, 0, 1]
    protocol.crcInit = 0
    protocol.crcBitOrder = CRC_REFLECT
    protocol.crcReverseOut = False
    protocol.crcFinalXor = [0, 0]
    protocol.crcPad = CRC_NOPAD
    protocol.crcPadCount = 8
    protocol.crcPadVal =0
    protocol.crcPadCountOptions = [0, 8, 16, 32]

    return protocol
