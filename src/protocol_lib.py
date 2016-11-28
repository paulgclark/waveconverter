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
    deviceName = Column(String(250), nullable=False)
    deviceYear = Column(String(250), nullable=False)
    deviceType = Column(Integer)
      
    # RF demodulation vars
    frequency = Column(Integer)
    fskDeviation = Column(Integer)
    channelWidth = Column(Integer)
    transitionWidth = Column(Integer)
    modulation = Column(Integer)
    threshold = Column(Integer)
        
    # framing vars
    interPacketWidth = Column(Integer)
    interPacketSymbol = Column(Integer)
    preambleSymbolHigh = Column(Integer)
    preambleSymbolLow = Column(Integer)
    preambleSize = Column(PickleType) # list some preambles have different lengths
    headerLevel = Column(Integer)
    headerWidth = Column(Integer)
    packetSize = Column(Integer) # rename to payloadSize
    preambleSync = Column(Integer)
        
    # timing vars
    unitWidth = Column(Integer)
    encodingType = Column(Integer)
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
    headerWidth_samp = Column(Integer) #
    pwmOneSymbol_samp = Column(PickleType) # list
    pwmZeroSymbol_samp = Column(PickleType) # list
    pwmSymbolSize_samp = Column(Integer)

    
    def __init__(self, protocolId):
        self.protocolId = protocolId # maybe search through database to find max value and +1
        # initializing all the lists with default sizes make things easier later
        self.preambleSize = [0, 0]
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
        print "Device Name:" + str(self.deviceName)
        print "Device Year:" + str(self.deviceYear)
        print "Device Type:" + str(self.deviceType)

    def printProtocolFull(self):
        print "Protocol ID:" + str(self.protocolId)
        print "Device Name:" + str(self.deviceName)
        print "Device Year:" + str(self.deviceYear)
        print "Device Type:" + str(self.deviceType)
        print "RF Properties:"
        print " Frequency(MHz): " + str(self.frequency)
        print " Modulation: " + str(self.modulation)
        print " Channel Width(kHz): " + str(self.channelWidth)
        print " Transition Width(kHz): " + str(self.transitionWidth)
        print " FSK Deviation(kHz): " + str(self.fskDeviation)
        print "Framing Properties:"
        print " Time between transmissions(us): " + str(self.interPacketWidth)
        print " Preamble Low Time (us): " + str(self.preambleSymbolLow)
        print " Preamble High Time (us): " + str(self.preambleSymbolHigh)
        print " Preamble Length 1: " + str(self.preambleSize[0])
        print " Preamble Length 2: " + str(self.preambleSize[1])
        print " Header Length: " + str(self.headerWidth)
        print "Demod Properties:"
        print " Encoding: " + str(self.encodingType)
        print " PWM Symbol Size: " + str(self.pwmSymbolSize)
        print " PWM 1: " + str(self.pwmOneSymbol)
        print " PWM 0: " + str(self.pwmZeroSymbol)
        print " TX Size: " + str(self.packetSize)
        print "CRC Properties:"
        print " CRC Low Addr: " + str(self.crcLow)
        print " CRC High Addr: " + str(self.crcHigh)
        print " CRC Low Data Addr: " + str(self.crcDataLow)
        print " CRC High Data Addr: " + str(self.crcDataHigh)
        print " CRC Poly: " + str(self.crcPoly)
        print " CRC Init: " + str(self.crcInit)
        print " CRC Bit Order: " + str(self.crcBitOrder) 
        print " CRC Reverse: " + str(self.crcReverseOut)
        print " CRC Final XOR: " + str(self.crcFinalXor)
        print " CRC Pad: " + str(self.crcPad)
        print " CRC Pad Count: " + str(self.crcPadCount)
        print " CRC Pad Val: " + str(self.crcPadVal)
        print " CRC Pad Count Options: " + str(self.crcPadCountOptions)
        print "Stat Properties:"
        print " ID Addr Low: " + str(self.idAddrLow)
        print " ID Addr High: " + str(self.idAddrHigh)
        print " Value 1 Addr Low: " + str(self.val1AddrLow)
        print " value 1 Addr High: " + str(self.val1AddrHigh)
        print " Value 2 Addr Low: " + str(self.val2AddrLow)
        print " value 2 Addr High: " + str(self.val2AddrHigh)
        print " Value 3 Addr Low: " + str(self.val3AddrLow)
        print " value 3 Addr High: " + str(self.val3AddrHigh)
        print "Timing Propertied Re-Calculated in units of samples:"
        print " Unit Width (samples): " + str(self.unitWidth_samp)
        print " Inter-Packet Width (samples): " + str(self.interPacketWidth_samp)
        print " Preamble Symbol Low (samples): " + str(self.preambleSymbolLow_samp)
        print " Preamble Symbol High (samples): " + str(self.preambleSymbolHigh_samp)
        print " Header Width (samples): " + str(self.headerWidth_samp)
        print " PWM 1 Symbol (samples): " + str(self.pwmOneSymbol_samp)
        print " PWM 1 Symbol (samples): " + str(self.pwmZeroSymbol_samp)
        print " PWM Symbol Size (samples): " + str(self.pwmSymbolSize_samp)

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
    print '{:5s} {:5s} {:20s} {:20s}'.format("   ID", "Year", "Name", "Type")
    # get a list of items in database
    for proto in protocolSession.query(ProtocolDefinition):
        print '{:5d} {:5s} {:20s} {:20s}'.format(proto.protocolId, proto.deviceYear, proto.deviceName, wcv.devTypeStrings[proto.deviceType]) 

def fetchProtocol(protocolId):
    global protocolSession
    proto = protocolSession.query(ProtocolDefinition).get(protocolId)
    proto.convertTimingToSamples(wcv.basebandSampleRate)
    return proto

"""
# - export library to a text file(?)
# is this needed?
def exportProtocolToText(protocolId):
    global protocolSession
    proto = protocolSession.query(ProtocolDefinition).get(protocolId)
    # output data to text file (should this be user readable?)
"""    
    
