# grab global variables and defines
# execfile('waveConvertVars.py')
from waveConvertVars import *

# The following class contains the packet protocol used in the decoding process. An
# object of this class will be used as the source of all decoding parameters. It will
# be loaded with information from the selected protocol of the packet library. This 
# library will contain a number of pre-loaded protocols and allow for saving user-defined
# protocols as well.
class ProtocolDefinition:
    def __init__(self, interPacketWidth=0, interPacketSymbol=0, unitWidth=0, unitError=0,
                 packetSize=0, preambleSync=0, preambleSymbolHigh=0, preambleSymbolLow=0,
                 preambleSize = [70, 16], headerLevel=0, headerWidth=0, encodingType=0,
                 pwmOneSymbol=[45,245], pwmZeroSymbol=[90,200], pwmSymbolSize=0,
                 glitchFilterCount=0, idAddrLow=0, idAddrHigh=0, valAddrLow=0, valAddrHigh=0,
                 crcLow=0, crcHigh=0, crcDataLow=0, crcDataHigh=0, crcPoly=[1,1,1],
                 crcInit=0, crcBitOrder=0, crcReverseOut=0, crcFinalXor=False,
                 crcPad=0, crcPadCount=0, crcPadVal=0, crcPadCountOptions=0,
                 name="", protocolID=99999):
        self.name = name
        self.protocolID = protocolID
        self.interPacketWidth = interPacketWidth
        self.interPacketSymbol = interPacketSymbol
        self.unitWidth = unitWidth
        self.unitError = unitError
        self.packetSize = packetSize
        self.preambleSync = preambleSync
        self.preambleSymbolHigh = preambleSymbolHigh
        self.preambleSymbolLow = preambleSymbolLow
        self.preambleSize = preambleSize
        self.headerLevel = headerLevel
        self.headerWidth = headerWidth
        self.encodingType = encodingType
        self.pwmOneSymbol = pwmOneSymbol
        self.pwmZeroSymbol = pwmZeroSymbol
        self.pwmSymbolSize = pwmSymbolSize
        self.glitchFilterCount = glitchFilterCount
        self.idAddrLow = idAddrLow
        self.idAddrHigh = idAddrHigh
        self.valAddrLow = valAddrLow
        self.valAddrHigh = valAddrHigh
        self.crcLow = crcLow
        self.crcHigh = crcHigh
        self.crcDataLow = crcDataLow
        self.crcDataHigh = crcDataHigh
        self.crcPoly = crcPoly
        self.crcInit = crcInit
        self.crcBitOrder = crcBitOrder
        self.crcReverseOut = crcReverseOut
        self.crcFinalXor = crcFinalXor
        self.crcPad = crcPad
        self.crcPadCount = crcPadCount
        self.crcPadVal =crcPadVal
        self.crcPadCountOptions = crcPadCountOptions
        
    #def __str__(self):
    #    return "x-value" + str(self.x) + " y-value" + str(self.y)


"""
# The following vars are hard coded globals. Need to move to a class-based model
volvoFobConfig = 0
volvo400 = 0
chevyFobConfig = 1
chevy400 = 0
civicFobConfig = 0
highlanderFobConfig = 0
infinitiFob = 0
chevyTPM400 = 0
tahoeTPM400 = 0

if volvoFobConfig:
    # packet and waveform specific items
    INTERPACKET_WIDTH = 1000
    INTERPACKET_SYMBOL = DATA_ZERO
    UNIT_WIDTH = 160
    UNIT_ERROR = 0.2
    PACKET_SIZE = 71

    # this defines one cycle of preamble timing
    PREAMBLE_SYNC = False
    PREAMBLE_SYMBOL_HIGH = UNIT_WIDTH
    PREAMBLE_SYMBOL_LOW = UNIT_WIDTH
    # some preambles have multiple valid lengths, especially if a cluster
    # of identical packets are sent; in this case, put the preamble count
    # of the initial packet in the first list position, with the preamble
    # count of the successive packets in the second list position
    PREAMBLE_SIZE = [70, 16]

    # header follows preamble and is typically longer than the data width
    HEADER_LEVEL = DATA_ZERO
    HEADER_WIDTH = 4*UNIT_WIDTH

    # Manchester or PWM encoding
    #ENCODING = NO_ENCODING
    ENCODING = STD_MANCHESTER
    #ENCODING = INV_MANCHESTER
    #ENCODING = PWM

    # PWM parameters; both symbols should be the same size
    PWM_ONE_SYMBOL = [45, 245]
    PWM_ZERO_SYMBOL = [90, 200]
    PWM_SYMBOL_SIZE = sum(PWM_ONE_SYMBOL)

    # size of glitches (in samples) that will be filtered out
    GLITCH_FILTER_COUNT = 4

    #####################
    # statistics controls
    #ID_ADDR_LOW = 33
    #ID_ADDR_HIGH = 65
    ID_ADDR_LOW = 66
    ID_ADDR_HIGH = 67
    VAL_ADDR_LOW = 24
    VAL_ADDR_HIGH = 31

    #####################
    # CRC parameters
    CRC_LOW = 66
    CRC_HIGH = 67
    CRC_DATA_LOW = 1
    CRC_DATA_HIGH = 32
    CRC_POLY = [1, 1, 1]
    CRC_INIT = 0
    CRC_BIT_ORDER = CRC_NORM
    #CRC_BIT_ORDER = CRC_REVERSE
    #CRC_BIT_ORDER = CRC_REFLECT
    CRC_REVERSE_OUT = False
    CRC_FINAL_XOR = [0, 1]
    CRC_PAD = CRC_NOPAD
    #CRC_PAD = CRC_PAD_TO_EVEN
    #CRC_PAD = CRC_PAD_ABS
    CRC_PAD_COUNT = 8
    CRC_PAD_VAL = 0
    #CRC_PAD_COUNT_OPTIONS = [0, 8, 16, 32]
    CRC_PAD_COUNT_OPTIONS = [0]

elif volvo400:
    # packet and waveform specific items
    INTERPACKET_WIDTH = 2000
    INTERPACKET_SYMBOL = DATA_ZERO
    UNIT_WIDTH = 320
    UNIT_ERROR = 0.2
    PACKET_SIZE = 71

    # this defines one cycle of preamble timing
    PREAMBLE_SYNC = False
    PREAMBLE_SYMBOL_HIGH = UNIT_WIDTH
    PREAMBLE_SYMBOL_LOW = UNIT_WIDTH
    # some preambles have multiple valid lengths, especially if a cluster
    # of identical packets are sent; in this case, put the preamble count
    # of the initial packet in the first list position, with the preamble
    # count of the successive packets in the second list position
    PREAMBLE_SIZE = [70, 16]

    # header follows preamble and is typically longer than the data width
    HEADER_LEVEL = DATA_ZERO
    HEADER_WIDTH = 5*UNIT_WIDTH # should be 4, kludge; fix main code

    # Manchester or PWM encoding
    #ENCODING = NO_ENCODING
    ENCODING = STD_MANCHESTER
    #ENCODING = INV_MANCHESTER
    #ENCODING = PWM

    # PWM parameters; both symbols should be the same size
    PWM_ONE_SYMBOL = [45, 245]
    PWM_ZERO_SYMBOL = [90, 200]
    PWM_SYMBOL_SIZE = sum(PWM_ONE_SYMBOL)

    # size of glitches (in samples) that will be filtered out
    GLITCH_FILTER_COUNT = 4

    #####################
    # statistics controls
    #ID_ADDR_LOW = 33
    #ID_ADDR_HIGH = 65
    ID_ADDR_LOW = 66
    ID_ADDR_HIGH = 67
    VAL_ADDR_LOW = 24
    VAL_ADDR_HIGH = 31

    #####################
    # CRC parameters
    CRC_LOW = 66
    CRC_HIGH = 67
    CRC_DATA_LOW = 1
    CRC_DATA_HIGH = 32
    CRC_POLY = [1, 1, 1]
    CRC_INIT = 0
    CRC_BIT_ORDER = CRC_NORM
    #CRC_BIT_ORDER = CRC_REVERSE
    #CRC_BIT_ORDER = CRC_REFLECT
    CRC_REVERSE_OUT = False
    CRC_FINAL_XOR = [0, 1]
    CRC_PAD = CRC_NOPAD
    #CRC_PAD = CRC_PAD_TO_EVEN
    #CRC_PAD = CRC_PAD_ABS
    CRC_PAD_COUNT = 8
    CRC_PAD_VAL = 0
    #CRC_PAD_COUNT_OPTIONS = [0, 8, 16, 32]
    CRC_PAD_COUNT_OPTIONS = [0]

elif chevyFobConfig:
    # packet and waveform specific items
    TEMP_FUDGE_FACTOR = 2
    INTERPACKET_WIDTH = 1000
    INTERPACKET_SYMBOL = DATA_ZERO
    UNIT_WIDTH = 45 * TEMP_FUDGE_FACTOR
    UNIT_ERROR = 0.2
    PACKET_SIZE = 67

    # this defines one cycle of preamble timing
    PREAMBLE_SYNC = False
    PREAMBLE_SYMBOL_HIGH = 50 * TEMP_FUDGE_FACTOR
    PREAMBLE_SYMBOL_LOW = 100 * TEMP_FUDGE_FACTOR
    # some preambles have multiple valid lengths
    PREAMBLE_SIZE = [10]

    # header follows preamble and is typically longer than the data width
    HEADER_LEVEL = DATA_ZERO
    HEADER_WIDTH = 480 * TEMP_FUDGE_FACTOR

    # Manchester or PWM encoding
    ENCODING = PWM

    # PWM parameters; both symbols should be the same size
    PWM_ZERO_SYMBOL = [45*TEMP_FUDGE_FACTOR, 245*TEMP_FUDGE_FACTOR]
    PWM_ONE_SYMBOL = [90*TEMP_FUDGE_FACTOR, 200*TEMP_FUDGE_FACTOR]
    PWM_SYMBOL_SIZE = sum(PWM_ONE_SYMBOL)

    # size of glitches (in samples) that will be filtered out
    GLITCH_FILTER_COUNT = 4

    #####################
    # statistics controls
    #ID_ADDR_LOW = 33
    #ID_ADDR_HIGH = 65
    ID_ADDR_LOW = 66
    ID_ADDR_HIGH = 67
    VAL_ADDR_LOW = 24
    VAL_ADDR_HIGH = 31

    # CRC parameters
    CRC_LOW = 65
    CRC_HIGH = 66
    CRC_DATA_LOW = 0
    CRC_DATA_HIGH = 31
    CRC_POLY = [1, 0, 1]
    CRC_INIT = 0
    #CRC_BIT_ORDER = CRC_NORM
    #CRC_BIT_ORDER = CRC_REVERSE
    CRC_BIT_ORDER = CRC_REFLECT
    CRC_REVERSE_OUT = False
    CRC_FINAL_XOR = [0, 0] 
    CRC_PAD = CRC_NOPAD
    #CRC_PAD = CRC_PAD_TO_EVEN
    #CRC_PAD = CRC_PAD_ABS
    CRC_PAD_COUNT = 8
    CRC_PAD_VAL = 0
    CRC_PAD_COUNT_OPTIONS = [0, 8, 16, 32]
    #CRC_PAD_COUNT_OPTIONS = [0]

elif chevy400:
    # packet and waveform specific items
    INTERPACKET_WIDTH = 2000
    INTERPACKET_SYMBOL = DATA_ZERO
    UNIT_WIDTH = 90
    UNIT_ERROR = 0.2
    PACKET_SIZE = 67

    # this defines one cycle of preamble timing
    PREAMBLE_SYNC = False
    PREAMBLE_SYMBOL_HIGH = 100
    PREAMBLE_SYMBOL_LOW = 200
    # some preambles have multiple valid lengths
    PREAMBLE_SIZE = [10]

    # header follows preamble and is typically longer than the data width
    HEADER_LEVEL = DATA_ZERO
    HEADER_WIDTH = 960

    # Manchester or PWM encoding
    ENCODING = PWM

    # PWM parameters; both symbols should be the same size
    PWM_ZERO_SYMBOL = [90, 490]
    PWM_ONE_SYMBOL = [180, 400]
    PWM_SYMBOL_SIZE = sum(PWM_ONE_SYMBOL)

    # size of glitches (in samples) that will be filtered out
    GLITCH_FILTER_COUNT = 4

    #####################
    # statistics controls
    #ID_ADDR_LOW = 33
    #ID_ADDR_HIGH = 65
    ID_ADDR_LOW = 66
    ID_ADDR_HIGH = 67
    VAL_ADDR_LOW = 24
    VAL_ADDR_HIGH = 31

    # CRC parameters
    CRC_LOW = 65
    CRC_HIGH = 66
    CRC_DATA_LOW = 0
    CRC_DATA_HIGH = 31
    CRC_POLY = [1, 0, 1]
    CRC_INIT = 0
    #CRC_BIT_ORDER = CRC_NORM
    #CRC_BIT_ORDER = CRC_REVERSE
    CRC_BIT_ORDER = CRC_REFLECT
    CRC_REVERSE_OUT = False
    CRC_FINAL_XOR = [0, 0] 
    CRC_PAD = CRC_NOPAD
    #CRC_PAD = CRC_PAD_TO_EVEN
    #CRC_PAD = CRC_PAD_ABS
    CRC_PAD_COUNT = 8
    CRC_PAD_VAL = 0
    CRC_PAD_COUNT_OPTIONS = [0, 8, 16, 32]
    #CRC_PAD_COUNT_OPTIONS = [0]

elif civicFobConfig:
    # packet and waveform specific items
    INTERPACKET_WIDTH = 120 # this is too small, need a resync capability
    INTERPACKET_SYMBOL = DATA_ZERO
    UNIT_WIDTH = 45
    UNIT_ERROR = 0.2
    PACKET_SIZE = 67

    # this defines one cycle of preamble timing
    PREAMBLE_SYNC = True
    PREAMBLE_SYMBOL_HIGH = 41
    PREAMBLE_SYMBOL_LOW = 41
    # some preambles have multiple valid lengths
    PREAMBLE_SIZE = [16]

    # header follows preamble and is typically longer than the data width
    HEADER_LEVEL = DATA_ZERO
    HEADER_WIDTH = 147

    # Manchester or PWM encoding
    ENCODING = STD_MANCHESTER

    # Next section unused
    # PWM parameters; both symbols should be the same size
    PWM_ZERO_SYMBOL = [45, 245]
    PWM_ONE_SYMBOL = [90, 200]
    PWM_SYMBOL_SIZE = sum(PWM_ONE_SYMBOL)

    # size of glitches (in samples) that will be filtered out
    GLITCH_FILTER_COUNT = 4

    #####################
    # statistics controls
    #ID_ADDR_LOW = 33
    #ID_ADDR_HIGH = 65
    ID_ADDR_LOW = 66
    ID_ADDR_HIGH = 67
    VAL_ADDR_LOW = 24
    VAL_ADDR_HIGH = 31

    # CRC parameters
    CRC_LOW = 65
    CRC_HIGH = 66
    CRC_DATA_LOW = 0
    CRC_DATA_HIGH = 31
    CRC_POLY = [1, 0, 1]
    CRC_INIT = 0
    #CRC_BIT_ORDER = CRC_NORM
    #CRC_BIT_ORDER = CRC_REVERSE
    CRC_BIT_ORDER = CRC_REFLECT
    CRC_REVERSE_OUT = False
    CRC_FINAL_XOR = [0, 0] 
    CRC_PAD = CRC_NOPAD
    #CRC_PAD = CRC_PAD_TO_EVEN
    #CRC_PAD = CRC_PAD_ABS
    CRC_PAD_COUNT = 8
    CRC_PAD_VAL = 0
    CRC_PAD_COUNT_OPTIONS = [0, 8, 16, 32]
    #CRC_PAD_COUNT_OPTIONS = [0]

elif chevyTPM400:
    # packet and waveform specific items
    INTERPACKET_WIDTH = 2000
    INTERPACKET_SYMBOL = DATA_ZERO
    UNIT_WIDTH = 72
    UNIT_ERROR = 0.2
    PACKET_SIZE = 34

    # this defines one cycle of preamble timing
    PREAMBLE_SYNC = False
    PREAMBLE_SYMBOL_HIGH = 144
    PREAMBLE_SYMBOL_LOW = 72
    # some preambles have multiple valid lengths
    PREAMBLE_SIZE = [5]

    # header follows preamble and is typically longer than the data width
    HEADER_LEVEL = DATA_ZERO
    HEADER_WIDTH = 216

    # Manchester or PWM encoding
    ENCODING = PWM

    # PWM parameters; both symbols should be the same size
    PWM_ZERO_SYMBOL = [72, 144]
    PWM_ONE_SYMBOL = [144, 72]
    PWM_SYMBOL_SIZE = sum(PWM_ONE_SYMBOL)

    # size of glitches (in samples) that will be filtered out
    GLITCH_FILTER_COUNT = 4

    #####################
    # statistics controls
    #ID_ADDR_LOW = 33
    #ID_ADDR_HIGH = 65
    ID_ADDR_LOW = 66
    ID_ADDR_HIGH = 67
    VAL_ADDR_LOW = 24
    VAL_ADDR_HIGH = 31

    # CRC parameters
    CRC_LOW = 65
    CRC_HIGH = 66
    CRC_DATA_LOW = 0
    CRC_DATA_HIGH = 31
    CRC_POLY = [1, 0, 1]
    CRC_INIT = 0
    #CRC_BIT_ORDER = CRC_NORM
    #CRC_BIT_ORDER = CRC_REVERSE
    CRC_BIT_ORDER = CRC_REFLECT
    CRC_REVERSE_OUT = False
    CRC_FINAL_XOR = [0, 0] 
    CRC_PAD = CRC_NOPAD
    #CRC_PAD = CRC_PAD_TO_EVEN
    #CRC_PAD = CRC_PAD_ABS
    CRC_PAD_COUNT = 8
    CRC_PAD_VAL = 0
    CRC_PAD_COUNT_OPTIONS = [0, 8, 16, 32]
    #CRC_PAD_COUNT_OPTIONS = [0]

elif tahoeTPM400:
    # packet and waveform specific items
    INTERPACKET_WIDTH = 2000
    INTERPACKET_SYMBOL = DATA_ZERO
    UNIT_WIDTH = 44
    UNIT_ERROR = 0.4
    PACKET_SIZE = 34

    # this defines one cycle of preamble timing
    PREAMBLE_SYNC = True
    PREAMBLE_SYMBOL_HIGH = UNIT_WIDTH
    PREAMBLE_SYMBOL_LOW = UNIT_WIDTH
    # some preambles have multiple valid lengths
    PREAMBLE_SIZE = [40]

    # header follows preamble and is typically longer than the data width
    HEADER_LEVEL = DATA_NULL # no header
    HEADER_WIDTH = 0

    # Manchester or PWM encoding
    ENCODING = INV_MANCHESTER

    # PWM parameters; both symbols should be the same size
    PWM_ZERO_SYMBOL = [72, 144]
    PWM_ONE_SYMBOL = [144, 72]
    PWM_SYMBOL_SIZE = sum(PWM_ONE_SYMBOL)

    # size of glitches (in samples) that will be filtered out
    GLITCH_FILTER_COUNT = 4

    #####################
    # statistics controls
    #ID_ADDR_LOW = 33
    #ID_ADDR_HIGH = 65
    ID_ADDR_LOW = 66
    ID_ADDR_HIGH = 67
    VAL_ADDR_LOW = 24
    VAL_ADDR_HIGH = 31

    # CRC parameters
    CRC_LOW = 65
    CRC_HIGH = 66
    CRC_DATA_LOW = 0
    CRC_DATA_HIGH = 31
    CRC_POLY = [1, 0, 1]
    CRC_INIT = 0
    #CRC_BIT_ORDER = CRC_NORM
    #CRC_BIT_ORDER = CRC_REVERSE
    CRC_BIT_ORDER = CRC_REFLECT
    CRC_REVERSE_OUT = False
    CRC_FINAL_XOR = [0, 0] 
    CRC_PAD = CRC_NOPAD
    #CRC_PAD = CRC_PAD_TO_EVEN
    #CRC_PAD = CRC_PAD_ABS
    CRC_PAD_COUNT = 8
    CRC_PAD_VAL = 0
    CRC_PAD_COUNT_OPTIONS = [0, 8, 16, 32]
    #CRC_PAD_COUNT_OPTIONS = [0]

elif highlanderFobConfig:
    # packet and waveform specific items
    INTERPACKET_WIDTH = 120 # this is too small, need a resync capability
    INTERPACKET_SYMBOL = DATA_ZERO
    UNIT_WIDTH = 140
    UNIT_ERROR = 0.2
    PACKET_SIZE = 248

    # this defines one cycle of preamble timing
    PREAMBLE_SYNC = True
    PREAMBLE_SYMBOL_HIGH = UNIT_WIDTH
    PREAMBLE_SYMBOL_LOW = UNIT_WIDTH
    # some preambles have multiple valid lengths
    PREAMBLE_SIZE = [8]

    # header follows preamble and is typically longer than the data width
    HEADER_LEVEL = DATA_NULL # no header
    HEADER_WIDTH = 147

    # Manchester or PWM encoding
    ENCODING = STD_MANCHESTER

    # Next section unused
    # PWM parameters; both symbols should be the same size
    PWM_ZERO_SYMBOL = [45, 245]
    PWM_ONE_SYMBOL = [90, 200]
    PWM_SYMBOL_SIZE = sum(PWM_ONE_SYMBOL)

    # size of glitches (in samples) that will be filtered out
    GLITCH_FILTER_COUNT = 4

    #####################
    # statistics controls
    #ID_ADDR_LOW = 33
    #ID_ADDR_HIGH = 65
    ID_ADDR_LOW = 66
    ID_ADDR_HIGH = 67
    VAL_ADDR_LOW = 24
    VAL_ADDR_HIGH = 31

    # CRC parameters
    CRC_LOW = 65
    CRC_HIGH = 66
    CRC_DATA_LOW = 0
    CRC_DATA_HIGH = 31
    CRC_POLY = [1, 0, 1]
    CRC_INIT = 0
    #CRC_BIT_ORDER = CRC_NORM
    #CRC_BIT_ORDER = CRC_REVERSE
    CRC_BIT_ORDER = CRC_REFLECT
    CRC_REVERSE_OUT = False
    CRC_FINAL_XOR = [0, 0] 
    CRC_PAD = CRC_NOPAD
    #CRC_PAD = CRC_PAD_TO_EVEN
    #CRC_PAD = CRC_PAD_ABS
    CRC_PAD_COUNT = 8
    CRC_PAD_VAL = 0
    CRC_PAD_COUNT_OPTIONS = [0, 8, 16, 32]
    #CRC_PAD_COUNT_OPTIONS = [0]

elif infinitiFob:
    # packet and waveform specific items
    INTERPACKET_WIDTH = 120 # this is too small, need a resync capability
    INTERPACKET_SYMBOL = DATA_ZERO
    UNIT_WIDTH = 82
    UNIT_ERROR = 0.2
    PACKET_SIZE = 248

    # this defines one cycle of preamble timing
    PREAMBLE_SYNC = True
    PREAMBLE_SYMBOL_HIGH = UNIT_WIDTH
    PREAMBLE_SYMBOL_LOW = UNIT_WIDTH
    # some preambles have multiple valid lengths
    PREAMBLE_SIZE = [15]

    # header follows preamble and is typically longer than the data width
    HEADER_LEVEL = DATA_ONE # no header
    HEADER_WIDTH = 300

    # Manchester or PWM encoding
    ENCODING = STD_MANCHESTER

    # Next section unused
    # PWM parameters; both symbols should be the same size
    PWM_ZERO_SYMBOL = [45, 245]
    PWM_ONE_SYMBOL = [90, 200]
    PWM_SYMBOL_SIZE = sum(PWM_ONE_SYMBOL)

    # size of glitches (in samples) that will be filtered out
    GLITCH_FILTER_COUNT = 4

    #####################
    # statistics controls
    #ID_ADDR_LOW = 33
    #ID_ADDR_HIGH = 65
    ID_ADDR_LOW = 66
    ID_ADDR_HIGH = 67
    VAL_ADDR_LOW = 24
    VAL_ADDR_HIGH = 31

    # CRC parameters
    CRC_LOW = 65
    CRC_HIGH = 66
    CRC_DATA_LOW = 0
    CRC_DATA_HIGH = 31
    CRC_POLY = [1, 0, 1]
    CRC_INIT = 0
    #CRC_BIT_ORDER = CRC_NORM
    #CRC_BIT_ORDER = CRC_REVERSE
    CRC_BIT_ORDER = CRC_REFLECT
    CRC_REVERSE_OUT = False
    CRC_FINAL_XOR = [0, 0] 
    CRC_PAD = CRC_NOPAD
    #CRC_PAD = CRC_PAD_TO_EVEN
    #CRC_PAD = CRC_PAD_ABS
    CRC_PAD_COUNT = 8
    CRC_PAD_VAL = 0
    CRC_PAD_COUNT_OPTIONS = [0, 8, 16, 32]
    #CRC_PAD_COUNT_OPTIONS = [0]



# if no config has been specified, then just quit
else:
    exit(0)
"""