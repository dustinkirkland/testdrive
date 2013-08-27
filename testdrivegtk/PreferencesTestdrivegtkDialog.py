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
gettext.textdomain('testdrive')

ISO_REPOSITORY = ['cdimage', 'releases']
MEM_SIZE_TAB = ['256', '384', '512', '1024', '2048',_('Other...')]
DISK_SIZE_TAB = ['4', '6', '8', '10', '16',_('Other...')]

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
        self.set_title(_("TestDrive Preferences"))
        self.logger = logger1

        ##################################################################
        ###### Starting code of instancing TestDrive in Prefereces #######
        ##################################################################
        # Instancing a testdrive object.
        self.td = testdrive.Testdrive('testdrive-gtk')

        # Initializing local variables, loading config files, setting defaults.
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

        # Initialize widgets and its values
        self.initialize_widgets()
        self.initialize_widgets_values()
        self.logger.debug(_('finish_initialization()'))
        
        self.builder.get_object("txt_gral_cache")

    def initialize_variables(self):
        self.virt_method = None
        self.mem = None
        self.disk_size = None
        self.flavors = ""
        self.arch = []
        self.repo = None
        self.r = None

    def initialize_widgets(self):
        ##################################################################
        ########### Initializing all the widgets in variables ############
        ##################################################################
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
        self.btn_update_iso_list_cache = self.builder.get_object("btn_update_iso_list_cache")
        self.btn_update_iso_list_cache.connect("clicked", self.on_force_iso_list_update)

        # Ubuntu Releases
        self.chk_arch_i386 = self.builder.get_object("chk_arch_i386")
        self.chk_arch_i386.connect("clicked", self.on_select_arch, "i386")
        self.chk_arch_amd64 = self.builder.get_object("chk_arch_amd64")
        self.chk_arch_amd64.connect("clicked", self.on_select_arch, "amd64")

        # Ubuntu Repositories Combo Box
        self.tb_general_prefs = self.builder.get_object("tb_general_prefs")
        self.cb_ubuntu_repo = gtk.combo_box_new_text()
        self.cb_ubuntu_repo.set_size_request(260, -1)
        self.cb_ubuntu_repo.append_text(_('Select Repository:'))
        for repo in ISO_REPOSITORY:     
            self.cb_ubuntu_repo.append_text(repo)
        self.cb_ubuntu_repo.connect('changed', self.on_select_iso_image_repo)
        self.cb_ubuntu_repo.set_active(0)
        self.cb_ubuntu_repo.show()
        self.tb_general_prefs.attach(self.cb_ubuntu_repo, 1,2,7,8)
        # Ubuntu Releases Combo Box
        self.cb_ubuntu_release = gtk.combo_box_new_text()
        self.cb_ubuntu_release.set_size_request(260, -1)
        self.cb_ubuntu_release.connect('changed', self.on_select_ubuntu_release)
        self.cb_ubuntu_release.append_text(_('Select Release:'))
        self.cb_ubuntu_release.set_active(0)
        self.cb_ubuntu_release.show()
        self.tb_general_prefs.attach(self.cb_ubuntu_release, 1,2,8,9)
        
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
        for mem in MEM_SIZE_TAB:        
            self.cbe_mem_size.append_text(mem)
        self.cbe_mem_size.connect('changed', self.on_select_mem)

        # Initialize Disk Size Options
        self.cbe_disk_size = self.builder.get_object("cbe_disk_size")
        self.cbe_disk_size.remove_text(0)
        for disk in DISK_SIZE_TAB:
            self.cbe_disk_size.append_text(disk)
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
        self.chk_flavor_lubuntu = self.builder.get_object("chk_flavor_lubuntu")
        self.chk_flavor_lubuntu.connect("clicked", self.on_select_flavors)
        self.chk_flavor_ubuntukylin = self.builder.get_object("chk_flavor_ubuntukylin")
        self.chk_flavor_ubuntukylin.connect("clicked", self.on_select_flavors)
        self.chk_flavor_other = self.builder.get_object("chk_flavor_other")
        self.chk_flavor_other.connect("clicked", self.on_select_flavors)

    def initialize_config_files(self):
        ##################################################################
        ########### Read the configuration file for settings #############
        ##################################################################
        config_files = ["/etc/%s" % self.td.PKGRC, "%s/.%s" % (self.td.HOME, self.td.PKGRC), "%s/.config/%s/%s" % (self.td.HOME, self.td.PKG, self.td.PKGRC) ]
        for file in config_files:
            if os.path.exists(file):
                try:
                    # Load config files for class
                    self.td.load_config_file(file)
                    # Load config files for local variables
                    #self.load_config_files(file)
                    self.logger.debug(_("Reading config file: [%s]") % file)
                except:
                    self.logger.debug(_("Unable to load config file [%s]") % file)
                #   return False
            #return True

    def initialize_widgets_values(self):
        ##################################################################
        ###### Initialize the widget values - Displayes information ######
        ##################################################################
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
        elif self.td.MEM == '1024':
            self.cbe_mem_size.set_active(3)
        elif self.td.MEM == '2048':
            self.cbe_mem_size.set_active(4)
        else:
            self.cbe_mem_size.append_text(self.td.MEM)
            self.cbe_mem_size.set_active(6)

        # Disk Size
        if self.td.DISK_SIZE == '4G':
            self.cbe_disk_size.set_active(0)
        elif self.td.DISK_SIZE == '6G':
            self.cbe_disk_size.set_active(1)
        elif self.td.DISK_SIZE == '8G':
            self.cbe_disk_size.set_active(2)
        elif self.td.DISK_SIZE == '10G':
            self.cbe_disk_size.set_active(3)
        elif self.td.DISK_SIZE == '16G':
            self.cbe_disk_size.set_active(4)
        else:
            self.cbe_disk_size.append_text(self.td.DISK_SIZE.replace("G", ""))
            self.cbe_disk_size.set_active(6)

        # KVM Args
        self.txt_kvm_args.set_text(self.td.KVM_ARGS)
        
        # SMP
        if self.td.SMP:
            self.txt_smp_nbr.set_text(self.td.SMP)
            self.lb_smp_available.set_text(_(" of %s available.") % commands.getoutput("grep -c ^processor /proc/cpuinfo"))

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
                elif flavor == 'lubuntu':
                    self.chk_flavor_lubuntu.set_active(True)
                elif flavor == 'ubuntukylin':
                    self.chk_flavor_ubuntukylin.set_active(True)
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

    def update_iso_cache(self, force_update = False):
        ##################################################################
        ###### Code to update the ISO list from the repository Cache #####
        ##################################################################
        update_cache = None
        cdimage = False
        """ Verify if the ISO list is cached, if not, set variable to update/create it. """
        if force_update is True:
            update_cache = 1
            pass
        elif self.td.is_iso_list_cached() is False:
            update_cache = 1
        # If ISO list is cached, verify if it is expired. If it is, set variable to update it.
        elif self.td.is_iso_list_cache_expired() is True:
            update_cache = 1

        """ If variable set to update, obtain the ISO list from the Ubuntu CD Image repository. """
        if update_cache == 1:
            self.logger.info(_("Obtaining Ubuntu ISO list from %s...") % self.td.u)
            try:
                cdimage = self.td.obtain_ubuntu_iso_list_from_repo()
            except:
                self.logger.error(_("Could not obtain the Ubuntu ISO list from %s...") % self.td.u)

        """ If the ISO List was obtained, update the cache file"""
        if cdimage:
            self.logger.info(_("Updating the Ubuntu ISO list cache..."))
            try:
                self.td.update_ubuntu_iso_list_cache(cdimage)
            except:
                self.logger.error(_("Unable to update the Ubuntu ISO list cache..."))

    def get_preferences(self):
        """Returns preferences for testdrivegtk."""
        self.logger.debug(_("get_preferences()"))
        return self.td

    def _load_preferences(self):
        # TODO: add preferences to the self._preferences dict default
        # preferences that will be overwritten if some are saved
        pass

    def _save_preferences(self):
        ##################################################################
        ########### Saving the preferences to the config file ############
        ##################################################################
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

    def on_select_virt_method(self, widget, virt=None):
        # On selecting the viratualization method
        self.virt_method = virt
        # If Virtualization method is KVM, display related options.
        if virt == 'kvm':
            self.txt_kvm_args.set_sensitive(True)
            self.txt_smp_nbr.set_sensitive(True)
        else:
            self.txt_kvm_args.set_sensitive(False)
            self.txt_smp_nbr.set_sensitive(False)

    def on_select_mem(self, entry):
        # On selecting RAM memory.
        if entry.child.get_text() == MEM_SIZE_TAB[4]:
            entry.child.set_editable(True)
            self.mem = 'other'
        elif entry.get_active() >= 0:
            entry.child.set_editable(False)
            self.mem = entry.child.get_text()

    def on_select_disk_size(self, entry):
        # On selecting disk size
        if entry.child.get_text() == DISK_SIZE_TAB[3]:
            entry.child.set_editable(True)
            self.disk_size = 'other'
        elif entry.get_active() >= 0:
            entry.child.set_editable(False)
            self.disk_size = entry.child.get_text()

    def on_select_flavors(self, widget):
        # On selecting Ubuntu Flavors
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
        if self.chk_flavor_lubuntu.get_active():
            self.flavors = self.flavors + "lubuntu, "
        if self.chk_flavor_ubuntukylin.get_active():
            self.flavors = self.flavors + "ubuntukylin, "
        if self.chk_flavor_other.get_active():
            self.flavors = self.flavors + "other, "

    def on_select_arch(self, widget, arch):
        # On selecting the architecture
        if widget.get_active() == True:
            self.arch.append(arch)
        if widget.get_active() == False:
            self.arch.remove(arch)

    def on_txt_gral_cache_focus_out_event(self, widget, data=None):
        # When the CACHE text is changed, update related cache paths.
        txt_cache = self.txt_gral_cache.get_text()
        self.txt_iso_cache.set_text("%s/iso" % txt_cache)
        self.txt_img_cache.set_text("%s/img" % txt_cache)

    def on_cache_cleanup_clicked(self, widget, cache_path):
        # Method to cleanup cache
        filelist = os.listdir(cache_path)

        if not filelist:
            return

        try:
            for file in filelist:
                path = "%s/%s" % (cache_path, file)
                os.unlink(path)
        except:
            on_error_dlg(_("Unable to clean up files from [%s]") % cache_path)
    
    def on_select_iso_image_repo(self, widget):
        ##################################################################
        #### Select image repo, populate Release combobox accordingly ####
        ##################################################################
        model = widget.get_model()
        index = widget.get_active()
        if index:
            old_repo = self.td.p
            self.repo = model[index][0]
            self.td.p = self.repo
            self.txt_iso_list_cache.set_text("%s/%s.isos" % (self.td.CACHE, self.td.p))

            # Update cache commented given the hack to sync every repo on initialization
            #self.update_iso_cache()
            # Populate the releases combobox
            self.cb_ubuntu_release.get_model().clear()
            self.cb_ubuntu_release.append_text(_('Select Release:'))
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

    def on_force_iso_list_update(self, widget):
        selected_repo = self.td.p
        for repo in ISO_REPOSITORY:
            self.td.p = repo
            self.update_iso_cache(True)
        self.td.p = selected_repo

    def update_preferences(self):
        ##################################################################
        ###### Prepare the preferences to be saved in the config fiel ####
        ##################################################################
        self.preferences = []
        # CACHE Variables
        if self.txt_gral_cache.get_text() != None:
            self.td.CACHE = self.txt_gral_cache.get_text()
            self.preferences.append(['cache', self.td.CACHE])
        if self.txt_img_cache.get_text() != None:
            self.td.CACHE_IMG = self.txt_img_cache.get_text()
            self.preferences.append(['cache_img', self.td.CACHE_IMG])
        if self.txt_iso_cache.get_text() != None:
            self.td.CACHE_ISO = self.txt_iso_cache.get_text()
            self.preferences.append(['cache_iso', self.td.CACHE_ISO])

        # Repo selection
        if self.repo != None:
            self.preferences.append(['p', self.td.p])

        if self.r != None:
            self.td.r = self.r
            self.preferences.append(['r', self.td.r])

        # KVM Args
        if self.txt_kvm_args.get_text() != None:
            self.td.KVM_ARGS = self.txt_kvm_args.get_text()
            self.preferences.append(['kvm_args', self.td.KVM_ARGS])

        if self.txt_smp_nbr.get_text() != None:
            self.td.SMP = self.txt_smp_nbr.get_text()
            self.preferences.append(['smp', self.td.SMP])

        #ARCHs
        if 'amd64' in self.arch and 'i386' in self.arch:
            self.td.m = self.arch
            self.td.m.sort()
            self.preferences.append(['m', ' '.join(self.td.m)])
        elif 'amd64' in self.arch or 'i386' in self.arch:
            self.td.m = self.arch
            self.preferences.append(['m', self.td.m[0]])

        # VIRT Methods
        if self.virt_method != None:
            self.td.VIRT = self.virt_method
            self.preferences.append(['virt', self.td.VIRT])

        # Memory - TODO: Add validation of text
        if self.mem == 'other':
            self.mem = self.cbe_mem_size.child.get_text()
        if self.mem != None or self.mem not in MEM_SIZE_TAB:
            self.td.MEM = self.mem
            self.preferences.append(['mem', self.td.MEM])

        # Disk Size - TODO: Add validation of text
        if self.disk_size == 'other':
            self.disk_size = self.cbe_disk_size.child.get_text()
        if self.disk_size != None or self.disk_size not in DISK_SIZE_TAB:
            self.td.DISK_SIZE = "%sG" % self.disk_size
            self.preferences.append(['disk_size', self.td.DISK_SIZE])

        # Flavors
        self.td.f = self.flavors[:-2]
        self.preferences.append(['f', self.td.f])

if __name__ == "__main__":
    dialog = PreferencesTestdrivegtkDialog()
    dialog.show()
    gtk.main()
