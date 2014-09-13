
import os


class VirtException(Exception):
    pass


class VirtBase(object):

    def run(self, cmd):
        return(os.system(cmd))

    def run_or_die(self, cmd):
        if self.run(cmd) != 0:
            raise VirtException("Failed executing command: `%s`" % cmd)
