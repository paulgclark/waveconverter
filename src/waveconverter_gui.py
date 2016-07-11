# This module contains the GUI code that interfaces with the glade xml file

import os
import waveConvertVars as wcv
from demod_rf import ook_flowgraph
from demod_rf import fsk_flowgraph
from waveconverterEngine import decodeBaseband
from waveconverterEngine import packetsToFormattedString
from breakWave import basebandFileToList
from breakWave import breakBaseband
from protocol_lib import ProtocolDefinition
from protocol_lib import protocolSession
from protocol_lib import fetchProtocol
from waveConvertVars import protocol # NEED to eliminate
from waveconverterEngine import basebandTx

# for plotting baseband
try:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from numpy import arange, pi, random, linspace
    import matplotlib.cm as cm
    from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
    #from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
except:
    print "The WaveConverter GUI requires matplotlib"
    exit(1)

import numpy as np

# require Gtk 3.0+ to work
try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Pango, cairo # note gtk+3 uses Gtk, not gtk
except:
    print "The WaveConverter GUI requires GTK 3.0. Exiting..."
    exit(1)

class TopWindow:
    
    def on_window1_destroy(self, object, data=None):
        print "quit with cancel"
        Gtk.main_quit()
    
    def on_gtk_quit_activate(self, menuitem, data=None):
        print "quit from menu"
        Gtk.main_quit()
        
    def on_gtk_about_activate(self, menuitem, data=None):
        print "help about selected"
        self.response = self.aboutdialog.run()
        self.aboutdialog.hide()
        
    def on_loadProtocol_clicked(self, menuitem, data=None):
        print "load protocol dialog started"
        
        # generate liststore from protocols in database
        protocolStore = Gtk.ListStore(int, str, str, str, str, float) # ID, name, modulation, freq
        for proto in protocolSession.query(ProtocolDefinition):
            if proto.modulation == 0:
                modString = "OOK"
            else:
                modString = "FSK"
            protocolStore.append([proto.protocolId, 
                                  proto.deviceType,
                                  proto.deviceName,
                                  proto.deviceYear,
                                  modString, 
                                  proto.frequency])
            print "adding protocol to selection list: " + str(proto.protocolId) + "  " + proto.name + "   " + modString + "   " + str(proto.frequency)
         
        self.protocolTreeView.set_model(protocolStore)
        self.protocolName = self.protocolDialog.run()
        self.protocolDialog.hide()

    # when the user clicks on a protocol selection, store the index
    # of the selection
    def on_protocolTreeView_selection_changed(self, data=None):
        try:
            (model, pathlist) = self.protocolTreeSelection.get_selected_rows()
            tree_iter = model.get_iter(pathlist[0])
            self.currentProtocolDialogSelection = model.get_value(tree_iter,0)
        except:
            self.currentProtocolDialogSelection = 0 # first time through, the list will not exist
        if wcv.verbose:
            print "Current Selection: " + str(self.currentProtocolDialogSelection)
        
    # when the user clicks the OK button, read the selected protocol from the
    # database, then hide the dialog 
    def on_protocolDialogOKButton_clicked(self, data=None):
        print "dialog OK clicked"
        wcv.protocol = fetchProtocol(self.currentProtocolDialogSelection)
        self.populateProtocolToGui(protocol)
        self.protocolDialog.hide()
        
    def on_protocolDialogCancelButton_clicked(self, data=None):
        print "dialog cancel clicked"
        self.protocolDialog.hide()
        
    def on_gtk_rfFileOpen_activate(self, menuitem, data=None):
        print "menu RF File Open"
        self.fcd = Gtk.FileChooserDialog("Open IQ File...",
                                         None,
                                         Gtk.FileChooserAction.OPEN,
                                         (Gtk.STOCK_CANCEL,
                                          Gtk.ResponseType.CANCEL,
                                          Gtk.STOCK_OPEN,
                                          Gtk.ResponseType.ACCEPT))
        self.response = self.fcd.run()
        if self.response == Gtk.ResponseType.ACCEPT:
            print "Selected filepath: %s" % self.fcd.get_filename()
            wcv.iqFileName = self.fcd.get_filename()
            iqFileNameEntryWidget = self.builder.get_object("iqFileNameEntry")
            Gtk.Entry.set_text(iqFileNameEntryWidget, str(wcv.iqFileName))
            self.fcd.destroy()
            
    def on_transmissionNumberSelect_value_changed(self, spinButton, data=None):
        txNum = spinButton.get_value_as_int()
        if wcv.verbose:
            print "Selecting TX #" + str(txNum)
            
        if txNum < len(wcv.basebandDataByTx):
            wcv.txNum = txNum
            self.drawBasebandPlot(wcv.basebandDataByTx[wcv.txNum], 
                                  wcv.tMin, wcv.tMax, wcv.basebandSampleRate)
        
    def on_panRightButton_clicked(self, button, data=None):
        if wcv.verbose:
            print "Panning Right"
            
        # get center point of current plot
        center = (wcv.tMax + wcv.tMin)/2.0
        # get current zoom size
        zoomSize = 1.0*(wcv.tMax - wcv.tMin)
        
        # change center by increasing it to midway between current center 
        # and right-most extent
        center += zoomSize/4
        
        # update extents and redraw
        wcv.tMin = int((center - zoomSize/2.0) + 0.5)
        wcv.tMax = int((center + zoomSize/2.0) + 0.5)
        
        # trap for panning right past max extent
        if wcv.tMax > 100:
            wcv.tMax = 100
            wcv.tMin = 100 - zoomSize
            
        self.drawBasebandPlot(wcv.basebandDataByTx[wcv.txNum], 
                              wcv.tMin, wcv.tMax, wcv.basebandSampleRate)
        
            
    def on_panLeftButton_clicked(self, button, data=None):
        if wcv.verbose:
            print "Panning Left"
            
        # get center point of current plot
        center = (wcv.tMax + wcv.tMin)/2.0
        # get current zoom size
        zoomSize = 1.0*(wcv.tMax - wcv.tMin)
        
        # change center by decreasing it to midway between current center 
        # and left-most extent
        center -= zoomSize/4
        
        # update extents and redraw
        wcv.tMin = int((center - zoomSize/2.0) + 0.5)
        wcv.tMax = int((center + zoomSize/2.0) + 0.5)
        
        # trap for panning left past min extent
        if wcv.tMin < 0:
            wcv.tMin = 0
            wcv.tMax = zoomSize
            
        self.drawBasebandPlot(wcv.basebandDataByTx[wcv.txNum], 
                              wcv.tMin, wcv.tMax, wcv.basebandSampleRate)
            
    def on_zoomFullButton_clicked(self, button, data=None):
        if wcv.verbose:
            print "Zooming Out Full"
        wcv.tMin = 0
        wcv.tMax = 100
        
        self.drawBasebandPlot(wcv.basebandDataByTx[wcv.txNum], 
                              wcv.tMin, wcv.tMax, wcv.basebandSampleRate)
            
    def on_zoomInButton_clicked(self, button, data=None):
        if wcv.verbose:
            print "Zooming In"
            
        # get center point of current plot
        center = (wcv.tMax + wcv.tMin)/2.0
        # get current zoom size and cut in half
        zoomSize = (wcv.tMax - wcv.tMin)/2.0
        
        wcv.tMin = int((center - zoomSize/2.0) + 0.5)
        wcv.tMax = int((center + zoomSize/2.0) + 0.5)
        
        self.drawBasebandPlot(wcv.basebandDataByTx[wcv.txNum], 
                              wcv.tMin, wcv.tMax, wcv.basebandSampleRate)
        
    def on_zoomOutButton_clicked(self, button, data=None):
        if wcv.verbose:
            print "Zooming Out"
            
        # get center point of current plot
        center = (wcv.tMax + wcv.tMin)/2.0
        # get current zoom size and double
        zoomSize = (wcv.tMax - wcv.tMin)*2.0
        
        print "center: " + str(center)
        print "zoomSize: " + str(zoomSize)
        
        wcv.tMin = int((center - zoomSize/2.0) + 0.5)
        wcv.tMax = int((center + zoomSize/2.0) + 0.5)
        print "tMin: " + str(wcv.tMin)
        print "tMax: " + str(wcv.tMax)
        
        # trap for zoom out past max extent
        if wcv.tMin < 0:
            wcv.tMin = 0
            
        if wcv.tMax > 100:
            wcv.tMax = 100
        
        self.drawBasebandPlot(wcv.basebandDataByTx[wcv.txNum], 
                              wcv.tMin, wcv.tMax, wcv.basebandSampleRate)
        
        
    # the following functions grab values from the GUI widgets, consolidating the two lines
    # of code into one. Each function takes the text name of the widget and returns its current
    # value. Conversely, it assigns the value to the widget.
    def getIntFromEntry(self, widgetName):
        tempWidget = self.builder.get_object(widgetName)
        return int(tempWidget.get_text())
    
    def getFloatFromEntry(self, widgetName):
        tempWidget = self.builder.get_object(widgetName)
        return float(tempWidget.get_text())
    
    def getIntFromEntryBox(self, widgetName):
        tempWidget = self.builder.get_object(widgetName)
        return int(tempWidget.get_active())

    def getListFromEntry(self, widgetName):
        tempWidget = self.builder.get_object(widgetName)
        listString = tempWidget.get_text().strip('[]') # resolves to comma-separated list of values
        listItemsText = listString.split(',')
        tempList = []
        for item in listItemsText:
            tempList.append(int(item))
        
        return tempList
             
    #def setIntToEntry(self, widgetName, value):
    #    tempWidget = self.builder.get_object(widgetName)
    #    Gtk.Entry.set_text(tempWidget, str(value))
    
    #def setFloatToEntry(self, widgetName, value):
    #    tempWidget = self.builder.get_object(widgetName)
    #    Gtk.Entry.set_text(tempWidget, str(value))

    def setEntry(self, widgetName, value):
        tempWidget = self.builder.get_object(widgetName)
        Gtk.Entry.set_text(tempWidget, str(value))
        
    def setEntryBox(self, widgetName, value):
        tempWidget = self.builder.get_object(widgetName)
        Gtk.ComboBox.set_active(tempWidget, value)
    
    #def setIntToEntryBox(self, widgetName, value):
    #    tempWidget = self.builder.get_object(widgetName)
    #    Gtk.ComboBox.set_active(tempWidget, value)
        
    #def setListToEntry(self, widgetName, value):
    #    tempWidget = self.builder.get_object(widgetName)
    #    print "fill"
        
    # plots the input list as a waveform, displaying the data between
    # tMin and tMax, which are percentages of the duration of the waveform. For example,
    # 0, 100 shows the entire waveform (0% to 100%), while 25, 75 shows the middle half;
    # waveformSampleRate provides the timing info to compute the horizontal axis
    def drawBasebandPlot(self, waveformDataList, tMin, tMax, waveformSampleRate):
        
        localWaveform = list(waveformDataList) # make local copy
        # truncate large input lists; cairo can only handle 18980 point plots
        #if len(waveformDataList) > 18901:
        #    waveformDataList = waveformDataList[0:18900]
        # NEED to replace this with a smart removal of trailing zeroes from each tx 
        if len(localWaveform) > 14001:
            localWaveform = localWaveform[0:14000]
        
        # compute 
        waveformLength = len(localWaveform)
        startIndex = int((tMin/100.0) * waveformLength)
        stopIndex =  int((tMax/100.0) * waveformLength)
        
        # compute plot area in milliseconds    
        stepSize = (1/waveformSampleRate) * 1000.0
        startTime = startIndex * stepSize
        stopTime = stopIndex * stepSize
        
        if wcv.verboseZoom:
            print "displaying new plot"
            print "list size = " + str(waveformLength)
            print "tMin(%) = " + str(tMin)
            print "tMax(%) = " + str(tMax)
            print "start Index = " + str(startIndex)
            print "stop Index = " + str(stopIndex)
            print "start time = " + str(startTime)
            print "stop time = " + str(stopTime)
            
        # get gui widget
        #context = plotWidget.get_style_context;
        #width = plotWidget.get_allocated_width;
        #height = plotWidget.get_allocated_height;
        
        t = arange(startTime, stopTime, stepSize)
        s = localWaveform[startIndex:stopIndex]
        # NEED: sometimes t and s arrays are sized differently, probably due to rounding
        if wcv.verboseZoom:
            print "length of waveform list: " + str(len(s))
            print "step size:               " + str(stepSize)
            print "length of time vector:   " + str(len(t))
        self.axis.clear() # clear plot before re-plotting
        self.axis.plot(t,s)

        #self.axis.axis([0, len(waveformDataList)*stepSize, -0.1, 1.1])
        self.axis.axis([startTime, stopTime, -0.1, 1.1])
        self.axis.set_xlabel('time (ms)') # replace with time unit
        self.axis.set_ylabel('Baseband Signal') # replace with ???
        self.canvas.draw()
        
       
    # when the RF Demod button is pushed, we need to take all the settings 
    # that the user has entered into the gui and place them in the current 
    # protocol object; we then call a flowgraph object with the RF
    # configuration specified
    def on_Demodulate_clicked(self, button, data=None):
        print "pushed RF Demod Button"
        
        ## get all of the values entered on this screen
        wcv.center_freq = 1000000 * self.getFloatFromEntry("centerFreqEntry")
        wcv.samp_rate = 1000000 * self.getFloatFromEntry("sampRateEntry")
        wcv.protocol.modulation = self.getIntFromEntryBox("modulationEntryBox")
        wcv.protocol.frequency = 1000000 * self.getFloatFromEntry("frequencyEntry")
        wcv.protocol.channelWidth = 1000 * self.getFloatFromEntry("channelWidthEntry")
        wcv.protocol.transitionWidth = 1000 * self.getFloatFromEntry("transitionWidthEntry")
        wcv.protocol.threshold = self.getFloatFromEntry("thresholdEntry")
        wcv.protocol.convertTimingToSamples(wcv.basebandSampleRate)

        if wcv.verbose:
            print "modulation (ook=0)    = " + str(wcv.protocol.modulation)
            print "samp_rate (Hz)        = " + str(wcv.samp_rate)
            print "baseband rate (Hz)    = " + str(wcv.basebandSampleRate)
            print "center_freq (Hz)      = " + str(wcv.center_freq)
            print "tune frequency (Hz)   = " + str(wcv.protocol.frequency)
            print "channel width (Hz)    = " + str(wcv.protocol.channelWidth)
            print "transition width (Hz) = " + str(wcv.protocol.transitionWidth)
            print "threshold             = " + str(wcv.protocol.threshold)
            print "iq File Name          = " + wcv.iqFileName
            print "Waveform File Name    = " + wcv.waveformFileName

        # create flowgraph object and execute flowgraph
        try:
            if wcv.verbose:
                print "Running Demodulation Flowgraph"
            if wcv.protocol.modulation == wcv.MOD_OOK:
                flowgraphObject = ook_flowgraph(wcv.samp_rate, # rate_in
                                                wcv.basebandSampleRate, # rate_out
                                                wcv.center_freq,
                                                wcv.protocol.frequency, 
                                                wcv.protocol.channelWidth,
                                                wcv.protocol.transitionWidth,
                                                wcv.protocol.threshold,
                                                wcv.iqFileName,
                                                wcv.waveformFileName) # temp digfile
                flowgraphObject.run()
            elif wcv.protocol.modulation == wcv.MOD_FSK:
                flowgraphObject = fsk_flowgraph(wcv.samp_rate, # samp_rate_in 
                                                wcv.basebandSampleRate, # rate_out 
                                                wcv.center_freq,
                                                wcv.protocol.frequency, # tune_freq
                                                wcv.protocol.channelWidth,
                                                wcv.protocol.transitionWidth,
                                                wcv.protocol.threshold,
                                                wcv.protocol.fskDeviation,
                                                wcv.iqFileName, 
                                                wcv.waveformFileName) # temp file
                flowgraphObject.run()
            else:
                print "Invalid modulation type selected" # NEED to put in status bar or pop-up
            
        except [[KeyboardInterrupt]]:
            pass
        
        # read baseband waveform data from file
        wcv.basebandData = basebandFileToList(wcv.waveformFileName) # NEED get list from flowgraph; unnecessary file reads kill perf
        
        # split the baseband into individual transmissions and then store each
        # in its own transmission object, to be decoded later
        wcv.basebandDataByTx = breakBaseband(wcv.basebandData, wcv.protocol.interPacketWidth_samp)
        runningSampleCount = 0
        wcv.txList = []
        for iTx in wcv.basebandDataByTx[1:]: # ignore the first transmission, it's spurious
            timeStamp_us = 1000000.0 * runningSampleCount/wcv.basebandSampleRate
            runningSampleCount += len(iTx)
            #print "baseband size" + str(len(wcv.txList)) + ":  " + str(len(iTx))
            wcv.txList.append(basebandTx(len(wcv.txList), timeStamp_us, iTx))
        
        # now plot the first transmission, zoomed out
        wcv.tMin = 0
        wcv.tMax = 100
        #self.drawBasebandPlot(wcv.basebandDataByTx[1], wcv.tMin, wcv.tMax, wcv.basebandSampleRate)
        self.drawBasebandPlot(wcv.txList[1].waveformData, wcv.tMin, wcv.tMax, wcv.basebandSampleRate)
        
        # set range for the tx-select spin button
        #self.txSelectSpinButton.set_range(0, len(wcv.basebandDataByTx)-1)
        self.txSelectSpinButton.set_range(0, len(wcv.txList)-1)
        
        # update the transmission status
        
        print "Flowgraph completed"
    
    # when the Decode button is pushed, we need to take all the settings 
    # that the user has entered into the gui and place them in the current 
    # protocol object; we then call the decoder engine to extract the payload
    def on_Decode_clicked(self, button, data=None):
        if wcv.verbose:
            print "Now Decoding Baseband"
            
        #wcv.protocol.modulation = self.getIntFromEntryBox("modulationEntryBox")
        #wcv.protocol.frequency = 1000000 * self.getFloatFromEntry("frequencyEntry")
        # get framing properties
        wcv.protocol.preambleSymbolLow = self.getIntFromEntry("preambleLowEntry")
        wcv.protocol.preambleSymbolHigh = self.getIntFromEntry("preambleHighEntry")
        wcv.protocol.preambleSize[0] = self.getIntFromEntry("preambleSize1Entry")
        try:
            wcv.protocol.preambleSize[1] = self.getIntFromEntry("preambleSize2Entry")
        except:
            wcv.protocol.preambleSize[1] = 0
        wcv.protocol.headerWidth  = self.getIntFromEntry("headerLengthEntry")
        wcv.protocol.interPacketWidth = self.getIntFromEntry("interPacketWidthEntry")
        
        # get decode properties
        wcv.protocol.encodingType = self.getIntFromEntryBox("encodingEntryBox")
        wcv.protocol.unitWidth = self.getIntFromEntry("payloadUnitEntry")
        wcv.protocol.pwmSymbolSize = self.getIntFromEntry("pwmPeriodEntry")
        # compute PWM units from percentage in GUI
        wcv.protocol.pwmZeroSymbol[0] = int(wcv.protocol.pwmSymbolSize*(100-self.getFloatFromEntry("pwmZeroEntry"))/100.0)
        wcv.protocol.pwmZeroSymbol[1] = int(wcv.protocol.pwmSymbolSize*self.getFloatFromEntry("pwmZeroEntry")/100.0)
        wcv.protocol.pwmOneSymbol[0] = int(wcv.protocol.pwmSymbolSize*(100-self.getFloatFromEntry("pwmOneEntry"))/100.0)
        wcv.protocol.pwmOneSymbol[1] = int(wcv.protocol.pwmSymbolSize*self.getFloatFromEntry("pwmOneEntry")/100.0)
        
        # load CRC properties
        wcv.protocol.crcPoly = self.getListFromEntry("crcPolynomialEntry")
        wcv.protocol.crcLow = self.getIntFromEntry("crcStartAddrEntry")
        wcv.protocol.crcDataLow = self.getIntFromEntry("addrDataLowEntry")
        wcv.protocol.crcDataHigh = self.getIntFromEntry("addrDataHighEntry")
        wcv.protocol.crcInit = self.getIntFromEntry("crcInitEntry")
        wcv.protocol.crcBitOrder = self.getIntFromEntryBox("crcReflectEntryBox")
        if self.getIntFromEntryBox("crcReverseOutEntryBox") == 1:
            wcv.protocol.crcReverseOut = True
        else:
            wcv.protocol.crcReverseOut = False
        wcv.protocol.crcFinalXor = self.getListFromEntry("crcFinalXorEntry")
        wcv.protocol.crcPad = self.getIntFromEntryBox("crcPadEntryBox")
        wcv.protocol.crcPadCount = 8*self.getIntFromEntryBox("crcPadCountEntryBox")
        
        # when we load new values for the protocol, we need to do the
        # conversion from microseconds to samples
        wcv.protocol.convertTimingToSamples(wcv.basebandSampleRate)
        
        if wcv.verbose:
            print "baseband sample rate:" + str(wcv.basebandSampleRate)
            wcv.protocol.printProtocolFull()
           
        # call decode engine for each transmission
        i = 0
        print "tx list length: " + str(len(wcv.txList))
        for iTx in wcv.txList:
            if i == len(wcv.txList) - 1: # NEED: fix this kludge, last tx in list is wonky
                iTx.display()
            else:
                iTx.decodeTx(wcv.protocol)
            i+=1
            
            wcv.decodeOutputString += iTx.binaryString
        """
        # call decode engine
        wcv.payloadList = decodeBaseband(wcv.waveformFileName,
                                         wcv.basebandSampleRate,
                                         wcv.outFileName,
                                         wcv.protocol,
                                         wcv.outputHex)
        
        wcv.decodeOutputString = packetsToFormattedString(wcv.payloadList, wcv.protocol, 
                                                          wcv.outputHex) 
        """
        # change the text in all windows (NEED a framed approach)
        self.decodeTextViewWidget1 = self.builder.get_object("decodeTextView1")
        self.decodeTextViewWidget1.modify_font(Pango.font_description_from_string('Courier 12'))
        self.decodeTextViewWidget1.get_buffer().set_text(wcv.decodeOutputString)
        self.decodeTextViewWidget2 = self.builder.get_object("decodeTextView2")
        self.decodeTextViewWidget2.modify_font(Pango.font_description_from_string('Courier 12'))
        self.decodeTextViewWidget2.get_buffer().set_text(wcv.decodeOutputString)
        self.decodeTextViewWidget3 = self.builder.get_object("decodeTextView3")
        self.decodeTextViewWidget3.modify_font(Pango.font_description_from_string('Courier 12'))
        self.decodeTextViewWidget3.get_buffer().set_text(wcv.decodeOutputString)
        
    # when a new protocol is loaded, we use its information to populate GUI
    def populateProtocolToGui(self, protocol):

    
        # add global WC control values
        self.setEntry("centerFreqEntry", wcv.center_freq/1000000.0)
        self.setEntry("sampRateEntry", wcv.samp_rate/1000000.0)
        self.setEntry("glitchFilterEntry", wcv.glitchFilterCount)
        self.setEntry("unitTimingErrorEntry", wcv.timingError*100.0)
        
        # add RF properties
        self.setEntry("iqFileNameEntry", wcv.iqFileName)
        self.setEntry("frequencyEntry", wcv.protocol.frequency/1000000.0)
        self.setEntry("channelWidthEntry", wcv.protocol.channelWidth/1000.0)
        self.setEntry("transitionWidthEntry", wcv.protocol.transitionWidth/1000.0)
        self.setEntryBox("modulationEntryBox", wcv.protocol.modulation)
        self.setEntry("fskDeviationEntry", wcv.protocol.fskDeviation/1000.0)
        self.setEntry("thresholdEntry", wcv.protocol.threshold)
        
        # add preamble properties
        self.setEntry("preambleLowEntry", wcv.protocol.preambleSymbolLow)
        self.setEntry("preambleHighEntry", wcv.protocol.preambleSymbolHigh)
        self.setEntry("preambleSize1Entry", int(wcv.protocol.preambleSize[0]))
        self.setEntry("preambleSize2Entry", wcv.protocol.preambleSize[1])
        self.setEntry("headerLengthEntry", wcv.protocol.headerWidth)
        self.setEntry("interPacketWidthEntry", wcv.protocol.interPacketWidth)
        
        # add payload properties
        self.setEntryBox("encodingEntryBox", wcv.protocol.encodingType)
        self.setEntry("payloadUnitEntry", wcv.protocol.unitWidth)
        self.setEntry("pwmPeriodEntry", wcv.protocol.pwmSymbolSize)
        self.setEntry("pwmZeroEntry", 
                      "{0:.1f}".format(100.0*wcv.protocol.pwmZeroSymbol[1]/wcv.protocol.pwmSymbolSize))
        self.setEntry("pwmOneEntry", 
                      "{0:.1f}".format(100.0*wcv.protocol.pwmOneSymbol[1]/wcv.protocol.pwmSymbolSize))

        # add CRC properties
        self.setEntry("crcLengthEntry", len(wcv.protocol.crcPoly))
        self.setEntry("crcStartAddrEntry", wcv.protocol.crcLow)
        self.setEntry("addrDataLowEntry", wcv.protocol.crcDataLow)
        self.setEntry("addrDataHighEntry", wcv.protocol.crcDataHigh)
        self.setEntry("crcPolynomialEntry", wcv.protocol.crcPoly)
        self.setEntry("crcInitEntry", wcv.protocol.crcInit)
        self.setEntryBox("crcReflectEntryBox", wcv.protocol.crcBitOrder)
        self.setEntryBox("crcReverseOutEntryBox", wcv.protocol.crcReverseOut)
        self.setEntry("crcFinalXorEntry", wcv.protocol.crcFinalXor)
        self.setEntryBox("crcPadEntryBox", wcv.protocol.crcPad)
        self.setEntryBox("crcPadCountEntryBox", wcv.protocol.crcPadCount/8)
        
        # add payload statistics properties
        # NEED to fill out
            
        
    def __init__(self, protocol):
        #global protocol
        self.gladefile = "gui/top_level.glade"
        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.gladefile)
        self.builder.connect_signals(self)
        
        # required setup for spin button range
        self.txSelectSpinButton = self.builder.get_object("transmissionNumberSelect")
        self.spinButtonAdjustment = Gtk.Adjustment(0, 0, 0, 1, 1, 1)
        self.txSelectSpinButton.set_adjustment(self.spinButtonAdjustment)
        
        # setup for plot window
        self.plotWidget = self.builder.get_object("basebandPlot")
        self.figure = Figure(figsize=(8,6), dpi=71) # replace with ???
        self.axis = self.figure.add_subplot(111)
        t = arange(0, 100, 1)
        s = arange(0, 100, 1)
        self.axis.plot(t,s)
        self.axis.axis([0, 100, -0.1, 1.1])
        self.axis.set_xlabel('time (ms)') # replace with time unit
        self.axis.set_ylabel('Baseband Signal') # replace with ???
        self.canvas = FigureCanvas(self.figure)  # a Gtk.DrawingArea
        self.canvas.set_size_request(400,40)
        self.plotWidget.add_with_viewport(self.canvas)
        self.plotWidget.show_all()
        
        # setup for protocol dialog
        self.protocolDialog = self.builder.get_object("protocolDialog")
        self.protocolTreeView = self.builder.get_object("protocolTreeView")
        self.protocolTreeSelection = self.builder.get_object("protocolTreeView_selection")
        
        # now add cell renderers for each column of protocol dialog
        renderer_ID = Gtk.CellRendererText()
        column_ID = Gtk.TreeViewColumn("ID", renderer_ID, text=0)
        self.protocolTreeView.append_column(column_ID)
        renderer_type = Gtk.CellRendererText()
        column_type = Gtk.TreeViewColumn("Type", renderer_type, text=1)
        self.protocolTreeView.append_column(column_type)
        renderer_device = Gtk.CellRendererText()
        column_device = Gtk.TreeViewColumn("Device", renderer_device, text=2)
        self.protocolTreeView.append_column(column_device)
        renderer_year = Gtk.CellRendererText()
        column_year = Gtk.TreeViewColumn("Year", renderer_year, text=3)
        self.protocolTreeView.append_column(column_year)
        renderer_mod = Gtk.CellRendererText()
        column_mod = Gtk.TreeViewColumn("Modulation", renderer_mod, text=4)
        self.protocolTreeView.append_column(column_mod)
        renderer_freq = Gtk.CellRendererText()
        column_freq = Gtk.TreeViewColumn("Frequency", renderer_freq, text=5)
        self.protocolTreeView.append_column(column_freq)
        
        
        self.window = self.builder.get_object("window1")
        self.aboutdialog = self.builder.get_object("aboutdialog1")
        #self.statusbar = self.builder.get_object("statusbar1")
        self.window.show()
        
        # if we were passed a protocol via the command line or via
        # manual definition, populate gui with those values
        #if not (protocol_number == -1):
        self.populateProtocolToGui(protocol) 
            
