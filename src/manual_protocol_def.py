# This file is used to manually set up a new protocol definition. This 
# can be saved to the library or simply used and discarded.
from protocol_lib import ProtocolDefinition, getNextProtocolId, getDeviceTypeStringKey
import waveConvertVars as wcv

def manualProtocolAssign():
    protocol = ProtocolDefinition(getNextProtocolId())

    # ONLY EDIT THIS SECTION BELOW
    protocol.deviceMake = "New Device Make"
    protocol.deviceModel = "New Device Model"
    protocol.deviceYear = "2000"
    protocol.deviceType = getDeviceTypeStringKey("Key Fob")
    
    protocol.frequency = 100.0*1000000.0 
    protocol.modulation = wcv.MOD_OOK 
    protocol.fskDeviation = 10*1000.0
    protocol.channelWidth = 20*1000.0
    protocol.transitionWidth = 1.0*1000.0 
    protocol.threshold = 0.5
    protocol.fskSquelchLeveldB = 0
    protocol.glitchFilterCount = 2

    # Misc Properties
    protocol.unitWidth = 100
    
    # Framing Info
    protocol.interPacketWidth = 3000 
    protocol.interPacketSymbol = wcv.DATA_ZERO # PRO ONLY
    protocol.packetSize = 24
    protocol.preambleType = wcv.PREAMBLE_REG
    protocol.preambleSync = False # PRO ONLY
    protocol.preambleSize = [10, 999]
    protocol.preambleSymbolLow = 100
    protocol.preambleSymbolHigh = 100
    protocol.headerLevel = wcv.DATA_ZERO # PRO ONLY
    protocol.headerWidth = 500
    protocol.arbPreambleList = []
    protocol.preamblePulseCount = 0

    # Payload Info 
    protocol.encodingType = wcv.PWM 
    protocol.pwmSymbolOrder01 = False
    protocol.pwmOneSymbol = [100, 200]
    protocol.pwmZeroSymbol = [200, 100]
    protocol.pwmSymbolSize = sum(protocol.pwmOneSymbol) # COMPUTED

    # CRC Info
    protocol.crcLow = 0
    protocol.crcHigh = 0
    protocol.crcDataLow = 0
    protocol.crcDataHigh = 0
    protocol.crcPoly = [] #
    protocol.crcInit = 0
    protocol.crcBitOrder = wcv.CRC_REFLECT 
    protocol.crcReverseOut = False
    protocol.crcFinalXor = [0, 0]
    protocol.crcPad = wcv.CRC_NOPAD
    protocol.crcPadCount = 8 
    protocol.crcPadVal = 0 # PRO ONLY
    protocol.crcPadCountOptions = [0, 8, 16, 32]
    
    # Payload Data Addresses
    protocol.idAddrLow = 0
    protocol.idAddrHigh = 0
    protocol.val1AddrLow = 0
    protocol.val1AddrHigh = 0
    protocol.val2AddrLow = 0
    protocol.val2AddrHigh = 0
    protocol.val3AddrLow = 0
    protocol.val3AddrHigh = 0
    
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
