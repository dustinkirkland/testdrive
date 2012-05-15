# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2010 Canonical Ltd.
# 
# Authors:
#   Andres Rodriguez <andreserl@ubuntu.com>
# 
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

import gtk

from testdrivegtk.helpers import get_builder

import gettext
from gettext import gettext as _
gettext.textdomain('testdrive')

import commands
version = commands.getstatusoutput("dpkg -l testdrive-gtk | tail -n1 | awk '{print $3}'")

__version__ = version[1].split("-0")[0]
__licensenotice__ = 'This program is free software: you can redistribute it and/or modify\n\
it under the terms of the GNU General Public License as published by\n\
the Free Software Foundation, either version 3 of the License, or\n\
(at your option) any later version.\n\
\n\
This program is distributed in the hope that it will be useful,\n\
but WITHOUT ANY WARRANTY; without even the implied warranty of\n\
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n\
GNU General Public License for more details.\n\
\n\
You should have received a copy of the GNU General Public License\n\
along with this program.  If not, see <http://www.gnu.org/licenses/>.'
__authors__ = ['Andres Rodriguez <andreserl@ubuntu.com>']
__description__ = 'PyGTK Front-end for TestDrive'
__website__ = "https://launchpad.net/testdrive"
__copyright__ = "Copyright © 2010 - 2012 Canonical Ltd."

class AboutTestdrivegtkDialog(gtk.AboutDialog):
    __gtype_name__ = "AboutTestdrivegtkDialog"

    def __new__(cls):
        """Special static method that's automatically called by Python when 
        constructing a new instance of this class.

        Returns a fully instantiated AboutTestdrivegtkDialog object.
        """
        builder = get_builder('AboutTestdrivegtkDialog')
        new_object = builder.get_object("about_testdrivegtk_dialog")
        new_object.finish_initializing(builder)
        return new_object

    def finish_initializing(self, builder):
        """Called while initializing this instance in __new__

        finish_initalizing should be called after parsing the ui definition
        and creating a AboutTestdrivegtkDialog object with it in order to
        finish initializing the start of the new AboutTestdrivegtkDialog
        instance.

        Put your initialization code in here and leave __init__ undefined.
        """
        # Get a reference to the builder and set up the signals.
        self.builder = builder
        self.builder.connect_signals(self)

        # Code for other initialization actions should be added here.
        dialog = builder.get_object("about_testdrivegtk_dialog")
        
        dialog.set_version(__version__)
        dialog.set_authors(__authors__)
        dialog.set_comments(__description__)
        dialog.set_license(__licensenotice__)
        dialog.set_website(__website__)
        dialog.set_copyright(__copyright__)

if __name__ == "__main__":
    dialog = AboutTestdrivegtkDialog()
    dialog.show()
    gtk.main()
