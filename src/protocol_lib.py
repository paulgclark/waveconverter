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

# PC - vars to make global controls override parts of protocol def:
#   unit_error
#   glitch_filter
from waveConvertVars import *

class ProtocolDefinition:

  def __init__(self):
    self.name = ""

    # error correction properties, can be overridden by user inputs
    self.timing_error = 0
    self.glitch_filter_count = 0

    # for discriminating between packets
    self.interpacket_width_min = 0
    self.interpacket_symbol = DATA_ZERO
    self.preamble_sync = False

    # preamble definition
    self.preamble_symbol_width_low = 0
    self.preamble_symbol_width_high = 0
    self.preamble_size = [1]
      # preambles should be defined arbitrarily; but for now we assume
      # that each one is a regularly repeating sequence

    # header definition
    self.header_level = DATA_ZERO
    self.header_width = 0

    # payload characteristics
    self.unit_width_payload = 0
    self.packet_size = 0
    self.encoding = NO_ENCODING
    
    # pwm parameters, if necessary
    self.pwm_zero_timing = [0, 0]
    self.pwm_one_timing = [0, 0]

    # PACKET DATA STRUCTURE
    self.id_addr_low = 0
    self.id_addr_high = 0
    self.val_addr_low = [0]  # multiple values possible
    self.val_addr_high = [0]

    # CRC parameters
    self.crc_addr_low = 0
    self.crc_addr_high = 0
    self.crc_target_addr_low = 0 # data on which CRC is calculated
    self.crc_target_addr_high = 0
    self.crc_polynomial = [1, 1, 1]
    self.crc_init = [0, 0, 0]
    self.crc_bit_order = CRC_NORM # can also reverse or byte-wise reflect
    self.crc_reverse_output = False
    self.crc_final_xor = [0, 0, 0]
    self.crc_pad = CRC_NOPAD # can also pad to even or pad to absolute
    self.crc_pad_count = 8
    self.crc_pad_val = 0
    self.crc_pad_count_options = [0] # for reversing CRC

