from twisted.application import service, strports
from nevow import appserver

import frontend, axiomstore as store, iblogengine
from smtpserver import BlogSMTPFactory

application = service.Application('blogengine')
db = store.initialize('db.axiom')
site = appserver.NevowSite(resource = frontend.UI())
site.remember(db, iblogengine.IStore)
strports.service("8080", site).setServiceParent(application)
strports.service("2500", BlogSMTPFactory(db)).setServiceParent(application)
