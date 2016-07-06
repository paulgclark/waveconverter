# This file is used to manually set up a new protocol definition. This 
# can be saved to the library or simply used and discarded.
from protocol_lib import ProtocolDefinition, getNextProtocolId
import waveConvertVars as wcv

def manualProtocolAssign():
    protocol = ProtocolDefinition(getNextProtocolId())
    protocol.name = "Temporary Protocol"
    protocol.protocolID = wcv.TEMP_PROTOCOL # this value reserved for current, unsaved protocol
    
    # ONLY EDIT THIS SECTION BELOW
    protocol.frequency = 314.938*1000000.0 ##
    protocol.modulation = wcv.MOD_OOK ##
    protocol.fskDeviation = 10*1000.0 ##
    protocol.channelWidth = 20*1000.0 ##
    protocol.transitionWidth = 1.5*1000.0 ## 
    protocol.threshold = 0.3 ##

    # Misc Properties
    protocol.unitWidth = 90
    
    # Framing Info
    protocol.interPacketWidth = 3000 # 
    protocol.interPacketSymbol = wcv.DATA_ZERO # PRO ONLY
    protocol.packetSize = 67
    protocol.preambleSync = False # PRO ONLY
    protocol.preambleSize = [10, 999]
    protocol.preambleSymbolLow = 200
    protocol.preambleSymbolHigh = 100
    protocol.headerLevel = wcv.DATA_ZERO # PRO ONLY
    protocol.headerWidth = 960 #
    
    # Payload Info 
    protocol.encodingType = wcv.PWM 
    protocol.pwmOneSymbol = [90, 490] #
    protocol.pwmZeroSymbol = [180, 400] #
    protocol.pwmSymbolSize = sum(protocol.pwmOneSymbol) # COMPUTED

    # CRC Info
    protocol.crcLow = 65 # COMPUTED
    protocol.crcHigh = 66 #COMPUTED
    protocol.crcDataLow = 0 #
    protocol.crcDataHigh = 31 #
    protocol.crcPoly = [1, 0, 1] #
    protocol.crcInit = 0 #
    protocol.crcBitOrder = wcv.CRC_REFLECT # 
    protocol.crcReverseOut = False #
    protocol.crcFinalXor = [0, 0] #
    protocol.crcPad = wcv.CRC_NOPAD #
    protocol.crcPadCount = 8 #
    protocol.crcPadVal = 0 # PRO ONLY
    protocol.crcPadCountOptions = [0, 8, 16, 32]
    
    # Payload Data Addresses
    protocol.idAddrLow = 66
    protocol.idAddrHigh = 67
    protocol.valAddrLow = 24
    protocol.valAddrHigh = 31
    

    return protocol
