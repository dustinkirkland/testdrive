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

import commands, os

class KVM:

	def __init__(self, testd):
		self.td = testd

	# Code to validate if virtualization is installed/supported
	def validate_virt(self):
		(status, output) = commands.getstatusoutput("kvm-ok")
		if status != 0:
			print(output)

	# Code to setup virtual machine
	def setup_virt(self):
		if self.td.p == 'uec-daily' or self.td.p == 'uec-releases':
			path = "%s/%s" % (self.td.CACHE_ISO, self.td.PATH_TO_ISO.split(".tar.gz")[0].split("_")[-1])
			self.ORIG_DISK = "%s.img" % path
			self.FLOPPY_FILE = "%s-floppy" % path
			self.run_or_die("kvm-img create -f qcow2 -b %s %s" % (self.ORIG_DISK, self.td.DISK_FILE))
		elif not os.path.exists(self.td.DISK_FILE) or self.td.is_disk_empty():
			print "Creating disk image [%s]..." % self.td.DISK_FILE
			self.run_or_die("kvm-img create -f qcow2 %s %s" % (self.td.DISK_FILE, self.td.DISK_SIZE))

	# Code launch virtual machine
	def launch_virt(self):
		print "Running the Virtual Machine..."
		#os.system("kvm -m %s -smp %s -cdrom %s -drive file=%s,if=virtio,cache=writeback,index=0,boot=on %s" % (self.td.MEM, self.td.SMP, self.td.PATH_TO_ISO, self.td.DISK_FILE, self.td.KVM_ARGS))
		if self.td.p == 'uec-daily' or self.td.p == 'uec-releases':
			cmd = "kvm -boot a -fda %s -drive file=%s,if=virtio" % (self.FLOPPY_FILE, self.td.DISK_FILE)
		else:		
			cmd = "kvm -m %s -smp %s -cdrom %s -drive file=%s,if=virtio,cache=writeback,index=0,boot=on %s" % (self.td.MEM, self.td.SMP, self.td.PATH_TO_ISO, self.td.DISK_FILE, self.td.KVM_ARGS)
		return cmd

	def run(self, cmd):
		return(os.system(cmd))

	def run_or_die(self, cmd):
		if self.run(cmd) != 0:
			print "Command failed\n    `%s`" % cmd
