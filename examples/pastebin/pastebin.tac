from twisted.application import strports
from twisted.application import service

from twisted.web import static

from nevow import appserver
from nevow import vhost

from pastebin import interfaces
from pastebin.service import FSPasteBinService
from pastebin.web import pages


application = service.Application('pastebin')

pastebin = FSPasteBinService('data')
pastebin.setServiceParent(application)

appResource = pages.RootPage(pastebin)
appResource.putChild('robots.txt', static.File('static/robots.txt'))
vResource = vhost.VHostMonsterResource()
appResource.putChild('vhost', vResource)


strports.service("8080", appserver.NevowSite(appResource)).setServiceParent(application)
