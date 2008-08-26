from twisted.application import internet
from twisted.application import service
from nevow import appserver
import helloworld

application = service.Application('helloworld')
site = appserver.NevowSite(helloworld.HelloWorld())
webServer = internet.TCPServer(8080, site)
webServer.setServiceParent(application)

