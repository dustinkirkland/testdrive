# -*- coding: utf-8 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import sys
import os
import gtk

from testdrivegtk.testdrivegtkconfig import getdatapath

class AboutTestdrivegtkDialog(gtk.AboutDialog):
    __gtype_name__ = "AboutTestdrivegtkDialog"

    def __init__(self):
        """__init__ - This function is typically not called directly.
        Creation of a AboutTestdrivegtkDialog requires redeading the associated ui
        file and parsing the ui definition extrenally, 
        and then calling AboutTestdrivegtkDialog.finish_initializing().
    
        Use the convenience function NewAboutTestdrivegtkDialog to create 
        NewAboutTestdrivegtkDialog objects.
    
        """
        pass

    def finish_initializing(self, builder):
        """finish_initalizing should be called after parsing the ui definition
        and creating a AboutTestdrivegtkDialog object with it in order to finish
        initializing the start of the new AboutTestdrivegtkDialog instance.
    
        """
        #get a reference to the builder and set up the signals
        self.builder = builder
        self.builder.connect_signals(self)

        #code for other initialization actions should be added here

def NewAboutTestdrivegtkDialog():
    """NewAboutTestdrivegtkDialog - returns a fully instantiated
    AboutTestdrivegtkDialog object. Use this function rather than
    creating a AboutTestdrivegtkDialog instance directly.
    
    """

    #look for the ui file that describes the ui
    ui_filename = os.path.join(getdatapath(), 'ui', 'AboutTestdrivegtkDialog.ui')
    if not os.path.exists(ui_filename):
        ui_filename = None

    builder = gtk.Builder()
    builder.add_from_file(ui_filename)    
    dialog = builder.get_object("about_testdrivegtk_dialog")
    dialog.finish_initializing(builder)
    return dialog

if __name__ == "__main__":
    dialog = NewAboutTestdrivegtkDialog()
    dialog.show()
    gtk.main()

