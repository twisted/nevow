
from twisted.python import util

from nevow import athena

import echothing

chatthingPkg = athena.AutoJSPackage(util.sibpath(echothing.__file__, 'js'))
