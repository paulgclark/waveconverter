# This module contains the GUI code that interfaces with the glade xml file

import os
import waveConvertVars as wcv
from breakWave import basebandFileToList
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
from statEngine import plugin_stats_stdout
from collections import Counter
import numpy as np
import webbrowser
from operator import itemgetter
from waveConvertVars import showAllTx

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
 
    spinButtonPressed = -1
    
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
    # and stores them in the appropriate global variable. This function is called before
    # demodulating, decoding or computing stats
    def transferGUIDataToGlobals(self):
        wcv.center_freq = 1000000.0 * self.getFloatFromEntry("centerFreqEntry")
        wcv.samp_rate = 1000000.0 * self.getFloatFromEntry("sampRateEntry")
        wcv.timingError = self.getFloatFromEntry("unitTimingErrorEntry")/100.0
        wcv.timeBetweenTx = self.getIntFromEntry("interPacketWidthEntry")
        wcv.glitchFilterCount = self.getIntFromEntry("glitchFilterEntry")
        wcv.protocol.convertTimingToSamples(wcv.basebandSampleRate)
    
    # This function grabs all of the entries that the user has made into the GUI
    # and stores them in the active protocol object. This function is called before
    # saving or using any protocol
    def transferGUIDataToProtocol(self):
        ## get all of the values entered on the demodulation tab
        wcv.iqFileName = self.getStringFromEntry("iqFileNameEntry")
        wcv.waveformFileName = self.getStringFromEntry("bbFileNameEntry")
        wcv.center_freq = 1000000.0 * self.getFloatFromEntry("centerFreqEntry")
        wcv.samp_rate = 1000000.0 * self.getFloatFromEntry("sampRateEntry")
        wcv.protocol.modulation = self.getIntFromEntryBox("modulationEntryBox")
        wcv.protocol.frequency = 1000000.0 * self.getFloatFromEntry("frequencyEntry")
        wcv.protocol.frequencyHopList = self.getListFromEntry("frequencyHopListEntry")
        wcv.protocol.channelWidth = 1000.0 * self.getFloatFromEntry("channelWidthEntry")
        wcv.protocol.transitionWidth = 1000.0 * self.getFloatFromEntry("transitionWidthEntry")
        wcv.protocol.threshold = self.getFloatFromEntry("thresholdEntry")
        wcv.protocol.fskSquelchLeveldB = self.getFloatFromEntry("fskSquelchEntry")
        # may not have an FSK deviation value entered if user is working with OOK
        try:
            wcv.protocol.fskDeviation = 1000.0 * self.getFloatFromEntry("fskDeviationEntry")
        except:
            wcv.protocol.fskDeviation = 0.0
        # get baseband frequency from protocol
        wcv.protocol.bb_samp_rate = 1000000.0 * self.getFloatFromEntry("bbSampRateEntry")
        wcv.basebandSampleRate = wcv.protocol.bb_samp_rate
        wcv.protocol.interPacketSymbol = self.getIntFromEntryBox("idleLevelEntryBox")
        
        
        # get framing properties
        wcv.protocol.preambleType = self.getIntFromEntryBox("preambleTypeEntryBox")
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
        wcv.protocol.arbPreambleList = self.getListFromEntry("arbitraryPreambleTimingEntry")
        wcv.protocol.preamblePulseCount = self.getIntFromEntry("preamblePulseCountEntry")
        
        # get decode properties
        wcv.protocol.encodingType = self.getIntFromEntryBox("encodingEntryBox")
        wcv.protocol.unitWidth = self.getIntFromEntry("payloadUnitEntry")
        if self.getIntFromEntryBox("pwmOrderEntryBox") == 1:
            wcv.protocol.pwmSymbolOrder01 = False
        else:
            wcv.protocol.pwmSymbolOrder01 = True
        wcv.protocol.pwmZeroSymbol[0] = self.getIntFromEntry("pwmZeroLowEntry")
        wcv.protocol.pwmZeroSymbol[1] = self.getIntFromEntry("pwmZeroHighEntry")
        wcv.protocol.pwmOneSymbol[0] = self.getIntFromEntry("pwmOneLowEntry")
        wcv.protocol.pwmOneSymbol[1] = self.getIntFromEntry("pwmOneHighEntry")
        wcv.protocol.packetSize = self.getIntFromEntry("numPayloadBitsEntry")
        
        # load CRC properties
        wcv.protocol.crcPoly = self.getListFromEntry("crcPolynomialEntry")
        for i in xrange(wcv.NUM_CRC):
            wcv.protocol.crcAddr[i][0] = self.getIntFromEntry("crc" + str(i+1) + "StartAddrEntry")
            wcv.protocol.crcAddr[i][1] = wcv.protocol.crcAddr[i][0] + len(wcv.protocol.crcPoly) - 2 # poly is one longer than actual range
            wcv.protocol.crcData[i][0] = self.getIntFromEntry("crc" + str(i+1) + "DataLowEntry")
            wcv.protocol.crcData[i][1] = self.getIntFromEntry("crc" + str(i+1) + "DataHighEntry")
        wcv.protocol.crcInit = self.getIntFromEntry("crcInitEntry")
        wcv.protocol.crcBitOrder = self.getIntFromEntryBox("crcReflectEntryBox")
        wcv.protocol.crcReverseOut = self.getIntFromEntryBox("crcReverseOutEntryBox")
        wcv.protocol.crcFinalXor = self.getListFromEntry("crcFinalXorEntry")
        wcv.protocol.crcPad = self.getIntFromEntryBox("crcPadEntryBox")
        wcv.protocol.crcPadCount = 8*self.getIntFromEntryBox("crcPadCountEntryBox")
        
        # get ACS properties
        wcv.protocol.acsLength = self.getIntFromEntry("acsBitLengthEntry")
        wcv.protocol.acsInvertData = bool(self.getIntFromEntryBox("acsInvertEntryBox"))
        for i in xrange(wcv.NUM_ACS):
            wcv.protocol.acsInitSum[i] = self.getIntFromEntry("acs" + str(i+1) + "InitEntry")
            wcv.protocol.acsAddr[i][0] = self.getIntFromEntry("acs" + str(i+1) + "AddrLowEntry")
            wcv.protocol.acsAddr[i][1] = self.getIntFromEntry("acs" + str(i+1) + "AddrHighEntry")
            wcv.protocol.acsData[i][0] = self.getIntFromEntry("acs" + str(i+1) + "DataLowEntry")
            wcv.protocol.acsData[i][1] = self.getIntFromEntry("acs" + str(i+1) + "DataHighEntry")

        # get stats properties
        for i in xrange(wcv.NUM_ID_FIELDS):
            wcv.protocol.idAddr[i][0] = self.getIntFromEntry("id"+str(i+1)+"AddrLowEntry")
            wcv.protocol.idAddr[i][1] = self.getIntFromEntry("id"+str(i+1)+"AddrHighEntry")
        for i in xrange(wcv.NUM_VAL_FIELDS):
            wcv.protocol.valAddr[i][0] = self.getIntFromEntry("val"+str(i+1)+"AddrLowEntry")
            wcv.protocol.valAddr[i][1] = self.getIntFromEntry("val"+str(i+1)+"AddrHighEntry")

        # these parameters are currently unused but must be in protocol to keep sqllite happy
        wcv.protocol.headerLevel = 0
        wcv.protocol.preambleSync = False
        wcv.protocol.crcPadVal = 0
                
        # when we load new values for the protocol, we need to do the
        # conversion from microseconds to samples
        wcv.protocol.convertTimingToSamples(wcv.basebandSampleRate)
        
        
    def on_loadProtocol_clicked(self, menuitem, data=None):
        if wcv.verbose:
            print "load protocol dialog started"
        
        # generate liststore from protocols in database
        protocolStore = Gtk.ListStore(int, str, str, str, str, str, int) # ID, type, make, model, year, modulation, freq
        for proto in protocolSession.query(ProtocolDefinition):
            # use strings to display modulation and device types
            if proto.modulation == 0:
                modString = "OOK"
            else:
                modString = "FSK"
            devTypeString = wcv.devTypeStrings[proto.deviceType]
            protocolStore.append([proto.protocolId, 
                                  devTypeString,
                                  proto.deviceMake,
                                  proto.deviceModel,
                                  proto.deviceYear,
                                  modString,
                                  proto.frequency])
            if wcv.verbose:
                print "adding protocol to selection list: " + str(proto.protocolId) + \
                      "  " + devTypeString + \
                      "  " + proto.deviceMake + "   " + proto.deviceModel + "  " + proto.deviceYear + \
                      "   " + modString + "   " + str(proto.frequency)
         
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
        if wcv.verbose:
            print wcv.protocol.fullProtocolString()
        
    # this function is called when the toolbar "save as" button is clicked,
    # it brings up a dialog asking the user for a protocol name for the new
    # protocol to be stored under
    def on_saveAsProtocol_clicked(self, menuitem, data=None):
        if wcv.verbose:
            print "save as protocol dialog started"
        
        # clear any existing text in dialog window (previously entered protocol info)
        self.setEntry("protocolSaveAsDeviceMakeEntry", "")
        self.setEntry("protocolSaveAsDeviceModelEntry", "")
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
        wcv.protocol.deviceMake = self.getStringFromEntry("protocolSaveAsDeviceMakeEntry") 
        wcv.protocol.deviceModel = self.getStringFromEntry("protocolSaveAsDeviceModelEntry")
        wcv.protocol.deviceYear = self.getIntFromEntry("protocolSaveAsDeviceYearEntry")
        wcv.protocol.deviceType = self.getIntFromEntryBox("protocolSaveAsDeviceTypeEntryBox")
        if wcv.verbose:
            print wcv.protocol.fullProtocolString()
                    
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
            
    def on_gtk_bbFileOpen_activate(self, menuitem, data=None):
        if wcv.verbose:
            print "menu BB File Open"
        self.fcd = Gtk.FileChooserDialog("Open BB File...",
                                         None,
                                         Gtk.FileChooserAction.OPEN,
                                         (Gtk.STOCK_CANCEL,
                                          Gtk.ResponseType.CANCEL,
                                          Gtk.STOCK_OPEN,
                                          Gtk.ResponseType.ACCEPT))
        self.response = self.fcd.run()
        if self.response == Gtk.ResponseType.ACCEPT:
            print "Selected filepath: %s" % self.fcd.get_filename()
            wcv.waveformFileName = self.fcd.get_filename()
            bbFileNameEntryWidget = self.builder.get_object("bbFileNameEntry")
            Gtk.Entry.set_text(bbFileNameEntryWidget, str(wcv.waveformFileName))
            self.fcd.destroy()
            
    def on_userGuideMenu_activate(self, menuitem, data=None):
        if wcv.verbose:
            print "opening user guide..."

        # get path of doc directory (assuming this is running in src subdir of install directory
        os.chdir('../doc')
        docPath = os.getcwd()
        webbrowser.open('file://' + docPath + '/user_guide.pdf')
                    
    def changeTxNumberToView(self, txNum):
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
        
    def on_transmissionNumberSelect2_value_changed(self, spinButton, data=None):
        # find out if this was the button pressed
        if self.spinButtonPressed == -1:
            self.spinButtonPressed = 2
        
            txNum = spinButton.get_value_as_int() - 1 # button counts from 1 to n; array from 0 to n-1
        
            # first update the other two widgets in other tabs
            self.setSpinButtonValue("transmissionNumberSelect", txNum + 1)
            self.setSpinButtonValue("transmissionNumberSelect1", txNum + 1)        
        
            # then change the view
            self.changeTxNumberToView(txNum)
            
            # now return control
            self.spinButtonPressed = -1

    def on_transmissionNumberSelect1_value_changed(self, spinButton, data=None):
        # find out if this was the button pressed
        if self.spinButtonPressed == -1:
            self.spinButtonPressed = 1
            
            txNum = spinButton.get_value_as_int() - 1 # button counts from 1 to n; array from 0 to n-1
        
            # first update the other two widgets in other tabs
            self.setSpinButtonValue("transmissionNumberSelect", txNum + 1)
            self.setSpinButtonValue("transmissionNumberSelect2", txNum + 1)        
        
            # then change the view
            self.changeTxNumberToView(txNum)

            # now return control
            self.spinButtonPressed = -1
        
    def on_transmissionNumberSelect_value_changed(self, spinButton, data=None):
        # find out if this was the button pressed
        if self.spinButtonPressed == -1:
            self.spinButtonPressed = 0
            
            txNum = spinButton.get_value_as_int() - 1 # button counts from 1 to n; array from 0 to n-1
        
            # first update the other two widgets in other tabs
            self.setSpinButtonValue("transmissionNumberSelect1", txNum + 1)
            self.setSpinButtonValue("transmissionNumberSelect2", txNum + 1)      
        
            self.changeTxNumberToView(txNum)
            
            # now return control
            self.spinButtonPressed = -1

    def on_panRightButton_clicked(self, button, data=None):
        if wcv.verboseZoom:
            print "Panning Right"
            
        # get center point of current plot
        center = (wcv.tMax + wcv.tMin)/2.0
        # get current zoom size
        zoomSize = 1.0*(wcv.tMax - wcv.tMin)
        
        # change center by increasing it to midway between current center 
        # and right-most extent
        center += zoomSize/4
        
        # update extents and redraw
        wcv.tMin = (center - zoomSize/2.0) # int((center - zoomSize/2.0) + 0.5)
        wcv.tMax = (center + zoomSize/2.0) # int((center + zoomSize/2.0) + 0.5)
        
        # trap for panning right past max extent
        if wcv.tMax > 100:
            wcv.tMax = 100
            wcv.tMin = 100 - zoomSize
            
        self.drawBasebandPlot(wcv.txList[wcv.txNum].waveformData, 
                              wcv.tMin, wcv.tMax, wcv.basebandSampleRate)
        
            
    def on_panLeftButton_clicked(self, button, data=None):
        if wcv.verboseZoom:
            print "Panning Left"
            
        # get center point of current plot
        center = (wcv.tMax + wcv.tMin)/2.0
        # get current zoom size
        zoomSize = 1.0*(wcv.tMax - wcv.tMin)
        
        # change center by decreasing it to midway between current center 
        # and left-most extent
        center -= zoomSize/4
        
        # update extents and redraw
        wcv.tMin = (center - zoomSize/2.0) # int((center - zoomSize/2.0) + 0.5)
        wcv.tMax = (center + zoomSize/2.0) # int((center + zoomSize/2.0) + 0.5)
        
        # trap for panning left past min extent
        if wcv.tMin < 0:
            wcv.tMin = 0
            wcv.tMax = zoomSize
            
        self.drawBasebandPlot(wcv.txList[wcv.txNum].waveformData, 
                              wcv.tMin, wcv.tMax, wcv.basebandSampleRate)
            
    def on_zoomFullButton_clicked(self, button, data=None):
        if wcv.verboseZoom:
            print "Zooming Out Full"
        wcv.tMin = 0.0 # 0
        wcv.tMax = 100.0 # 100
        
        self.drawBasebandPlot(wcv.txList[wcv.txNum].waveformData, 
                              wcv.tMin, wcv.tMax, wcv.basebandSampleRate)
            
    def on_zoomInButton_clicked(self, button, data=None):
        if wcv.verboseZoom:
            print "Zooming In"
            
        # get center point of current plot
        center = (wcv.tMax + wcv.tMin)/2.0
        # get current zoom size and cut in half
        zoomSize = (wcv.tMax - wcv.tMin)/2.0
        
        wcv.tMin = (center - zoomSize/2.0) # int((center - zoomSize/2.0) + 0.5)
        wcv.tMax = (center + zoomSize/2.0) # int((center + zoomSize/2.0) + 0.5)
        
        self.drawBasebandPlot(wcv.txList[wcv.txNum].waveformData, 
                              wcv.tMin, wcv.tMax, wcv.basebandSampleRate)
        
    def on_zoomOutButton_clicked(self, button, data=None):
        if wcv.verboseZoom:
            print "Zooming Out"
            
        # get center point of current plot
        center = (wcv.tMax + wcv.tMin)/2.0
        # get current zoom size and double
        zoomSize = (wcv.tMax - wcv.tMin)*2.0
        
        if wcv.verboseZoom:
            print "center: " + str(center)
            print "zoomSize: " + str(zoomSize)
        
        wcv.tMin = (center - zoomSize/2.0) # int((center - zoomSize/2.0) + 0.5)
        wcv.tMax = (center + zoomSize/2.0) # int((center + zoomSize/2.0) + 0.5)
        if wcv.verbose:
            print "tMin: " + str(wcv.tMin)
            print "tMax: " + str(wcv.tMax)
        
        # trap for zoom out past max extent
        if wcv.tMin < 0:
            wcv.tMin = 0.0 # 0
            
        if wcv.tMax > 100:
            wcv.tMax = 100.0 # 100
        
        self.drawBasebandPlot(wcv.txList[wcv.txNum].waveformData, 
                              wcv.tMin, wcv.tMax, wcv.basebandSampleRate)
        
        
    # 
    def on_showAllButton_toggled(self, button, data=None):
        wcv.showAllTx = self.getBoolFromToolToggle("showAllButton")
        if wcv.verboseZoom:
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
        listString = tempWidget.get_text().strip('[]') # resolves to string of comma-separated values
        listItemsText = listString.split(',')
        tempList = []
        
        # first check if we have an empty list
        if not listItemsText or listItemsText == ['']:
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
            
    def setSpinButtonValue(self, widgetName, value):
        tempWidget = self.builder.get_object(widgetName)
        Gtk.SpinButton.set_value(tempWidget, value)

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
        
        # decimate large input lists; cairo can only handle 18980 point plots
        if len(waveformDataList) > 18000:
            # NEED to replace this with decimated waveform, not truncated
            if wcv.verboseZoom:
                print "Baseband waveform longer than 18k samples, decimating..."
            decimationFactor = 1 + int(len(waveformDataList)/18000)
            localWaveform = waveformDataList[::decimationFactor]
        else:
            localWaveform = list(waveformDataList) # make local copy
            decimationFactor = 1  
        
        # for use in building the horizontal axis labels
        waveformLength = len(waveformDataList)
        startIndex = int((tMin/100.0) * waveformLength)
        stopIndex =  int((tMax/100.0) * waveformLength)
        # for operating on the actual plot data that's been decimated above
        waveformLengthDecimated = len(localWaveform) 
        startIndexDecimated = int((tMin/100.0) * waveformLengthDecimated)
        stopIndexDecimated =  int((tMax/100.0) * waveformLengthDecimated)
        
        # compute plot area in milliseconds    
        stepSize = (1/waveformSampleRate) * 1000.0
        startTime = startIndex * stepSize
        stopTime = stopIndex * stepSize
        
        if wcv.verboseZoom:
            print "displaying new plot"
            print "list size = " + str(waveformLength)
            print "tMin(%) = " + str(tMin)
            print "tMax(%) = " + str(tMax)
            print "start Index = " + str(startIndexDecimated)
            print "stop Index = " + str(stopIndexDecimated)
            print "start time = " + str(startTime)
            print "stop time = " + str(stopTime)
            
        t = arange(startTime, stopTime, stepSize*decimationFactor)
        s = localWaveform[startIndexDecimated:stopIndexDecimated]
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

        # get values from GUI        
        self.transferGUIDataToGlobals()
        self.transferGUIDataToProtocol()
        
        # if we have a baseband file name, use it to get the bb data
        if len(wcv.waveformFileName) > 0:
            wcv.basebandData = basebandFileToList(wcv.waveformFileName)
        elif len(wcv.iqFileName) > 0:
            wcv.basebandData = demodIQFile(verbose = wcv.verbose,
                                           modulationType = wcv.protocol.modulation,
                                           iqSampleRate = wcv.samp_rate,
                                           basebandSampleRate = wcv.basebandSampleRate,
                                           centerFreq = wcv.center_freq,
                                           frequency = wcv.protocol.frequency,
                                           frequencyHopList = wcv.protocol.frequencyHopList,
                                           channelWidth = wcv.protocol.channelWidth,
                                           transitionWidth = wcv.protocol.transitionWidth,
                                           threshold = wcv.protocol.threshold,
                                           fskSquelch = wcv.protocol.fskSquelchLeveldB,
                                           fskDeviation = wcv.protocol.fskDeviation,
                                           iqFileName = wcv.iqFileName,
                                           waveformFileName = ""
                                           )
        else:
            print "No IQ or baseband file given"
            return 0
        
        # read baseband waveform data from file
        if wcv.verbose:
            print "baseband data length (raw): " + str(len(wcv.basebandData))

        # split the baseband into individual transmissions and then store each
        # in its own transmission list, to be decoded later
        wcv.txList = buildTxList(basebandData = wcv.basebandData,
                                 basebandSampleRate =  wcv.basebandSampleRate,
                                 interTxTiming = wcv.protocol.interPacketWidth_samp,
                                 glitchFilterCount = wcv.glitchFilterCount,
                                 interTxLevel = wcv.protocol.interPacketSymbol,
                                 verbose = wcv.verbose)
        
        # debug only
        if wcv.verbose:
            print "Number of transmissions broken down: " + str(len(wcv.txList))
            for tx in wcv.txList:
                print "tx waveform list length: " + str(len(tx.waveformData))
                
        if len(wcv.txList) == 0:
            self.setLabel("signalCountLabel", "<b>NO SIGNALS FOUND</b>", 1) # NEED: use bold and/or red text?
            self.setLabel("signalCountLabel1", "<b>NO SIGNALS FOUND</b>", 1)
            self.setLabel("signalCountLabel2", "<b>NO SIGNALS FOUND</b>", 1)
            print "NO SIGNALS FOUND AFTER DEMODULATION"
            return(1)
        else:
            self.setLabel("signalCountLabel", "Signals Found: " + str(len(wcv.txList)))
            self.setLabel("signalCountLabel1", "Signals Found: " + str(len(wcv.txList)))
            self.setLabel("signalCountLabel2", "Signals Found: " + str(len(wcv.txList)))
        
        # now plot the first transmission, zoomed out
        wcv.tMin = 0
        wcv.tMax = 100
        #if wcv.verbose:
        #    print "txListLength: " + str(len(wcv.txList[0].waveformData)) + " tMin/Max: " + str(wcv.tMin) + " " + str(wcv.tMax) + " bbsr: " + str(wcv.basebandSampleRate)
        #    print wcv.txList[0].waveformData
        self.drawBasebandPlot(wcv.txList[0].waveformData, wcv.tMin, wcv.tMax, wcv.basebandSampleRate)
        
        # set range for the tx-select spin button
        self.txSelectSpinButton.set_range(1, len(wcv.txList)+1)
        self.txSelectSpinButton1.set_range(1, len(wcv.txList)+1)
        self.txSelectSpinButton2.set_range(1, len(wcv.txList)+1)
        
        # update the transmission status
        if wcv.verbose:
            print "Baseband separated into individual transmissions."

    def on_modulationEntryBox_changed(self, data=None):
        wcv.protocol.modulation = self.getBoolFromEntryBox("modulationEntryBox")
        if wcv.protocol.modulation == wcv.MOD_OOK:
            self.activateEntry("thresholdEntry")
            self.deactivateEntry("fskDeviationEntry")
            self.deactivateEntry("fskSquelchEntry")
        elif wcv.protocol.modulation == wcv.MOD_FSK:
            self.deactivateEntry("thresholdEntry")
            self.activateEntry("fskDeviationEntry")
            self.activateEntry("fskSquelchEntry")

    def on_encodingEntryBox_changed(self, data=None):
        wcv.protocol.encodingType = self.getIntFromEntryBox("encodingEntryBox")
        # if one of the Manchester types, deactivate the PWM entry boxes and activate the unit entry
        if wcv.protocol.encodingType == wcv.STD_MANCHESTER or wcv.protocol.encodingType == wcv.INV_MANCHESTER:
            self.activateEntry("payloadUnitEntry")
            self.deactivateEntry("pwmZeroLowEntry")
            self.deactivateEntry("pwmZeroHighEntry")
            self.deactivateEntry("pwmOneLowEntry")
            self.deactivateEntry("pwmOneHighEntry")
        # for the NO ENCODING state, we need only the unit timing
        elif wcv.protocol.encodingType == wcv.NO_ENCODING:
            self.deactivateEntry("payloadUnitEntry")
            self.activateEntry("pwmZeroLowEntry")
            self.deactivateEntry("pwmZeroHighEntry")
            self.deactivateEntry("pwmOneLowEntry")
            self.activateEntry("pwmOneHighEntry")            
        # if PWM/PIE, deactivate unit entry boxes and activate the PWM entries
        else:
            self.deactivateEntry("payloadUnitEntry")
            self.activateEntry("pwmZeroLowEntry")
            self.activateEntry("pwmZeroHighEntry")
            self.activateEntry("pwmOneLowEntry")
            self.activateEntry("pwmOneHighEntry")
             
    # create signal from preamble type box and gray out all the unused properties
    def on_preambleTypeEntryBox_changed(self, data=None):
        wcv.protocol.preambleType = self.getIntFromEntryBox("preambleTypeEntryBox")
        # if we are doing a regular preamble, then gray out the arbitrary entry
        if wcv.protocol.preambleType == wcv.PREAMBLE_REG:
            self.activateEntry("preambleLowEntry")
            self.activateEntry("preambleHighEntry")
            self.activateEntry("preambleSize1Entry")
            self.activateEntry("preambleSize2Entry")
            self.activateEntry("headerLengthEntry")
            self.deactivateEntry("arbitraryPreambleTimingEntry")
            self.deactivateEntry("preamblePulseCountEntry")
        # else gray out everything but the arbitrary entry
        elif wcv.protocol.preambleType == wcv.PREAMBLE_ARB:
            self.deactivateEntry("preambleLowEntry")
            self.deactivateEntry("preambleHighEntry")
            self.deactivateEntry("preambleSize1Entry")
            self.deactivateEntry("preambleSize2Entry")
            self.deactivateEntry("headerLengthEntry")
            self.activateEntry("arbitraryPreambleTimingEntry")
            self.deactivateEntry("preamblePulseCountEntry")
        else:            
            self.deactivateEntry("preambleLowEntry")
            self.deactivateEntry("preambleHighEntry")
            self.deactivateEntry("preambleSize1Entry")
            self.deactivateEntry("preambleSize2Entry")
            self.deactivateEntry("headerLengthEntry")
            self.deactivateEntry("arbitraryPreambleTimingEntry")
            self.activateEntry("preamblePulseCountEntry")
    
    # when the Decode button is pushed, we need to take all the settings 
    # that the user has entered into the gui and place them in the current 
    # protocol object; we then call the decoder engine to extract the payload
    def on_Decode_clicked(self, button, data=None):
        if wcv.verbose:
            print "Now Decoding Baseband"

        # get values from GUI        
        self.transferGUIDataToGlobals()
        self.transferGUIDataToProtocol()
        
        if wcv.verbose:
            print "baseband sample rate:" + str(wcv.basebandSampleRate)
            print wcv.protocol.fullProtocolString()
            print "tx list length: " + str(len(wcv.txList))
          
        (wcv.txList, wcv.decodeOutputString) = decodeAllTx(protocol = wcv.protocol, 
                                                           txList = wcv.txList, 
                                                           outputHex = wcv.outputHex,
                                                           timingError = wcv.timingError,
                                                           glitchFilterCount = wcv.glitchFilterCount,
                                                           verbose = wcv.verbose,
                                                           showAllTx = wcv.showAllTx)
        
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
        if len(wcv.protocol.crcPoly) <= 0:
            crcStringOut = "N/A"
        else:
            crcStringOut =  str(crcValidCount) + "/" + str(numTx)
        self.setLabel("guiGoodPackets1", str(txValidCount) + "/" + str(numTx))
        self.setLabel("guiPreambleMatches1", str(preambleValidCount) + "/" + str(numTx))
        self.setLabel("guiEncodingValid1", str(encodingValidCount) + "/" + str(numTx))
        self.setLabel("guiCrcPass1", crcStringOut)
        
        self.setLabel("guiGoodPackets2", str(txValidCount) + "/" + str(numTx))
        self.setLabel("guiPreambleMatches2", str(preambleValidCount) + "/" + str(numTx))
        self.setLabel("guiEncodingValid2", str(encodingValidCount) + "/" + str(numTx))
        self.setLabel("guiCrcPass2", crcStringOut)
        
        self.setLabel("guiGoodPackets3", str(txValidCount) + "/" + str(numTx))
        self.setLabel("guiPreambleMatches3", str(preambleValidCount) + "/" + str(numTx))
        self.setLabel("guiEncodingValid3", str(encodingValidCount) + "/" + str(numTx))
        self.setLabel("guiCrcPass3", crcStringOut)
        
        self.setLabel("guiGoodPackets4", str(txValidCount) + "/" + str(numTx))
        self.setLabel("guiPreambleMatches4", str(preambleValidCount) + "/" + str(numTx))
        self.setLabel("guiEncodingValid4", str(encodingValidCount) + "/" + str(numTx))
        self.setLabel("guiCrcPass4", crcStringOut)
                        
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
            
        # get values from GUI
        self.transferGUIDataToGlobals()
        self.transferGUIDataToProtocol()

        (wcv.bitProbList, idListMaster, valListMaster, payloadLenList) = computeStats(txList = wcv.txList, 
                                                                                      protocol = wcv.protocol, 
                                                                                      showAllTx = wcv.showAllTx)
        
        # experimental new feature
        #from statEngine import computeUavStats
        plugin_stats_stdout(txList = wcv.txList,
                            protocol = wcv.protocol,
                            showAllTx = wcv.showAllTx)
        """
        uavValList = computeUavStats(txList = wcv.txList,
                                     protocol = wcv.protocol,
                                     showAllTx = wcv.showAllTx)
        """

        (wcv.bitProbString, idStatString, valuesString) = buildStatStrings(bitProbList = wcv.bitProbList, 
                                                                           idListMaster = idListMaster, 
                                                                           valListMaster = valListMaster,
                                                                           payloadLenList = payloadLenList, 
                                                                           outputHex = wcv.outputHex)
        
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
        self.setEntry("bbFileNameEntry", wcv.waveformFileName)
        self.setEntry("frequencyEntry", wcv.protocol.frequency/1000000.0)
        self.setEntry("frequencyHopListEntry", wcv.protocol.frequencyHopList)
        self.setEntry("channelWidthEntry", wcv.protocol.channelWidth/1000.0)
        self.setEntry("transitionWidthEntry", wcv.protocol.transitionWidth/1000.0)
        self.setEntryBox("modulationEntryBox", wcv.protocol.modulation)
        self.setEntry("fskDeviationEntry", wcv.protocol.fskDeviation/1000.0)
        self.setEntry("thresholdEntry", wcv.protocol.threshold)
        self.setEntry("fskSquelchEntry", wcv.protocol.fskSquelchLeveldB)
        self.setEntry("bbSampRateEntry", wcv.protocol.bb_samp_rate/1000000.0)
        self.setEntryBox("idleLevelEntryBox", wcv.protocol.interPacketSymbol)
        
        # add preamble properties
        self.setEntryBox("preambleTypeEntryBox", wcv.protocol.preambleType)
        self.setEntry("preambleLowEntry", wcv.protocol.preambleSymbolLow)
        self.setEntry("preambleHighEntry", wcv.protocol.preambleSymbolHigh)
        self.setEntry("preambleSize1Entry", int(wcv.protocol.preambleSize[0]))
        self.setEntry("preambleSize2Entry", int(wcv.protocol.preambleSize[1]))
        self.setEntry("headerLengthEntry", wcv.protocol.headerWidth)
        self.setEntry("interPacketWidthEntry", wcv.protocol.interPacketWidth)
        self.setEntry("arbitraryPreambleTimingEntry", wcv.protocol.arbPreambleList)
        self.setEntry("preamblePulseCountEntry" , wcv.protocol.preamblePulseCount)
                
        # add payload properties
        self.setEntryBox("encodingEntryBox", wcv.protocol.encodingType)
        self.setEntry("payloadUnitEntry", wcv.protocol.unitWidth)
        if wcv.protocol.pwmSymbolOrder01:
            self.setEntryBox("pwmOrderEntryBox", 0)
        else:
            self.setEntryBox("pwmOrderEntryBox", 1)

        self.setEntry("pwmZeroLowEntry", wcv.protocol.pwmZeroSymbol[0])
        self.setEntry("pwmZeroHighEntry", wcv.protocol.pwmZeroSymbol[1])
        self.setEntry("pwmOneLowEntry", wcv.protocol.pwmOneSymbol[0])
        self.setEntry("pwmOneHighEntry", wcv.protocol.pwmOneSymbol[1])
        self.setEntry("numPayloadBitsEntry", wcv.protocol.packetSize)

        # add CRC properties
        self.setEntry("crcLengthEntry", len(wcv.protocol.crcPoly))
        for i in xrange(wcv.NUM_CRC):
            self.setEntry("crc" + str(i+1) + "StartAddrEntry", wcv.protocol.crcAddr[i][0])
            self.setEntry("crc" + str(i+1) + "DataLowEntry", wcv.protocol.crcData[i][0])
            self.setEntry("crc" + str(i+1) + "DataHighEntry", wcv.protocol.crcData[i][1])
        self.setEntry("crcPolynomialEntry", wcv.protocol.crcPoly)
        self.setEntry("crcInitEntry", wcv.protocol.crcInit)
        self.setEntryBox("crcReflectEntryBox", wcv.protocol.crcBitOrder)
        self.setEntryBox("crcReverseOutEntryBox", wcv.protocol.crcReverseOut)
        self.setEntry("crcFinalXorEntry", wcv.protocol.crcFinalXor)
        self.setEntryBox("crcPadEntryBox", wcv.protocol.crcPad)
        self.setEntryBox("crcPadCountEntryBox", wcv.protocol.crcPadCount/8)
        
        # add the ACS properties
        self.setEntry("acsBitLengthEntry", wcv.protocol.acsLength)
        self.setEntryBox("acsInvertEntryBox", int(wcv.protocol.acsInvertData))
        for i in xrange(wcv.NUM_ACS):
            self.setEntry("acs" + str(i+1) + "InitEntry", wcv.protocol.acsInitSum[i])
            self.setEntry("acs" + str(i+1) + "AddrLowEntry", wcv.protocol.acsAddr[i][0])
            self.setEntry("acs" + str(i+1) + "AddrHighEntry", wcv.protocol.acsAddr[i][1])            
            self.setEntry("acs" + str(i+1) + "DataLowEntry", wcv.protocol.acsData[i][0])
            self.setEntry("acs" + str(i+1) + "DataHighEntry", wcv.protocol.acsData[i][1])

        # add payload statistics properties
        self.setEntry("id1AddrLowEntry", wcv.protocol.idAddr[0][0])
        self.setEntry("id1AddrHighEntry", wcv.protocol.idAddr[0][1])
        self.setEntry("id2AddrLowEntry", wcv.protocol.idAddr[1][0])
        self.setEntry("id2AddrHighEntry", wcv.protocol.idAddr[1][1])
        self.setEntry("id3AddrLowEntry", wcv.protocol.idAddr[2][0])
        self.setEntry("id3AddrHighEntry", wcv.protocol.idAddr[2][1])
        self.setEntry("id4AddrLowEntry", wcv.protocol.idAddr[3][0])
        self.setEntry("id4AddrHighEntry", wcv.protocol.idAddr[3][1])
        self.setEntry("id5AddrLowEntry", wcv.protocol.idAddr[4][0])
        self.setEntry("id5AddrHighEntry", wcv.protocol.idAddr[4][1])
        self.setEntry("id6AddrLowEntry", wcv.protocol.idAddr[5][0])
        self.setEntry("id6AddrHighEntry", wcv.protocol.idAddr[5][1])
        self.setEntry("val1AddrLowEntry", wcv.protocol.valAddr[0][0])
        self.setEntry("val1AddrHighEntry", wcv.protocol.valAddr[0][1])
        self.setEntry("val2AddrLowEntry", wcv.protocol.valAddr[1][0])
        self.setEntry("val2AddrHighEntry", wcv.protocol.valAddr[1][1])
        self.setEntry("val3AddrLowEntry", wcv.protocol.valAddr[2][0])
        self.setEntry("val3AddrHighEntry", wcv.protocol.valAddr[2][1])
            
        
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
        #
        self.txSelectSpinButton1 = self.builder.get_object("transmissionNumberSelect1")
        self.spinButtonAdjustment1 = Gtk.Adjustment(0, 0, 0, 1, 1, 1)
        self.txSelectSpinButton1.set_adjustment(self.spinButtonAdjustment1)
        #
        self.txSelectSpinButton2 = self.builder.get_object("transmissionNumberSelect2")
        self.spinButtonAdjustment2 = Gtk.Adjustment(0, 0, 0, 1, 1, 1)
        self.txSelectSpinButton2.set_adjustment(self.spinButtonAdjustment2)
        
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
        renderer_make = Gtk.CellRendererText()
        column_make = Gtk.TreeViewColumn("Make", renderer_make, text=2)
        self.protocolTreeView.append_column(column_make)
        renderer_model = Gtk.CellRendererText()
        column_model = Gtk.TreeViewColumn("Model", renderer_model, text=3)
        self.protocolTreeView.append_column(column_model)
        renderer_year = Gtk.CellRendererText()
        column_year = Gtk.TreeViewColumn("Year", renderer_year, text=4)
        self.protocolTreeView.append_column(column_year)
        renderer_mod = Gtk.CellRendererText()
        column_mod = Gtk.TreeViewColumn("Modulation", renderer_mod, text=5)
        self.protocolTreeView.append_column(column_mod)
        renderer_freq = Gtk.CellRendererText()
        column_freq = Gtk.TreeViewColumn("Frequency", renderer_freq, text=6)
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
