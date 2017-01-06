# This file is used to manually set up the database containing the protocol library.
# This may need to be replaced eventually by a scheme that takes a gold database and 
# modifies it as needed. For the early stages of development, this is easier.
from protocol_lib import ProtocolDefinition, getNextProtocolId
import waveConvertVars as wcv

def getDeviceTypeStringKey(deviceString):
    for keyVal in wcv.devTypeStrings:
        if wcv.devTypeStrings[keyVal] == deviceString:
            return keyVal
    
def buildProtocolDatabase():
    protocol = ProtocolDefinition(getNextProtocolId())
    
    # ONLY EDIT THIS SECTION BELOW
    protocol.deviceMake = "Chevrolet"
    protocol.deviceModel = "Colorado"
    protocol.deviceYear = "2011"
    protocol.deviceType = getDeviceTypeStringKey("Key Fob")
    #protocol.protocolID = wcv.TEMP_PROTOCOL # this value reserved for current, unsaved protocol
    
    # ONLY EDIT THIS SECTION BELOW
    protocol.frequency = 314.938*1000000.0 ##
    protocol.modulation = wcv.MOD_OOK ##
    protocol.fskDeviation = 10*1000.0 ##
    protocol.channelWidth = 20*1000.0 ##
    protocol.transitionWidth = 1.5*1000.0 ## 
    protocol.threshold = 0.3 ##
    protocol.fskSquelchLeveldB = 0
    protocol.glitchFilterCount = 2

    # Misc Properties
    protocol.unitWidth = 225 # 90
    
    # Framing Info
    protocol.interPacketWidth = 4000 
    protocol.interPacketSymbol = wcv.DATA_ZERO # PRO ONLY
    protocol.packetSize = 67
    protocol.preambleType = wcv.PREAMBLE_REG
    protocol.preambleSync = False # PRO ONLY
    protocol.preambleSize = [10, 999]
    protocol.preambleSymbolLow = 500 # 200
    protocol.preambleSymbolHigh = 200 # 100
    protocol.headerLevel = wcv.DATA_ZERO # PRO ONLY
    protocol.headerWidth = 2400 # 960 #
    protocol.arbPreambleList = []
    protocol.preamblePulseCount = 0
    
    # Payload Info 
    protocol.encodingType = wcv.PWM
    protocol.pwmSymbolOrder01 = False
    protocol.pwmZeroSymbol = [1225, 225]# [180, 400] #
    protocol.pwmOneSymbol = [1000, 450]# [90, 490] #
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
    protocol.idAddrLow = 32
    protocol.idAddrHigh = 63
    protocol.val1AddrLow = 24
    protocol.val1AddrHigh = 31
    protocol.val2AddrLow = 32
    protocol.val2AddrHigh = 33
    protocol.val3AddrLow = 34
    protocol.val3AddrHigh = 35
    
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
    
    protocol.saveProtocol() # add to database
    
########## second element in database
    protocol = ProtocolDefinition(getNextProtocolId())
    protocol.deviceMake = "Volvo"
    protocol.deviceModel = "S60"
    protocol.deviceYear = "2003"
    protocol.deviceType = getDeviceTypeStringKey("Key Fob")
    #protocol.protocolID = wcv.TEMP_PROTOCOL # this value reserved for current, unsaved protocol
    
    # ONLY EDIT THIS SECTION BELOW
    protocol.frequency = 314.938*1000000.0 ## TBD
    protocol.modulation = wcv.MOD_OOK ##
    protocol.fskDeviation = 10*1000.0 ##
    protocol.channelWidth = 20*1000.0 ##
    protocol.transitionWidth = 1.5*1000.0 ## 
    protocol.threshold = 0.3 ##
    protocol.fskSquelchLeveldB = 0
    protocol.glitchFilterCount = 2

    # Misc Properties
    protocol.unitWidth = 400
    
    # Framing Info
    protocol.interPacketWidth = 2500 # NEED to figure out correct value, or move to preamble sync 
    protocol.interPacketSymbol = wcv.DATA_ZERO # PRO ONLY
    protocol.packetSize = 71
    protocol.preambleType = wcv.PREAMBLE_REG
    protocol.preambleSync = False # PRO ONLY
    protocol.preambleSize = [16, 70]
    protocol.preambleSymbolLow = protocol.unitWidth
    protocol.preambleSymbolHigh = protocol.unitWidth
    protocol.headerLevel = wcv.DATA_ZERO # PRO ONLY
    protocol.headerWidth = 4*protocol.unitWidth
    protocol.arbPreambleList = []
    protocol.preamblePulseCount = 0
    
    # Payload Info 
    protocol.encodingType = wcv.STD_MANCHESTER
    protocol.pwmSymbolOrder01 = True
    protocol.pwmOneSymbol = [1, 1]
    protocol.pwmZeroSymbol = [1, 1]
    protocol.pwmSymbolSize = sum(protocol.pwmOneSymbol) # COMPUTED

    # CRC Info
    protocol.crcLow = 66 # COMPUTED
    protocol.crcHigh = 67 #COMPUTED
    protocol.crcDataLow = 1 #
    protocol.crcDataHigh = 32 #
    protocol.crcPoly = [1, 1, 1] #
    protocol.crcInit = 0 #
    protocol.crcBitOrder = wcv.CRC_NORM # 
    protocol.crcReverseOut = False #
    protocol.crcFinalXor = [0, 1] #
    protocol.crcPad = wcv.CRC_NOPAD #
    protocol.crcPadCount = 8 #
    protocol.crcPadVal = 0 # PRO ONLY
    protocol.crcPadCountOptions = [0, 8, 16, 32]
    
    # Payload Data Addresses
    protocol.idAddrLow = 66
    protocol.idAddrHigh = 67
    protocol.val1AddrLow = 24
    protocol.val1AddrHigh = 31
    protocol.val2AddrLow = 32
    protocol.val2AddrHigh = 33
    protocol.val3AddrLow = 34
    protocol.val3AddrHigh = 35    
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

    protocol.saveProtocol() # add to database
    
########## third element in database
    protocol = ProtocolDefinition(getNextProtocolId())
    protocol.deviceMake = "Leviton"
    protocol.deviceModel = "KUJCE9103"
    protocol.deviceYear = "2010"
    protocol.deviceType = getDeviceTypeStringKey("Fan Controller")
    #protocol.protocolID = wcv.TEMP_PROTOCOL # this value reserved for current, unsaved protocol
    
    # ONLY EDIT THIS SECTION BELOW
    protocol.frequency = 304.48*1000000.0 ## TBD
    protocol.modulation = wcv.MOD_OOK ##
    protocol.fskDeviation = 10*1000.0 ##
    protocol.channelWidth = 130*1000.0 ##
    protocol.transitionWidth = 5*1000.0 ## 
    protocol.threshold = 0.05 ##
    protocol.fskSquelchLeveldB = 0
    protocol.glitchFilterCount = 2

    # Misc Properties
    protocol.unitWidth = 400
    
    # Framing Info
    protocol.interPacketWidth = 3000 # NEED to figure out correct value, or move to preamble sync 
    protocol.interPacketSymbol = wcv.DATA_ZERO # PRO ONLY
    protocol.packetSize = 12
    protocol.preambleType = wcv.PREAMBLE_REG
    protocol.preambleSync = False # PRO ONLY
    protocol.preambleSize = [1, 999]
    protocol.preambleSymbolLow = 400
    protocol.preambleSymbolHigh = 400
    protocol.headerLevel = wcv.DATA_ZERO # PRO ONLY
    protocol.headerWidth = -1
    protocol.arbPreambleList = []
    protocol.preamblePulseCount = 0
    
    # Payload Info 
    protocol.encodingType = wcv.PWM
    protocol.pwmSymbolOrder01 = True
    protocol.pwmZeroSymbol = [804, 396]
    protocol.pwmOneSymbol = [396, 804]
    protocol.pwmSymbolSize = sum(protocol.pwmOneSymbol) # COMPUTED

    # CRC Info
    protocol.crcLow = -1 # COMPUTED
    protocol.crcHigh = -1 #COMPUTED
    protocol.crcDataLow = -1 #
    protocol.crcDataHigh = -1 #
    protocol.crcPoly = [] #
    protocol.crcInit = 0 #
    protocol.crcBitOrder = wcv.CRC_REFLECT # 
    protocol.crcReverseOut = False #
    protocol.crcFinalXor = [0, 0] #
    protocol.crcPad = wcv.CRC_NOPAD #
    protocol.crcPadCount = 8 #
    protocol.crcPadVal = 0 # PRO ONLY
    protocol.crcPadCountOptions = [0, 8, 16, 32]
    
    # Payload Data Addresses
    protocol.idAddrLow = 2 # NEED
    protocol.idAddrHigh = 5 # NEED
    protocol.val1AddrLow = 6
    protocol.val1AddrHigh = 11
    protocol.val2AddrLow = 32
    protocol.val2AddrHigh = 33
    protocol.val3AddrLow = 34
    protocol.val3AddrHigh = 35
    
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

    protocol.saveProtocol() # add to database
    
########## fourth element in database
    protocol = ProtocolDefinition(getNextProtocolId())
    protocol.deviceMake = "LaCrosse"
    protocol.deviceModel = "WS-7014CH"
    protocol.deviceYear = "2005"
    protocol.deviceType = getDeviceTypeStringKey("Weather Station")
    #protocol.protocolID = wcv.TEMP_PROTOCOL # this value reserved for current, unsaved protocol
    
    # ONLY EDIT THIS SECTION BELOW
    protocol.frequency = 433.935*1000000.0 ## TBD
    protocol.modulation = wcv.MOD_OOK ##
    protocol.fskDeviation = 10*1000.0 ##
    protocol.channelWidth = 40*1000.0 ##
    protocol.transitionWidth = 1.5*1000.0 ## 
    protocol.threshold = 0.045 ##
    protocol.fskSquelchLeveldB = 0
    protocol.glitchFilterCount = 2

    # Misc Properties
    protocol.unitWidth = 400
    
    # Framing Info
    protocol.interPacketWidth = 3000 # NEED to figure out correct value, or move to preamble sync 
    protocol.interPacketSymbol = wcv.DATA_ZERO # PRO ONLY
    protocol.packetSize = 42
    protocol.preambleType = wcv.PREAMBLE_REG
    protocol.preambleSync = False # PRO ONLY
    protocol.preambleSize = [2, 999]
    protocol.preambleSymbolLow = 1150
    protocol.preambleSymbolHigh = 1150
    protocol.headerLevel = wcv.DATA_ZERO # PRO ONLY
    protocol.headerWidth = -1
    protocol.arbPreambleList = []
    protocol.preamblePulseCount = 0
    
    # Payload Info 
    protocol.encodingType = wcv.PWM
    protocol.pwmSymbolOrder01 = True
    protocol.pwmZeroSymbol = [1150, 550]
    protocol.pwmOneSymbol = [1150, 1150]
    protocol.pwmSymbolSize = sum(protocol.pwmOneSymbol) # COMPUTED

    # CRC Info
    protocol.crcLow = -1 # COMPUTED
    protocol.crcHigh = -1 #COMPUTED
    protocol.crcDataLow = -1 #
    protocol.crcDataHigh = -1 #
    protocol.crcPoly = [] #
    protocol.crcInit = 0 #
    protocol.crcBitOrder = wcv.CRC_REFLECT # 
    protocol.crcReverseOut = False #
    protocol.crcFinalXor = [0, 0] #
    protocol.crcPad = wcv.CRC_NOPAD #
    protocol.crcPadCount = 8 #
    protocol.crcPadVal = 0 # PRO ONLY
    protocol.crcPadCountOptions = [0, 8, 16, 32]
    
    # Payload Data Addresses
    protocol.idAddrLow = 2 # NEED
    protocol.idAddrHigh = 5 # NEED
    protocol.val1AddrLow = 6
    protocol.val1AddrHigh = 11
    protocol.val2AddrLow = 32
    protocol.val2AddrHigh = 33
    protocol.val3AddrLow = 34
    protocol.val3AddrHigh = 35
    
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

    protocol.saveProtocol() # add to database
    
########## fifth element in database
    protocol = ProtocolDefinition(getNextProtocolId())
    protocol.deviceMake = "Lexus"
    protocol.deviceModel = "RS430"
    protocol.deviceYear = "2012"
    protocol.deviceType = getDeviceTypeStringKey("Key Fob")
    #protocol.protocolID = wcv.TEMP_PROTOCOL # this value reserved for current, unsaved protocol
    
    # ONLY EDIT THIS SECTION BELOW
    protocol.frequency = 315.058*1000000.0 ## TBD
    protocol.modulation = wcv.MOD_FSK ##
    protocol.fskDeviation = 15*1000.0 ##
    protocol.channelWidth = 30*1000.0 ##
    protocol.transitionWidth = 6*1000.0 ## 
    protocol.threshold = 0.045 ##
    protocol.fskSquelchLeveldB = -40
    protocol.glitchFilterCount = 2

    # Misc Properties
    protocol.unitWidth = 700
    
    # Framing Info
    protocol.interPacketWidth = 3000 # NEED to figure out correct value, or move to preamble sync 
    protocol.interPacketSymbol = wcv.DATA_ZERO # PRO ONLY
    protocol.packetSize = 42
    protocol.preambleType = wcv.PREAMBLE_REG
    protocol.preambleSync = False # PRO ONLY
    protocol.preambleSize = [8, 999]
    protocol.preambleSymbolLow = 700
    protocol.preambleSymbolHigh = 700
    protocol.headerLevel = wcv.DATA_ZERO # PRO ONLY
    protocol.headerWidth = -1
    protocol.arbPreambleList = []
    protocol.preamblePulseCount = 0
    
    # Payload Info 
    protocol.encodingType = wcv.STD_MANCHESTER
    protocol.pwmSymbolOrder01 = True
    protocol.pwmZeroSymbol = [1150, 550]
    protocol.pwmOneSymbol = [1150, 1150]
    protocol.pwmSymbolSize = sum(protocol.pwmOneSymbol) # COMPUTED

    # CRC Info
    protocol.crcLow = -1 # COMPUTED
    protocol.crcHigh = -1 #COMPUTED
    protocol.crcDataLow = -1 #
    protocol.crcDataHigh = -1 #
    protocol.crcPoly = [] #
    protocol.crcInit = 0 #
    protocol.crcBitOrder = wcv.CRC_REFLECT # 
    protocol.crcReverseOut = False #
    protocol.crcFinalXor = [0, 0] #
    protocol.crcPad = wcv.CRC_NOPAD #
    protocol.crcPadCount = 8 #
    protocol.crcPadVal = 0 # PRO ONLY
    protocol.crcPadCountOptions = [0, 8, 16, 32]
    
    # Payload Data Addresses
    protocol.idAddrLow = 2 # NEED
    protocol.idAddrHigh = 5 # NEED
    protocol.val1AddrLow = 6
    protocol.val1AddrHigh = 11
    protocol.val2AddrLow = 32
    protocol.val2AddrHigh = 33
    protocol.val3AddrLow = 34
    protocol.val3AddrHigh = 35
    
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

    protocol.saveProtocol() # add to database
    
    
########## sixth element in database
    protocol = ProtocolDefinition(getNextProtocolId())
    protocol.deviceMake = "Toyota"
    protocol.deviceModel = "Highlander"    
    protocol.deviceYear = "2015"
    protocol.deviceType = getDeviceTypeStringKey("Key Fob")
    #protocol.protocolID = wcv.TEMP_PROTOCOL # this value reserved for current, unsaved protocol
    
    # ONLY EDIT THIS SECTION BELOW
    protocol.frequency = 315.15*1000000.0 ## TBD
    protocol.modulation = wcv.MOD_FSK ##
    protocol.fskDeviation = 30*1000.0 ##
    protocol.channelWidth = 60*1000.0 ##
    protocol.transitionWidth = 6*1000.0 ## 
    protocol.threshold = 0.045 ##
    protocol.fskSquelchLeveldB = -40
    protocol.glitchFilterCount = 2

    # Misc Properties
    protocol.unitWidth = 700
    
    # Framing Info
    protocol.interPacketWidth = 3000 # NEED to figure out correct value, or move to preamble sync 
    protocol.interPacketSymbol = wcv.DATA_ZERO # PRO ONLY
    protocol.packetSize = 42
    protocol.preambleType = wcv.PREAMBLE_REG
    protocol.preambleSync = False # PRO ONLY
    protocol.preambleSize = [8, 999]
    protocol.preambleSymbolLow = 700
    protocol.preambleSymbolHigh = 700
    protocol.headerLevel = wcv.DATA_ZERO # PRO ONLY
    protocol.headerWidth = -1
    protocol.arbPreambleList = []
    protocol.preamblePulseCount = 0
    
    # Payload Info 
    protocol.encodingType = wcv.STD_MANCHESTER
    protocol.pwmSymbolOrder01 = True
    protocol.pwmZeroSymbol = [1150, 550]
    protocol.pwmOneSymbol = [1150, 1150]
    protocol.pwmSymbolSize = sum(protocol.pwmOneSymbol) # COMPUTED

    # CRC Info
    protocol.crcLow = -1 # COMPUTED
    protocol.crcHigh = -1 #COMPUTED
    protocol.crcDataLow = -1 #
    protocol.crcDataHigh = -1 #
    protocol.crcPoly = [] #
    protocol.crcInit = 0 #
    protocol.crcBitOrder = wcv.CRC_REFLECT # 
    protocol.crcReverseOut = False #
    protocol.crcFinalXor = [0, 0] #
    protocol.crcPad = wcv.CRC_NOPAD #
    protocol.crcPadCount = 8 #
    protocol.crcPadVal = 0 # PRO ONLY
    protocol.crcPadCountOptions = [0, 8, 16, 32]
    
    # Payload Data Addresses
    protocol.idAddrLow = 2 # NEED
    protocol.idAddrHigh = 5 # NEED
    protocol.val1AddrLow = 6
    protocol.val1AddrHigh = 11
    protocol.val2AddrLow = 32
    protocol.val2AddrHigh = 33
    protocol.val3AddrLow = 34
    protocol.val3AddrHigh = 35
    
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

    protocol.saveProtocol() # add to database
    
########## seventh element in database
    protocol = ProtocolDefinition(getNextProtocolId())
    protocol.deviceMake = "Chevrolet"
    protocol.deviceModel = "Tahoe"    
    protocol.deviceYear = "2014"
    protocol.deviceType = getDeviceTypeStringKey("TPM Sensor")
    #protocol.protocolID = wcv.TEMP_PROTOCOL # this value reserved for current, unsaved protocol
    
    # ONLY EDIT THIS SECTION BELOW
    protocol.frequency = 312.91*1000000.0 ## TBD
    protocol.modulation = wcv.MOD_OOK ##
    protocol.fskDeviation = 30*1000.0 ##
    protocol.channelWidth = 120*1000.0 ##
    protocol.transitionWidth = 12*1000.0 ## 
    protocol.threshold = 0.005 ##
    protocol.fskSquelchLeveldB = -40
    protocol.glitchFilterCount = 2

    # Misc Properties
    protocol.unitWidth = 700
    
    # Framing Info
    protocol.interPacketWidth = 3000 # NEED to figure out correct value, or move to preamble sync 
    protocol.interPacketSymbol = wcv.DATA_ZERO # PRO ONLY
    protocol.packetSize = 38
    protocol.preambleType = wcv.PREAMBLE_CNT
    protocol.preambleSync = False # PRO ONLY
    protocol.preambleSize = [8, 999]
    protocol.preambleSymbolLow = 700
    protocol.preambleSymbolHigh = 700
    protocol.headerLevel = wcv.DATA_ZERO # PRO ONLY
    protocol.headerWidth = -1
    protocol.arbPreambleList = []
    protocol.preamblePulseCount = 12
    
    # Payload Info 
    protocol.encodingType = wcv.PWM
    protocol.pwmSymbolOrder01 = False
    protocol.pwmZeroSymbol = [380, 170]
    protocol.pwmOneSymbol = [220, 350]
    protocol.pwmSymbolSize = sum(protocol.pwmOneSymbol) # COMPUTED

    # CRC Info
    protocol.crcLow = -1 # COMPUTED
    protocol.crcHigh = -1 #COMPUTED
    protocol.crcDataLow = -1 #
    protocol.crcDataHigh = -1 #
    protocol.crcPoly = [] #
    protocol.crcInit = 0 #
    protocol.crcBitOrder = wcv.CRC_REFLECT # 
    protocol.crcReverseOut = False #
    protocol.crcFinalXor = [0, 0] #
    protocol.crcPad = wcv.CRC_NOPAD #
    protocol.crcPadCount = 8 #
    protocol.crcPadVal = 0 # PRO ONLY
    protocol.crcPadCountOptions = [0, 8, 16, 32]
    
    # Payload Data Addresses
    protocol.idAddrLow = 1 # NEED
    protocol.idAddrHigh = 2 # NEED
    protocol.val1AddrLow = 1
    protocol.val1AddrHigh = 2
    protocol.val2AddrLow = 1
    protocol.val2AddrHigh = 2
    protocol.val3AddrLow = 1
    protocol.val3AddrHigh = 2
    
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

    protocol.saveProtocol() # add to database
    
