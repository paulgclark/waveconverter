import re

def fileNameTextToFloat(valStr, unitStr):
    # if there's a 'p' character, then we have to deal with decimal vals
    if 'p' in valStr:
        regex = re.compile(r"([0-9]+)p([0-9]+)")
        wholeVal = regex.findall(valStr)[0][0]
        decimalVal = regex.findall(valStr)[0][1]
        baseVal = 1.0*int(wholeVal) + 1.0*int(decimalVal)/10**len(decimalVal)
    else:
        baseVal = 1.0*int(valStr)

    if unitStr == "G":
        multiplier = 1e9
    elif unitStr == "M":
        multiplier = 1e6
    elif unitStr == "k":
        multiplier = 1e3
    else:
        multiplier = 1.0

    return baseVal * multiplier


class iqFileObject():
    def __init__(self, prefix = None, centerFreq = None,
                       sampRate = None, fileName = None):
        # if no file name is specified, store the parameters
        if fileName is None:
            self.prefix = prefix
            self.centerFreq = centerFreq
            self.sampRate = sampRate
        # if the file name is specified, we must derive the parameters
        # from the file name
        else:
            # first check if we have a simple file name or a name+path
            regex = re.compile(r"\/")
            if regex.match(fileName):
                # separate the filename from the rest of the path
                regex = re.compile(r"\/([a-zA-Z0-9_.]+)$")
                justName = regex.findall(fileName)[0]
            else:
                justName = fileName
            # get the substrings representing the values
            regex = re.compile(r"_c([0-9p]+)([GMK])_s([0-9p]+)([GMk])\.iq$")
            paramList = regex.findall(justName)
            try:
                centerValStr = paramList[0][0]
                centerUnitStr = paramList[0][1]
                sampValStr = paramList[0][2]
                sampUnitStr = paramList[0][3]

                self.centerFreq = fileNameTextToFloat(centerValStr, centerUnitStr)
                self.sampRate = fileNameTextToFloat(sampValStr, sampUnitStr)
            except:
                return


    def fileName(self):
        tempStr = self.prefix
        # add center frequency
        # first determine if we should use k, M, G or nothing
        # then divide by the appropriate unit
        if self.centerFreq > 1e9:
            unitMag = 'G'
            wholeVal = int(1.0*self.centerFreq/1e9)
            decimalVal = (1.0*self.centerFreq - 1e9*wholeVal)
            decimalVal = int(decimalVal/1e7)
        elif self.centerFreq > 1e6:
            unitMag = 'M'
            wholeVal = int(1.0*self.centerFreq/1e6)
            decimalVal = (1.0*self.centerFreq - 1e6*wholeVal)
            decimalVal = int(decimalVal/1e4)
        elif self.centerFreq > 1e3:
            unitMag = 'k'
            wholeVal = int(1.0*self.centerFreq/1e3)
            decimalVal = (1.0*self.centerFreq - 1e3*wholeVal)
            decimalVal = int(decimalVal/1e1)
        else:
            unitMag = ''
            value = int(self.centerFreq)
        if decimalVal == 0:
            tempStr += "_c{}{}".format(wholeVal, unitMag)
        else:
            tempStr += "_c{}p{}{}".format(wholeVal, decimalVal, unitMag)

        # do the same thing for the sample rate
        if self.sampRate > 1e6:
            unitMag = 'M'
            wholeVal = int(1.0*self.sampRate/1e6)
            decimalVal = (1.0*self.sampRate - 1e6*wholeVal)
            decimalVal = int(decimalVal/1e4)
        elif self.sampRate > 1e3:
            unitMag = 'k'
            wholeVal = int(1.0*self.sampRate/1e3)
            decimalVal = (1.0*self.sampRate - 1e3*wholeVal)
            value = self.sampRate/1e1
        else:
            unitMag = ''
            value = int(self.sampRate)
        if decimalVal == 0:
            tempStr += "_s{}{}".format(wholeVal, unitMag)
        else:
            tempStr += "_s{}p{}{}".format(wholeVal, decimalVal, unitMag)
        tempStr += ".iq"
        return tempStr

