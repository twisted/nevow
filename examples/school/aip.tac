from twisted.application import strports, service

from twisted.cred.portal import IRealm, Portal
from twisted.cred.checkers import ICredentialsChecker, AllowAnonymousAccess
from twisted.cred.credentials import IAnonymous

from axiom.store import Store
from nevow import appserver, guard

from aip import iaip, store as astore

class AxiomRequest(appserver.NevowRequest):
    def __init__(self, store, *a, **kw):
        appserver.NevowRequest.__init__(self, *a, **kw)
        self.store = store

    def process(self, *a, **kw):
        return self.store.transact(appserver.NevowRequest.process, self, *a, **kw)


class AxiomSite(appserver.NevowSite):
    def __init__(self, store, *a, **kw):
        appserver.NevowSite.__init__(self, *a, **kw)
        self.store = store
        self.requestFactory = lambda *a, **kw: AxiomRequest(self.store, *a, **kw)

application = service.Application('aip')

s = Store('aip.axiom')

#Uncomment when running the first time
## l = astore.LoginSystem(store=s)
## l.install()
## l.create_teacher('Pippo',
##                 'Pippo',
##                 '5th street',
##                 '03344555',
##                 'VLNALSDA#342',
##                 'pippo',
##                 'pippo')

realm = IRealm(s)
chkr = ICredentialsChecker(s)

p = Portal(realm)
p.registerChecker(AllowAnonymousAccess(), IAnonymous)
p.registerChecker(chkr)

res = guard.SessionWrapper(p)

site = AxiomSite(s, res)
site.remember(s, iaip.IStore)

webserver = strports.service('8080', site)
webserver.setServiceParent(application)
