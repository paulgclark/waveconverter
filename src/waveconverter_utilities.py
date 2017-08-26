import sys

# this function reads a waveconverter output file and
# returns a list of the baseband data contained within
def getTxDataFromWaveConverterFile(fileName):
    txMasterList = []

    # open the baseband file
    try:
        wcFile = file(fileName, "r")
        fileString = wcFile.read()
    except:
        print "Trouble reading waveconverter output file {}, exiting...".format(fileName)
        exit(1)

    # get rid of the lines not containing BB data
    txData = False
    for line in fileString.splitlines():
        # we have entered the section containing the raw tx data
        if txData:
            # if the line is blank, then we have exited this section
            if line == "":
                break
            else:
                txList = []
                for byteString in line.split()[1:]:
                    for ch in byteString:
                        txList.append(int(ch))
                txMasterList.append(txList)
        if "TX Num" in line:
            txData = True
    
    # convert BB data to bitList
    return txMasterList
