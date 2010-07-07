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

import os, platform, commands, tempfile, hashlib, ConfigParser, time
import xdg.BaseDirectory

class Testdrive:
	def __init__(self, pkg_section):
		self.HOME = os.getenv("HOME", "")
		self.ISO_URL = os.getenv("ISO_URL", "")
		self.VIRT = os.getenv("VIRT", "")
		self.CACHE = os.getenv("CACHE", None)
		self.CACHE_ISO = os.getenv("CACHE_ISO", None)
		self.CACHE_IMG = os.getenv("CACHE_IMG", None)
		self.CLEAN_IMG = os.getenv("CLEAN_IMG", None)
		self.MEM = os.getenv("MEM", "")
		self.SMP = os.getenv("SMP", "")
		self.DISK_FILE = os.getenv("DISK_FILE", "")
		self.DISK_SIZE = os.getenv("DISK_SIZE", "")
		self.KVM_ARGS = os.getenv("KVM_ARGS", "")
		self.VBOX_NAME = os.getenv("VBOX_NAME", "")
		self.PKG = "testdrive"
		self.PKGRC = "%src" % self.PKG
		self.r = None
		self.m = None
		self.f = None
		self.PROTO = None
		self.ISO_PATH_HEADER = None
		self.PKG_SECTION = pkg_section

	def set_values(self, var, value):
		if var == 'kvm_args':
			self.KVM_ARGS = value
		if var == 'mem':
			self.MEM = value
		if var == 'smp':
			self.SMP = value
		if var == 'disk_size':
			self.DISK_SIZE = value
		if var == 'cache':
			self.CACHE = value
		if var == 'cache_img':
			self.CACHE_IMG = value
		if var == 'clean_img':
			self.CLEAN_IMG = value
		if var == 'iso_url':
			self.ISO_URL = value
		if var == 'virt':
			self.VIRT = value
		if var == 'disk_file':
			self.DISK_FILE = value
		if var == 'r':
			self.r = value
		if var == 'u':
			self.u = value
		if var == 'm':
			self.m = [value]
		if var == 'f':
			self.f = value

	def load_config_file(self, config_file):
		cfg = ConfigParser.ConfigParser()
		cfg.read(config_file)
		try:
			defaults = cfg.items('testdrive-common')
			for items in defaults:
				self.set_values(items[0], items[1])
		except:
			pass
		try:
			configitems = cfg.items(self.PKG_SECTION)
			for items in configitems:
				self.set_values(items[0], items[1])
		except:
			pass

	## TODO: This possible needs to go outside the class due to in PyGTK front end we might need the list of ISO's before even instancing an object
	def list_isos(self, ISOS):
		ISO = []
		for iso in ISOS:
			if iso.split()[1] == self.r:
				# TODO: Add support for UEC
				category = iso.split()[0]
				if category == 'ubuntu-netbook':
					category = 'ubuntu'
				elif category == 'ubuntu-server':
					category = 'ubuntu'
				elif category == 'kubuntu-netbook':
					category = 'kubuntu'
				flavor = iso.split()[0].capitalize()
				if flavor == 'Ubuntu-netbook':
					flavor = 'Ubuntu'
				elif flavor == 'Kubuntu-netbook':
					flavor = 'Kubuntu'
				elif flavor == 'Ubuntustudio':
					flavor = 'Ubuntu Studio'
				elif flavor == 'Ubuntu-server':
					flavor = 'Ubuntu'
				release = iso.split()[1]
				url = iso.split()[2]
				arch = url.split(".iso")[0].split("-")[-1]
				image = url.split("-%s.iso" % arch)[0].split("-")[-1].capitalize()
				if image == 'Dvd':
					image = url.split("-%s.iso" % arch)[0].split("-")[-1].swapcase()
				name = "%s %s" % (flavor, image)
				# Name: Shows a description
				# URL: Shows the URL from where it downloads the ISO
				# Arch: Shows the architecture (amd64|i386)
				# Category: The header used to save the ISO, i.e.: ubuntu_lucid-desktop-i386.iso kubuntu_lucid-desktop-i386.iso
				if arch in self.m:
					ISO.append({"name":name, "url":"%s%s" % (self.u, url), "arch":arch, "category":category})
		return ISO

	def get_virt(self):
		acceleration = 0
		# Check if KVM acceleration can be used
		if commands.getstatusoutput("which kvm-ok")[0] == 0:
			# If we have kvm-ok, let's use it...
			if commands.getstatusoutput("kvm-ok")[0] == 0:
				acceleration = 1
		else:
			# Okay, we don't have kvm-ok, so let's hack it...
			if commands.getstatusoutput("egrep \"^flags.*:.*(svm|vmx)\" /proc/cpuinfo")[0] == 0:
				acceleration = 1
		# Prefer KVM if acceleration available and installed
		if acceleration == 1 and commands.getstatusoutput("which kvm"):
			return "kvm"
		# Okay, no KVM, VirtualBox maybe?
		if commands.getstatusoutput("which VBoxManage")[0] == 0:
			return "virtualbox"
		# No VirtualBox, how about Parallels?
		if commands.getstatusoutput("which prlctl")[0] == 0:
			return "parallels"
		# No hypervisor found; error out with advice
		if acceleration == 1:
			return 1
		else:
			return 0

	def set_defaults(self):
		# Set defaults where undefined
		if self.CACHE is None:
			if xdg.BaseDirectory.xdg_cache_home:
				self.CACHE = "%s/%s" % (xdg.BaseDirectory.xdg_cache_home, self.PKG)
			else:
				self.CACHE = "%s/.cache/%s" % (self.HOME, self.PKG)

		if self.CACHE_IMG is None:
			self.CACHE_IMG = '%s/img' % self.CACHE
		if not os.path.exists(self.CACHE_IMG):
			os.makedirs(self.CACHE_IMG, 0700)
		# if running the image from /dev/shm, remove the image when done
		# (unless CLEAN_IMG is set)
		if self.CLEAN_IMG is None:
			if self.CACHE_IMG == '/dev/shm':
				self.CLEAN_IMG = True
			else:
				self.CLEAN_IMG = False

		if self.CACHE_ISO is None:
			self.CACHE_ISO = '%s/iso' % self.CACHE
		if not os.path.exists(self.CACHE_ISO):
			os.makedirs(self.CACHE_ISO, 0700)

		if len(self.SMP) == 0:
			self.SMP = commands.getoutput("grep -c ^processor /proc/cpuinfo")

		if len(self.DISK_SIZE) == 0:
			self.DISK_SIZE = "6G"

		if len(self.KVM_ARGS) == 0:
			self.KVM_ARGS = "-usb -usbdevice tablet -net nic,model=virtio -net user -soundhw es1370"

		if len(self.VBOX_NAME) == 0:
			self.VBOX_NAME = self.PKG

		if self.ISO_PATH_HEADER == None:
			self.ISO_PATH_HEADER = 'other'

		if self.f == None:
			self.f = 'ubuntu'

		if self.m is None:
			if platform.machine() == "x86_64":
				self.m = ["amd64", "i386"]
			else:
				self.m = ["i386"]

	def run(self, cmd):
		return(os.system(cmd))

	def get_proto(self):
		if self.PROTO == "rsync":
			cmd = "rsync -azP %s %s" % (self.ISO_URL, self.PATH_TO_ISO)
			return cmd
		elif self.PROTO == "http" or self.PROTO == "ftp":
			if self.run("wget --spider -S %s 2>&1 | grep 'HTTP/1.. 200 OK'" % self.ISO_URL) != 0:
				#error("ISO not found at [%s]" % self.ISO_URL)
				return 1
			ZSYNC_WORKED = 0
			if commands.getstatusoutput("which zsync")[0] == 0:
				#if self.run("cd %s && zsync %s.zsync" % (self.CACHE_ISO, self.ISO_URL)) != 0:
				if self.run("zsync %s.zsync -o %s" % (self.ISO_URL, self.PATH_TO_ISO)) != 0:
					# If the zsync failed, use wget
					cmd = "wget %s -O %s" % (self.ISO_URL, self.PATH_TO_ISO)
					return cmd
				else:
					return 0
			else:
				# Fall back to wget
				cmd = "wget %s -O %s" % (self.ISO_URL, self.PATH_TO_ISO)
				return cmd
		elif self.PROTO == "file":
			# If the iso is on file:///, use the ISO in place
			self.PATH_TO_ISO = self.ISO_URL.partition("://")[2]
			# Get absolute path if a relative path is used
			DIR = commands.getoutput("cd `dirname '%s'` && pwd" % self.PATH_TO_ISO)
			FILE = os.path.basename("%s" % self.PATH_TO_ISO)
			self.PATH_TO_ISO = "%s/%s" % (DIR, FILE)
			return 0
		else:
			#error("Unsupported protocol [%s]" % self.PROTO)
			return 2

	def md5sum(self, file):
		fh = open(file, 'rb')
		x = fh.read()
		fh.close()
		m = hashlib.md5()
		m.update(x)
		return m.hexdigest()

	def delete_image(self):
		# if requested to clean out the image mark it to be done
		if self.CLEAN_IMG:
			rm_disk = True
		else:
			rm_disk = False

		# If disk image is stock (e.g., you just ran a LiveCD, no installation),
		# purge it automatically.
		if os.path.exists(self.DISK_FILE):
			if os.path.getsize(self.DISK_FILE) == 262144 and self.md5sum(self.DISK_FILE) == "1da7553f642332ec9fb58a6094d2c8ef":
				# Clean up kvm qcow2 image
				rm_disk = True
			if os.path.getsize(self.DISK_FILE) == 24576:
				# Clean up vbox image
				rm_disk = True
			elif os.path.getsize(self.DISK_FILE) == 0:
				# Clean up empty file
				rm_disk = True
			if rm_disk:
				#info("Cleaning up disk image [%s]..." % DISK_FILE)
				os.unlink(self.DISK_FILE)
				return True
		return False

	def set_launch_path(self):
		# Move from set_defaults, due to merge of upstream rev 189
		ISO_NAME = "%s_%s" % (self.ISO_PATH_HEADER, os.path.basename(self.ISO_URL))
		self.PROTO = self.ISO_URL.partition(":")[0]
		self.PATH_TO_ISO = "%s/%s" % (self.CACHE_ISO, ISO_NAME)

	def launch_usb_creator(self):
		if os.path.exists("/usr/bin/usb-creator-gtk"):
			os.execv("/usr/bin/usb-creator-gtk", ["usb-creator-gtk", "-i", self.PATH_TO_ISO])
		else:
			os.execv("/usr/bin/usb-creator-kde", ["usb-creator-kde", "-i", self.PATH_TO_ISO])

	def is_disk_empty(self):
		(status, output) = commands.getstatusoutput("file %s | grep -qs 'empty'" % self.DISK_FILE)
		if status == 0:
			return True
		return False

	# Obtain available ISO's from Ubuntu cdimage.
	def is_iso_list_cached(self):
		if not os.path.exists(self.CACHE):
			os.makedirs(self.CACHE, 0700)
		if not os.path.exists("%s/isos" % self.CACHE):
			return False
		return True

	def is_iso_list_cache_expired(self):
		cache_time = time.localtime(os.path.getmtime("%s/isos" % self.CACHE))
		local_time = time.localtime()
		time_difference = time.mktime(local_time) - time.mktime(cache_time)
		# Check for new release at most every 12hrs (60*60*12 = 43200)
		if time_difference >= 43200:
			return True
		return False

	def cdimage_obtain_ubuntu_iso_list(self):
		(status, output) = commands.getstatusoutput("wget -q -O- http://cdimage.ubuntu.com/.manifest-daily | egrep '(amd64|i386)'")
		return output

	def update_ubuntu_iso_list_cache(self, str):
		try:
			f = open("%s/isos" % self.CACHE,'w')
			f.write(str)
			f.close
		except IOError:
			pass

	def get_ubuntu_iso_list(self):
		try:
			f = open("%s/isos" % self.CACHE, 'r')
			ISO = f.readlines()
			f.close
		except IOError:
			pass
		return ISO

	def set_ubuntu_release_codename(self, isos):
		codename = []
		for iso in isos:
			codename.append(iso.split()[1])
		codename.sort()
		self.r = codename[-1]

	def create_disk_file(self):
		return tempfile.mkstemp(".img", "testdrive-disk-", "%s" % self.CACHE_IMG)[1]
