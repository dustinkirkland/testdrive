#!/usr/bin/env python
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

###################### DO NOT TOUCH THIS (HEAD TO THE SECOND PART) ######################

import os
import sys
from glob import glob

try:
    import DistUtilsExtra.auto
except ImportError:
    print >> sys.stderr, 'To build testdrivegtk you need https://launchpad.net/python-distutils-extra'
    sys.exit(1)
assert DistUtilsExtra.auto.__version__ >= '2.18', 'needs DistUtilsExtra.auto >= 2.18'

def update_data_path(prefix, oldvalue=None):

    try:
        fin = file('testdrivegtk/testdrivegtkconfig.py', 'r')
        fout = file(fin.name + '.new', 'w')

        for line in fin:            
            fields = line.split(' = ') # Separate variable from value
            if fields[0] == '__testdrivegtk_data_directory__':
                # update to prefix, store oldvalue
                if not oldvalue:
                    oldvalue = fields[1]
                    line = "%s = '%s'\n" % (fields[0], prefix)
                else: # restore oldvalue
                    line = "%s = %s" % (fields[0], oldvalue)
            fout.write(line)

        fout.flush()
        fout.close()
        fin.close()
        os.rename(fout.name, fin.name)
    except (OSError, IOError), e:
        print ("ERROR: Can't find testdrivegtk/testdrivegtkconfig.py")
        sys.exit(1)
    return oldvalue


def update_desktop_file(datadir):

    try:
        fin = file('testdrive-gtk.desktop.in', 'r')
        fout = file(fin.name + '.new', 'w')

        for line in fin:            
            if 'Icon=' in line:
                line = "Icon=%s\n" % (datadir + 'media/testdrive-gtk.xpm')
            fout.write(line)
        fout.flush()
        fout.close()
        fin.close()
        os.rename(fout.name, fin.name)
    except (OSError, IOError), e:
        print ("ERROR: Can't find testdrive-gtk.desktop.in")
        sys.exit(1)


class InstallAndUpdateDataDirectory(DistUtilsExtra.auto.install_auto):
    def run(self):
        previous_value = update_data_path(self.prefix + '/share/testdrivegtk/')
        #update_desktop_file(self.prefix + '/share/testdrivegtk/')
        DistUtilsExtra.auto.install_auto.run(self)
        update_data_path(self.prefix, previous_value)


        
##################################################################################
###################### YOU SHOULD MODIFY ONLY WHAT IS BELOW ######################
##################################################################################

DistUtilsExtra.auto.setup(
    name='testdrive',
    version='3.25',
    license='GPL-3',
    author='Andres Rodriguez',
    author_email='andreserl@ubuntu.com',
    description='Test Drive an Ubuntu ISO',
    long_description='Download and run an Ubuntu ISO in a Virtual Machine',
    url='https://launchpad.net/testdrive',
    packages=[  'testdrive',
            'testdrive.virt',
            'testdrivegtk'],
    scripts=['bin/testdrive', 'bin/testdrive-gtk'],
    data_files=[    ('/etc', ['testdriverc']),
            ('share/testdrive', ['testdriverc']),
            ('share/testdrivegtk/ui', glob('data/ui/*.ui')),
            ('share/testdrivegtk/ui', glob('data/ui/*.xml')),
            ('share/testdrivegtk/media', glob('data/media/*.png')),
            ('share/testdrivegtk/media', glob('data/media/*.svg'))
            #('share/pixmaps', glob('data/media/testdrive-gtk.xpm')),
            #('share/testdrivegtk/indicator', glob('indicator/testdrive-gtk'))
            #('share/indicators/messages/applications', glob('indicator/testdrive-gtk'))
            ],
    cmdclass={'install': InstallAndUpdateDataDirectory}
    )

