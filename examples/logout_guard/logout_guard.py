"""
How to access the session from guard's logout function.
"""

# Some resource for our site
from zope.interface import implements

from nevow import guard
from nevow import rend
from nevow import loaders
from nevow import tags as T
from nevow import url

class MyRootResource(rend.Page):
    addSlash = True
    docFactory = loaders.stan(
        T.html[
            T.body[
               T.a(href=url.here.child(guard.LOGOUT_AVATAR))['Click here to log out']
               ]
            ]
        )

# Cred-specific implementation
#

from twisted.cred.portal import IRealm
from nevow.inevow import IResource

class Mind:
    def __init__(self, request, credentials):
        self.request = request
        self.credentials = credentials

class MyRealm:
    implements(IRealm)
    
    def requestAvatar(self, avatar_id, mind, *interfaces):
        if IResource in interfaces:
            return (
                IResource, 
                MyRootResource(),
                self.createLogout(avatar_id, mind)
                )
        raise NotImplementedError
            
    def createLogout(self, avatar_id, mind):
        def logout():
            # This will be a nevow.guard.GuardSession instance
            session = mind.request.getSession()
            print 'Logging avatar', avatar_id, 'out of session', session
        return logout

# Code for examples.tac
#

from twisted.cred.portal import Portal
from twisted.cred.checkers import AllowAnonymousAccess
from twisted.cred.credentials import IAnonymous
from nevow.guard import SessionWrapper

def createResource():
    portal = Portal(MyRealm())
    portal.registerChecker(AllowAnonymousAccess(), IAnonymous)

    # Here is the vital part: specifying a mindFactory for guard to use
    return SessionWrapper(portal, mindFactory=Mind)

