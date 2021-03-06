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

import sys
import commands, os, uuid, logging

from .base import VirtException, VirtBase


logger = logging.getLogger("testdrive.virt.kvm")


class KVM(VirtBase):

    def __init__(self, td):
        self.p = td.p
        self.CACHE_ISO = td.CACHE_ISO
        self.PATH_TO_ISO = td.PATH_TO_ISO
        self.DISK_FILE = td.DISK_FILE
        self.KVM_ARGS = td.KVM_ARGS
        self.MEM = td.MEM
        self.SMP = td.SMP
        self.DISK_SIZE = td.DISK_SIZE

    def is_disk_empty(self):
        (status, output) = commands.getstatusoutput("file %s | grep -qs 'empty'" % self.DISK_FILE)
        if status == 0:
            return True
        return False

    # Code to validate if virtualization is installed/supported
    def validate_virt(self):
        (status, output) = commands.getstatusoutput("kvm-ok")
        if status != 0:
            logger.warn("kvm-ok failed: %s", output)
        (status, output) = commands.getstatusoutput("dpkg -l qemu-utils")
        if status != 0:
            raise VirtException("Package qemu-utils is not installed.")

    def get_kvm_img_path(self):
        """Get kvm-img or qemu-img path and return it.

            Fall back to deprecated kvm-img. It may appear to be better
            to call just `which qemu-img kvm-img` but this way is cleaner.
        """
        for cmd in ['qemu-img', 'kvm-img']:
            status, output = commands.getstatusoutput('which %s' % (cmd))
            if status == 0 and output:
                return output.strip()
        raise VirtException("Can not find qemu-img nor kvm-img!")

    # Code to setup virtual machine
    def setup_virt(self):
        kvm_img = self.get_kvm_img_path()
        if self.p == 'cloud-daily' or self.p == 'cloud-releases':
            #path = "%s/%s" % (self.CACHE_ISO, self.PATH_TO_ISO.split(".tar.gz")[0].split("_")[-1])
            path = "%s/%s" % (self.CACHE_ISO, os.path.basename(self.PATH_TO_ISO).split(".tar.gz")[0])
            self.ORIG_DISK = "%s.img" % path
            self.FLOPPY_FILE = "%s-floppy" % path
            self.run_or_die("%s create -f qcow2 -b %s %s" % (kvm_img, self.ORIG_DISK, self.DISK_FILE))
        elif not os.path.exists(self.DISK_FILE) or self.is_disk_empty():
            logger.info("Creating disk image [%s] with [size:%s]..." % (self.DISK_FILE, self.DISK_SIZE))
            self.run_or_die("%s create -f qcow2 %s %s" % (kvm_img, self.DISK_FILE, self.DISK_SIZE))

    # Code launch virtual machine
    def launch_virt(self):
        logger.info("Running the Virtual Machine...")
        UUID = uuid.uuid4()
        if self.p == 'cloud-daily' or self.p == 'cloud-releases':
            cmd = "qemu-system-x86_64 -uuid %s -boot a -fda %s -drive file=%s,if=virtio %s" % (UUID, self.FLOPPY_FILE, self.DISK_FILE, self.KVM_ARGS)
        else:
            cmd = "qemu-system-x86_64 -uuid %s -m %s -smp %s -cdrom %s -drive file=%s,if=virtio,cache=writeback,index=0 %s" % (UUID, self.MEM, self.SMP, self.PATH_TO_ISO, self.DISK_FILE, self.KVM_ARGS)
        return cmd

