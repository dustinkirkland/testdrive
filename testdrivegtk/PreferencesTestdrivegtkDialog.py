# -*- coding: utf-8 -*-
### BEGIN LICENSE
# Copyright (C) 2010 Canonical Ltd.
# 
# Authors:
# 	Andres Rodriguez <andreserl@ubuntu.com>
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

#from desktopcouch.records.server import CouchDatabase
#from desktopcouch.records.record import Record
import gtk
import ConfigParser
import os
import commands
from testdrive import testdrive

from testdrivegtk.helpers import get_builder

import gettext
from gettext import gettext as _
gettext.textdomain('testdrivegtk')

ISO_REPOSITORY = ['cdimage', 'releases']

class PreferencesTestdrivegtkDialog(gtk.Dialog):
	__gtype_name__ = "PreferencesTestdrivegtkDialog"
	preferences = {}

	def __new__(cls):
		"""Special static method that's automatically called by Python when 
		constructing a new instance of this class.

		Returns a fully instantiated PreferencesTestdrivegtkDialog object.
		"""
		import logging
		logging.basicConfig(level=logging.DEBUG)
		logger1 = logging.getLogger('gtkpreferences')
		logger1.debug('__new__')

		builder = get_builder('PreferencesTestdrivegtkDialog')
		new_object = builder.get_object("preferences_testdrivegtk_dialog")
		new_object.finish_initializing(builder, logger1)
		return new_object

	def finish_initializing(self, builder, logger1):
		"""Called while initializing this instance in __new__

		finish_initalizing should be called after parsing the ui definition
		and creating a PreferencesTestdrivegtkDialog object with it in order to
		finish initializing the start of the new PerferencesTestdrivegtkDialog
		instance.

		Put your initialization code in here and leave __init__ undefined.
		"""
		# Get a reference to the builder and set up the signals.
		self.builder = builder
		self.builder.connect_signals(self)
		self.set_title("TestDrive Front-end Preferences")
		self.logger = logger1

		##################################################################
		###### Starting code of instancing TestDrive in Prefereces #######
		##################################################################
		self.td = testdrive.Testdrive('testdrive-gtk')

		self.initialize_variables()
		self.initialize_config_files()
		self.td.set_defaults()

		# Grab the selected repo and store it temporarly.
		# Then, use the hardcoded repos to update the cache.
		# Finally, default the initially selected repo.
		selected_repo = self.td.p
		for repo in ISO_REPOSITORY:
			self.td.p = repo
			self.update_iso_cache()
		self.td.p = selected_repo

		self.initialize_widgets()
		self.initialize_widgets_values()
		self.logger.debug('finish_initialization()')

	def update_iso_cache(self):
		update_cache = None
		cdimage = False
		""" Verify if the ISO list is cached, if not, set variable to update/create it. """
		if self.td.is_iso_list_cached() is False:
			update_cache = 1
		# If ISO list is cached, verify if it is expired. If it is, set variable to update it.
		elif self.td.is_iso_list_cache_expired() is True:
			update_cache = 1

		""" If variable set to update, obtain the ISO list from the Ubuntu CD Image repository. """
		if update_cache == 1:
			self.logger.info('Obtaining Ubuntu ISO list from %s...' % self.td.u)
			try:
				cdimage = self.td.obtain_ubuntu_iso_list_from_repo()
			except:
				self.logger.error('Could not obtain the Ubuntu USO list from %s...' % self.td.u)

		""" If the ISO List was obtained, update the cache file"""
		if cdimage:
			self.logger.info('Updating the Ubuntu ISO list cache...')
			try:
				self.td.update_ubuntu_iso_list_cache(cdimage)
			except:
				self.logger.error('Unable to update the Ubuntu ISO list cache...')

	def get_preferences(self):
		"""Returns preferences for testdrivegtk."""
		self.logger.debug('get_preferences()')
		return self.td

	def _load_preferences(self):
		# TODO: add preferences to the self._preferences dict default
		# preferences that will be overwritten if some are saved
		pass

	def _save_preferences(self):
		if self.preferences:
			config = ConfigParser.RawConfigParser()
			config.add_section(self.td.PKG_SECTION)
			for prefs in self.preferences:
				config.set(self.td.PKG_SECTION, prefs[0], prefs[1])
			# Writing our configuration file
			path = "%s/.%s" % (self.td.HOME, self.td.PKGRC)
			with open(path, 'wb') as configfile:
				config.write(configfile)

	def ok(self, widget, data=None):
		"""The user has elected to save the changes.

		Called before the dialog returns gtk.RESONSE_OK from run().
		"""

		# Make any updates to self._preferences here. e.g.
		#self._preferences["preference1"] = "value2"
		self.update_preferences()
		self._save_preferences()

	def cancel(self, widget, data=None):
		"""The user has elected cancel changes.

		Called before the dialog returns gtk.RESPONSE_CANCEL for run()
		"""
		# Restore any changes to self._preferences here.
		pass

	def on_error_dlg(self, data=None):
		errorbox = gtk.MessageDialog(self, 
			gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR, 
			gtk.BUTTONS_CLOSE, data)
		response = errorbox.run()
		errorbox.destroy()

	def initialize_variables(self):
		self.virt_method = None
		self.mem = None
		self.disk_size = None
		self.flavors = ""
		self.arch = []
		self.repo = None
		self.r = None

	def on_select_virt_method(self, widget, virt=None):
		self.virt_method = virt
		if virt == 'kvm':
			self.lb_kvm_args.show()
			self.txt_kvm_args.show()
			self.lb_smp_nbr.show()
			self.txt_smp_nbr.show()
			self.lb_smp_available.show()
		else:
			self.txt_kvm_args.hide()
			self.lb_kvm_args.hide()
			self.lb_smp_nbr.hide()
			self.txt_smp_nbr.hide()
			self.lb_smp_available.hide()
		#print "%s was toggled %s" % (data, ("OFF", "ON")[widget.get_active()])

	def on_select_mem(self, entry):
		if entry.child.get_text() == 'Other...':
			entry.child.set_editable(True)
			self.mem = 'other'
		elif entry.get_active() >= 0:
			entry.child.set_editable(False)
			self.mem = entry.child.get_text()

	def on_select_disk_size(self, entry):
		if entry.child.get_text() == 'Other...':
			entry.child.set_editable(True)
			self.disk_size = 'other'
		elif entry.get_active() >= 0:
			entry.child.set_editable(False)
			self.disk_size = entry.child.get_text()

	def on_select_flavors(self, widget):
		self.flavors = ""
		if self.chk_flavor_ubuntu.get_active():
			self.flavors = self.flavors + "ubuntu, "
		if self.chk_flavor_kubuntu.get_active():
			self.flavors = self.flavors + "kubuntu, "
		if self.chk_flavor_xubuntu.get_active():
			self.flavors = self.flavors + "xubuntu, "
		if self.chk_flavor_edubuntu.get_active():
			self.flavors = self.flavors + "edubuntu, "
		if self.chk_flavor_mythbuntu.get_active():
			self.flavors = self.flavors + "mythbuntu, "
		if self.chk_flavor_ubuntustudio.get_active():
			self.flavors = self.flavors + "ubuntustudio, "
		if self.chk_flavor_other.get_active():
			self.flavors = self.flavors + "other, "

	def on_select_arch(self, widget, arch):
		if widget.get_active() == True:
			self.arch.append(arch)
		if widget.get_active() == False:
			self.arch.remove(arch)

	def on_txt_gral_cache_focus_out_event(self, widget, data=None):
		txt_cache = self.txt_gral_cache.get_text()
		#if self.txt_iso_cache.get_text() == self.td.CACHE_ISO:
		self.txt_iso_cache.set_text("%s/iso" % txt_cache)
		#if self.txt_img_cache.get_text() == self.td.CACHE_IMG:
		self.txt_img_cache.set_text("%s/img" % txt_cache)

	def on_cache_cleanup_clicked(self, widget, cache_path):
		filelist = os.listdir(cache_path)

		if not filelist:
			return

		try:
			for file in filelist:
				path = "%s/%s" % (cache_path, file)
				os.unlink(path)
		except:
			on_error_dlg("Unable to clean up files from [%s]" % cache_path)
	
	def on_select_iso_image_repo(self, widget):
		model = widget.get_model()
		index = widget.get_active()
		if index:
			old_repo = self.td.p
			self.repo = model[index][0]
			self.td.p = self.repo		

			# Update cache commented given the hack to sync every repo on initialization
			#self.update_iso_cache()
			# Populate the releases combobox
			self.cb_ubuntu_release.get_model().clear()
			self.cb_ubuntu_release.append_text('Select Release:')
			self.cb_ubuntu_release.set_active(0)
			isos = self.td.get_ubuntu_iso_list()
			codenames = []
			for iso in isos:
				codenames.append(iso.split()[1])
			codenames = list(set(codenames))
			codenames.sort()
			codenames.reverse()
			c = i = 0
			for release in codenames:
				self.cb_ubuntu_release.append_text(release)
				c += 1
				if release == self.td.r and self.td.p == old_repo:
					i = c
			if self.td.r is None:
				self.cb_ubuntu_release.set_active(1)
			if i != 0:
				self.cb_ubuntu_release.set_active(i)
		else:
			self.repo = None

	def on_select_ubuntu_release(self, widget):
		model = widget.get_model()
		index = widget.get_active()
		if index > 0:
			self.r = model[index][0]
		else:
			self.r = None

	def initialize_widgets(self):
		# Initialize Data Paths
		self.txt_gral_cache = self.builder.get_object("txt_gral_cache")
		self.txt_img_cache = self.builder.get_object("txt_img_cache")
		self.txt_iso_cache = self.builder.get_object("txt_iso_cache")
		self.txt_iso_list_cache = self.builder.get_object("txt_iso_list_cache")
		# Clean Ups
		self.btn_iso_clean = self.builder.get_object("btn_iso_clean")
		self.btn_iso_clean.connect("clicked", self.on_cache_cleanup_clicked, self.td.CACHE_ISO)
		self.btn_img_clean = self.builder.get_object("btn_img_clean")
		self.btn_img_clean.connect("clicked", self.on_cache_cleanup_clicked, self.td.CACHE_IMG)

		# Ubuntu Releases
		self.chk_arch_i386 = self.builder.get_object("chk_arch_i386")
		self.chk_arch_i386.connect("clicked", self.on_select_arch, "i386")
		self.chk_arch_amd64 = self.builder.get_object("chk_arch_amd64")
		self.chk_arch_amd64.connect("clicked", self.on_select_arch, "amd64")

		# Ubuntu Repositories Combo Box
		self.tb_ubuntu_release_prefs = self.builder.get_object("tb_ubuntu_release_prefs")
		self.cb_ubuntu_repo = gtk.combo_box_new_text()
		self.cb_ubuntu_repo.append_text('Select Repository:')
		for repo in ISO_REPOSITORY:		
			self.cb_ubuntu_repo.append_text(repo)
		self.cb_ubuntu_repo.connect('changed', self.on_select_iso_image_repo)
		self.cb_ubuntu_repo.set_active(0)
		self.cb_ubuntu_repo.show()
		self.tb_ubuntu_release_prefs.attach(self.cb_ubuntu_repo, 1,2,0,1)
		# Ubuntu Releases Combo Box
		self.cb_ubuntu_release = gtk.combo_box_new_text()
		self.cb_ubuntu_release.connect('changed', self.on_select_ubuntu_release)
		self.cb_ubuntu_release.append_text('Select Release:')
		self.cb_ubuntu_release.set_active(0)
		self.cb_ubuntu_release.show()
		self.tb_ubuntu_release_prefs.attach(self.cb_ubuntu_release, 1,2,1,2)
		
		# Initialize Virtualization Method Options
		self.opt_virt_kvm = self.builder.get_object("opt_virt_kvm")
		self.opt_virt_kvm.connect("toggled", self.on_select_virt_method, "kvm")
		self.opt_virt_vbox = self.builder.get_object("opt_virt_vbox")
		self.opt_virt_vbox.connect("toggled", self.on_select_virt_method, "virtualbox")
		self.opt_virt_parallels = self.builder.get_object("opt_virt_parallels")
		self.opt_virt_parallels.connect("toggled", self.on_select_virt_method, "parallels")

		# Initialize Memory Options
		self.cbe_mem_size = self.builder.get_object("cbe_mem_size")
		self.cbe_mem_size.remove_text(0)
		self.cbe_mem_size.append_text('256')
		self.cbe_mem_size.append_text('384')
		self.cbe_mem_size.append_text('512')
		self.cbe_mem_size.append_text('Other...')
		self.cbe_mem_size.connect('changed', self.on_select_mem)

		# Initialize Disk Size Options
		self.cbe_disk_size = self.builder.get_object("cbe_disk_size")
		self.cbe_disk_size.remove_text(0)
		self.cbe_disk_size.append_text('4G')
		self.cbe_disk_size.append_text('6G')
		self.cbe_disk_size.append_text('8G')
		self.cbe_disk_size.append_text('Other...')
		self.cbe_disk_size.connect('changed', self.on_select_disk_size)

		# KVM Args
		self.txt_kvm_args = self.builder.get_object("txt_kvm_args")
		self.lb_kvm_args = self.builder.get_object("lb_kvm_args")

		# SMP
		self.lb_smp_nbr = self.builder.get_object("lb_smp_nbr")
		self.txt_smp_nbr = self.builder.get_object("txt_smp_nbr")
		self.lb_smp_available = self.builder.get_object("lb_smp_available")

		# Flavors
		self.chk_flavor_ubuntu = self.builder.get_object("chk_flavor_ubuntu")
		self.chk_flavor_ubuntu.connect("clicked", self.on_select_flavors)
		self.chk_flavor_kubuntu = self.builder.get_object("chk_flavor_kubuntu")
		self.chk_flavor_kubuntu.connect("clicked", self.on_select_flavors)
		self.chk_flavor_xubuntu = self.builder.get_object("chk_flavor_xubuntu")
		self.chk_flavor_xubuntu.connect("clicked", self.on_select_flavors)
		self.chk_flavor_edubuntu = self.builder.get_object("chk_flavor_edubuntu")
		self.chk_flavor_edubuntu.connect("clicked", self.on_select_flavors)
		self.chk_flavor_mythbuntu = self.builder.get_object("chk_flavor_mythbuntu")
		self.chk_flavor_mythbuntu.connect("clicked", self.on_select_flavors)
		self.chk_flavor_ubuntustudio = self.builder.get_object("chk_flavor_ubuntustudio")
		self.chk_flavor_ubuntustudio.connect("clicked", self.on_select_flavors)
		self.chk_flavor_other = self.builder.get_object("chk_flavor_other")
		self.chk_flavor_other.connect("clicked", self.on_select_flavors)

	def initialize_config_files(self):
		# prime configuration with defaults
		config_files = ["/etc/%s" % self.td.PKGRC, "%s/.%s" % (self.td.HOME, self.td.PKGRC), "%s/.config/%s/%s" % (self.td.HOME, self.td.PKG, self.td.PKGRC) ]
		for file in config_files:
			if os.path.exists(file):
				try:
					# Load config files for class
					self.td.load_config_file(file)
					# Load config files for local variables
					#self.load_config_files(file)
					self.logger.debug("Reading config file: [%s]" % file)
				except:
					self.logger.debug('Unable to load config file [%s]' % file)
				#	return False
			#return True

	def initialize_widgets_values(self):

		# CACHE Variables
		self.txt_gral_cache.set_text(self.td.CACHE)
		self.txt_img_cache.set_text(self.td.CACHE_IMG)
		self.txt_iso_cache.set_text(self.td.CACHE_ISO)

		# Determine the selected repository
		if self.td.p == 'cdimage':
			self.cb_ubuntu_repo.set_active(1)
		elif self.td.p == 'releases':
			self.cb_ubuntu_repo.set_active(2)

		# VIRT Methods
		if self.td.VIRT == 'kvm':
			self.opt_virt_kvm.set_active(True)
		elif self.td.VIRT == 'virtualbox':
			self.opt_virt_vbox.set_active(True)
		elif self.td.VIRT == 'parallels':
			self.opt_virt_parallels.set_active(True)

		# Memory
		if self.td.MEM == '256':
			self.cbe_mem_size.set_active(0)
		elif self.td.MEM == '384':
			self.cbe_mem_size.set_active(1)
		elif self.td.MEM == '512':
			self.cbe_mem_size.set_active(2)
		else:
			self.cbe_mem_size.set_active(3)
			self.cbe_mem_size.append_text(self.td.MEM)

		# Disk Size
		if self.td.DISK_SIZE == '4G':
			self.cbe_disk_size.set_active(0)
		elif self.td.DISK_SIZE == '6G':
			self.cbe_disk_size.set_active(1)
		elif self.td.DISK_SIZE == '8G':
			self.cbe_disk_size.set_active(2)
		else:
			self.cbe_disk_size.set_active(3)
			self.cbe_disk_size.append_text(self.td.DISK_SIZE)

		# KVM Args
		self.txt_kvm_args.set_text(self.td.KVM_ARGS)
		
		# SMP
		if self.td.SMP:
			self.txt_smp_nbr.set_text(self.td.SMP)
			if self.td.VIRT == 'kvm':
				self.lb_smp_available.set_text(" of %s available." % commands.getoutput("grep -c ^processor /proc/cpuinfo"))

		# Flavors
		i = 0
		while(i != -1):
			try:
				flavor = self.td.f.split()[i].replace(',', '')
				if flavor == 'ubuntu':
					self.chk_flavor_ubuntu.set_active(True)
				elif flavor == 'kubuntu':
					self.chk_flavor_kubuntu.set_active(True)
				elif flavor == 'xubuntu':
					self.chk_flavor_xubuntu.set_active(True)
				elif flavor == 'edubuntu':
					self.chk_flavor_edubuntu.set_active(True)
				elif flavor == 'mythbuntu':
					self.chk_flavor_mythbuntu.set_active(True)
				elif flavor == 'ubuntustudio':
					self.chk_flavor_ubuntustudio.set_active(True)
				elif flavor == 'other':
					self.chk_flavor_other.set_active(True)
				else:
					break
			except:
				i = -1
				break
			i = i + 1

		# Architectures
		for arch in self.td.m:
			if arch == 'i386':
				self.chk_arch_i386.set_active(True)
			if arch == 'amd64':
				self.chk_arch_amd64.set_active(True)

	def update_preferences(self):
		self.preferences = []
		# CACHE Variables
		if self.td.CACHE != self.txt_gral_cache.get_text():
			self.td.CACHE = self.txt_gral_cache.get_text()
			self.preferences.append(['cache', self.td.CACHE])
		if self.td.CACHE_IMG != self.txt_img_cache.get_text():
			self.td.CACHE_IMG = self.txt_img_cache.get_text()
			self.preferences.append(['cache_img', self.td.CACHE_IMG])
		if self.td.CACHE_ISO != self.txt_iso_cache.get_text():
			self.td.CACHE_ISO = self.txt_iso_cache.get_text()
			self.preferences.append(['cache_iso', self.td.CACHE_ISO])

		# Repo selection
		if self.repo != None:
			self.preferences.append(['p', self.td.p])

		if self.td.r != self.r:
			self.td.r = self.r
			if self.r !=None:
				self.preferences.append(['r', self.td.r])

		# KVM Args
		if self.td.KVM_ARGS != self.txt_kvm_args.get_text():
			self.td.KVM_ARGS = self.txt_kvm_args.get_text()
			self.preferences.append(['kvm_args', self.td.KVM_ARGS])

		if self.td.SMP != self.txt_smp_nbr.get_text():
			self.td.SMP = self.txt_smp_nbr.get_text()
			self.preferences.append(['smp', self.td.SMP])

		#ARCHs
		if 'amd64' in self.arch and 'i386' in self.arch:
			self.td.m = self.arch
			pass
		elif 'amd64' in self.arch or 'i386' in self.arch:
			self.td.m = self.arch
			self.preferences.append(['m', self.td.m[0]])

		# VIRT Methods
		if self.td.VIRT != self.virt_method and self.virt_method != None:
			self.td.VIRT = self.virt_method
			self.preferences.append(['virt', self.td.VIRT])

		# Memory - TODO: Add validation of text
		if self.mem == 'other':
			self.mem = self.cbe_mem_size.child.get_text()
		if self.td.MEM != self.mem:
			self.td.MEM = self.mem
			self.preferences.append(['mem', self.td.MEM])

		# Disk Size - TODO: Add validation of text
		if self.disk_size == 'other':
			self.disk_size = self.cbe_disk_size.child.get_text()
		if self.td.DISK_SIZE != self.disk_size:
			self.td.DISK_SIZE = self.disk_size
			self.preferences.append(['disk_size', self.td.DISK_SIZE])

		# Flavors
		#if self.td.f != self.flavors[:-2]:
		self.td.f = self.flavors[:-2]
		self.preferences.append(['f', self.td.f])

if __name__ == "__main__":
	dialog = PreferencesTestdrivegtkDialog()
	dialog.show()
	gtk.main()
