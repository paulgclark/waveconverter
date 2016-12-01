# This module contains the GUI code that interfaces with the glade xml file

import os
import waveConvertVars as wcv
from waveconverterEngine import decodeBaseband
from waveconverterEngine import packetsToFormattedString
from protocol_lib import ProtocolDefinition, getNextProtocolId
from protocol_lib import protocolSession
from protocol_lib import fetchProtocol
from waveConvertVars import protocol # NEED to eliminate
from waveconverterEngine import basebandTx
from waveconverterEngine import demodIQFile
from waveconverterEngine import buildTxList
from waveconverterEngine import decodeAllTx
from statEngine import computeStats
from statEngine import buildStatStrings
from collections import Counter
import numpy as np
import webbrowser

# for plotting baseband
try:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from numpy import arange, pi, random, linspace
    import matplotlib.cm as cm
    from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
    #from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
except:
    print "The WaveConverter GUI requires matplotlib. Exiting..."
    exit(1)

# require Gtk 3.0+ to work
try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Pango, cairo, GObject # note gtk+3 uses Gtk, not gtk
except:
    print "The WaveConverter GUI requires GTK 3.0. Exiting..."
    exit(1)
#from IPython.core.payload import PayloadManager


class TopWindow:
    
    def on_window1_destroy(self, object, data=None):
        if wcv.verbose:
            print "quit with cancel"
        Gtk.main_quit()
    
    def on_gtk_quit_activate(self, menuitem, data=None):
        if wcv.verbose:
            print "quit from menu"
        Gtk.main_quit()
        
    def on_gtk_about_activate(self, menuitem, data=None):
        if wcv.verbose:
            print "help about selected"
        self.response = self.aboutdialog.run()
        self.aboutdialog.hide()
    
    # This function grabs all of the entries that the user has made into the GUI
    # and stores them in the active protocol object. This function is called before
    # saving or using any protocol
    def transferGUIDataToProtocol(self):
        ## get all of the values entered on the demodulation tab
        wcv.center_freq = 1000000.0 * self.getFloatFromEntry("centerFreqEntry")
        wcv.samp_rate = 1000000.0 * self.getFloatFromEntry("sampRateEntry")
        wcv.protocol.modulation = self.getIntFromEntryBox("modulationEntryBox")
        wcv.protocol.frequency = 1000000.0 * self.getFloatFromEntry("frequencyEntry")
        wcv.protocol.channelWidth = 1000.0 * self.getFloatFromEntry("channelWidthEntry")
        wcv.protocol.transitionWidth = 1000.0 * self.getFloatFromEntry("transitionWidthEntry")
        wcv.protocol.threshold = self.getFloatFromEntry("thresholdEntry")
        # may not have an FSK deviation value entered if user is working with OOK
        try:
            wcv.protocol.fskDeviation = self.getFloatFromEntry("fskDeviationEntry")
        except:
            wcv.protocol.fskDeviation = 0.0
        
        # get framing properties
        wcv.protocol.preambleSymbolLow = self.getIntFromEntry("preambleLowEntry")
        wcv.protocol.preambleSymbolHigh = self.getIntFromEntry("preambleHighEntry")
        # the preamble size is a list of possible values
        wcv.protocol.preambleSize[0] = self.getIntFromEntry("preambleSize1Entry")
        # there may not be a second value entered into the GUI
        try:
            wcv.protocol.preambleSize[1] = self.getIntFromEntry("preambleSize2Entry")
        except:
            wcv.protocol.preambleSize[1] = 0
                
        wcv.protocol.headerWidth  = self.getIntFromEntry("headerLengthEntry")
        wcv.protocol.interPacketWidth = self.getIntFromEntry("interPacketWidthEntry")
        
        # get decode properties
        wcv.protocol.encodingType = self.getIntFromEntryBox("encodingEntryBox")
        wcv.protocol.unitWidth = self.getIntFromEntry("payloadUnitEntry")
        wcv.protocol.pwmZeroSymbol[0] = self.getIntFromEntry("pwmZeroLowEntry")
        wcv.protocol.pwmZeroSymbol[1] = self.getIntFromEntry("pwmZeroHighEntry")
        wcv.protocol.pwmOneSymbol[0] = self.getIntFromEntry("pwmOneLowEntry")
        wcv.protocol.pwmOneSymbol[1] = self.getIntFromEntry("pwmOneHighEntry")
        wcv.protocol.packetSize = self.getIntFromEntry("numPayloadBitsEntry")
        
        #wcv.protocol.pwmSymbolSize = self.getIntFromEntry("pwmPeriodEntry")
        # compute PWM units from percentage in GUI
        #wcv.protocol.pwmZeroSymbol[0] = int(wcv.protocol.pwmSymbolSize*(100.0-self.getFloatFromEntry("pwmZeroEntry"))/100.0)
        #wcv.protocol.pwmZeroSymbol[1] = int(wcv.protocol.pwmSymbolSize*self.getFloatFromEntry("pwmZeroEntry")/100.0)
        #wcv.protocol.pwmOneSymbol[0] = int(wcv.protocol.pwmSymbolSize*(100.0-self.getFloatFromEntry("pwmOneEntry"))/100.0)
        #wcv.protocol.pwmOneSymbol[1] = int(wcv.protocol.pwmSymbolSize*self.getFloatFromEntry("pwmOneEntry")/100.0)
        
        # load CRC properties
        wcv.protocol.crcPoly = self.getListFromEntry("crcPolynomialEntry")
        wcv.protocol.crcLow = self.getIntFromEntry("crcStartAddrEntry")
        wcv.protocol.crcHigh = wcv.protocol.crcLow + len(wcv.protocol.crcPoly)
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
        
        # get stats properties
        wcv.protocol.idAddrLow = self.getIntFromEntry("idAddrLowEntry")
        wcv.protocol.idAddrHigh = self.getIntFromEntry("idAddrHighEntry")
        wcv.protocol.val1AddrLow = self.getIntFromEntry("val1AddrLowEntry")
        wcv.protocol.val1AddrHigh = self.getIntFromEntry("val1AddrHighEntry")
        wcv.protocol.val2AddrLow = self.getIntFromEntry("val2AddrLowEntry")
        wcv.protocol.val2AddrHigh = self.getIntFromEntry("val2AddrHighEntry")
        wcv.protocol.val3AddrLow = self.getIntFromEntry("val3AddrLowEntry")
        wcv.protocol.val3AddrHigh = self.getIntFromEntry("val3AddrHighEntry")
        
        # these parameters are currently unused but must be in protocol to keep sqllite happy
        wcv.protocol.interPacketSymbol = 0
        wcv.protocol.headerLevel = 0
        wcv.protocol.preambleSync = False
        wcv.protocol.crcHigh = 0
        wcv.protocol.crcPadVal = 0
                
        # when we load new values for the protocol, we need to do the
        # conversion from microseconds to samples
        wcv.protocol.convertTimingToSamples(wcv.basebandSampleRate)
        
        
    def on_loadProtocol_clicked(self, menuitem, data=None):
        if wcv.verbose:
            print "load protocol dialog started"
        
        # generate liststore from protocols in database
        protocolStore = Gtk.ListStore(int, str, str, str, str, float) # ID, name, modulation, freq
        for proto in protocolSession.query(ProtocolDefinition):
            # use strings to display modulation and device types
            if proto.modulation == 0:
                modString = "OOK"
            else:
                modString = "FSK"
            devTypeString = wcv.devTypeStrings[proto.deviceType]
            protocolStore.append([proto.protocolId, 
                                  devTypeString, #proto.deviceType,
                                  proto.deviceName,
                                  proto.deviceYear,
                                  modString, 
                                  proto.frequency])
            if wcv.verbose:
                print "adding protocol to selection list: " + str(proto.protocolId) + \
                      "  " + proto.deviceName + "   " + modString + "   " + str(proto.frequency)
         
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
        if wcv.verbose:
            print "dialog OK clicked"
        wcv.protocol = fetchProtocol(self.currentProtocolDialogSelection)
        self.populateProtocolToGui(protocol)
        self.protocolDialog.hide()
        
    def on_protocolDialogCancelButton_clicked(self, data=None):
        if wcv.verbose:
            print "dialog cancel clicked"
        self.protocolDialog.hide()
        
    def on_saveProtocol_clicked(self, menuitem, data=None):
        if wcv.verbose:
            print "save protocol dialog started"
            
        # pull in all the user-entered data and save to current protocol         
        self.transferGUIDataToProtocol()

        # store protocol in database under current ID
        wcv.protocol.saveProtocol()
        wcv.protocol.printProtocolFull()
        
    # this function is called when the toolbar "save as" button is clicked,
    # it brings up a dialog asking the user for a protocol name for the new
    # protocol to be stored under
    def on_saveAsProtocol_clicked(self, menuitem, data=None):
        if wcv.verbose:
            print "save as protocol dialog started"
        
        # clear any existing text in dialog window (previously entered protocol info)
        self.setEntry("protocolSaveAsDeviceNameEntry", "")
        self.setEntry("protocolSaveAsDeviceYearEntry", "")
        self.setEntryBox("protocolSaveAsDeviceTypeEntryBox", -1)
        
        # bring up "Save As" dialog
        self.protocolSaveAsReturn = self.protocolSaveAsDialog.run()
        self.protocolSaveAsDialog.hide()

    # when the user clicks the OK button, read the selected protocol from the
    # database, then hide the dialog 
    def on_protocolSaveAsOKButton_clicked(self, data=None):
        if wcv.verbose:
            print "SAVE-AS OK clicked"

        # pull in all the user-entered data and save to current protocol, plus protocol name
        wcv.protocol = ProtocolDefinition(getNextProtocolId())
        self.transferGUIDataToProtocol()
        wcv.protocol.deviceName = self.getStringFromEntry("protocolSaveAsDeviceNameEntry") 
        wcv.protocol.deviceYear = self.getIntFromEntry("protocolSaveAsDeviceYearEntry")
        wcv.protocol.deviceType = self.getIntFromEntryBox("protocolSaveAsDeviceTypeEntryBox")
        if wcv.verbose:
            wcv.protocol.printProtocolFull()
                    
        # store protocol in database under current ID
        wcv.protocol.saveProtocol()
        
        # NEED: check if name already exists, if it does, prompt for new name (loop until name is OK)
        self.protocolSaveAsDialog.hide()
        
    def on_protocolSaveAsCancelButton_clicked(self, data=None):
        if wcv.verbose:
            print "SAVE-AS cancel button clicked"
        self.protocolSaveAsDialog.hide()
        
    def on_gtk_rfFileOpen_activate(self, menuitem, data=None):
        if wcv.verbose:
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
            
    def on_userGuideMenu_activate(self, menuitem, data=None):
        if wcv.verbose:
            print "opening user guide..."

        # get path of doc directory (assuming this is running in src subdir of install directory
        os.chdir('../doc')
        docPath = os.getcwd()
        webbrowser.open('file://' + docPath + '/user_guide.pdf')
        
             
    def on_transmissionNumberSelect_value_changed(self, spinButton, data=None):
        txNum = spinButton.get_value_as_int() - 1 # button counts from 1 to n; array from 0 to n-1
        # reset the Min and Max extents of plot for new waveform
        wcv.tMin = 0
        wcv.tMax = 100
        
        if wcv.verbose:
            print "Selecting TX #" + str(txNum)
            
        if txNum < len(wcv.txList):
            wcv.txNum = txNum
            self.drawBasebandPlot(wcv.txList[wcv.txNum].waveformData, 
                                  wcv.tMin, wcv.tMax, wcv.basebandSampleRate)
        else:
            print "Reached end of transmission list"
        
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
            
        self.drawBasebandPlot(wcv.txList[wcv.txNum].waveformData, 
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
            
        self.drawBasebandPlot(wcv.txList[wcv.txNum].waveformData, 
                              wcv.tMin, wcv.tMax, wcv.basebandSampleRate)
            
    def on_zoomFullButton_clicked(self, button, data=None):
        if wcv.verbose:
            print "Zooming Out Full"
        wcv.tMin = 0
        wcv.tMax = 100
        
        self.drawBasebandPlot(wcv.txList[wcv.txNum].waveformData, 
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
        
        self.drawBasebandPlot(wcv.txList[wcv.txNum].waveformData, 
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
        
        self.drawBasebandPlot(wcv.txList[wcv.txNum].waveformData, 
                              wcv.tMin, wcv.tMax, wcv.basebandSampleRate)
        
        
    # 
    def on_showAllButton_toggled(self, button, data=None):
        wcv.showAllTx = self.getBoolFromToolToggle("showAllButton")
        if wcv.verbose:
            print "View Stats for All TX changed to " + str(wcv.showAllTx)
        # if stats are up, redo them
        if not wcv.bitProbString == "":
            self.on_runStat_clicked(button)
            
    def on_hexButton_toggled(self, button, data=None):
        wcv.outputHex = self.getBoolFromToolToggle("hexButton")
            
        if wcv.verbose:
            print "Hex Output Mode change to " + str(wcv.outputHex)
        # if tx display is are up, redo them
        if len(wcv.txList) != 0:
            self.on_Decode_clicked(button)
        
        # if stats are up, redo them
        if not wcv.bitProbString == "":
            self.on_runStat_clicked(button)
    
    # the following functions grab values from the GUI widgets, consolidating the two lines
    # of code into one. Each function takes the text name of the widget and returns its current
    # value. Conversely, it assigns the value to the widget.
    def getIntFromEntry(self, widgetName):
        tempWidget = self.builder.get_object(widgetName)
        return int(tempWidget.get_text())
    
    def getFloatFromEntry(self, widgetName):
        tempWidget = self.builder.get_object(widgetName)
        return float(tempWidget.get_text())

    def getStringFromEntry(self, widgetName):
        tempWidget = self.builder.get_object(widgetName)
        return str(tempWidget.get_text())
    
    def getIntFromEntryBox(self, widgetName):
        tempWidget = self.builder.get_object(widgetName)
        return int(tempWidget.get_active())
    
    def getBoolFromToolToggle(self, widgetName):
        tempWidget = self.builder.get_object(widgetName)
        return tempWidget.get_active()
        
    def getBoolFromEntryBox(self, widgetName):
        tempWidget = self.builder.get_object(widgetName)
        intVal = int(tempWidget.get_active())
        if intVal == 0:
            return(False)
        else:
            return(True)

    def getListFromEntry(self, widgetName):
        tempWidget = self.builder.get_object(widgetName)
        listString = tempWidget.get_text().strip('[]') # resolves to comma-separated list of values
        listItemsText = listString.split(',')
        tempList = []
        
        # first check if we have an empty list
        if listItemsText:
            return []
        
        # otherwise build the list and return it
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
    
    def setLabel(self, widgetName, value, style = 0):
        tempWidget = self.builder.get_object(widgetName)
        if style == 1:
            Gtk.Label.set_markup(tempWidget, value)
        else:
            Gtk.Label.set_text(tempWidget, value)
        
    #def setIntToEntryBox(self, widgetName, value):
    #    tempWidget = self.builder.get_object(widgetName)
    #    Gtk.ComboBox.set_active(tempWidget, value)
        
    #def setListToEntry(self, widgetName, value):
    #    tempWidget = self.builder.get_object(widgetName)
    #    print "fill"
    def deactivateEntry(self, widgetName):
        tempWidget = self.builder.get_object(widgetName)
        tempWidget.set_sensitive(False)

    def activateEntry(self, widgetName):
        tempWidget = self.builder.get_object(widgetName)
        tempWidget.set_sensitive(True)
        
    # plots the input list as a waveform, displaying the data between
    # tMin and tMax, which are percentages of the duration of the waveform. For example,
    # 0, 100 shows the entire waveform (0% to 100%), while 25, 75 shows the middle half;
    # waveformSampleRate provides the timing info to compute the horizontal axis
    def drawBasebandPlot(self, waveformDataList, tMin, tMax, waveformSampleRate):
        
        localWaveform = list(waveformDataList) # make local copy
        
        # NEED to decimate larger lists to fit under 18k
        # truncate large input lists; cairo can only handle 18980 point plots
        #if len(waveformDataList) > 18901:
        #    waveformDataList = waveformDataList[0:18900]
        # NEED to replace this with a smart removal of trailing zeroes from each tx 
        if len(localWaveform) > 14001:
            # NEED to replace this with decimated waveform, not truncated
            print "Warning: baseband waveform longer than 14k samples, truncating..."
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
        # sometimes t and s arrays are sized differently, probably due to rounding
        minSize = min(len(t), len(s))
        if len(t) != minSize:
            t = t[0:minSize]
        if len(s) != minSize:
            s = s[0:minSize]
        
        if wcv.verboseZoom:
            print "length of waveform list: " + str(len(s))
            print "step size:               " + str(stepSize)
            print "length of time vector:   " + str(len(t))
        self.axis.clear() # clear plot before re-plotting
        self.axis.plot(t,s)
        self.axis.grid(True)

        self.axis.axis([startTime, stopTime, -0.1, 1.1])
        self.axis.set_xlabel('time (ms)') # replace with time unit
        self.axis.set_ylabel('Baseband Signal') # replace with ???
        self.canvas.draw()
        self.canvas1.draw()
        self.canvas2.draw()
        
       
    # when the RF Demod button is pushed, we need to take all the settings 
    # that the user has entered into the gui and place them in the current 
    # protocol object; we then call a flowgraph object with the RF
    # configuration specified
    def on_Demodulate_clicked(self, button, data=None):
        print "pushed RF Demod Button"
        
        # NEED to get all other globals relevant to demodulation
        # iq file name? in case it was manually typed?
        # 
        
        ## get all of the values entered on this screen
        wcv.center_freq = 1000000 * self.getFloatFromEntry("centerFreqEntry")
        wcv.samp_rate = 1000000 * self.getFloatFromEntry("sampRateEntry")
        wcv.timingError = self.getFloatFromEntry("unitTimingErrorEntry")/100.0
        wcv.timeBetweenTx = self.getIntFromEntry("interPacketWidthEntry")
        wcv.glitchFilterCount = self.getIntFromEntry("glitchFilterEntry")
        wcv.protocol.modulation = self.getIntFromEntryBox("modulationEntryBox")
        wcv.protocol.frequency = 1000000 * self.getFloatFromEntry("frequencyEntry")
        wcv.protocol.channelWidth = 1000 * self.getFloatFromEntry("channelWidthEntry")
        wcv.protocol.transitionWidth = 1000 * self.getFloatFromEntry("transitionWidthEntry")
        wcv.protocol.threshold = self.getFloatFromEntry("thresholdEntry")
        wcv.protocol.fskDeviation = self.getFloatFromEntry("fskDeviationEntry")
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
            print "FSK Deviation (Hz)    = " + str(wcv.protocol.fskDeviation)
            print "iq File Name          = " + wcv.iqFileName
            print "Waveform File Name    = " + wcv.waveformFileName

        # demodulate the iq data
        wcv.basebandData = demodIQFile(verbose = wcv.verbose,
                                       modulationType = wcv.protocol.modulation,
                                       iqSampleRate = wcv.samp_rate,
                                       basebandSampleRate = wcv.basebandSampleRate,
                                       centerFreq = wcv.center_freq,
                                       frequency = wcv.protocol.frequency,
                                       channelWidth = wcv.protocol.channelWidth,
                                       transitionWidth = wcv.protocol.transitionWidth,
                                       threshold = wcv.protocol.threshold,
                                       fskDeviation = wcv.protocol.fskDeviation,
                                       iqFileName = wcv.iqFileName,
                                       waveformFileName = wcv.waveformFileName
                                       )
        # read baseband waveform data from file
        if wcv.verbose:
            print "baseband data length (raw): " + str(len(wcv.basebandData))

        # split the baseband into individual transmissions and then store each
        # in its own transmission list, to be decoded later
        wcv.txList = buildTxList(basebandData = wcv.basebandData,
                                 basebandSampleRate =  wcv.basebandSampleRate,
                                 interTxTiming = wcv.protocol.interPacketWidth_samp,
                                 glitchFilterCount = wcv.glitchFilterCount,
                                 verbose = wcv.verbose
                                 )
        
        # debug only
        if wcv.verbose:
            print "Number of transmissions broken down: " + str(len(wcv.txList))
            for tx in wcv.txList:
                print "tx waveform list length: " + str(len(tx.waveformData))
                
        if len(wcv.txList) == 0:
            self.setLabel("signalCountLabel", "<b>NO SIGNALS FOUND</b>", 1) # NEED: use bold and/or red text?
            print "NO SIGNALS FOUND AFTER DEMODULATION"
            return(1)
        else:
            self.setLabel("signalCountLabel", "Signals Found: " + str(len(wcv.txList)))
        
        # now plot the first transmission, zoomed out
        wcv.tMin = 0
        wcv.tMax = 100
        if wcv.verbose:
            print "txListLength: " + str(len(wcv.txList[0].waveformData)) + " tMin/Max: " + str(wcv.tMin) + " " + str(wcv.tMax) + " bbsr: " + str(wcv.basebandSampleRate)
            print wcv.txList[0].waveformData
        self.drawBasebandPlot(wcv.txList[0].waveformData, wcv.tMin, wcv.tMax, wcv.basebandSampleRate)
        
        # set range for the tx-select spin button
        self.txSelectSpinButton.set_range(1, len(wcv.txList)+1)
        
        # update the transmission status
        if wcv.verbose:
            print "Baseband separated into individual transmissions."

    def on_encodingEntryBox_changed(self, data=None):
        wcv.protocol.encodingType = self.getIntFromEntryBox("encodingEntryBox")
        # if one of the Manchester types, deactivate the PWM entry boxes and activate the unit entry
        if wcv.protocol.encodingType == 1 or wcv.protocol.encodingType == 2:
            self.activateEntry("payloadUnitEntry")
            self.deactivateEntry("pwmZeroLowEntry")
            self.deactivateEntry("pwmZeroHighEntry")
            self.deactivateEntry("pwmOneLowEntry")
            self.deactivateEntry("pwmOneHighEntry")
        # if PWM/PIE, deactivate unit entry boxes and activate the PWM entries
        else:
            self.deactivateEntry("payloadUnitEntry")
            self.activateEntry("pwmZeroLowEntry")
            self.activateEntry("pwmZeroHighEntry")
            self.activateEntry("pwmOneLowEntry")
            self.activateEntry("pwmOneHighEntry")
             
    # when the Decode button is pushed, we need to take all the settings 
    # that the user has entered into the gui and place them in the current 
    # protocol object; we then call the decoder engine to extract the payload
    def on_Decode_clicked(self, button, data=None):
        if wcv.verbose:
            print "Now Decoding Baseband"
        
        # get global vars
        wcv.center_freq = self.getFloatFromEntry("centerFreqEntry")*1000000.0
        wcv.samp_rate = self.getFloatFromEntry("sampRateEntry")*1000000.0
        wcv.glitchFilterCount = self.getIntFromEntry("glitchFilterEntry")
        wcv.timingError = self.getFloatFromEntry("unitTimingErrorEntry")/100.0
        wcv.timeBetweenTx = self.getIntFromEntry("interPacketWidthEntry")
            
        self.transferGUIDataToProtocol()
        if wcv.verbose:
            print "baseband sample rate:" + str(wcv.basebandSampleRate)
            wcv.protocol.printProtocolFull()
            print "tx list length: " + str(len(wcv.txList))
          
        (wcv.txList, wcv.decodeOutputString) = decodeAllTx(protocol = wcv.protocol, 
                                                           txList = wcv.txList, 
                                                           outputHex = wcv.outputHex,
                                                           timingError = wcv.timingError,
                                                           glitchFilterCount = wcv.glitchFilterCount,
                                                           verbose = wcv.verbose)
        
        # update the display of tx valid flags
        interPacketValidCount = 0
        preambleValidCount = 0
        headerValidCount = 0
        encodingValidCount = 0
        crcValidCount = 0
        txValidCount = 0
        for iTx in wcv.txList:
            interPacketValidCount += iTx.interPacketTimingValid
            preambleValidCount += iTx.preambleValid
            headerValidCount += iTx.headerValid
            encodingValidCount += iTx.encodingValid
            crcValidCount += iTx.crcValid
            txValidCount += iTx.txValid
        
        numTx = len(wcv.txList)
        self.setLabel("guiGoodPackets1", str(txValidCount) + "/" + str(numTx))
        self.setLabel("guiPreambleMatches1", str(preambleValidCount) + "/" + str(numTx))
        self.setLabel("guiEncodingValid1", str(encodingValidCount) + "/" + str(numTx))
        self.setLabel("guiCrcPass1", str(crcValidCount) + "/" + str(numTx))
        
        self.setLabel("guiGoodPackets2", str(txValidCount) + "/" + str(numTx))
        self.setLabel("guiPreambleMatches2", str(preambleValidCount) + "/" + str(numTx))
        self.setLabel("guiEncodingValid2", str(encodingValidCount) + "/" + str(numTx))
        self.setLabel("guiCrcPass2", str(crcValidCount) + "/" + str(numTx))
        
        self.setLabel("guiGoodPackets3", str(txValidCount) + "/" + str(numTx))
        self.setLabel("guiPreambleMatches3", str(preambleValidCount) + "/" + str(numTx))
        self.setLabel("guiEncodingValid3", str(encodingValidCount) + "/" + str(numTx))
        self.setLabel("guiCrcPass3", str(crcValidCount) + "/" + str(numTx))
        
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
        
    
    def on_runStat_clicked(self, button, data=None):
        if wcv.verbose:
            print "Now Computing Payload Statistics..."
            
        # get stats properties
        wcv.protocol.idAddrLow = self.getIntFromEntry("idAddrLowEntry")
        wcv.protocol.idAddrHigh = self.getIntFromEntry("idAddrHighEntry")
        wcv.protocol.val1AddrLow = self.getIntFromEntry("val1AddrLowEntry")
        wcv.protocol.val1AddrHigh = self.getIntFromEntry("val1AddrHighEntry")
        wcv.protocol.val2AddrLow = self.getIntFromEntry("val2AddrLowEntry")
        wcv.protocol.val2AddrHigh = self.getIntFromEntry("val2AddrHighEntry")
        wcv.protocol.val3AddrLow = self.getIntFromEntry("val3AddrLowEntry")
        wcv.protocol.val3AddrHigh = self.getIntFromEntry("val3AddrHighEntry")

        (wcv.bitProbList, idListCounter, value1List) = computeStats(txList = wcv.txList, protocol = wcv.protocol, showAllTx = wcv.showAllTx)
        (wcv.bitProbString, idStatString, valuesString) = buildStatStrings(bitProbList = wcv.bitProbList, idListCounter = idListCounter, value1List = value1List, outputHex = wcv.outputHex)
        
        # display bit probabilities in correct GUI element
        self.bitProbTextViewWidget = self.builder.get_object("bitProbTextView")
        #self.bitProbTextViewWidget.modify_font(Pango.font_description_from_string('Courier 8'))
        self.bitProbTextViewWidget.get_buffer().set_text(wcv.bitProbString)
        
        # display ID frequency data
        self.idValuesTextViewWidget = self.builder.get_object("idValuesTextView")
        #self.idValuesTextViewWidget.modify_font(Pango.font_description_from_string('Courier 8'))
        self.idValuesTextViewWidget.get_buffer().set_text(idStatString)
        
        # need to add values 2 and 3 (or make into a list)        
        ### print value ranges
        self.idValuesTextViewWidget = self.builder.get_object("fieldValuesTextView")
        #self.idValuesTextViewWidget.modify_font(Pango.font_description_from_string('Courier 8'))
        self.idValuesTextViewWidget.get_buffer().set_text(valuesString)

        
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
        self.setEntry("preambleSize2Entry", int(wcv.protocol.preambleSize[1]))
        self.setEntry("headerLengthEntry", wcv.protocol.headerWidth)
        self.setEntry("interPacketWidthEntry", wcv.protocol.interPacketWidth)
        
        # add payload properties
        self.setEntryBox("encodingEntryBox", wcv.protocol.encodingType)
        self.setEntry("payloadUnitEntry", wcv.protocol.unitWidth)
        self.setEntry("pwmZeroLowEntry", wcv.protocol.pwmZeroSymbol[0])
        self.setEntry("pwmZeroHighEntry", wcv.protocol.pwmZeroSymbol[1])
        self.setEntry("pwmOneLowEntry", wcv.protocol.pwmOneSymbol[0])
        self.setEntry("pwmOneHighEntry", wcv.protocol.pwmOneSymbol[1])
        self.setEntry("numPayloadBitsEntry", wcv.protocol.packetSize)
        #self.setEntry("pwmPeriodEntry", wcv.protocol.pwmSymbolSize)
        #self.setEntry("pwmZeroEntry", 
        #             "{0:.1f}".format(100.0*wcv.protocol.pwmZeroSymbol[1]/wcv.protocol.pwmSymbolSize))
        #self.setEntry("pwmOneEntry", 
        #              "{0:.1f}".format(100.0*wcv.protocol.pwmOneSymbol[1]/wcv.protocol.pwmSymbolSize))

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
        self.setEntry("idAddrLowEntry", wcv.protocol.idAddrLow)
        self.setEntry("idAddrHighEntry", wcv.protocol.idAddrHigh)
        self.setEntry("val1AddrLowEntry", wcv.protocol.val1AddrLow)
        self.setEntry("val1AddrHighEntry", wcv.protocol.val1AddrHigh)
        self.setEntry("val2AddrLowEntry", wcv.protocol.val2AddrLow)
        self.setEntry("val2AddrHighEntry", wcv.protocol.val2AddrHigh)
        self.setEntry("val3AddrLowEntry", wcv.protocol.val3AddrLow)
        self.setEntry("val3AddrHighEntry", wcv.protocol.val3AddrHigh)
            
        
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
        
        # setup axis, canvas and figure
        self.figure = Figure(figsize=(8,6), dpi=71) # replace with ???
        self.axis = self.figure.add_subplot(111)
        t = arange(0, 100, 1)
        s = arange(0, 100, 1)
        self.axis.plot(t,s)
        self.axis.axis([0, 100, -0.1, 1.1])
        self.axis.set_xlabel('time (ms)')
        self.axis.set_ylabel('Baseband Signal')
        self.canvas = FigureCanvas(self.figure)  # a Gtk.DrawingArea
        self.canvas1 = FigureCanvas(self.figure)
        self.canvas2 = FigureCanvas(self.figure)
        self.canvas.set_size_request(400,40)
        self.canvas1.set_size_request(400,40)
        self.canvas2.set_size_request(400,40)
        
        # each canvas should be identical; assign to the widgets on 3 tabs
        self.plotWidget = self.builder.get_object("basebandPlot")
        self.plotWidget1 = self.builder.get_object("basebandPlot1")
        self.plotWidget2 = self.builder.get_object("basebandPlot2")
        self.plotWidget.add_with_viewport(self.canvas)
        self.plotWidget1.add_with_viewport(self.canvas1)
        self.plotWidget2.add_with_viewport(self.canvas2)
        self.plotWidget.show_all()
        self.plotWidget1.show_all()
        self.plotWidget2.show_all()
        
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
        #self.userGuideWindow = self.builder.get_object("userGuideWindow")
        self.protocolSaveAsDialog = self.builder.get_object("protocolSaveAsDialog")
        #self.statusbar = self.builder.get_object("statusbar1")
        self.window.unmaximize() # doesn't seem to work
        self.window.show()
        
        # if we were passed a protocol via the command line or via
        # manual definition, populate gui with those values
        #if not (protocol_number == -1):
        self.populateProtocolToGui(protocol) 
