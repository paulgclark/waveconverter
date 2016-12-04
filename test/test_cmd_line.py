import os
from IPython.core.payload import PayloadManager
os.chdir('../src')
import sys
sys.path.append(os.getcwd())
import unittest
__unittest = True
import waveConvertVars as wcv
import waveconverterEngine as weng
from gnuradio import eng_notation
from protocol_lib import ProtocolDefinition, getNextProtocolId
from protocol_lib import protocolSession
from protocol_lib import fetchProtocol
from waveconverterEngine import demodIQFile
from waveconverterEngine import buildTxList
from waveconverterEngine import decodeAllTx
from statEngine import computeStats
from statEngine import buildStatStrings

# used to suppress stdout for waveconverter execution
import cStringIO
# for executing the command line and re-directing output to a string
import subprocess
# for searching through output text file
import re

# globals
debug = False

class TestCommandLine(unittest.TestCase):
        
    def setUp(self):
        self.verbose = False

        # we will then turn it back on for unittest output
        saved_stdout = sys.stdout
        if not self.verbose:
            sys.stdout = cStringIO.StringIO()

        os.chdir('../src')
        os.system("./packet_decode.py -p 4 -b ../input_files/weather_s100k.bb > ../test/tmp/tmp_output.txt")
        os.chdir('../test')

        # now read back the info contained in the temp file
        self.outputString = open("./tmp/tmp_output.txt", 'r').read()
 
        # turn stdout back on
        if not self.verbose:
            sys.stdout = saved_stdout
        
        pass
        

    # grep through the output to confirm that the expected transmissions are there
    def test_compareCmdLineOutput(self):

        regexStringList = []
        # check that the two transmissions are correctly output
        regexStringList.append(r"1\s+11010111\s+11101000\s+11100010\s+11101010\s+00101110\s+01")
        regexStringList.append(r"2\s+11010111\s+11101000\s+11100010\s+11101010\s+00101110\s+01")
        # check that the ID count is correct
        regexStringList.append(r"Count\s+ID\s+2\s+0101")

        for regexString in regexStringList:
            self.assertRegexpMatches(self.outputString, regexString)
        
        pass
        

if __name__ == '__main__':
    unittest.main()

