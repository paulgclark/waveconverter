from breakWave import breakdownWaveform
from widthToBits import decodePacket
from waveconverterEngine import packetsToFormattedString
from iqFileArgParse import iqFileObject

# these are global defines and vars used throughout the waveConverter app
verbose = False
verboseZoom = False
bbOutFileName = "../output_files/waveform_out_file.bb"
outputHex = False
protocol_number = 0
runWithGui = True
waveformFileName = ""
outFileName = ""
buildNewDatabase = False
saveBasebandToFile = False
argcHelp = False

# we'll only be working on one transmission at a time, so these are global
basebandData = []
basebandDataByTx = [] # broken down by individual transmissions
payloadList = ""
decodeOutputString = ""
bitProbString = ""
bitProbList = []

# these variable maintain the zoom and waveform window positions
tMin = 0.0
tMax = 100.0
txNum = 0

# these global variables are associated with the current IQ File, not any
# specific protocol
# NEED: extract these from the filename if formatted with "c100M" or "s8M"
iqFileName = ""
inputFileObject = None
center_freq = 0.0
samp_rate = 0.0
glitchFilterCount = 2
timingError = 0.20
showAllTx = True
timeBetweenTx = -1 # this value overrides that of the protocol; -1 means no value has been passed
frequency = -1.0 # another override value
threshold = -0.1 # another override value
squelch = -1.0 # another override value

# this value is used for the sample rate of the digital baseband file
basebandSampleRate = 100000.0  #100000.0*10#5 # good default rate

# GUI parameters
NUM_ID_FIELDS = 6
NUM_VAL_FIELDS = 3
NUM_CRC = 2
NUM_ACS = 2

# define a global protocol variable
from protocol_lib import ProtocolDefinition
protocol = ProtocolDefinition(-1)

# global transmission list; this will be cleared each time the decode or demod button 
# is clicked 
txList = []

devTypeStrings = {0 : "Unknown",
                  1 : "Key Fob", 
                  2 : "TPM Sensor", 
                  3 : "Fan Controller", 
                  4 : "RC Vehicle", 
                  5 : "Weather Station"}

# protocol library defines
TEMP_PROTOCOL = 0

# RF defines
MOD_UNDEFINED = -1
MOD_OOK = 0
MOD_FSK = 1
MOD_FSK_HOP = 2

# parameter types for import
PARAM_BOOL = 0
PARAM_INT = 1
PARAM_FLOAT = 2
PARAM_STR = 3
PARAM_LIST = 4

# enumerated type for symbols
#from enum import Enum
#class symbolType(Enum):
ILLEGAL_VALUE = -4
BAD_WIDTH = -3
END_OF_FILE = -1
DATA_ZERO = 0
DATA_ONE = 1
DATA_NULL = 2

GOOD_WIDTH = 1
UNIT_1X = 1
UNIT_2X = 2

# for tracking the state in the main loop state machine
#class engineState(Enum):
PREAMBLE_STATE = 1
HEADER_STATE = 2
DATA_STATE = 3
BETWEEN_PACKETS_STATE = 4

# preamble types
PREAMBLE_REG = 0
PREAMBLE_ARB = 1
PREAMBLE_CNT = 2

# Manchester encoding
NO_ENCODING = 0
STD_MANCHESTER = 1
INV_MANCHESTER = 2
PWM = 3
PAIRED00_01 = 4
ENCODING_OPTIONS = [NO_ENCODING, STD_MANCHESTER, INV_MANCHESTER, PWM, PAIRED00_01]

# CRC Status
CRC_PASS = 1
CRC_FAIL = 0

# CRC input bit order
CRC_NORM = 0 # data bits are processed from MSB to LSB
CRC_REVERSE = 1 # data bits are processed from LSB to MSB
CRC_REFLECT = 2 # data processed from MSByte to LSByte, but each byte reversed
CRC_BIT_ORDER_OPTIONS = [CRC_NORM, CRC_REVERSE, CRC_REFLECT]

# different options to pad the packet
CRC_NOPAD = 0
CRC_PAD_TO_EVEN = 1 # pad packet so it will be an even multiple of the pad count
CRC_PAD_ABS = 2 # pad packet with pad count worth of bits
CRC_PAD_OPTIONS = [CRC_NOPAD, CRC_PAD_TO_EVEN, CRC_PAD_ABS]

def stringToIntegerList(inputString):
    listString = inputString.strip('[]') # resolves to string of comma-separated values
    listItemsText = listString.split(',')
    tempList = []
        
    # first check if we have an empty list
    if not listItemsText or listItemsText == ['']:
        return []
        
    # otherwise build the list and return it
    for item in listItemsText:
        tempList.append(int(item))
    return tempList
