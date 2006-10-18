
from twisted.python import util

from nevow import athena

import nevow

nevowPkg = athena.AutoJSPackage(util.sibpath(nevow.__file__, 'js'))
