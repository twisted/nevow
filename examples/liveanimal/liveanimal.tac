
from nevow.appserver import NevowSite
from liveanimal import createResource

from twisted.application import service, internet

application = service.Application('HADHF')
internet.TCPServer(
    4242,
    NevowSite(
        createResource(),
        logPath="web.log")
).setServiceParent(application)
