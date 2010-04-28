import os, platform, commands, tempfile, hashlib, ConfigParser, time
from launchpadlib.launchpad import Launchpad

class Testdrive:
	def __init__(self):
		self.HOME = os.getenv("HOME", "")
		self.ISO_URL = os.getenv("ISO_URL", "")
		self.VIRT = os.getenv("VIRT", "")
		self.CACHE = os.getenv("CACHE", None)
		self.CACHE_ISO = os.getenv("CACHE_ISO", None)
		self.CACHE_IMG = os.getenv("CACHE_IMG", None)
		self.CACHE_CODENAME = os.getenv("CACHE_CODENAME", None)
		self.CLEAN_IMG = os.getenv("CLEAN_IMG", None)
		self.MEM = os.getenv("MEM", "")
		self.DISK_FILE = os.getenv("DISK_FILE", "")
		self.DISK_SIZE = os.getenv("DISK_SIZE", "")
		self.KVM_ARGS = os.getenv("KVM_ARGS", "")
		self.VBOX_NAME = os.getenv("VBOX_NAME", "")
		self.PKG = "testdrive"
		self.PKGRC = "%src" % self.PKG
		#self.config_files = ["/etc/%s" % self.PKGRC, "%s/.%s" % (self.HOME, self.PKGRC), "%s/.config/%s/%s" % (self.HOME, self.PKG, self.PKGRC) ]
		self.r = None
		self.PROTO = None
		self.CACHE_LP = self.HOME+"./launchpadlib/cache"

	def set_values(self, var, value):
		if var == 'kvm_args':
			self.KVM_ARGS = value
		if var == 'mem':
			self.MEM = value
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

	def load_config_file(self, config_file):
		cfg = ConfigParser.ConfigParser()
		cfg.read(config_file)
		configitems = cfg.items(self.PKG)
		for items in configitems:
			self.set_values(items[0], items[1])

	## TODO: This possible needs to go outside the class due to in PyGTK front end we might need the list of ISO's before even instancing an object
	def list_isos(self):
		if platform.machine() == "x86_64":
			self.m = ["amd64", "i386"]
		ISO = []
		for a in self.m:
			ISO.append({"name":"Ubuntu Desktop (%s-%s)"%(self.r,a), "url":"%s/daily-live/current/%s-desktop-%s.iso"%(self.u,self.r,a)})
			ISO.append({"name":"Ubuntu Server (%s-%s)"%(self.r,a), "url":"%s/ubuntu-server/daily/current/%s-server-%s.iso"%(self.u,self.r,a)})
			ISO.append({"name":"Ubuntu Alternate (%s-%s)"%(self.r,a), "url":"%s/daily/current/%s-alternate-%s.iso"%(self.u,self.r,a)})
			ISO.append({"name":"Ubuntu DVD (%s-%s)"%(self.r,a), "url":"%s/dvd/current/%s-dvd-%s.iso"%(self.u,self.r,a)})
		ISO.append({"name":"Ubuntu Netbook (%s-%s)"%(self.r,a), "url":"%s/ubuntu-netbook/daily-live/current/%s-netbook-%s.iso"%(self.u,self.r,a)})
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
			#info("Using VirtualBox for virtual machine hosting...")
			return "virtualbox"
		# No VirtualBox, how about Parallels?
		if commands.getstatusoutput("which prlctl")[0] == 0:
			#info("Using Parallels Desktop for virtual machine hosting...")
			return "parallels"
		# No hypervisor found; error out with advice
		if acceleration == 1:
			return 1
		else:
			return 0

	def set_defaults(self):
		# Set defaults where undefined
		if self.CACHE is None:
			self.CACHE = "%s/.cache/%s" % (self.HOME, self.PKG)

		if self.CACHE_CODENAME is None:
			self.CACHE_CODENAME = '%s/current' % self.CACHE

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

		if len(self.MEM) == 0:
			total = commands.getoutput("grep ^MemTotal /proc/meminfo | awk '{print $2}'")
			if total > 1000000:
				self.MEM = 512
			elif total > 750000:
				self.MEM = 384
			else:
				self.MEM = 256

		if len(self.DISK_FILE) == 0:
			self.DISK_FILE = tempfile.mkstemp(".img", "testdrive-disk-", "%s" % self.CACHE_IMG)[1]

		if len(self.DISK_SIZE) == 0:
			self.DISK_SIZE = "6G"

		if len(self.KVM_ARGS) == 0:
			self.KVM_ARGS = "-usb -usbdevice tablet -net nic,model=virtio -net user -soundhw es1370"

		if len(self.VBOX_NAME) == 0:
			self.VBOX_NAME = self.PKG

	def run(self, cmd):
		return(os.system(cmd))

	def get_proto(self):
		if self.PROTO == "rsync":
			cmd = "rsync -azP %s %s" % (self.ISO_URL, self.PATH_TO_ISO)
			return cmd
		elif self.PROTO == "http" or self.PROTO == "ftp":
			if self.run("wget --spider -S %s 2>&1 | grep 'HTTP/1.. 200 OK'" % self.ISO_URL) != 0:
				#error("ISO not found at [%s]" % self.ISO_URL)
				return 0
			ZSYNC_WORKED = 0
			if commands.getstatusoutput("which zsync")[0] == 0:
				if self.run("cd %s && zsync %s.zsync" % (self.CACHE_ISO, self.ISO_URL)) != 0:
					# If the zsync failed, use wget
					cmd = "wget %s -O %s" % (self.ISO_URL, self.PATH_TO_ISO)
					return cmd
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
		else:
			#error("Unsupported protocol [%s]" % self.PROTO)
			return 1

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
		ISO_NAME = os.path.basename(self.ISO_URL)
		self.PROTO = self.ISO_URL.partition(":")[0]
		self.PATH_TO_ISO = "%s/%s" % (self.CACHE_ISO, ISO_NAME)

	def launch_usb_creator(self):
		if os.path.exists("/usr/bin/usb-creator-gtk"):
			os.execv("/usr/bin/usb-creator-gtk", ["usb-creator-gtk", "-i", self.PATH_TO_ISO])
		else:
			os.execv("/usr/bin/usb-creator-kde", ["usb-creator-kde", "-i", self.PATH_TO_ISO])

	def lp_obtain_release_codename(self):
		launchpad = Launchpad.login_anonymously('testdrive', 'production', self.CACHE)
		return launchpad.distributions['ubuntu'].current_series.name

	def is_codename_cached(self):
		if not os.path.exists(self.CACHE):
			os.makedirs(self.CACHE, 0700)
		if not os.path.exists("%s/current" % self.CACHE):
			return False
		return True

	def is_cache_expired(self):
		cache_time = time.localtime(os.path.getmtime("%s/current" % self.CACHE))
		local_time = time.localtime()
		time_difference = time.mktime(local_time) - time.mktime(cache_time)
		# Check for new release at most once-per-week (60*60*24*7 = 604800)
		if time_difference >= 604800:
			return True
		return False

	def update_ubuntu_codename_cache(self, str):
		try:
			f = open("%s/current" % self.CACHE,'w')
			f.write(str)
			f.close
		except IOError:
			pass

	def get_ubuntu_codename(self):
		try:
			f = open("%s/current" % self.CACHE,'r')
			codename = f.read()
			f.close
		except IOError:
			pass
		return codename
