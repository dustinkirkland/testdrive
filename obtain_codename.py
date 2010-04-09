from launchpadlib.launchpad import Launchpad
from launchpadlib.errors import HTTPError
from httplib2 import ServerNotFoundError
import time, os, commands

#1. If no local cache, obtain from launchpad
#2. If local cache, and if it is expired, update from launchpad
#3. If local cache, and not expired, NOT update from launchpad
#4. release will always be loaded from the cache
#5. If no internet connection use cache file

HOME = os.getenv("HOME", "")
PKG = "testdrive"
lpcachedir = HOME+"/.launchpadlib/cache"
# If I use the default CACHE path, it mas be set to defaults BEFORE updating the release cache.
# If I someone changes the config file for the CACHE, the release file should be changed, however, it wont be able to create the ISO list.

def lp_obtain_release():
    try:
       launchpad = Launchpad.login_anonymously('testdrive', 'production', lpcachedir)
    except ServerNotFoundError as error:
       print "WARNING: %s" % error
       return False
    except HTTPError as error:
       print "ERROR: %s has occurred" % error
       return False
    return launchpad.distributions['ubuntu'].current_series.name

# Test case 1:
# 1.1. INTERNET: Create cache file by fetching LP
# 1.2. NO INTERNET: Fail to create cache file, exiting program
# Test case 2:
# 2.1. INTERNET: Update cache file
# 2.2. NO INTERNET: Fail to update cache file, Using old one

def obtain_devel_release():
    path = "%s/.cache/%s/current" % (HOME, PKG)

    if not os.path.exists(path):
       print "INFO: Caching current Ubuntu development release...\n"
       current_release = lp_obtain_release()
       if not current_release:
          print "ERROR: Please create file %s containing the current Ubuntu Development Release\n" % (path)
          return True
       os.system("mkdir -p %s/.cache/%s" % (HOME, PKG))
       os.system("echo %s > %s" % (current_release, path))
       return

    cache_time = time.localtime(os.path.getmtime(path))
    local_time = time.localtime()
    time_difference = time.mktime(local_time) - time.mktime(cache_time)

    if time_difference >= 604800:
       print "INFO: Updating current Ubuntu development release cache...\n"
       current_release = lp_obtain_release()
       if not current_release:
          print "WARNING: Cannot update the current Ubuntu development release. Using expired cache...\n"
          return
       os.system("echo %s > %s" % (current_release, path))

release_error = obtain_devel_release()
if release_error:
   exit(0)
print "Continuing execution"
path = "%s/.cache/%s/current" % (HOME, PKG)
(status, output) = commands.getstatusoutput('cat %s' % path)
print output
