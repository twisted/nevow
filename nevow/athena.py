import itertools, os

from zope.interface import implements

from twisted.internet import defer, error, reactor
from twisted.python import log, failure

from nevow import inevow, rend, loaders, url, static, json, util, tags, guard

ATHENA_XMLNS_URI = "http://divmod.org/ns/athena/0.7"

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

class ConnectionLostTransport(object):
    implements(inevow.IResource)

    def locateChild(self, ctx, segments):
        return rend.NotFound

    def renderHTTP(self, ctx):
        return json.serialize((u'close', ()))

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
            d = json.serialize((u'noop', ()))
        requestContent = req.content.read()
        args, kwargs = json.parse(requestContent)

        method = getattr(self, 'action_' + req.args['action'][0])
        method(ctx, *args, **kwargs)
        return d

    def _cbCall(self, result, requestId):
        def cb((d, req)):
            res = result
            success = True
            if isinstance(res, failure.Failure):
                success = False
                res = unicode(result.getErrorMessage())
            message = json.serialize((u'respond', (unicode(requestId), success, res)))
            d.callback(message)
        self.livePage.getTransport().addCallback(cb)

    def action_call(self, ctx, method, objectID, *args, **kw):
        """
        Handle a remote call initiated by the client.
        """
        func = self.livePage._localObjects[objectID].locateMethod(ctx, method)
        requestId = inevow.IRequest(ctx).getHeader('Request-Id')
        if requestId is not None:
            result = defer.maybeDeferred(func, *args, **kw)
            result.addBoth(self._cbCall, requestId)
        else:
            try:
                func(*args, **kw)
            except:
                log.msg("Unhandled error in event handler:")
                log.err()

    def action_respond(self, ctx, response):
        """
        Handle the response from the client to a call initiated by the server.
        """
        responseId = inevow.IRequest(ctx).getHeader('Response-Id')
        if responseId is None:
            log.msg("No Response-Id given")
            return

        success, result = response
        callDeferred = self.livePage._remoteCalls.pop(responseId)
        if success:
            callDeferred.callback(result)
        else:
            callDeferred.errback(Exception(result))

    def action_noop(self, ctx):
        """
        Handle noop, used to initialise and ping the live transport.
        """
        pass


class LivePageFactory:
    noisy = True

    def __init__(self):
        self.clients = {}

    def addClient(self, client):
        clientID = self._newClientID()
        self.clients[clientID] = client
        if self.noisy:
            log.msg("Rendered new LivePage %r: %r" % (client, clientID))
        return clientID

    def getClient(self, clientID):
        return self.clients[clientID]

    def removeClient(self, clientID):
        # State-tracking bugs may make it tempting to make the next line a
        # 'pop', but it really shouldn't be; if the Page instance with this
        # client ID is already gone, then it should be gone, which means that
        # this method can't be called with that argument.
        del self.clients[clientID]
        if self.noisy:
            log.msg("Disconnected old LivePage %r" % (clientID,))

    def _newClientID(self):
        return guard._sessionCookie()



class LivePage(rend.Page):
    transportFactory = LivePageTransport
    transportLimit = 2
    factory = LivePageFactory()
    _rendered = False
    _noTransportsDisconnectCall = None
    _transportCount = 0
    _didDisconnect = False

    # This is the number of seconds that is acceptable for a LivePage to be
    # considered 'connected' without any transports still active.  In other
    # words, if the browser cannot make requests for more than this timeout
    # (due to network problems, blocking javascript functions, or broken
    # proxies) then deferreds returned from notifyOnDisconnect() will be
    # errbacked with ConnectionLost, and the LivePage will be removed from the
    # factory's cache, and then likely garbage collected.
    TRANSPORTLESS_DISCONNECT_TIMEOUT = 30

    # This is the amount of time that each 'transport' request will remain open
    # to the server.  Although the underlying transport, i.e. the conceptual
    # connection established by the sequence of requests, remains alive, it is
    # necessary to periodically cancel requests to avoid browser and proxy
    # bugs.
    TRANSPORT_IDLE_TIMEOUT = 300

    def __init__(self, iface, rootObject, *a, **kw):
        super(LivePage, self).__init__(*a, **kw)

        self.iface = iface
        self.rootObject = rootObject


    # A note on timeout/disconnect logic: whenever a live client goes from some
    # transports to no transports, a timer starts; whenever it goes from no
    # transports to some transports, the timer is stopped; if the timer ever
    # expires the connection is considered lost; every time a transport is
    # added a timer is started; when the transport is used up, the timer is
    # stopped; if the timer ever expires, the transport has a no-op sent down
    # it; if an idle transport is ever disconnected, the connection is
    # considered lost; this lets the server notice clients who actively leave
    # (closed window, browser navigates away) and network congestion/errors
    # (unplugged ethernet cable, etc)

    def _becomeLive(self):
        """
        Assign this LivePage a clientID, associate it with a factory, and begin
        tracking its state.  This only occurs when a LivePage is *rendered*,
        not when it is instantiated.
        """
        self.clientID = self.factory.addClient(self)
        self._requestIDCounter = itertools.count().next
        self._transportQueue = defer.DeferredQueue(size=self.transportLimit)
        self._remoteCalls = {}
        self._disconnectNotifications = []

        # Mapping of Object-ID to a Python object that will accept messages
        # from the client.
        self._localObjects = {}

        # Counter for assigning local object IDs
        self._localObjectIDCounter = itertools.count().next

        # Do this later: list of RemoteReference weakrefs with decref callbacks
        # self._remoteObjects = ???

        self.addLocalObject(self)

        self._transportTimeouts = {}
        self._noTransports()


    def renderHTTP(self, ctx):
        assert not self._rendered, "Cannot render a LivePage more than once"
        assert self.factory is not None, "Cannot render a LivePage without a factory"
        self._rendered = True

        self._becomeLive()

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
            gotD.callback('')
        self.getTransport().addCallback(cbTransport)


    def _activeTransportDisconnect(self, error, req):
        # XXX I don't think this will ever be a KeyError... but what if someone
        # wrote a response to the request, and halfway through the socket
        # kerploded... we might get here in that case?
        timeoutCall = self._transportTimeouts.pop(req, None)
        if timeoutCall is not None:
            timeoutCall.cancel()
        self._disconnected(error)


    def addTransport(self, req):
        neverEverCache(req)
        activeChannel(req)

        req.notifyFinish().addErrback(self._activeTransportDisconnect, req)

        # _transportCount can be negative
        if self._transportCount == 0:
            self._someTransports()
        self._transportCount += 1

        self._newTransport(req)

        d = defer.Deferred()
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
        d.callback(json.serialize((u'call', (methodName, requestID, args))))

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

    def render_liveglue(self, ctx, data):
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

    def newTransport(self):
        return self.transportFactory(self)

    def child_transport(self, ctx):
        req = inevow.IRequest(ctx)
        clientID = req.getHeader('Livepage-ID')
        try:
            client = self.factory.getClient(clientID)
        except KeyError:
            return ConnectionLostTransport()
        else:
            # another instance, probably same class as me, but whatever; any
            # athena-based live page will do
            return client.newTransport()

    def locateMethod(self, ctx, methodName):
        if methodName in self.iface:
            return getattr(self.rootObject, methodName)
        raise AttributeError(methodName)

class LiveFragment(rend.Fragment):
    """
    Base-class for fragments of a LivePage.  When being rendered, a
    LiveFragment has a special ID attribute added to its top-level
    tag.  This attribute is used to dispatch calls from the client
    onto the correct object (this one).

    The C{docFactory} for a LiveFragment must provide a slot,
    C{nevow:athena_id} which will be filled by the framework.  For
    example, an xml template for a LiveFragment might start like this:

        <div>
            <nevow:attr name="athena:id"><nevow:slot name="athena:id" /></nevow:attr>

    Since this is a lot of typing, a convenience mechanism is
    provided.  Given an XML namespace identifier 'nevow' which refers
    to <http://nevow.com/ns/nevow/0.1>, you can rewrite the above as:

        <div nevow:render="athenaID">

    JavaScript handlers for elements inside this <div> can use
    C{Nevow.Athena.refByDOM} to invoke methods on this LiveFragment
    instance:

            <form onsubmit="Nevow.Athena.Widget.get(this).callRemote('foo', bar); return false;">

    By default, only methods named in the C{allowedMethods} mapping
    may be invoked by the client.
    """

    allowedMethods = {}

    def rend(self, context, data):
        self._athenaID = self.page.addLocalObject(self)
        context.fillSlots('athena:id', self._athenaID)
        return super(LiveFragment, self).rend(context, data)

    def locateMethod(self, ctx, methodName):
        if methodName in self.allowedMethods:
            return getattr(self, methodName)
        raise AttributeError(methodName)

    def render_athenaID(self, ctx, data):
        return ctx.tag(**liveFragmentID)

    def callRemote(self, methodName, *varargs):
        return self.page.callRemote("Nevow.Athena.callByAthenaID", self._athenaID, unicode(methodName, 'ascii'), varargs)

# Helper for docFactories defined with stan:
# tags.foo(..., **liveFragmentID)
liveFragmentID = {'athena:id': tags.slot('athena:id'), 'xmlns:athena': ATHENA_XMLNS_URI}
