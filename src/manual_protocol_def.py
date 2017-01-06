# This file is used to manually set up a new protocol definition. This 
# can be saved to the library or simply used and discarded.
from protocol_lib import ProtocolDefinition, getNextProtocolId
import waveConvertVars as wcv

def manualProtocolAssign():
    protocol = ProtocolDefinition(getNextProtocolId())
    protocol.deviceName = "TBD"
    protocol.deviceYear = "2001"
    protocol.deviceType = 1
    #protocol.protocolID = wcv.TEMP_PROTOCOL # this value reserved for current, unsaved protocol
    
    # ONLY EDIT THIS SECTION BELOW
    protocol.frequency = 300.0*1000000.0 ##
    protocol.modulation = wcv.MOD_OOK ##
    protocol.fskDeviation = 10*1000.0 ##
    protocol.channelWidth = 50*1000.0 ##
    protocol.transitionWidth = 5*1000.0 ## 
    protocol.threshold = 0.1 ##
    protocol.fskSquelchLeveldB = 10

    # Misc Properties
    protocol.unitWidth = 100# 90
    
    # Framing Info
    protocol.interPacketWidth = 3000 # 3000 NEED to figure out correct value, or move to preamble sync 
    protocol.interPacketSymbol = wcv.DATA_ZERO # PRO ONLY
    protocol.packetSize = 10
    protocol.preambleSync = False # PRO ONLY
    protocol.preambleType = wcv.PREAMBLE_REG
    protocol.preambleSize = [10, 999]
    protocol.preambleSymbolLow = 100 # 200
    protocol.preambleSymbolHigh = 100 # 100
    protocol.headerLevel = wcv.DATA_ZERO # PRO ONLY
    protocol.headerWidth = -1 # 960 #
    protocol.arbPreambleList = []
    
    # Payload Info 
    protocol.encodingType = wcv.PWM 
    protocol.pwmOneSymbol = [100, 200]# [90, 490] #
    protocol.pwmZeroSymbol = [200, 100]# [180, 400] #
    protocol.pwmSymbolSize = sum(protocol.pwmOneSymbol) # COMPUTED

    # CRC Info
    protocol.crcLow = 0 # COMPUTED
    protocol.crcHigh = 1 #COMPUTED
    protocol.crcDataLow = 0 #
    protocol.crcDataHigh = 1 #
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
    protocol.idAddrLow = 0
    protocol.idAddrHigh = 1
    protocol.val1AddrLow = 0
    protocol.val1AddrHigh = 1
    protocol.val2AddrLow = 0
    protocol.val2AddrHigh = 1
    protocol.val3AddrLow = 0
    protocol.val3AddrHigh = 1
    
    # provide initial values for these
    protocol.unitWidth_samp = 1
    protocol.interPacketWidth_samp = 1 
    protocol.preambleSymbolLow_samp = 1
    protocol.preambleSymbolHigh_samp = 1
    protocol.headerWidth_samp = 1
    protocol.arbPreambleList_samp = []
    protocol.pwmOneSymbol_samp = [1, 1]
    protocol.pwmZeroSymbol_samp = [1, 1]
    protocol.pwmSymbolSize_samp = 2
    

    return protocol
