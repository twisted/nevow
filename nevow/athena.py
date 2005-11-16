import itertools, os

from zope.interface import implements

from twisted.internet import defer, error, reactor
from twisted.python import log

from nevow import inevow, rend, loaders, url, static, json, util, tags, guard

class LivePageError(Exception):
    """base exception for livepage errors"""

def neverEverCache(request):
    """
    Set headers to indicate that the response to this request should
    never, ever be cached.
    """
    request.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate')
    request.setHeader('Pragma', 'no-cache')

def activeChannel(request):
    """
    Mark this connection as a 'live' channel by setting the
    Connection: close header and flushing all headers immediately.
    """
    request.setHeader("Connection", "close")
    request.write('')

class LivePageTransport(object):
    implements(inevow.IResource)

    def __init__(self, livePage):
        self.livePage = livePage

    def locateChild(self, ctx, segments):
        return rend.NotFound

    def renderHTTP(self, ctx):
        req = inevow.IRequest(ctx)
        try:
            d = self.livePage.addTransport(req)
        except defer.QueueOverflow:
            log.msg("Fast transport-close path")
            d = defer.succeed('')
        args = req.args.get('args', [()])[0]
        if args != ():
            args = json.parse(args)
        kwargs = req.args.get('kw', [{}])[0]
        if kwargs != {}:
            kwargs = json.parse(kwargs)
        method = getattr(self, 'action_' + req.args['action'][0])
        method(ctx, *args, **kwargs)
        return d

    def _cbCall(self, result, requestId):
        def cb((d, req)):
            d.callback((None, unicode(requestId), u'text/json', result))
        self.livePage.getTransport().addCallback(cb)

    def _ebCall(self, err, method, func):
        log.msg("Dispatching %r to %r failed unexpectedly:" % (method, func))
        log.err(err)
        return err

    def action_call(self, ctx, method, objectID, *args, **kw):
        func = self.livePage._localObjects[objectID].locateMethod(ctx, method)
        requestId = inevow.IRequest(ctx).getHeader('Request-Id')
        if requestId is not None:
            result = defer.maybeDeferred(func, *args, **kw)
            result.addErrback(self._ebCall, method, func)
            result.addBoth(self._cbCall, requestId)
        else:
            try:
                func(*args, **kw)
            except:
                log.msg("Unhandled error in event handler:")
                log.err()

    def action_respond(self, ctx, *args, **kw):
        responseId = inevow.IRequest(ctx).getHeader('Response-Id')
        if responseId is None:
            log.msg("No Response-Id given")
            return

        self.livePage._remoteCalls.pop(responseId).callback((args, kw))

    def action_noop(self, ctx):
        pass


class LivePageFactory:
    noisy = True

    def __init__(self, pageFactory):
        self._pageFactory = pageFactory
        self.clients = {}

        self._transportQueue = {}
        self._requestIDCounter = {}
        self._remoteCalls = {}
        self._transportCount = {}
        self._noTransportsDisconnectCall = {}
        self._didDisconnect = {}
        self._transportTimeouts = {}
        self._disconnectNotifications = {}
        self._localObjects = {}
        self._localObjectIDCounter = {}

    def clientFactory(self, context):
        livepageId = inevow.IRequest(context).getHeader('Livepage-Id')
        if livepageId is not None:
            livepage = self.clients.get(livepageId)
            if livepage is not None:
                # A returning, known client.  Give them their page.
                return livepage
            else:
                # A really old, expired client.  Or maybe an evil
                # hax0r.  Give them a fresh new page and log the
                # occurrence.
                if self.noisy:
                    log.msg("Unknown Livepage-Id: %r" % (livepageId,))
                return self._manufactureClient()
        else:
            # A brand new client.  Give them a brand new page!
            return self._manufactureClient()

    def _manufactureClient(self):
        cl = self._pageFactory()
        cl.factory = self
        return cl

    def addClient(self, client):
        id = self._newClientID()
        self.clients[id] = client
        if self.noisy:
            log.msg("Rendered new LivePage %r: %r" % (client, id))
        return id

    def removeClient(self, clientID):
        del self.clients[clientID]
        if self.noisy:
            log.msg("Disconnected old LivePage %r" % (clientID,))

    def _newClientID(self):
        return guard._sessionCookie()

    def getClients(self):
        return self.clients.values()



def liveLoader(PageClass, FactoryClass=LivePageFactory):
    """
    Helper for handling Page creation for LivePage applications.

    Example::

        class Foo(Page):
            child_app = liveLoader(MyLivePage)

    This is an experimental convenience function.  Consider it even less
    stable than the rest of this module.
    """
    fac = FactoryClass(PageClass)
    def liveChild(self, ctx):
        return fac.clientFactory(ctx)
    return liveChild


class LivePage(rend.Page):
    transportFactory = LivePageTransport
    transportLimit = 2
    _rendered = False

    TRANSPORTLESS_DISCONNECT_TIMEOUT = 30
    TRANSPORT_IDLE_TIMEOUT = 300

    # HAHAHA
    def _cheat(attr, default=None):
        def get(self):
            return getattr(self.factory, attr).get(self.clientID, default)
        def set(self, value):
            getattr(self.factory, attr)[self.clientID] = value
        return property(get, set)

    _transportQueue = _cheat('_transportQueue')
    _requestIDCounter = _cheat('_requestIDCounter')
    _remoteCalls = _cheat('_remoteCalls')
    _transportCount = _cheat('_transportCount', 0)
    _noTransportsDisconnectCall = _cheat('_noTransportsDisconnectCall')
    _didDisconnect = _cheat('_didDisconnect')
    _transportTimeouts = _cheat('_transportTimeouts')
    _disconnectNotifications = _cheat('_disconnectNotifications')

    # Mapping of Object-ID to a Python object that will accept
    # messages from the client.
    _localObjects = _cheat('_localObjects')

    # Counter for assigning local object IDs
    _localObjectIDCounter = _cheat('_localObjectIDCounter')

    # Do this later: list of RemoteReference weakrefs with decref callbacks
    # _remoteObjects = _cheat('_remoteObjects')

    def __init__(self, iface, rootObject, *a, **kw):
        super(LivePage, self).__init__(*a, **kw)

        self.iface = iface
        self.rootObject = rootObject

        if self.__class__.__dict__.get('factory') is None:
            self.__class__.factory = LivePageFactory(lambda: self.__class__(*a, **kw))

#     A note on timeout/disconnect logic: whenever a live client goes from some
#     transports to no transports, a timer starts; whenever it goes from no
#     transports to some transports, the timer is stopped; if the timer ever
#     expires the connection is considered lost; every time a transport is
#     added a timer is started; when the transport is used up, the timer is
#     stopped; if the timer ever expires, the transport has a no-op sent down
#     it; if an idle transport is ever disconnected, the connection is
#     considered lost; this lets the server notice clients who actively leave
#     (closed window, browser navigates away) and network congestion/errors
#     (unplugged ethernet cable, etc)

    def renderHTTP(self, ctx):
        assert not self._rendered, "Cannot render a LivePage more than once"
        assert self.factory is not None, "Cannot render a LivePage without a factory"
        self._rendered = True
        self.clientID = self.factory.addClient(self)
        self._requestIDCounter = itertools.count().next
        self._transportQueue = defer.DeferredQueue(size=self.transportLimit)
        self._remoteCalls = {}
        self._disconnectNotifications = []

        self._localObjects = {}
        self._localObjectIDCounter = itertools.count().next

        self.addLocalObject(self)

        self._transportTimeouts = {}
        self._noTransports()

        neverEverCache(inevow.IRequest(ctx))
        return rend.Page.renderHTTP(self, ctx)

    def _noTransports(self):
        assert self._noTransportsDisconnectCall is None
        self._noTransportsDisconnectCall = reactor.callLater(
            self.TRANSPORTLESS_DISCONNECT_TIMEOUT, self._noTransportsDisconnect)

    def _someTransports(self):
        self._noTransportsDisconnectCall.cancel()
        self._noTransportsDisconnectCall = None

    def _newTransport(self, req):
        self._transportTimeouts[req] = reactor.callLater(
            self.TRANSPORT_IDLE_TIMEOUT, self._idleTransportDisconnect, req)

    def _noTransportsDisconnect(self):
        self._noTransportsDisconnectCall = None
        self._disconnected(error.TimeoutError("No transports created by client"))

    def _disconnected(self, reason):
        if not self._didDisconnect:
            self._didDisconnect = True
            notifications = self._disconnectNotifications
            self._disconnectNotifications = None
            for d in notifications:
                d.errback(reason)
            calls = self._remoteCalls
            self._remoteCalls = {}
            for (reqID, resD) in calls.iteritems():
                resD.errback(reason)
            self.factory.removeClient(self.clientID)

    def _idleTransportDisconnect(self, req):
        del self._transportTimeouts[req]
        # This is lame.  Queue may be the wrong way to store requests. :/
        def cbTransport((gotD, gotReq)):
            assert req is gotReq
            # We aren't actually sending a no-op here, just closing the
            # connection.  That's probably okay though.  The client will just
            # reconnect.
            gotD.callback([])
        self.getTransport().addCallback(cbTransport)

    def _activeTransportDisconnect(self, error, req):
        # XXX I don't think this will ever be a KeyError... but what if someone
        # wrote a response to the request, and halfway through the socket
        # kerploded... we might get here in that case?
        timeoutCall = self._transportTimeouts.pop(req, None)
        if timeoutCall is not None:
            timeoutCall.cancel()
        self._disconnected(error)

    def _ebOutput(self, err):
        msg = u"%s: %s" % (err.type.__name__, err.getErrorMessage())
        return 'throw new Error(%s);' % (json.serialize(msg),)

    def addTransport(self, req):
        neverEverCache(req)
        activeChannel(req)

        self.clientID = req.getHeader('Livepage-ID')

        req.notifyFinish().addErrback(self._activeTransportDisconnect, req)

        # _transportCount can be negative
        if self._transportCount == 0:
            self._someTransports()
        self._transportCount += 1

        self._newTransport(req)

        d = defer.Deferred()
        d.addCallbacks(json.serialize, self._ebOutput)
        self._transportQueue.put((d, req))
        return d

    def getTransport(self):
        self._transportCount -= 1
        if self._transportCount == 0:
            self._noTransports()
        def cbTransport((d, req)):
            timeoutCall = self._transportTimeouts.pop(req, None)
            if timeoutCall is not None:
                timeoutCall.cancel()
            return (d, req)
        return self._transportQueue.get().addCallback(cbTransport)

    def _cbCallRemote(self, (d, req), methodName, args):
        requestID = u's2c%i' % (self._requestIDCounter(),)
        objectID = 0
        d.callback((requestID, None, (objectID, methodName, tuple(args))))

        resultD = defer.Deferred()
        self._remoteCalls[requestID] = resultD
        return resultD

    def addLocalObject(self, obj):
        objID = self._localObjectIDCounter()
        self._localObjects[objID] = obj
        return objID

    def callRemote(self, methodName, *args):
        d = self.getTransport()
        d.addCallback(self._cbCallRemote, unicode(methodName, 'ascii'), args)
        return d

    def notifyOnDisconnect(self):
        d = defer.Deferred()
        self._disconnectNotifications.append(d)
        return d

    def render_liveglue(self, ctx):
        if True:
            mk = tags.script(type='text/javascript', src=url.here.child("mochikit.js"))
        else:
            mk = [
              tags.script(type='text/javascript', src=url.here.child('MochiKit').child(fName))
              for fName in ['Base.js', 'Async.js']]

        return [
            mk,
            tags.script(type='text/javascript', src=url.here.child('MochiKitLogConsole.js')),
            tags.script(type='text/javascript', src=url.here.child("athena.js")),
            tags.script(type='text/javascript')[tags.raw("""
                Nevow.Athena.livepageId = '%s';
            """ % self.clientID)],
        ]

    _javascript = {'mochikit.js': 'MochiKit.js',
                   'athena.js': 'athena.js',
                   'MochiKitLogConsole.js': 'MochiKitLogConsole.js'}
    def childFactory(self, ctx, name):
        if name in self._javascript:
            return static.File(util.resource_filename('nevow', self._javascript[name]))

    def child_MochiKit(self, ctx):
        return static.File(util.resource_filename('nevow', 'MochiKit'))

    def child_transport(self, ctx):
        return self.transportFactory(self)

    def locateMethod(self, ctx, methodName):
        if methodName in self.iface:
            return getattr(self.rootObject, methodName)
        raise AttributeError(methodName)

class LiveFragment(rend.Fragment):

    allowedMethods = {}

    def rend(self, context, data):
        myID = self.page.addLocalObject(self)
        context.fillSlots('live-fragment-id', myID)
        self.docFactory = loaders.stan(
            tags.div(id='athena_' + str(myID))[
                self.docFactory.load()])
        return super(LiveFragment, self).rend(context, data)

    def locateMethod(self, ctx, methodName):
        if methodName in self.allowedMethods:
            return getattr(self, methodName)
        raise AttributeError(methodName)
