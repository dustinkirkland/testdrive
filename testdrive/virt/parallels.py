#!/usr/bin/python
#
#    testdrive - run today's Ubuntu development ISO, in a virtual machine
#    Copyright (C) 2009 Canonical Ltd.
#    Copyright (C) 2009 Dustin Kirkland
#
#    Authors: Dustin Kirkland <kirkland@canonical.com>
#             Andres Rodriguez <andreserl@ubuntu.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import commands, os, time

class Parallels:

    def __init__(self, td):
        self.HOME = td.HOME
        self.CACHE_ISO = td.CACHE_ISO
        self.PATH_TO_ISO = td.PATH_TO_ISO
        self.DISK_FILE = td.DISK_FILE
        self.MEM = td.MEM
        self.DISK_SIZE = td.DISK_SIZE
        self.VBOX_NAME = td.VBOX_NAME

    # Code to validate if virtualization is installed/supported
    def validate_virt(self):
        if commands.getstatusoutput("prlctl list %s | grep -qsv \"UUID\"" % self.VBOX_NAME)[0] == 0:
            self.run_or_die("prlctl delete %s" % self.VBOX_NAME)

    # Code to setup virtual machine
    def setup_virt(self):
        self.DISK_SIZE = self.DISK_SIZE.replace("G", "000")
        #info("Creating VM...")
        print "INFO: Creating VM..."
        self.run_or_die("prlctl create %s --ostype linux --distribution ubuntu" % self.VBOX_NAME)
        self.run_or_die("prlctl set %s --memsize %s" % (self.VBOX_NAME, self.MEM))
        self.run_or_die("prlctl set %s --device-del hdd0" % self.VBOX_NAME)
        self.run_or_die("prlctl set %s --device-add hdd --type expand --size %s --iface scsi --position 0:0" % (self.VBOX_NAME, self.DISK_SIZE))
        self.run_or_die("prlctl set %s --device-set cdrom0 --image %s" % (self.VBOX_NAME, self.PATH_TO_ISO))

    # Code launch virtual machine
    def launch_virt(self):
        #self.run_or_die("prlctl start %s" % self.td.VBOX_NAME)
        return "prlctl start %s" % self.VBOX_NAME
        # Loop as long as this VM is running
        #while commands.getstatusoutput("prlctl list %s | grep -qs stopped" % self.td.VBOX_NAME)[0] != 0:
        #   time.sleep(2)

    def run(self, cmd):
        return(os.system(cmd))

    def run_or_die(self, cmd):
        if self.run(cmd) != 0:
            #error("Command failed\n    `%s`" % cmd)
            print "Command failed\n    `%s`" % cmd
