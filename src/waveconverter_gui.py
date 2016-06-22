# This module contains the GUI code that interfaces with the glade xml file

#from waveConvertVars import *
import waveConvertVars as wcv
from demod_rf import ook_flowgraph

# require Gtk 3.0+ to work
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk # note gtk+3 uses Gtk, not gtk

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

#    def on_centerFreqEntry_activate(self, menuitem, data=None):
#        global protocol
#        print "Center Frequency changed"
#        wcv.center_freq = float(self.get_text()) * 1000000

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

    # when the RF Demod button is pushed, we need to take all the settings 
    # that the user has entered into the gui and place them in the current 
    # protocol object; we then call a flowgraph object with the RF
    # configuration specified
    def on_rfDemodButton_clicked(self, button, data=None):
        print "pushed RF Demod Button"
        
        ## get all of the values entered on this screen
        # get object for the center frequency input
        self.centerFreqEntryWidget = self.builder.get_object("centerFreqEntry")
        # then use the widget to get the text
        wcv.center_freq = float(self.centerFreqEntryWidget.get_text()) * 1000000
        self.sampRateEntryWidget = self.builder.get_object("sampRateEntry")
        wcv.samp_rate = float(self.sampRateEntryWidget.get_text()) * 1000000
        self.modulationEntryWidget = self.builder.get_object("modulationEntryBox")
        wcv.protocol.modulation = int(self.modulationEntryWidget.get_active())
        self.frequencyEntryWidget = self.builder.get_object("frequencyEntry")
        wcv.protocol.tuneFreq = float(self.frequencyEntryWidget.get_text()) * 1000000
        self.channelWidthEntryWidget = self.builder.get_object("channelWidthEntry")
        wcv.protocol.channelWidth = float(self.channelWidthEntryWidget.get_text()) * 1000
        self.transitionWidthEntryWidget = self.builder.get_object("transitionWidthEntry")
        wcv.protocol.transitionWidth = float(self.transitionWidthEntryWidget.get_text()) * 1000
        self.thresholdEntryWidget = self.builder.get_object("thresholdEntry")
        wcv.protocol.threshold = float(self.thresholdEntryWidget.get_text())

        if wcv.verbose:
            print "center_freq (Hz)      = " + str(wcv.center_freq)
            print "samp_rate (Hz)        = " + str(wcv.samp_rate)
            print "modulation            = " + str(wcv.protocol.modulation)
            print "tune frequency (Hz)   = " + str(wcv.protocol.tuneFreq)
            print "channel width (Hz)    = " + str(wcv.protocol.channelWidth)
            print "transition width (Hz) = " + str(wcv.protocol.transitionWidth)
            print "threshold             = " + str(wcv.protocol.threshold)
            print "iq File Name          = " + wcv.iqFileName

        # create flowgraph object and execute flowgraph
        try:
            if wcv.verbose:
                print "Running Demodulation Flowgraph"
            if wcv.protocol.modulation == wcv.MOD_OOK:
                flowgraphObject = ook_flowgraph(wcv.samp_rate, # rate_in
                                            wcv.basebandSampleRate, # rate_out
                                            wcv.center_freq, # center_freq
                                            wcv.protocol.tuneFreq, 
                                            wcv.protocol.channelWidth,
                                            wcv.protocol.transitionWidth,
                                            wcv.protocol.threshold,
                                            wcv.iqFileName, # iq_filename
                                            wcv.waveformFileName) # temp digfile
                flowgraphObject.run()
            else:
                print "FSK flowgraph not yet in place"
        except [[KeyboardInterrupt]]:
            pass
        print "Flowgraph completed"
    
    # use the protocol information to populate GUI
    def populateProtocolToGui(self, protocol):
        #global protocol
        # Add RF properties
        iqFileNameEntryWidget = self.builder.get_object("iqFileNameEntry")
        Gtk.Entry.set_text(iqFileNameEntryWidget, str(wcv.iqFileName))
        frequencyEntryWidget = self.builder.get_object("frequencyEntry") 
        Gtk.Entry.set_text(frequencyEntryWidget, str(wcv.protocol.frequency))
        channelWidthEntryWidget = self.builder.get_object("channelWidthEntry") 
        Gtk.Entry.set_text(channelWidthEntryWidget, str(wcv.protocol.channelWidth))
        transitionWidthEntryWidget = self.builder.get_object("transitionWidthEntry") 
        Gtk.Entry.set_text(transitionWidthEntryWidget, str(wcv.protocol.transitionWidth))
        modulationEntryBoxWidget = self.builder.get_object("modulationEntryBox") 
        #Gtk.ComboBox.set_active(modulationEntryBoxWidget, wcv.protocol.modulation)
        Gtk.ComboBox.set_active(modulationEntryBoxWidget, 1) # NEED TO FIX
        fskDeviationEntryWidget = self.builder.get_object("fskDeviationEntry") 
        Gtk.Entry.set_text(fskDeviationEntryWidget, str(wcv.protocol.fskDeviation))
        thresholdEntryWidget = self.builder.get_object("thresholdEntry") 
        Gtk.Entry.set_text(thresholdEntryWidget, str(wcv.protocol.threshold))

            
    def __init__(self, protocol_number, protocol):
        #global protocol
        self.gladefile = "gui/top_level.glade"
        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.gladefile)
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("window1")
        self.aboutdialog = self.builder.get_object("aboutdialog1")
        #self.statusbar = self.builder.get_object("statusbar1")
        self.window.show()
        
        # if we were passed a protocol via the command line or via
        # manual definition, populate gui with those values
        #if not (protocol_number == -1):
        self.populateProtocolToGui(protocol) 
            
