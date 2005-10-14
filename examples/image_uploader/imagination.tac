from twisted.application import service, strports
from nevow import appserver

import imagination, images

application = service.Application('blogengine')
db = images.initialize('db','fs')
site = appserver.NevowSite(resource = imagination.Root(db))
strports.service("8080", site).setServiceParent(application)
