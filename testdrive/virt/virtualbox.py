#!/usr/bin/python
#
#    testdrive - run today's Ubuntu development ISO, in a virtual machine
#    Copyright (C) 2009 Canonical Lself.td.
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

class VBox:

	def __init__(self, td):
		self.vboxversion = None
		self.HOME = td.HOME
		self.CACHE_ISO = td.CACHE_ISO
		self.PATH_TO_ISO = td.PATH_TO_ISO
		self.DISK_FILE = td.DISK_FILE
		self.MEM = td.MEM
		self.DISK_SIZE = td.DISK_SIZE
		self.VBOX_NAME = td.VBOX_NAME
		self.ISO_URL = td.ISO_URL

	def is_disk_empty(self):
		(status, output) = commands.getstatusoutput("file %s | grep -qs 'empty'" % self.DISK_FILE)
		if status == 0:
			return True
		return False

	# Code to validate if virtualization is installed/supported
	def validate_virt(self):
		# Determine which version of VirtualBox we have installed.  What is returned is
		# typically a string such as '3.1.0r55467', lets assume that the command line
		# is consistent within 3.0.x versions and 3.1.x version so extract this part of the
		# version string for comparison later
		self.vboxversion = commands.getoutput("VBoxManage --version")
		self.vboxversion = ( int(self.vboxversion.split(".")[0]), int(self.vboxversion.split(".")[1]) )
		if (3,0) <= self.vboxversion < (4,1):
			#info("VirtualBox %s detected." % self.vboxversion)
			print "INFO: VirtualBox %s.%s detected." % self.vboxversion
		else:
			#error("Unsupported version (%s) of VirtualBox; please install v3.0 or v3.1." % self.vboxversion)
			print "ERROR: Unsupported version (%s.%s) of VirtualBox; please install v3.* or v4.0." % self.vboxversion
			exit(0)

	# Code to setup virtual machine
	def setup_virt(self):
		self.run("sed -i \":HardDisk.*%s:d\" %s/.VirtualBox/VirtualBox.xml" % (self.DISK_FILE, self.HOME))
		if self.is_disk_empty():
			os.unlink(self.DISK_FILE)
		if not os.path.exists(self.DISK_FILE):
			self.DISK_SIZE = self.DISK_SIZE.replace("G", "000")
			#info("Creating disk image...")
			print "INFO: Creating disk image..."
			self.run_or_die("VBoxManage createhd --filename %s --size %s" % (self.DISK_FILE, self.DISK_SIZE))
		if self.vboxversion == (3,0):
			self.run("VBoxManage modifyvm %s --hda none" % self.VBOX_NAME)
		elif self.vboxversion > (3,0):
			self.run("VBoxManage storageattach %s --storagectl \"IDE Controller\" --port 0 --device 0 --type hdd --medium none" % self.VBOX_NAME)
			if self.PATH_TO_ISO != "/dev/null":
				self.run("VBoxManage storageattach %s --storagectl \"IDE Controller\" --port 0 --device 1 --type dvddrive --medium none" % self.VBOX_NAME)
		#info("Creating the Virtual Machine...")
		print "INFO: Creating the Virtual Machine..."
		if os.path.exists("%s/.VirtualBox/Machines/%s/%s.xml" % (self.HOME, self.VBOX_NAME, self.VBOX_NAME)):
			os.unlink("%s/.VirtualBox/Machines/%s/%s.xml" % (self.HOME, self.VBOX_NAME, self.VBOX_NAME))
		self.run("VBoxManage unregistervm %s --delete" % self.VBOX_NAME)
		self.run_or_die("VBoxManage createvm --register --name %s" % self.VBOX_NAME)
		self.run_or_die("VBoxManage modifyvm %s --memory %s" % (self.VBOX_NAME, self.MEM))
		# This should probably support more than just Ubuntu...
		if self.ISO_URL.find("amd64") >= 0:
			platform = "Ubuntu_64"
		else:
			platform = "Ubuntu"
		self.run_or_die("VBoxManage modifyvm %s --ostype %s" % (self.VBOX_NAME, platform))
		self.run_or_die("VBoxManage modifyvm %s --vram 128" % self.VBOX_NAME)
		self.run_or_die("VBoxManage modifyvm %s --boot1 disk" % self.VBOX_NAME)
		self.run_or_die("VBoxManage modifyvm %s --boot2 dvd" % self.VBOX_NAME)
		self.run_or_die("VBoxManage modifyvm %s --nic1 nat" % self.VBOX_NAME)

	# Code launch virtual machine
	def launch_virt(self):
		#info("Running the Virtual Machine...")
		print "Running the Virtual Machine..."
		if self.vboxversion == (3,0):
			self.run_or_die("VBoxManage modifyvm %s --hda %s" % (self.VBOX_NAME, self.DISK_FILE))
			self.run_or_die("VBoxManage startvm %s" % self.VBOX_NAME)
			if self.PATH_TO_ISO != "/dev/null":
				print(">>> %s <<<\n" % (self.PATH_TO_ISO))
				self.run_or_die("VBoxManage controlvm %s dvdattach %s" % (self.VBOX_NAME, self.PATH_TO_ISO))
		elif self.vboxversion > (3,0):
			self.run_or_die("VBoxManage storagectl %s --name \"IDE Controller\" --add ide" % self.VBOX_NAME)
			self.run_or_die("VBoxManage storageattach %s --storagectl \"IDE Controller\" --port 0 --device 0 --type hdd --medium %s" % (self.VBOX_NAME, self.DISK_FILE))
			if self.PATH_TO_ISO != "/dev/null":
				self.run_or_die("VBoxManage storageattach %s --storagectl \"IDE Controller\" --port 0 --device 1 --type dvddrive --medium %s" % (self.VBOX_NAME, self.PATH_TO_ISO))
			#self.run_or_die("VBoxManage startvm %s" % self.td.VBOX_NAME)
			return "VBoxManage startvm %s" % self.VBOX_NAME

		# Give this VM a few seconds to start up
		#time.sleep(5)
		# Loop as long as this VM is running
		#while commands.getstatusoutput("VBoxManage list runningvms | grep -qs %s" % self.td.VBOX_NAME)[0] == 0:
		#	time.sleep(2)

	def run(self, cmd):
		return(os.system(cmd))

	def run_or_die(self, cmd):
		if self.run(cmd) != 0:
			#error("Command failed\n    `%s`" % cmd)
			print "Command failed\n    `%s`" % cmd
