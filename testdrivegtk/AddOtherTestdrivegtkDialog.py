# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import gtk

from testdrivegtk.helpers import get_builder
import os, string, commands

import gettext
from gettext import gettext as _
gettext.textdomain('testdrive')

class AddOtherTestdrivegtkDialog(gtk.Dialog):
    __gtype_name__ = "AddothertestdrivegtkDialog"

    def __new__(cls, cache):
        """Special static method that's automatically called by Python when 
        constructing a new instance of this class.

        Returns a fully instantiated AddothertestdrivegtkDialog object.
        """
        builder = get_builder('AddOtherTestdrivegtkDialog')
        new_object = builder.get_object('addothertestdrivegtk_dialog')
        new_object.finish_initializing(builder, cache)
        return new_object

    def finish_initializing(self, builder, cache):
        """Called when we're finished initializing.

        finish_initalizing should be called after parsing the ui definition
        and creating a AddothertestdrivegtkDialog object with it in order to
        finish initializing the start of the new AddothertestdrivegtkDialog
        instance.
        """
        # Get a reference to the builder and set up the signals.
        self.builder = builder
        self.builder.connect_signals(self)
        self.CACHE = cache
        self.PROTO = None
        self.url = None
        self.desc = None

        # Initialize Widgets
        self.initialize_widgets()
        isos = self.get_other_isos_list_from_cache()
        self.i = 1
        if isos is True:
            self.initialize_isos_list()

    def ok(self, widget, data=None):
        """The user has elected to save the changes.

        Called before the dialog returns gtk.RESONSE_OK from run().
        """
        # Saving changes in the isos file
        path = "%s/other.isos" % self.CACHE
        try:
            f = open(path,'w')
            for item in self.liststore:
                iso = "other\tother\t\t%s\t\t%s\n" % (item[2], item[1])
                f.write(iso)
            f.close
        except IOError:
            pass

        pass

    def cancel(self, widget, data=None):
        """The user has elected cancel changes.

        Called before the dialog returns gtk.RESPONSE_CANCEL for run()
        """
        pass

    def on_select_sync_proto(self, widget):
        model = widget.get_model()
        index = widget.get_active()
        if index:
            self.PROTO = model[index][0]
        else:
            self.PROTO = None

    def on_error_dlg(self, data=None):
        errorbox = gtk.MessageDialog(self, 
            gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR, 
            gtk.BUTTONS_CLOSE, data)
        response = errorbox.run()
        errorbox.destroy()

    def on_info_dlg(self, data=None):
        errorbox = gtk.MessageDialog(self, 
            gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, 
            gtk.BUTTONS_CLOSE, data)
        errorbox.run()
        errorbox.destroy()

    def on_btn_add_iso_clicked(self, widget):
        ##################################################################
        ######### Adding new ISO's, however not yet saving them ##########
        ##################################################################
        add = self.on_validate_iso_url()
        if add is False:
            return

        # Adding ISO to list of ISO's
        old_proto = self.url.partition(":")[0]
        self.url = self.url.replace(old_proto, self.PROTO)

        # Add ISO to TreeView
        self.liststore.append([self.i, self.desc, self.url])

        self.txt_other_desc.set_text("")
        self.txt_other_url.set_text("")
        self.cb_sync_proto.set_active(0)

    def on_btn_del_iso_clicked(self, widget):
        # When Delete button is clicked, deletes it from the list store, 
        # but changes are not saved
        selection = self.treeview.get_selection()
        model, iter = selection.get_selected()
        if iter:
            model.remove(iter)
        return

    def on_validate_iso_url(self):
        ##################################################################
        ###### Validating that the input URL si correct and exists #######
        ##################################################################
        file = self.txt_other_url.get_text().strip()
        desc = self.txt_other_desc.get_text().replace(' ','-')

        if len(desc) == 0:
            self.on_error_dlg(_("Please insert a Description"))
            self.set_focus(self.txt_other_desc)
            return False

        if len(file) == 0:
            self.on_error_dlg(_("Please insert a URL"))
            self.set_focus(self.txt_other_url)
            return False

        self.desc = desc
        # If it's a URL, assume it's good
        for i in ("http", "ftp", "rsync", "file", "zsync"):
            if string.find(file, "%s://" % i) == 0:
                self.url = file
        #If it's a local path, test it for viability
        if commands.getstatusoutput("file \"%s\" | grep -qs \"ISO 9660\"" % file)[0] == 0:
            #return("file://%s" % file)
            self.url ="file://%s" % file

        if self.url is None:
            self.on_error_dlg(_("Invalid ISO URL [%s]") % file)
            return False

        # Validate if url exists
        proto = self.url.partition(":")[0]
        url = self.url
        print proto
        if proto == 'rsync' or proto == 'zsync':
            url = url.replace(proto, 'http')
        if proto == 'file':
            pass
        elif os.system("wget --spider -S %s 2>&1 | grep 'HTTP/1.. 200 OK'" % url) != 0:
            self.on_error_dlg(_("ISO not found at [%s]") % url)
            return False    

        if self.PROTO is None:
            self.on_error_dlg(_("No sync protocol has been selected, please select one."))
            return False
        else:
            return True

    def on_iso_list_expanded(self, expander, params):
        # When expander is clicked
        if expander.get_expanded():
            expander.add(self.scroll_iso_list)
        else:
            expander.remove(expander.child)
            self.resize(1, 1)

    def initialize_widgets(self):
        ##################################################################
        ############## Initializing Widget into variables ################
        ##################################################################
        self.txt_other_desc = self.builder.get_object("txt_other_desc")
        self.txt_other_url = self.builder.get_object("txt_other_url")

        # Initializing TreeView that will list the other ISO's
        self.liststore = gtk.ListStore(int, str, str)
        self.treeview = self.builder.get_object("tv_other_isos_list")
        self.treeview.columns = [None]*3
        self.treeview.columns[0] = gtk.TreeViewColumn('No.')
        self.treeview.columns[1] = gtk.TreeViewColumn(_('Description'))
        self.treeview.columns[2] = gtk.TreeViewColumn('URL')

        self.treeview.set_model(self.liststore)
        for n in range(3):
            # add columns to treeview
            self.treeview.append_column(self.treeview.columns[n])
            # create a CellRenderers to render the data
            self.treeview.columns[n].cell = gtk.CellRendererText()
            if n >= 1:
                self.treeview.columns[n].cell.set_property('editable', True)
            # add the cells to the columns
            self.treeview.columns[n].pack_start(self.treeview.columns[n].cell, True)
            # set the cell attributes to the appropriate liststore column
            self.treeview.columns[n].set_attributes(self.treeview.columns[n].cell, text=n)

        self.btn_add_other = self.builder.get_object("btn_add_iso")
        self.btn_add_other.connect("clicked", self.on_btn_add_iso_clicked)

        self.btn_del_iso = self.builder.get_object("btn_del_iso")
        self.btn_del_iso.connect("clicked", self.on_btn_del_iso_clicked)

        # Expander
        self.ex_other_iso_list = self.builder.get_object("ex_other_iso_list")
        self.ex_other_iso_list.connect('notify::expanded', self.on_iso_list_expanded)
        self.scroll_iso_list = self.builder.get_object("scrolledwindow1")
        self.ex_other_iso_list.remove(self.ex_other_iso_list.child)

        self.layout_table = self.builder.get_object("tb_other_iso")
        #Sync Protocol Combo Box
        self.cb_sync_proto = gtk.combo_box_new_text()
        self.cb_sync_proto.append_text(_("Select Protocol:"))
        self.cb_sync_proto.append_text("rsync")
        self.cb_sync_proto.append_text("zsync")
        #self.cb_sync_proto.append_text("wget")
        self.cb_sync_proto.append_text("file")
        self.cb_sync_proto.connect('changed', self.on_select_sync_proto)
        self.cb_sync_proto.set_active(0)
        self.cb_sync_proto.show()
        self.layout_table.attach(self.cb_sync_proto, 1,3,2,3, gtk.FILL | gtk.EXPAND, gtk.SHRINK)

    def get_other_isos_list_from_cache(self):
        ##################################################################
        ########### Obtaining the other ISO's from the CACHE #############
        ##################################################################
        if os.path.exists("%s/other.isos" % self.CACHE):
            try:
                f = open("%s/other.isos" % self.CACHE, 'r')
                self.ISOS = f.readlines()
                f.close
            except IOError:
                pass
        else:
            return False
        return True

    def initialize_isos_list(self):
        ##################################################################
        ###### Populating the TreeView with the ISOs from the CACHE ######
        ##################################################################
        for iso in self.ISOS:
            self.liststore.append([self.i, iso.split()[3], iso.split()[2]])
            self.i += 1

if __name__ == "__main__":
    dialog = AddOtherTestdrivegtkDialog()
    dialog.show()
    gtk.main()
