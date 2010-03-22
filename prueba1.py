execfile('/etc/testdriverc')

class Testdrive():
    def __init__(self):
	global KVM_ARGS
	global DISK_SIZE
	global MEM
	self.KVM_ARGS = KVM_ARGS
	self.DISK_SIZE = DISK_SIZE
	self.MEM = MEM

    def get_value(self, var):
        #var = "self." + var
	return eval("self." + var)

    def set_value(self):
        self.MEM = '100'
