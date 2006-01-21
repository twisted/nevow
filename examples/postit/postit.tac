from twisted.application import service, strports
from nevow import appserver

import postit, store

application = service.Application('postit')
db = store.initialize()
site = appserver.NevowSite(postit.Main(db))
strports.service("8080", site).setServiceParent(application)
