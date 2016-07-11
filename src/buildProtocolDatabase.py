# This file is used to manually set up the database containing the protocol library.
# This may need to be replaced eventually by a scheme that takes a gold database and 
# modifies it as needed. For the early stages of development, this is easier.
from protocol_lib import ProtocolDefinition, getNextProtocolId
import waveConvertVars as wcv

def buildProtocolDatabase():
    # zeroth protocol, the default that is loaded when none is specified
    protocol = ProtocolDefinition(getNextProtocolId())
    protocol.deviceName = "Device Name"
    protocol.deviceYear = "Year"
    protocol.deviceType = "Type"
    protocol.name = protocol.deviceName + ":" + protocol.deviceYear + ":" + protocol.deviceType
    #protocol.protocolID = wcv.TEMP_PROTOCOL # this value reserved for current, unsaved protocol
    
    # ONLY EDIT THIS SECTION BELOW
    protocol.frequency = 315*1000000.0 ##
    protocol.modulation = wcv.MOD_OOK ##
    protocol.fskDeviation = 10*1000.0 ##
    protocol.channelWidth = 20*1000.0 ##
    protocol.transitionWidth = 1.5*1000.0 ## 
    protocol.threshold = 0.3 ##

    # Misc Properties
    protocol.unitWidth = 100
    
    # Framing Info
    protocol.interPacketWidth = 2000 
    protocol.interPacketSymbol = wcv.DATA_ZERO # PRO ONLY
    protocol.packetSize = 100
    protocol.preambleSync = False # PRO ONLY
    protocol.preambleSize = [10, 999]
    protocol.preambleSymbolLow = 100 # 200
    protocol.preambleSymbolHigh = 100 # 100
    protocol.headerLevel = wcv.DATA_ZERO # PRO ONLY
    protocol.headerWidth = 500 # 960 #
    
    # Payload Info 
    protocol.encodingType = wcv.PWM 
    protocol.pwmOneSymbol = [100, 200]# [90, 490] #
    protocol.pwmZeroSymbol = [200, 100]# [180, 400] #
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
    
    # provide initial values for these
    protocol.unitWidth_samp = 1
    protocol.interPacketWidth_samp = 1 
    protocol.preambleSymbolLow_samp = 1
    protocol.preambleSymbolHigh_samp = 1
    protocol.headerWidth_samp = 1
    protocol.pwmOneSymbol_samp = [1, 1]
    protocol.pwmZeroSymbol_samp = [1, 1]
    protocol.pwmSymbolSize_samp = 2
    
    protocol.saveProtocol() # add to database
    
    
    # first protocol
    protocol = ProtocolDefinition(getNextProtocolId())
    protocol.deviceName = "Chevy Colorado"
    protocol.deviceYear = "2011"
    protocol.deviceType = "keyfob"
    protocol.name = protocol.deviceName + ":" + protocol.deviceYear + ":" + protocol.deviceType
    #protocol.protocolID = wcv.TEMP_PROTOCOL # this value reserved for current, unsaved protocol
    
    # ONLY EDIT THIS SECTION BELOW
    protocol.frequency = 314.938*1000000.0 ##
    protocol.modulation = wcv.MOD_OOK ##
    protocol.fskDeviation = 10*1000.0 ##
    protocol.channelWidth = 20*1000.0 ##
    protocol.transitionWidth = 1.5*1000.0 ## 
    protocol.threshold = 0.3 ##

    # Misc Properties
    protocol.unitWidth = 225 # 90
    
    # Framing Info
    protocol.interPacketWidth = 4000 # 3000 NEED to figure out correct value, or move to preamble sync 
    protocol.interPacketSymbol = wcv.DATA_ZERO # PRO ONLY
    protocol.packetSize = 67
    protocol.preambleSync = False # PRO ONLY
    protocol.preambleSize = [10, 999]
    protocol.preambleSymbolLow = 500 # 200
    protocol.preambleSymbolHigh = 250 # 100
    protocol.headerLevel = wcv.DATA_ZERO # PRO ONLY
    protocol.headerWidth = 2400 # 960 #
    
    # Payload Info 
    protocol.encodingType = wcv.PWM 
    protocol.pwmOneSymbol = [225, 1225]# [90, 490] #
    protocol.pwmZeroSymbol = [450, 1000]# [180, 400] #
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
    
    # provide initial values for these
    protocol.unitWidth_samp = 1
    protocol.interPacketWidth_samp = 1 
    protocol.preambleSymbolLow_samp = 1
    protocol.preambleSymbolHigh_samp = 1
    protocol.headerWidth_samp = 1
    protocol.pwmOneSymbol_samp = [1, 1]
    protocol.pwmZeroSymbol_samp = [1, 1]
    protocol.pwmSymbolSize_samp = 2
    
    protocol.saveProtocol() # add to database
    
########## second element in database
    protocol = ProtocolDefinition(getNextProtocolId())
    protocol.deviceName = "Volvo S60"
    protocol.deviceYear = "2003"
    protocol.deviceType = "keyfob"
    protocol.name = protocol.deviceName + ":" + protocol.deviceYear + ":" + protocol.deviceType
    #protocol.protocolID = wcv.TEMP_PROTOCOL # this value reserved for current, unsaved protocol
    
    # ONLY EDIT THIS SECTION BELOW
    protocol.frequency = 314.938*1000000.0 ## TBD
    protocol.modulation = wcv.MOD_OOK ##
    protocol.fskDeviation = 10*1000.0 ##
    protocol.channelWidth = 20*1000.0 ##
    protocol.transitionWidth = 1.5*1000.0 ## 
    protocol.threshold = 0.3 ##

    # Misc Properties
    protocol.unitWidth = 400
    
    # Framing Info
    protocol.interPacketWidth = 2500 # NEED to figure out correct value, or move to preamble sync 
    protocol.interPacketSymbol = wcv.DATA_ZERO # PRO ONLY
    protocol.packetSize = 71
    protocol.preambleSync = False # PRO ONLY
    protocol.preambleSize = [16, 70]
    protocol.preambleSymbolLow = protocol.unitWidth
    protocol.preambleSymbolHigh = protocol.unitWidth
    protocol.headerLevel = wcv.DATA_ZERO # PRO ONLY
    protocol.headerWidth = 4*protocol.unitWidth
    
    # Payload Info 
    protocol.encodingType = wcv.STD_MANCHESTER
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
    protocol.valAddrLow = 24
    protocol.valAddrHigh = 31
    
    # provide initial values for these
    protocol.unitWidth_samp = 1
    protocol.interPacketWidth_samp = 1 
    protocol.preambleSymbolLow_samp = 1
    protocol.preambleSymbolHigh_samp = 1
    protocol.headerWidth_samp = 1
    protocol.pwmOneSymbol_samp = [1, 1]
    protocol.pwmZeroSymbol_samp = [1, 1]
    protocol.pwmSymbolSize_samp = 2

    protocol.saveProtocol() # add to database
    
########## third element in database
    protocol = ProtocolDefinition(getNextProtocolId())
    protocol.deviceName = "Chevy Colorado"
    protocol.deviceYear = "2011"
    protocol.deviceType = "tpm"
    protocol.name = protocol.deviceName + ":" + protocol.deviceYear + ":" + protocol.deviceType
    #protocol.protocolID = wcv.TEMP_PROTOCOL # this value reserved for current, unsaved protocol
    
    # ONLY EDIT THIS SECTION BELOW
    protocol.frequency = 314.938*1000000.0 ## TBD
    protocol.modulation = wcv.MOD_OOK ##
    protocol.fskDeviation = 10*1000.0 ##
    protocol.channelWidth = 20*1000.0 ##
    protocol.transitionWidth = 1.5*1000.0 ## 
    protocol.threshold = 0.3 ##

    # Misc Properties
    protocol.unitWidth = 180
    
    # Framing Info
    protocol.interPacketWidth = 5000 # NEED to figure out correct value, or move to preamble sync 
    protocol.interPacketSymbol = wcv.DATA_ZERO # PRO ONLY
    protocol.packetSize = 34
    protocol.preambleSync = False # PRO ONLY
    protocol.preambleSize = [5, 999]
    protocol.preambleSymbolLow = protocol.unitWidth
    protocol.preambleSymbolHigh = 2*protocol.unitWidth
    protocol.headerLevel = wcv.DATA_ZERO # PRO ONLY
    protocol.headerWidth = 3*protocol.unitWidth
    
    # Payload Info 
    protocol.encodingType = wcv.PWM
    protocol.pwmOneSymbol = [2*protocol.unitWidth, protocol.unitWidth]
    protocol.pwmZeroSymbol = [protocol.unitWidth, 2*protocol.unitWidth]
    protocol.pwmSymbolSize = sum(protocol.pwmOneSymbol) # COMPUTED

    # CRC Info
    protocol.crcLow = -1 # COMPUTED
    protocol.crcHigh = -1 #COMPUTED
    protocol.crcDataLow = -1 #
    protocol.crcDataHigh = -1 #
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
    protocol.idAddrLow = 66 # NEED
    protocol.idAddrHigh = 67 # NEED
    protocol.valAddrLow = 24 # NEED
    protocol.valAddrHigh = 31 # NEED
    
    # provide initial values for these
    protocol.unitWidth_samp = 1
    protocol.interPacketWidth_samp = 1 
    protocol.preambleSymbolLow_samp = 1
    protocol.preambleSymbolHigh_samp = 1
    protocol.headerWidth_samp = 1
    protocol.pwmOneSymbol_samp = [1, 1]
    protocol.pwmZeroSymbol_samp = [1, 1]
    protocol.pwmSymbolSize_samp = 2

    protocol.saveProtocol() # add to database