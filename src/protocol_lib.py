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

from waveConvertVars import *
from sqlalchemy import *

#from sqlalchemy import Column, Integer, Unicode, UnicodeText, String
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy import Column, ForeignKey, Integer, String, PickleType
from sqlalchemy.sql import func

#from random import choice
#from string import letters
#from IPython.core.magics import namespace

# set up the connection to the protocol library sqllite database
engine = create_engine('sqlite:///protocol_library.db', echo=True)
Base = declarative_base(bind=engine)

# create session to connect to database containing stored protocol definitions 
Base.metadata.create_all()
Session = sessionmaker(bind=engine)
protocolSession = Session() # this is a global variable used by many protocol_lib functions

# define sqlalchemy class for storage of protocol object
class ProtocolDefinition(Base):
    __tablename__ = 'protocols'
    
    # waveconverter protocol library vars
    protocolId = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
      
    # RF demodulation vars
    frequency = Column(Integer)
    fsk_deviation = Column(String(250))
        
    # framing vars
    interPacketWidth = Column(Integer)
    interPacketSymbol = Column(Integer)
    preambleSymbolHigh = Column(Integer)
    preambleSymbolLow = Column(Integer)
    preambleSize = Column(PickleType) # list some preambles have different lengths
    headerLevel = Column(Integer)
    headerWidth = Column(Integer)
    packetSize = Column(Integer)
    preambleSync = Column(Integer)
        
    # timing vars
    unitWidth = Column(Integer)
    unitError = Column(Integer)
    encodingType = Column(Integer)
    pwmOneSymbol = Column(PickleType) # list with two elements
    pwmZeroSymbol = Column(PickleType) # list with two elements
    pwmSymbolSize = Column(Integer)
        
        # waveconverter filter vars
    glitchFilterCount = Column(Integer)
        
        # payload addresses for statistical analysis
    idAddrLow = Column(Integer)
    idAddrHigh = Column(Integer)
    valAddrLow = Column(Integer)
    valAddrHigh = Column(Integer)
        
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
    crcPadVal =Column(Integer)
    crcPadCountOptions = Column(PickleType) # list
    
    def __init__(self, protocolId):
        self.protocolId = protocolId # maybe search through database to find max value and +1
        # the rest of the features must be generated manually
    
    def printProtocolMinimal(self):
        print "protocolId:" + str(self.protocolId)
        print "name:" + str(self.name)
        
    def printProtocolFull(self):
        print "protocolId:" + str(self.protocolId)
        print "name:" + str(self.name)

    # - write modified protocol to disk
    def saveProtocol(self):
        global protocolSession
        protocolSession.merge(self)
        protocolSession.commit()

# The following functions perform higher level database manipulations    
# this method finds the next available ID that can be used for a new protocol
def getNextProtocolId():
    global protocolSession
    query = protocolSession.query(func.max(ProtocolDefinition.protocolId).label("maxId"))
    return query.one().maxId + 1
        
# - return size of library (number of protocol definitions)
def getProtocolCount():
    global protocolSession
    query = protocolSession.query(func.count(ProtocolDefinition.protocolId).label("numIDs"))
    return query.one().numIDs

       
# - return list of library elements, including the key parameters
def listProtocols():
    global protocolSession
    print "ID    Name          Mode      Encoding"
    # get a list of items in database
    for proto in protocolSession.query(ProtocolDefinition):
        print proto.protocolId, proto.name

def fetchProtocol(protocolId):
    global protocolSession
    proto = protocolSession.query(ProtocolDefinition).get(protocolId)
    return proto

# - export library to a text file(?)
# is this needed?
    