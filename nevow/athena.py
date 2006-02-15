# -*- test-case-name: nevow.test.test_athena -*-

import itertools, os, re

from zope.interface import implements

from twisted.internet import defer, error, reactor
from twisted.python import log, failure
from twisted import plugin

from nevow import inevow, plugins, flat
from nevow import rend, loaders, url, static, json, util, tags, guard

ATHENA_XMLNS_URI = "http://divmod.org/ns/athena/0.7"

class LivePageError(Exception):
    """base exception for livepage errors"""


def neverEverCache(request):
    """
    Set headers to indicate that the response to this request should never,
    ever be cached.
    """
    request.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate')
    request.setHeader('Pragma', 'no-cache')


def activeChannel(request):
    """
    Mark this connection as a 'live' channel by setting the Connection: close
    header and flushing all headers immediately.
    """
    request.setHeader("Connection", "close")
    request.write('')



class JSModules(object):
    """
    Serve implementation files for a JavaScript module system.

    @ivar mapping: A C{dict} mapping JavaScript module names (eg,
    'Nevow.Athena') to C{str} instances which name files containing
    JavaScript source implementing those modules.
    """
    implements(inevow.IResource)

    def __init__(self, mapping):
        self.mapping = mapping

    def renderHTTP(self, ctx):
        return rend.FourOhFour()

    def locateChild(self, ctx, segments):
        if len(segments) != 1:
            return rend.NotFound
        try:
            impl = self.mapping[segments[0]]
        except KeyError:
            return rend.NotFound
        else:
            return static.File(impl), []



# XXX Next two functions copied out of Mantissa/xmantissa/signup.py
def _insertDep(dependent, ordered):
    for dependency in dependent.dependencies():
        _insertDep(dependency, ordered)
    if dependent not in ordered:
        ordered.append(dependent)



def dependencyOrdered(coll):
    ordered = []
    for dependent in coll:
        _insertDep(dependent, ordered)
    return ordered



class JSModule(object):
    _modules = {}

    lastModified = 0
    deps = None

    def getOrCreate(cls, name, mapping):
        # XXX This implementation of getOrCreate precludes the
        # simultaneous co-existence of several different package
        # namespaces.
        if name in cls._modules:
            return cls._modules[name]
        mod = cls._modules[name] = cls(name, mapping)
        return mod
    getOrCreate = classmethod(getOrCreate)


    def __init__(self, name, mapping):
        self.name = name
        self.mapping = mapping


    _importExpression = re.compile('^// import (.+)$', re.MULTILINE)
    def _extractImports(self, fileObj):
        s = fileObj.read()
        for m in self._importExpression.finditer(s):
            yield self.getOrCreate(m.group(1), self.mapping)


    def dependencies(self):
        jsFile = self.mapping[self.name]
        if jsFile is None:
            return iter(())
        mtime = os.path.getmtime(jsFile)
        if mtime >= self.lastModified:
            depgen = self._extractImports(file(jsFile, 'r'))
            self.deps = dict.fromkeys(depgen).keys()
            self.lastModified = mtime
        return self.deps


    def allDependencies(self):
        if self.mapping[self.name] is None:
            return []
        else:
            mods = [self]
            return dependencyOrdered(mods)



class JSPackage(object):
    implements(plugin.IPlugin, inevow.IJavascriptPackage)

    def __init__(self, mapping):
        """
        @param mapping: A C{dict} mapping JS module names to C{str}
        representing filesystem paths containing their
        implementations.
        """
        self.mapping = mapping



def allJavascriptPackages():
    """
    Return a dictionary mapping JavaScript module names to local filenames
    which implement those modules.  This mapping is constructed from all the
    C{IJavascriptPackage} plugins available on the system.  It also includes
    C{Nevow.Athena} as a special case.
    """
    d = {}
    for p in plugin.getPlugIns(inevow.IJavascriptPackage, plugins):
        d.update(p.mapping)
    return d



class JSDependencies(object):
    """
    Keeps track of which JavaScript files depend on which other
    JavaScript files (because JavaScript is a very poor language and
    cannot do this itself).
    """

    _loadPlugins = False

    def __init__(self, mapping=None):
        if mapping is None:
            self.mapping = {
                u'Divmod': util.resource_filename('nevow', 'divmod.js'),
                u'Divmod.Defer': util.resource_filename('nevow', 'defer.js'),
                u'Divmod.Runtime': util.resource_filename('nevow', 'runtime.js'),
                u'Divmod.XML': util.resource_filename('nevow', 'xml.js'),
                u'Nevow': util.resource_filename('nevow', 'nevow.js'),
                u'Nevow.Athena': util.resource_filename('nevow', 'athena.js'),
                u'Nevow.Athena.Test': util.resource_filename('nevow.livetrial', 'livetest.js'),
                u'Nevow.Athena.Tests': util.resource_filename('nevow.test', 'livetest.js'),
                u'Nevow.TagLibrary': util.resource_filename('nevow.taglibrary', 'taglibrary.js'),
                u'Nevow.TagLibrary.TabbedPane': util.resource_filename('nevow.taglibrary', 'tabbedPane.js'),
                u'MochiKit': util.resource_filename('nevow', 'MochiKit.js')}
            self._loadPlugins = True
        else:
            self.mapping = mapping


    def getModuleForClass(self, className):
        if self._loadPlugins:
            self.mapping.update(allJavascriptPackages())
            self._loadPlugins = False

        jsMod = className
        while jsMod:
            try:
                jsFile = self.mapping[jsMod]
            except KeyError:
                if '.' not in jsMod:
                    break
                jsMod = '.'.join(jsMod.split('.')[:-1])
            else:
                return JSModule.getOrCreate(jsMod, self.mapping)
        raise RuntimeError("Unknown class: %r" % (className,))
jsDeps = JSDependencies()



class ConnectionLostTransport(object):
    implements(inevow.IResource)

    def locateChild(self, ctx, segments):
        return rend.NotFound

    def renderHTTP(self, ctx):
        return json.serialize((u'close', ()))



class JSException(Exception):
    """
    Exception class to wrap remote exceptions from JavaScript.
    """



class JSCode(object):
    """
    Class for mock code objects in mock JS frames.
    """

    def __init__(self, name, filename):
        self.co_name = name
        self.co_filename = filename



class JSFrame(object):
    """
    Class for mock frame objects in JS client-side traceback wrappers.
    """

    def __init__(self, func, fname, ln):
        self.f_back = None
        self.f_locals = {}
        self.f_globals = {}
        self.f_code = JSCode(func, fname)
        self.f_lineno = ln



class JSTraceback(object):
    """
    Class for mock traceback objects representing client-side JavaScript
    tracebacks.
    """

    def __init__(self, frame, ln):
        self.tb_frame = frame
        self.tb_lineno = ln
        self.tb_next = None



def parseStack(stack):
    """
    Extract function name, file name, and line number information from the
    string representation of a JavaScript trace-back.
    """
    frames = []
    for line in stack.split('\n'):
        if '@' not in line:
            continue
        func, rest = line.split('@', 1)
        if ':' not in rest:
            continue
        fname, ln = rest.rsplit(':', 1)
        ln = int(ln)
        frames.insert(0, (func, fname, ln))
    return frames

def buildTraceback(frames):
    """
    Build a chain of mock traceback objects from a serialized Error (or other
    exception) object, and return the head of the chain.
    """
    last = None
    first = None
    for func, fname, ln in frames:
        frame = JSFrame(func, fname, ln)
        tb = JSTraceback(frame, ln)
        if last:
            last.tb_next = tb
        else:
            first = tb
        last = tb
    return first


def getJSFailure(exc):
    """
    Convert a serialized client-side exception to a Failure.
    """
    text = '%s: %s' % (exc[u'name'], exc[u'message'])

    frames = []
    if u'stack' in exc:
        frames = parseStack(exc[u'stack'])

    return failure.Failure(JSException(text), exc_tb=buildTraceback(frames))



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
        asciiKwargs = {}
        for (k, v) in kwargs.iteritems():
            asciiKwargs[k.encode('ascii')] = v

        method = getattr(self, 'action_' + req.args['action'][0])
        method(ctx, *args, **asciiKwargs)
        return d


    def _cbCall(self, result, requestId):
        def cb((d, req)):
            res = result
            success = True
            if isinstance(res, failure.Failure):
                log.msg("Sending error to browser:")
                log.err(res)
                success = False
                res = (unicode(result.type.__name__, 'ascii'), unicode(result.getErrorMessage(), 'ascii'))
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
            callDeferred.errback(getJSFailure(result))


    def action_noop(self, ctx):
        """
        Handle noop, used to initialise and ping the live transport.
        """


    def action_close(self, ctx):
        """
        The client is going away.  Clean up after them.
        """
        self.livePage._disconnected(error.ConnectionDone("Connection closed"))


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


_thePrivateAthenaResource = static.File(util.resource_filename('nevow', 'athena_private'))


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

    page = property(lambda self: self)

    def __init__(self, iface=None, rootObject=None, jsModules=None, jsModuleRoot=None, transportRoot=None, *a, **kw):
        super(LivePage, self).__init__(*a, **kw)

        self.iface = iface
        self.rootObject = rootObject
        if jsModules is None:
            jsModules = JSPackage(jsDeps.mapping)
        self.jsModules = jsModules
        self.jsModuleRoot = jsModuleRoot
        if transportRoot is None:
            transportRoot = url.here
        self.transportRoot = transportRoot
        self.liveFragmentChildren = []
        self._includedModules = ['MochiKit', 'Divmod', 'Divmod.Defer', 'Divmod.Runtime', 'Nevow', 'Nevow.Athena']


    def _shouldInclude(self, moduleName):
        if moduleName not in self._includedModules:
            self._includedModules.append(moduleName)
            return True
        return False


    # Child lookup may be dependent on the application state
    # represented by a LivePage.  In this case, it is preferable to
    # dispatch child lookup on the same LivePage instance as performed
    # the initial rendering of the page.  Override the default
    # implementation of locateChild to do this where appropriate.
    def locateChild(self, ctx, segments):
        try:
            client = self.factory.getClient(segments[0])
        except KeyError:
            return super(LivePage, self).locateChild(ctx, segments)
        else:
            return client, segments[1:]


    def child___athena_private__(self, ctx):
        return _thePrivateAthenaResource


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

        if self.jsModuleRoot is None:
            self.jsModuleRoot = url.here.child(self.clientID).child('jsmodule')

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
        # Called when there are absolutely, positively no Requests
        # outstanding to be used as transports for server-to-client
        # events.  Set up a timeout to consider this client
        # disconnected.  It's possible for this to be called even if
        # there were already no transports, so check to make sure that
        # we don't have a timeout already.
        if self._noTransportsDisconnectCall is None:
            self._noTransportsDisconnectCall = reactor.callLater(
                self.TRANSPORTLESS_DISCONNECT_TIMEOUT, self._noTransportsDisconnect)


    def _someTransports(self):
        # Called when we find ourselves with a spare Request to be
        # used as a transport for server-to-client events.  If there
        # is a pending timeout, cancel it.  It's possible for this to
        # be called even if there was already a spare Request
        # (although highly unlikely), so it's okay if there is no
        # timeout call active.
        if self._noTransportsDisconnectCall is not None:
            self._noTransportsDisconnectCall.cancel()
            self._noTransportsDisconnectCall = None


    def _newTransport(self):
        # Called when a new Request becomes available but will
        # immediately be used as a transport for a server-to-client
        # event.  There will be an active timeout call in this case,
        # since the only time a Request can be immediately consumed is
        # when there were none available already.  Just push the
        # timeout back a bit.  Perhaps this is an optimization, rather
        # than a necessary step in the state machine.  I can't really
        # tell.
        assert self._noTransportsDisconnectCall is not None
        self._noTransportsDisconnectCall.reset(self.TRANSPORTLESS_DISCONNECT_TIMEOUT)


    def _noTransportsDisconnect(self):
        self._noTransportsDisconnectCall = None
        self._disconnected(error.TimeoutError("No transports created by client"))


    def _disconnected(self, reason):
        if not self._didDisconnect:
            self._didDisconnect = True

            if self._noTransportsDisconnectCall is not None:
                self._noTransportsDisconnectCall.cancel()
                self._noTransportsDisconnectCall = None

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
            gotD.callback(json.serialize((u'noop', ())))
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

        self._transportCount += 1
        if self._transportCount > 0:
            self._someTransports()
        else:
            self._newTransport()

        self._transportTimeouts[req] = reactor.callLater(
            self.TRANSPORT_IDLE_TIMEOUT, self._idleTransportDisconnect, req)

        d = defer.Deferred()
        self._transportQueue.put((d, req))
        return d


    def getTransport(self):
        self._transportCount -= 1
        if self._transportCount <= 0:
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

    def getJSModuleURL(self, moduleName):
        return self.jsModuleRoot.child(moduleName)

    def render_liveglue(self, ctx, data):
        return ctx.tag[
            tags.script(type='text/javascript', src=self.getJSModuleURL('MochiKit')),
            tags.script(type='text/javascript', src=self.getJSModuleURL('Divmod')),
            tags.script(type='text/javascript', src=self.getJSModuleURL('Divmod.Defer')),
            tags.script(type='text/javascript', src=self.getJSModuleURL('Divmod.Runtime')),
            tags.script(type='text/javascript', src=self.getJSModuleURL('Nevow')),
            tags.script(type='text/javascript', src=self.getJSModuleURL('Nevow.Athena')),
            tags.script(type='text/javascript')[tags.raw("""
                Divmod._location = '%(baseURL)s';
                Nevow.Athena.livepageId = '%(clientID)s';
            """ % {'clientID': self.clientID, 'baseURL': flat.flatten(self.transportRoot, ctx)})]
        ]

    def newTransport(self):
        return self.transportFactory(self)

    def child_jsmodule(self, ctx):
        return JSModules(self.jsModules.mapping)

    def child_transport(self, ctx):
        return self.newTransport()

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

    A LiveFragment must use the `liveFragment' renderer somewhere in
    its document template.  The node given this renderer will be the
    node used to construct a Widget instance in the browser (where it
    will be saved as the `node' property on the widget object).

    JavaScript handlers for elements inside this node can use
    C{Nevow.Athena.Widget.get} to retrieve the widget associated with
    this LiveFragment.  For example:

        <form onsubmit="Nevow.Athena.Widget.get(this).callRemote('foo', bar); return false;">

    The C{jsClass} attribute of a LiveFragment instance determines the
    JavaScript class used to construct its corresponding Widget.  This
    appears as the 'athena:class' attribute.

    JavaScript modules may import other JavaScript modules by using a
    special comment which Athena recognizes:

        // import Module.Name

    Different imports must be placed on different lines.  No other
    comment style is supported for these directives.  Only one space
    character must appear between the string 'import' and the name of
    the module to be imported.  No trailing whitespace or
    non-whitespace is allowed.  There must be exactly one space
    between '//' and 'import'.  There must be no preceeding whitespace
    on the line.

    Methods defined on this class which are named in the
    C{allowedMethods} mapping may be invoked by the client using
    C{Nevow.Athena.Widget.callRemote}.  Similarly, calling
    C{callRemote} on the LiveFragment will invoke a method defined on
    the Widget class in the browser.
    """

    allowedMethods = {}

    jsClass = u'Nevow.Athena.Widget'

    def __init__(self, *a, **k):
        super(LiveFragment, self).__init__(*a, **k)
        self.liveFragmentChildren = []

    def rend(self, context, data):
        self._athenaID = self.page.addLocalObject(self)
        context.fillSlots('athena:id', self._athenaID)
        return super(LiveFragment, self).rend(context, data)


    def setFragmentParent(self, fragmentParent):
        """
        Sets the L{LiveFragment} (or L{LivePage}) which is the logical parent
        of this fragment.  This should parallel the client-side hierarchy.

        All LiveFragments must have setFragmentParent called on them before
        they are rendered for the client; otherwise, they will be unable to
        properly hook up to the page.

        LiveFragments should have their own setFragmentParent called before
        calling setFragmentParent on any of their own children.  The normal way
        to accomplish this is to instantiate your fragment children during the
        render pass.

        If that isn't feasible, instead override setFragmentParent and
        instantiate your children there.

        This architecture might seem contorted, but what it allows that is
        interesting is adaptation of foreign objects to LiveFragment.  Anywhere
        you adapt to LiveFragment, setFragmentParent is the next thing that
        should be called.
        """
        self.fragmentParent = fragmentParent
        self.page = fragmentParent.page
        fragmentParent.liveFragmentChildren.append(self)


    def _getModuleForClass(self):
        return jsDeps.getModuleForClass(self.jsClass)


    def render_liveFragment(self, ctx, data):
        modules = [dep.name for dep in self._getModuleForClass().allDependencies()]

        return (

            # Import stuff
            [tags.script(type='text/javascript',
                         src=self.getJSModuleURL(mod))
             for mod in modules if self.page._shouldInclude(mod)],

            # Arrange to be instantiated
            tags.script(type='text/javascript')[
                """
                Nevow.Athena.Widget._widgetNodeAdded(%(athenaID)d);
                """ % {'athenaID': self._athenaID}],

            # Okay, application stuff, plus metadata
            ctx.tag(**{'xmlns:athena': ATHENA_XMLNS_URI,
                       'athena:id': self._athenaID,
                       'athena:class': self.jsClass}),

            )


    def getJSModuleURL(self, moduleName):
        return self.page.getJSModuleURL(moduleName)


    def locateMethod(self, ctx, methodName):
        if methodName in self.allowedMethods:
            return getattr(self, methodName)
        raise AttributeError(self, methodName)


    def callRemote(self, methodName, *varargs):
        return self.page.callRemote(
            "Nevow.Athena.callByAthenaID",
            self._athenaID,
            unicode(methodName, 'ascii'),
            varargs)



class IntrospectionFragment(LiveFragment):
    """
    Utility for developers which provides detailed information about
    the state of a live page.
    """

    jsClass = u'Nevow.Athena.IntrospectionWidget'

    docFactory = loaders.stan(
        tags.span(render=tags.directive('liveFragment'))[
        tags.a(
        href="#DEBUG_ME",
        class_='toggle-debug')["Debug"]])
