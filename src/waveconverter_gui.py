# This module contains the GUI code that interfaces with the glade xml file

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
        
    # when the RF Demod button is pushed, we need to take all the settings that the
    # user has entered into the gui and place them in the current protocol object 
    def on_rfDemodButton_clicked(self, button, data=None):
        global protocol
        global center_freq
        print "pushed RF Demod Button"
        
        # get all of the values entered on this screen
        # get object for the center frequency input
        self.centerFreqEntryWidget = self.builder.get_object("centerFreqEntry")
        # then use the widget to get the text
        center_freq = float(self.centerFreqEntryWidget.get_text())
        print "center_freq = " + str(center_freq)
    
    # use the protocol information to populate GUI
    def populateProtocolToGui(self, protocol):
        #global protocol
        # Add RF properties
        frequencyEntryWidget = self.builder.get_object("frequencyEntry") 
        Gtk.Entry.set_text(frequencyEntryWidget, str(protocol.frequency))
        channelWidthEntryWidget = self.builder.get_object("channelWidthEntry") 
        Gtk.Entry.set_text(channelWidthEntryWidget, str(protocol.channelWidth))
        transitionWidthEntryWidget = self.builder.get_object("transitionWidthEntry") 
        Gtk.Entry.set_text(transitionWidthEntryWidget, str(protocol.transitionWidth))
        modulationEntryBoxWidget = self.builder.get_object("modulationEntryBox") 
        Gtk.ComboBox.set_active(modulationEntryBoxWidget, protocol.modulation)
        fskDeviationEntryWidget = self.builder.get_object("fskDeviationEntry") 
        Gtk.Entry.set_text(fskDeviationEntryWidget, str(protocol.fskDeviation))
        
            
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
        
        # if we were passed a protocol via the command line, populate gui with those values
        if not (protocol_number == -1):
            self.populateProtocolToGui(protocol) 
            