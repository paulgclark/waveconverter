# these are global defines used throughout the waveConverter app

# protocol library defines
TEMP_PROTOCOL = 0


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

# Manchester encoding
NO_ENCODING = 0
STD_MANCHESTER = 1
INV_MANCHESTER = 2
PWM = 3
ENCODING_OPTIONS = [NO_ENCODING, STD_MANCHESTER, INV_MANCHESTER, PWM]

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
