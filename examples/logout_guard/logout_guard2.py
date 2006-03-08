"""
How to access the session from guard's logout function,
with an example of remembering values within the session.
"""

# A resource for our site
#

import random
from zope.interface import implements, Interface

from nevow import guard
from nevow import rend
from nevow import loaders
from nevow import tags as T
from nevow import url
from nevow.inevow import ISession

class IValueHistory(Interface):
    pass

class ISessionValue(Interface):
    pass

class MyRootResource(rend.Page):
    """Some resource."""

    addSlash = True

    def render_randomNumber(self, ctx, data):
        session = ISession(ctx)
        
        number = random.randrange(0, 100)
        session.setComponent(ISessionValue, number)
        
        history = session.getComponent(IValueHistory)
        if history is None:
            history = []
        history.append(number)
        session.setComponent(IValueHistory, history)
        
        return str(number)
    
    def render_valueHistory(self, ctx, data):
        session = ISession(ctx)
        history = session.getComponent(IValueHistory, default=[])
        return repr(history[:-1])
        
    docFactory = loaders.stan(
        T.html[
            T.body[
               T.p['Your random number is: ', render_randomNumber],
               T.p['Previous random numbers were: ', render_valueHistory],
               T.div[T.a(href=url.here)['Click here to get a new number']],
               T.div[T.a(href=url.here.child(guard.LOGOUT_AVATAR))['Click here to log out']],
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
            values = session.getComponent(IValueHistory)
            session.unsetComponent(IValueHistory)
            print 'Logging avatar', avatar_id, 'out of session', session
            print 'Random numbers generated were', values
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

    
