import os
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

# globals
debug = False
#debug = True

class TestFullFlow(unittest.TestCase):
    def loadBasicTestParameters(self):
        self.verbose = False
        self.samp_rate = 830e3
        self.center_freq = 304.55e6
        self.basebandSampleRate = 100e3
        self.iqFileName = "../input_files/fan_all_dip1101_pruned_dec_c304p55M_s830k.iq"
        self.waveformFileName = ""
        self.outputHex = False
        self.timingError = 0.2
        self.showAllTx = False
        self.timeBetweenTx = 3000
        self.timeBetweenTx_samp = self.timeBetweenTx * self.basebandSampleRate / 1e6
        self.frequency = 304.48e6
        self.glitchFilterCount = 2
        self.threshold = 0.05
        
        # set up globals
        wcv.samp_rate = self.samp_rate
        wcv.basebandSampleRate = self.basebandSampleRate
        
        # load protocol
        self.protocol = fetchProtocol(3)
        
        return(0)
        
    def loadExpectedData(self):
        # build list of expected values
        self.expectedPayloadData = []
        for n in xrange(15):
            self.expectedPayloadData.append([1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0]) # 0-14
        for n in xrange(15):
            self.expectedPayloadData.append([1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0]) # 15-29
        self.expectedPayloadData.append([])                                       # 30
        for n in xrange(8):
            self.expectedPayloadData.append([1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0]) # 31-38
        self.expectedPayloadData.append([])                                       # 39
        self.expectedPayloadData.append([])                                       # 40
        for n in xrange(4):
            self.expectedPayloadData.append([1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0]) # 41-44
        self.expectedPayloadData.append([])                                       # 45
        for n in xrange(8):
            self.expectedPayloadData.append([1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0]) # 46-53
        for n in xrange(15):
            self.expectedPayloadData.append([1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1]) # 54-68
            
        return(0)
        
    def setUp(self):
        # load setup values
        self.loadBasicTestParameters()
        # load expected values for comparison
        self.loadExpectedData()

        # suppress stdio during waveconverter execution by shunting it to a string object
        # we will then turn it back on for unittest output
        saved_stdout = sys.stdout
        if not self.verbose and not debug:
            sys.stdout = cStringIO.StringIO()
 
        # demodulate
        self.basebandData = demodIQFile(verbose = self.verbose,
                                        modulationType = self.protocol.modulation,
                                        iqSampleRate = self.samp_rate,
                                        basebandSampleRate = self.basebandSampleRate,
                                        centerFreq = self.center_freq,
                                        frequency = self.frequency,
                                        channelWidth = self.protocol.channelWidth,
                                        transitionWidth = self.protocol.transitionWidth,
                                        threshold = self.threshold,
                                        fskDeviation = self.protocol.fskDeviation,
                                        fskSquelch = self.protocol.fskSquelchLeveldB,
                                        frequencyHopList = self.protocol.frequencyHopList,
                                        iqFileName = self.iqFileName,
                                        waveformFileName = self.waveformFileName)

        # split transmissions
        self.txList = buildTxList(basebandData = self.basebandData,
                                  basebandSampleRate =  self.basebandSampleRate,
                                  interTxTiming = self.timeBetweenTx_samp,
                                  glitchFilterCount = self.glitchFilterCount,
                                  interTxLevel = self.protocol.interPacketSymbol,
                                  verbose = self.verbose)    

        # decode
        (self.txList, self.decodeOutputString) = decodeAllTx(protocol = self.protocol, 
                                                             txList = self.txList, 
                                                             outputHex = self.outputHex,
                                                             timingError = self.timingError,
                                                             glitchFilterCount = self.glitchFilterCount,
                                                             verbose = self.verbose,
                                                             showAllTx = self.showAllTx)
        
        # compute stats
        (self.bitProbList, self.idListMaster, self.valListMaster, self.payloadLenList) = computeStats(txList = self.txList, 
                                                                                                      protocol = self.protocol, 
                                                                                                      showAllTx = self.showAllTx)
        # compute stat string
        (self.bitProbString, self.idStatString, self.valuesString) = buildStatStrings(self.bitProbList, 
                                                                                      self.idListMaster, 
                                                                                      self.valListMaster, 
                                                                                      self.payloadLenList, 
                                                                                      self.outputHex)

        # turn stdout back on
        if not self.verbose and not debug:
            sys.stdout = saved_stdout
        
        pass
        

    # compare transmissions to expected
    def test_compareTx(self):
        for (i, tx) in enumerate(self.txList):
            if debug:
                print tx.framingValid
                print "TX-" + str(i) + ": (expected followed by actual)"
                print self.expectedPayloadData[i]
                print tx.fullBasebandData
            self.assertListEqual(tx.fullBasebandData, self.expectedPayloadData[i], "Bit comparison Error on TX#" + str(i))
            i += 1
        pass
        
    def test_framing(self):
        # build list of expected values
        expected = []
        for n in xrange(30):
            # preamble, header, framing, encoding, crc, txValid
            expected.append([True, True, True, True, True, True])    # 0-29
        expected.append([False, False, False, False, False, False])   # 30
        for n in xrange(8):
            expected.append([True, True, True, True, True, True])    # 31-38
        expected.append([False, False, False, False, False, False])   # 39
        expected.append([False, False, False, False, False, False])   # 40
        for n in xrange(4):
            expected.append([True, True, True, True, True, True])    # 41-44
        expected.append([False, False, False, False, False, False])    # 45
        for n in xrange(23):
            expected.append([True, True, True, True, True, True])    # 46-68
        
        i = 0
        for tx in self.txList:
            if debug:
                print str(i) + str(tx.preambleValid) + str(tx.headerValid) + str(tx.framingValid) + \
                      str(tx.encodingValid) + str(tx.crcValid) + str(tx.txValid)
            self.assertEqual(tx.preambleValid, expected[i][0], "Preamble Valid mismatch on TX#" + str(i))
            self.assertEqual(tx.headerValid, expected[i][1], "Header Valid mismatch on TX#" + str(i))
            self.assertEqual(tx.framingValid, expected[i][2], "Framing Valid mismatch on TX#" + str(i))
            self.assertEqual(tx.encodingValid, expected[i][3], "Encoding Valid mismatch on TX#" + str(i))
            self.assertEqual(tx.crcValid, expected[i][4], "CRC Valid mismatch on TX#" + str(i))
            self.assertEqual(tx.txValid, expected[i][5], "Transmission Valid mismatch on TX#" + str(i))
            i += 1
            
        pass
  
    def test_stats(self):
        import numpy as np

        # compute bit probabilities from the expected data, assuming good transmissions only
        sumArray = []
        goodTxCount = 0
        for payload in self.expectedPayloadData:
            if len(payload) == self.protocol.packetSize:
                goodTxCount += 1
                if sumArray == []:
                    sumArray = payload
                else:
                    sumArray = np.add(sumArray, payload)
        expectedBitProb = np.divide(sumArray, goodTxCount/100.0)

        # compare to values computed by code
        if debug:
            print expectedBitProb
            print self.bitProbList
        # number of probabilites should be identical
        self.assertEqual(len(self.bitProbList), len(expectedBitProb), "ERROR: expected length of bit probabilities list mismatch")
        for actual, expected in zip(self.bitProbList, expectedBitProb):
            self.assertAlmostEqual(actual, expected, msg = "ERROR: bit probablity mismatch " + str(actual) + " != " + str(expected))


        # compute id frequency from the expected data
        # create list of just the IDs in string form
        idList = []
        for payload in self.expectedPayloadData:
            idList.append(''.join(str(s) for s in payload[self.protocol.idAddr[0][0]:self.protocol.idAddr[0][1]+1]))
        # now create dictionary of IDs and their counts
        expectedIdCountDict = {}
        for id in idList:
            if not id == "": # ignore the empty strings
                if id not in expectedIdCountDict:
                    expectedIdCountDict[id] = 1
                else:
                    expectedIdCountDict[id] += 1

        # now compare ID counts to expected values
        if debug:
            print "\n"
            print self.idListMaster[0]
            print expectedIdCountDict
        self.assertEqual(len(self.idListMaster[0]), len(expectedIdCountDict), "ERROR: expected length of ID count list mismatch")
        for (idVal, idCount) in self.idListMaster[0].most_common():
            self.assertEqual(self.idListMaster[0][idVal], expectedIdCountDict[idVal], "ERROR: ID count mismatch")
        
        
        # build list of values from expected data
        expectedValue1List = []
        for payload in self.expectedPayloadData:
            if len(payload) == self.protocol.packetSize: # only considering good transmissions
                bitList = payload[self.protocol.valAddr[0][0]:self.protocol.valAddr[0][1]+1]
                # convert bits to number
                value = 0
                for bit in bitList:
                    value = (value << 1) | bit
                # add to list
                expectedValue1List.append(int(value))
        
        # compare values
        if debug:
            print self.valListMaster[0]
            print expectedValue1List
        self.assertEqual(len(self.valListMaster[0]), len(expectedValue1List), "ERROR: expected length of Values 1 list mismatch")
        for actual, expected in zip(self.valListMaster[0], expectedValue1List):
            self.assertEqual(actual, expected, msg = "ERROR: Value mismatch")

        pass

if __name__ == '__main__':
    unittest.main()

