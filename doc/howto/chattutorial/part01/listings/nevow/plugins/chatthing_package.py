
from twisted.python import util

from nevow import athena

import chatthing

chatthingPkg = athena.AutoJSPackage(util.sibpath(chatthing.__file__, 'js'))
