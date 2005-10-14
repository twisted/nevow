from twisted.application import service, strports
from nevow import appserver

import postit, store

application = service.Application('blogengine')
db = store.initialize('db','fs')
site = appserver.NevowSite(resource = postit.Main(db))
strports.service("8080", site).setServiceParent(application)
