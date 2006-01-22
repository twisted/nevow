from twisted.application import service, strports
from nevow import appserver

import imagination, images

application = service.Application('image_uploader')
db = images.initialize()
site = appserver.NevowSite(resource = imagination.Root(db))
strports.service("8080", site).setServiceParent(application)
