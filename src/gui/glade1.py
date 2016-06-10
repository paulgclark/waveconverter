#!/usr/bin/env python

#import gtk
from gi.repository import Gtk # note gtk+ 3 uses Gtk prefix, not gtk

class Buglump:

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

  def __init__(self):
    self.gladefile = "top_level.glade"
    self.builder = Gtk.Builder()
    self.builder.add_from_file(self.gladefile)
    self.builder.connect_signals(self)
    self.window = self.builder.get_object("window1")
    self.aboutdialog = self.builder.get_object("aboutdialog1")
    self.window.show()

if __name__ == "__main__":
  main = Buglump()
  Gtk.main()
