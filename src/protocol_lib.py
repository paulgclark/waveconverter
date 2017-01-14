# This file contains the code that manages the protocol definitions,
# including storing, retrieving and modifying. The defining characteristics
# for each protocol are contained in a protocol object, all of which 
# are contained in a dictionary.
# 
# This dictionary is written to a re-writeable binary file on the 
# user's machine. An initial install will have a dictionary pre-populated 
# with known protocols.
#
# The following functions are available for accessing the protocol library:
# - retrieve protocol definition from sqlite3 db
# - manually create new definition from input Python file
# - create new protocol definition (in memory)
# - return list of library elements
# - return size of library (number of protocol definitions)
# - write modified library to disk
# - export library to a text file(?)
# - 
#
# NOTE: All timing values are in microseconds 
#
# PC - vars to make global controls override parts of protocol def:
#   unit_error
#   glitch_filter

#from waveConvertVars import *
from sqlalchemy import *
import waveConvertVars as wcv

#from sqlalchemy import Column, Integer, Unicode, UnicodeText, String
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy import Column, ForeignKey, Integer, String, PickleType
from sqlalchemy.sql import func

# set up the connection to the protocol library sqllite database
engine = create_engine('sqlite:///protocol_library.db', echo=False)
Base = declarative_base(bind=engine)
# create session to connect to database containing stored protocol definitions 
Session = sessionmaker(bind=engine)
protocolSession = Session() # this is a global variable used by many protocol_lib functions


# define sqlalchemy class for storage of protocol object
class ProtocolDefinition(Base):
    __tablename__ = 'protocols'
    
    # waveconverter protocol library vars
    protocolId = Column(Integer, primary_key=True)
    deviceMake = Column(String(250), nullable=False)
    deviceModel = Column(String(250), nullable=False)
    deviceYear = Column(String(250), nullable=False)
    deviceType = Column(Integer)
      
    # RF demodulation vars
    frequency = Column(Integer)
    fskDeviation = Column(Integer)
    channelWidth = Column(Integer)
    transitionWidth = Column(Integer)
    modulation = Column(Integer)
    threshold = Column(Integer)
    fskSquelchLeveldB = Column(Integer)
    glitchFilterCount = Column(Integer) #
        
    # framing vars
    interPacketWidth = Column(Integer)
    interPacketSymbol = Column(Integer)
    preambleType = Column(Integer)
    preambleSymbolHigh = Column(Integer)
    preambleSymbolLow = Column(Integer)
    preambleSize = Column(PickleType) # list some preambles have different lengths
    headerLevel = Column(Integer)
    headerWidth = Column(Integer)
    arbPreambleList = Column(PickleType) # list of widths
    packetSize = Column(Integer) # rename to payloadSize
    preambleSync = Column(Integer)
    preamblePulseCount = Column(Integer)
             
    # timing vars
    unitWidth = Column(Integer)
    encodingType = Column(Integer)
    pwmSymbolOrder01 = Column(Integer) #
    pwmOneSymbol = Column(PickleType) # list with two elements
    pwmZeroSymbol = Column(PickleType) # list with two elements
    pwmSymbolSize = Column(Integer)
        
    # payload addresses for statistical analysis
    idAddrLow = Column(Integer)
    idAddrHigh = Column(Integer)
    val1AddrLow = Column(Integer)
    val1AddrHigh = Column(Integer)
    val2AddrLow = Column(Integer)
    val2AddrHigh = Column(Integer)
    val3AddrLow = Column(Integer)
    val3AddrHigh = Column(Integer)
        
    # CRC vars
    crcLow = Column(Integer)
    crcHigh = Column(Integer)
    crcDataLow = Column(Integer)
    crcDataHigh = Column(Integer)
    crcPoly = Column(PickleType) # list
    crcInit = Column(Integer)
    crcBitOrder = Column(Integer)
    crcReverseOut = Column(Integer)
    crcFinalXor = Column(PickleType) # list
    crcPad = Column(Integer)
    crcPadCount = Column(Integer)
    crcPadVal = Column(Integer)
    crcPadCountOptions = Column(PickleType) # list
    
    # These variables hold the current protocol's timing values in units of samples.
    # The protocol objects themselves hold the values in units of microseconds, but
    # the baseband waveforms may have different timescales due to the rate at which
    # they were sampled. The values here are computed after each change to the
    # protocol record.
    unitWidth_samp = Column(Integer)
    interPacketWidth_samp = Column(Integer) # 
    preambleSymbolLow_samp = Column(Integer)
    preambleSymbolHigh_samp = Column(Integer)
    arbPreambleList_samp = Column(PickleType)
    headerWidth_samp = Column(Integer) #
    pwmOneSymbol_samp = Column(PickleType) # list
    pwmZeroSymbol_samp = Column(PickleType) # list
    pwmSymbolSize_samp = Column(Integer)

    
    def __init__(self, protocolId):
        self.protocolId = protocolId # maybe search through database to find max value and +1
        # initializing all the lists with default sizes make things easier later
        self.preambleSize = [0, 0]
        self.arbPreambleList = []
        self.pwmOneSymbol = [0, 0]
        self.pwmZeroSymbol = [0, 0]
        self.pwmOneSymbol_samp = [0, 0]
        self.pwmZeroSymbol_samp = [0, 0]
        self.crcFinalXor = []
        self.crcPadCountOptions = []
        self.crcPoly = []
        # the rest of the features must be generated manually
    
    def printProtocolMinimal(self):
        print "protocolId:" + str(self.protocolId)
        print "Device Make:" + str(self.deviceMake)
        print "Device Model:" + str(self.deviceModel)
        print "Device Year:" + str(self.deviceYear)
        print "Device Type:" + str(self.deviceType)

    def fullProtocolString(self):
        outString = "Protocol ID: " + str(self.protocolId) + "\n"
        outString +=  "Device Make: " + str(self.deviceMake) + "\n"
        outString += "Device Model: " + str(self.deviceModel) + "\n"
        outString += "Device Year: " + str(self.deviceYear) + "\n"
        outString += "Device Type: " + str(self.deviceType) + "\n"
        outString += "RF Properties:\n"
        outString += " Frequency(MHz): " + str(self.frequency) + "\n"
        outString += " Modulation: " + str(self.modulation) + "\n"
        outString += " Channel Width(kHz): " + str(self.channelWidth) + "\n"
        outString += " Transition Width(kHz): " + str(self.transitionWidth) + "\n"
        outString += " FSK Deviation(kHz): " + str(self.fskDeviation) + "\n"
        outString += " FSK Squelch Level (dB): " + str(self.fskSquelchLeveldB) + "\n"
        outString += " Threshold: " + str(self.threshold) + "\n"
        outString += "Framing Properties:\n"
        outString += " Time between transmissions(us): " + str(self.interPacketWidth) + "\n"
        outString += " Preamble Type: " + str(self.preambleType) + "\n"
        outString += " Preamble Low Time (us): " + str(self.preambleSymbolLow) + "\n"
        outString += " Preamble High Time (us): " + str(self.preambleSymbolHigh) + "\n"
        outString += " Preamble Length 1: " + str(self.preambleSize[0]) + "\n"
        outString += " Preamble Length 2: " + str(self.preambleSize[1]) + "\n"
        outString += " Arbitrary Preamble: " + str(self.arbPreambleList) + "\n"
        outString += " Header Length: " + str(self.headerWidth) + "\n"
        outString += " Preamble Pulse Count: " + str(self.preamblePulseCount) + "\n"
        outString += " Preamble Sync: " + str(self.preambleSync) + "\n"
        outString += "Demod Properties:\n"
        outString += " Encoding: " + str(self.encodingType) + "\n"
        outString += " PWM Symbol Order: " + str(self.pwmSymbolOrder01) + "\n"
        outString += " PWM Symbol Size: " + str(self.pwmSymbolSize) + "\n"
        outString += " PWM 1: " + str(self.pwmOneSymbol) + "\n"
        outString += " PWM 0: " + str(self.pwmZeroSymbol) + "\n"
        outString += " Unit Width: " + str(self.unitWidth) + "\n"
        outString += " TX Size: " + str(self.packetSize) + "\n"
        outString += "CRC Properties:\n"
        outString += " CRC Low Addr: " + str(self.crcLow) + "\n"
        outString += " CRC High Addr: " + str(self.crcHigh) + "\n"
        outString += " CRC Low Data Addr: " + str(self.crcDataLow) + "\n"
        outString += " CRC High Data Addr: " + str(self.crcDataHigh) + "\n"
        outString += " CRC Poly: " + str(self.crcPoly) + "\n"
        outString += " CRC Init: " + str(self.crcInit) + "\n"
        outString += " CRC Bit Order: " + str(self.crcBitOrder) + "\n" 
        outString += " CRC Reverse: " + str(self.crcReverseOut) + "\n"
        outString += " CRC Final XOR: " + str(self.crcFinalXor) + "\n"
        outString += " CRC Pad: " + str(self.crcPad) + "\n"
        outString += " CRC Pad Count: " + str(self.crcPadCount) + "\n"
        outString += " CRC Pad Val: " + str(self.crcPadVal) + "\n"
        outString += " CRC Pad Count Options: " + str(self.crcPadCountOptions) + "\n"
        outString += "Stat Properties:\n"
        outString += " ID Addr Low: " + str(self.idAddrLow) + "\n"
        outString += " ID Addr High: " + str(self.idAddrHigh) + "\n"
        outString += " Value 1 Addr Low: " + str(self.val1AddrLow) + "\n"
        outString += " Value 1 Addr High: " + str(self.val1AddrHigh) + "\n"
        outString += " Value 2 Addr Low: " + str(self.val2AddrLow) + "\n"
        outString += " Value 2 Addr High: " + str(self.val2AddrHigh) + "\n"
        outString += " Value 3 Addr Low: " + str(self.val3AddrLow) + "\n"
        outString += " Value 3 Addr High: " + str(self.val3AddrHigh) + "\n"
        outString += "Timing Propertied Re-Calculated in units of samples:\n"
        outString += " Unit Width (samples): " + str(self.unitWidth_samp) + "\n"
        outString += " Inter-Packet Width (samples): " + str(self.interPacketWidth_samp) + "\n"
        outString += " Preamble Symbol Low (samples): " + str(self.preambleSymbolLow_samp) + "\n"
        outString += " Preamble Symbol High (samples): " + str(self.preambleSymbolHigh_samp) + "\n"
        outString += " Header Width (samples): " + str(self.headerWidth_samp) + "\n"
        outString += " Arbitrary Preamble List (samples): " + str(self.arbPreambleList_samp) + "\n"
        outString += " PWM 1 Symbol (samples): " + str(self.pwmOneSymbol_samp) + "\n"
        outString += " PWM 0 Symbol (samples): " + str(self.pwmZeroSymbol_samp) + "\n"
        outString += " PWM Symbol Size (samples): " + str(self.pwmSymbolSize_samp) + "\n"
        outString += "Currently Unused Parameters:\n"
        outString += " glitchFilterCount: " + str(self.glitchFilterCount) + "\n"
        outString += " interPacketSymbol: " + str(self.interPacketSymbol) + "\n"
        outString += " headerLevel: " + str(self.headerLevel) + "\n"
        outString += " preambleSync: " + str(self.preambleSync) + "\n"
        return outString

    # - write modified protocol to disk
    def saveProtocol(self):
        global protocolSession
        
        # explicitly copy and assign all list variables, else sqlalchemy will not catch changes
        # more elegant solution is to define the pickled objects as a mutable list
        copiedList = self.preambleSize[:]
        del self.preambleSize[:]
        self.preambleSize = copiedList
        
        copiedList = self.pwmOneSymbol[:]
        del self.pwmOneSymbol[:]
        self.pwmOneSymbol = copiedList
        
        copiedList = self.pwmZeroSymbol[:]
        del self.pwmZeroSymbol[:]
        self.pwmZeroSymbol = copiedList
        
        copiedList = self.crcPoly[:]
        del self.crcPoly[:]
        self.crcPoly = copiedList
        
        copiedList = self.crcFinalXor[:]
        del self.crcFinalXor[:]
        self.crcFinalXor = copiedList
     
        copiedList = self.crcPadCountOptions[:]
        del self.crcPadCountOptions[:]
        self.crcPadCountOptions = copiedList
        
        copiedList = self.arbPreambleList[:]
        del self.arbPreambleList[:]
        self.arbPreambleList = copiedList
            
        copiedList = self.arbPreambleList_samp[:]
        del self.arbPreambleList_samp[:]
        self.arbPreambleList_samp = copiedList

        try:
            protocolSession.merge(self)
        except:
            print "ERROR: problem adding or merging protocol entry to database"
        protocolSession.commit()
        
    # convert timing parameters from us to samples based on current sample rate
    def convertTimingToSamples(self, basebandSampleRate):
        #microsecondsPerSample = 1000000.0/samp_rate
        samplesPerMicrosecond = basebandSampleRate/1000000.0
        self.unitWidth_samp = int(self.unitWidth * samplesPerMicrosecond)
        self.interPacketWidth_samp = int(self.interPacketWidth * samplesPerMicrosecond)
        self.preambleSymbolLow_samp = int(self.preambleSymbolLow * samplesPerMicrosecond)
        self.preambleSymbolHigh_samp = int(self.preambleSymbolHigh * samplesPerMicrosecond)
        self.headerWidth_samp = int(self.headerWidth * samplesPerMicrosecond)
        self.pwmOneSymbol_samp[0] = int(self.pwmOneSymbol[0] * samplesPerMicrosecond)
        self.pwmOneSymbol_samp[1] = int(self.pwmOneSymbol[1] * samplesPerMicrosecond)
        self.pwmZeroSymbol_samp[0] = int(self.pwmZeroSymbol[0] * samplesPerMicrosecond)
        self.pwmZeroSymbol_samp[1] = int(self.pwmZeroSymbol[1] * samplesPerMicrosecond)
        self.pwmSymbolSize_samp = sum(self.pwmOneSymbol_samp)
        
        newArbList = []
        for timingVal in self.arbPreambleList:
            newArbList.append(int(timingVal * samplesPerMicrosecond))
        self.arbPreambleList_samp = newArbList
        
        return(0)

    # produces the maximum size, in integer samples, that a transmission
    # using this protocol can have
    def maxTransmissionSize(self):
        maxSize = 0
        
        # add the preamble size
        maxSize += (self.preambleSymbolLow_samp + self.preambleSymbolHigh_samp) * max(self.preambleSize)
        
        # add the header
        maxSize += self.headerWidth_samp 
        
        # add the payload and CRC
        if self.encodingType == 3: # make this PWM
            maxSize += self.pwmSymbolSize_samp * self.packetSize
            maxSize += self.pwmSymbolSize_samp * (self.crcHigh - self.crcLow)
        else: # assume it's a Manchester variant
            maxSize += (self.unitWidth_samp * 2) * self.packetSize
            maxSize += (self.unitWidth_samp * 2) * (self.crcHigh - self.crcLow)
            
        # scale up by max timing error and additional fudge factor
        maxSize = maxSize * (wcv.timingError + 0.05)
        
        return(int(maxSize))
    
    # this produces the max legal duration (in samples) of a signal level equal to zero
    # we'll use this to distinguish between a legal zero level within a transmission
    # and the inter-packet dead air
    def maxZeroTimeInTx(self):
        if self.encodingType == 3: # PWM
            maxSize = (wcv.timingError + 0.05) * max([self.headerWidth_samp, self.preambleSymbolLow_samp, self.pwmSymbolSize_samp])
        else:
            maxSize = (wcv.timingError + 0.05) * max([self.headerWidth_samp, self.preambleSymbolLow_samp, self.unitWidth_samp * 2])
        return(int(maxSize))


# sqlalchemy needs this after database class declaration
#if not wcv.argcHelp:
Base.metadata.create_all()


# The following functions perform higher level database manipulations    
# this method finds the next available ID that can be used for a new protocol
def getNextProtocolId():
    global protocolSession
    query = protocolSession.query(func.max(ProtocolDefinition.protocolId).label("maxId"))
    try:
        return query.one().maxId + 1 # if table is not empty
    except:
        return 1 # if table is empty
        
# - return size of library (number of protocol definitions)
def getProtocolCount():
    global protocolSession
    query = protocolSession.query(func.count(ProtocolDefinition.protocolId).label("numIDs"))
    return query.one().numIDs

# - return list of library elements, including the key parameters
def listProtocols():
    global protocolSession
    print '{:5s} {:5s} {:20s} {:20s} {:20s}'.format("   ID", "Year", "Make", "Model", "Type")
    # get a list of items in database
    for proto in protocolSession.query(ProtocolDefinition):
        print '{:5d} {:5s} {:20s} {:20s} {:20s}'.format(proto.protocolId, proto.deviceYear, proto.deviceMake, proto.deviceModel, wcv.devTypeStrings[proto.deviceType]) 

def fetchProtocol(protocolId):
    global protocolSession
    proto = protocolSession.query(ProtocolDefinition).get(protocolId)
    proto.convertTimingToSamples(wcv.basebandSampleRate)
    return proto

def parseProtocolText(inputString, parameterString, parameterType):
    inputLines = inputString.split("\n")
    for line in inputLines:
        linePair = line.split(": ")
        if linePair[0].strip() == parameterString:
            if parameterType == wcv.PARAM_STR:
                return linePair[1].strip()
            elif parameterType == wcv.PARAM_INT:
                return int(linePair[1].strip())
            elif parameterType == wcv.PARAM_FLOAT:
                return float(linePair[1].strip())
            elif parameterType == wcv.PARAM_BOOL:
                if int(linePair[1].strip()) == 1:
                    return True
                else:
                    return False
            elif parameterType == wcv.PARAM_LIST:
                return wcv.stringToIntegerList(linePair[1].strip())
    
    # if we reached here, then we did not fine the input parameter in the given protocol text
    print "Can't find " + parameterString + " in input text file. Exiting..."
    exit(1)
    
def createProtocolFromText(fileString):
    # parse input text and assign values to protocol
    protocol = ProtocolDefinition(getNextProtocolId())
    protocol.deviceMake = parseProtocolText(fileString, "Device Make", wcv.PARAM_STR)
    protocol.deviceModel = parseProtocolText(fileString, "Device Model", wcv.PARAM_STR)
    protocol.deviceYear = parseProtocolText(fileString, "Device Year", wcv.PARAM_STR)
    protocol.deviceType = parseProtocolText(fileString, "Device Type", wcv.PARAM_INT)
    
    protocol.frequency = parseProtocolText(fileString, "Frequency(MHz)", wcv.PARAM_FLOAT)
    protocol.modulation = parseProtocolText(fileString, "Modulation", wcv.PARAM_INT)
    protocol.channelWidth = parseProtocolText(fileString, "Channel Width(kHz)", wcv.PARAM_FLOAT)
    protocol.transitionWidth = parseProtocolText(fileString, "Transition Width(kHz)", wcv.PARAM_FLOAT)
    protocol.fskDeviation = parseProtocolText(fileString, "FSK Deviation(kHz)", wcv.PARAM_FLOAT)
    protocol.fskSquelchLeveldB = parseProtocolText(fileString, "FSK Squelch Level (dB)", wcv.PARAM_FLOAT)
    protocol.threshold = parseProtocolText(fileString, "Threshold", wcv.PARAM_FLOAT)
        
    protocol.interPacketWidth = parseProtocolText(fileString, "Time between transmissions(us)", wcv.PARAM_INT)
    protocol.preambleType = parseProtocolText(fileString, "Preamble Type", wcv.PARAM_INT)
    protocol.preambleSymbolLow = parseProtocolText(fileString, "Preamble Low Time (us)", wcv.PARAM_INT)
    protocol.preambleSymbolHigh = parseProtocolText(fileString, "Preamble High Time (us)", wcv.PARAM_INT)
    protocol.preambleSize[0] = parseProtocolText(fileString, "Preamble Length 1", wcv.PARAM_INT)
    protocol.preambleSize[1] = parseProtocolText(fileString, "Preamble Length 2", wcv.PARAM_INT)
    protocol.arbPreambleList = parseProtocolText(fileString, "Arbitrary Preamble", wcv.PARAM_LIST)
    protocol.headerWidth = parseProtocolText(fileString, "Header Length", wcv.PARAM_INT)
    protocol.preamblePulseCount = parseProtocolText(fileString, "Preamble Pulse Count", wcv.PARAM_INT)
    protocol.preambleSync = parseProtocolText(fileString, "Preamble Sync", wcv.PARAM_BOOL)
    
    protocol.encodingType = parseProtocolText(fileString, "Encoding", wcv.PARAM_INT)
    protocol.pwmSymbolOrder01 = parseProtocolText(fileString, "PWM Symbol Order", wcv.PARAM_BOOL)
    protocol.pwmSymbolSize = parseProtocolText(fileString, "PWM Symbol Size", wcv.PARAM_INT)
    protocol.pwmOneSymbol = parseProtocolText(fileString, "PWM 1", wcv.PARAM_LIST)
    protocol.pwmZeroSymbol = parseProtocolText(fileString, "PWM 0", wcv.PARAM_LIST)
    protocol.pwmSymbolSize = parseProtocolText(fileString, "PWM Symbol Size", wcv.PARAM_INT)
    protocol.unitWidth = parseProtocolText(fileString, "Unit Width", wcv.PARAM_INT)
    protocol.packetSize = parseProtocolText(fileString, "TX Size", wcv.PARAM_INT)
    
    protocol.crcLow = parseProtocolText(fileString, "CRC Low Addr", wcv.PARAM_INT)
    protocol.crcHigh = parseProtocolText(fileString, "CRC High Addr", wcv.PARAM_INT)
    protocol.crcDataLow = parseProtocolText(fileString, "CRC Low Data Addr", wcv.PARAM_INT)
    protocol.crcDataHigh = parseProtocolText(fileString, "CRC High Data Addr", wcv.PARAM_INT)
    protocol.crcPoly = parseProtocolText(fileString, "CRC Poly", wcv.PARAM_LIST)
    protocol.crcInit = parseProtocolText(fileString, "CRC Init", wcv.PARAM_INT)
    protocol.crcBitOrder = parseProtocolText(fileString, "CRC Bit Order", wcv.PARAM_INT)
    protocol.crcReverseOut = parseProtocolText(fileString, "CRC Reverse", wcv.PARAM_BOOL)
    protocol.crcFinalXor = parseProtocolText(fileString, "CRC Final XOR", wcv.PARAM_LIST)
    protocol.crcPad = parseProtocolText(fileString, "CRC Pad", wcv.PARAM_INT)
    protocol.crcPadCount = parseProtocolText(fileString, "CRC Pad Count", wcv.PARAM_INT)
    protocol.crcPadVal = parseProtocolText(fileString, "CRC Pad Val", wcv.PARAM_INT)
    protocol.crcPadCountOptions = parseProtocolText(fileString, "CRC Pad Count Options", wcv.PARAM_LIST)
    
    protocol.idAddrLow = parseProtocolText(fileString, "ID Addr Low", wcv.PARAM_INT)
    protocol.idAddrHigh = parseProtocolText(fileString, "ID Addr High", wcv.PARAM_INT)
    protocol.val1AddrLow = parseProtocolText(fileString, "Value 1 Addr Low", wcv.PARAM_INT)
    protocol.val1AddrHigh = parseProtocolText(fileString, "Value 1 Addr High", wcv.PARAM_INT)
    protocol.val2AddrLow = parseProtocolText(fileString, "Value 2 Addr Low", wcv.PARAM_INT)
    protocol.val2AddrHigh = parseProtocolText(fileString, "Value 2 Addr High", wcv.PARAM_INT)
    protocol.val3AddrLow = parseProtocolText(fileString, "Value 3 Addr Low", wcv.PARAM_INT)
    protocol.val3AddrHigh = parseProtocolText(fileString, "Value 3 Addr High", wcv.PARAM_INT)
    
    protocol.unitWidth_samp = parseProtocolText(fileString, "Unit Width (samples)", wcv.PARAM_INT)
    protocol.interPacketWidth_samp = parseProtocolText(fileString, "Inter-Packet Width (samples)", wcv.PARAM_INT)
    protocol.preambleSymbolLow_samp = parseProtocolText(fileString, "Preamble Symbol Low (samples)", wcv.PARAM_INT)
    protocol.preambleSymbolHigh_samp = parseProtocolText(fileString, "Preamble Symbol High (samples)", wcv.PARAM_INT)
    protocol.headerWidth_samp = parseProtocolText(fileString, "Header Width (samples)", wcv.PARAM_INT)
    protocol.arbPreambleList_samp = parseProtocolText(fileString, "Arbitrary Preamble List (samples)", wcv.PARAM_LIST)
    protocol.pwmOneSymbol_samp = parseProtocolText(fileString, "PWM 1 Symbol (samples)", wcv.PARAM_LIST)
    protocol.pwmZeroSymbol_samp = parseProtocolText(fileString, "PWM 0 Symbol (samples)", wcv.PARAM_LIST)
    protocol.pwmSymbolSize_samp = parseProtocolText(fileString, "PWM Symbol Size (samples)", wcv.PARAM_INT)

    # unused parameters that need to be set for sqllite to be happy
    protocol.glitchFilterCount = 2
    protocol.interPacketSymbol = 0
    protocol.headerLevel = 0
    
    # write protocol to database
    protocol.saveProtocol()
    return 0

# this is used by both the buildProtocolLibrary and manualProtocol files
def getDeviceTypeStringKey(deviceString):
    for keyVal in wcv.devTypeStrings:
        if wcv.devTypeStrings[keyVal] == deviceString:
            return keyVal
