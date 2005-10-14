from twisted.application import service, strports
from nevow import appserver
import chatola

site = appserver.NevowSite(chatola.createResource())
application = service.Application("chatola")
strports.service("8080", site).setServiceParent(application)
