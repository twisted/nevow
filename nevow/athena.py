# -*- test-case-name: nevow.test.test_athena -*-

import itertools, os, re, warnings

from zope.interface import implements

from twisted.internet import defer, error, reactor
from twisted.python import log, failure, context
from twisted.python.util import sibpath
from twisted import plugin

from nevow import inevow, plugins, flat
from nevow import rend, loaders, url, static
from nevow import json, util, tags, guard, stan
from nevow.util import CachedFile

from nevow.page import Element, renderer

ATHENA_XMLNS_URI = "http://divmod.org/ns/athena/0.7"

expose = util.Expose(
    """
    Allow one or more methods to be invoked by the client::

    | class Foo(LiveElement):
    |     def twiddle(self, x, y):
    |         ...
    |     def frob(self, a, b):
    |         ...
    |     expose(twiddle, frob)

    The Widget for Foo will be allowed to invoke C{twiddle} and C{frob}.
    """)



class OrphanedFragment(Exception):
    """
    Raised if you try to render a L{LiveFragment} without somehow first setting
    its fragment parent.
    """



class LivePageError(Exception):
    """
    Base exception for LivePage errors.
    """
    jsClass = u'Divmod.Error'



class NoSuchMethod(LivePageError):
    """
    Raised when an attempt is made to invoke a method which is not defined or
    exposed.
    """
    jsClass = u'Nevow.Athena.NoSuchMethod'

    def __init__(self, objectID, methodName):
        self.objectID = objectID
        self.methodName = methodName
        LivePageError.__init__(self, objectID, methodName)



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


    def resourceFactory(self, fileName):
        """
        Retrieve an L{inevow.IResource} which will render the contents of
        C{fileName}.
        """
        return static.File(fileName)


    def locateChild(self, ctx, segments):
        try:
            impl = self.mapping[segments[0]]
        except KeyError:
            return rend.NotFound
        else:
            return self.resourceFactory(impl), []



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
    packageDeps = []

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

        if '.' in name:
            parent = '.'.join(name.split('.')[:-1])
            self.packageDeps = [self.getOrCreate(parent, mapping)]

        self._cache = CachedFile(self.mapping[self.name], self._getDeps)


    def __repr__(self):
        return 'JSModule(%r)' % (self.name,)


    _importExpression = re.compile('^// import (.+)$', re.MULTILINE)
    def _extractImports(self, fileObj):
        s = fileObj.read()
        for m in self._importExpression.finditer(s):
            yield self.getOrCreate(m.group(1).decode('ascii'), self.mapping)



    def _getDeps(self, jsFile):
        """
        Calculate our dependencies given the path to our source.
        """
        depgen = self._extractImports(file(jsFile, 'r'))
        return self.packageDeps + dict.fromkeys(depgen).keys()


    def dependencies(self):
        """
        Return a list of names of other JavaScript modules we depend on.
        """
        return self._cache.load()


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


class AutoJSPackage(object):
    """
    An IJavascriptPackage implementation that scans an on-disk hierarchy
    locating modules and packages.
    """
    implements(plugin.IPlugin, inevow.IJavascriptPackage)

    def __init__(self, baseDir):
        """
        @param baseDir: A path to the root of a JavaScript packages/modules
        filesystem hierarchy.
        """
        self.mapping = {}
        EMPTY = sibpath(__file__, 'empty.js')

        _revMap = {baseDir: ''}
        for root, dirs, filenames in os.walk(baseDir):
            stem = _revMap[root]

            for dir in dirs:
                name = stem + dir
                path = os.path.join(root, dir, '__init__.js')
                if not os.path.exists(path):
                    path = EMPTY
                self.mapping[unicode(name, 'ascii')] = path
                _revMap[os.path.join(root, dir)] = name + '.'

            for fn in filenames:
                if fn == '__init__.js':
                    continue

                if fn[-3:] != '.js':
                    continue

                name = stem + fn[:-3]
                path = os.path.join(root, fn)
                self.mapping[unicode(name, 'ascii')] = path



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
            self.mapping = {}
            self._loadPlugins = True
        else:
            self.mapping = mapping


    def getModuleForName(self, className):
        """
        Return the L{JSModule} most likely to define the given name.
        """
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
    getModuleForClass = getModuleForName


jsDeps = JSDependencies()



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

        divide = rest.rfind(':')
        if divide == -1:
            fname, ln = rest, ''
        else:
            fname, ln = rest[:divide], rest[divide + 1:]
        ln = int(ln)
        frames.insert(0, (func, fname, ln))
    return frames

def buildTraceback(frames, modules):
    """
    Build a chain of mock traceback objects from a serialized Error (or other
    exception) object, and return the head of the chain.
    """
    last = None
    first = None
    for func, fname, ln in frames:
        fname = modules.get(fname.split('/')[-1], fname)
        frame = JSFrame(func, fname, ln)
        tb = JSTraceback(frame, ln)
        if last:
            last.tb_next = tb
        else:
            first = tb
        last = tb
    return first


def getJSFailure(exc, modules):
    """
    Convert a serialized client-side exception to a Failure.
    """
    text = '%s: %s' % (exc[u'name'], exc[u'message'])

    frames = []
    if u'stack' in exc:
        frames = parseStack(exc[u'stack'])

    return failure.Failure(JSException(text), exc_tb=buildTraceback(frames, modules))



class LivePageTransport(object):
    implements(inevow.IResource)

    def __init__(self, messageDeliverer, useActiveChannels=True):
        self.messageDeliverer = messageDeliverer
        self.useActiveChannels = useActiveChannels


    def locateChild(self, ctx, segments):
        return rend.NotFound


    def renderHTTP(self, ctx):
        req = inevow.IRequest(ctx)
        neverEverCache(req)
        if self.useActiveChannels:
            activeChannel(req)

        requestContent = req.content.read()
        messageData = json.parse(requestContent)

        response = self.messageDeliverer.basketCaseReceived(ctx, messageData)
        response.addCallback(json.serialize)
        req.notifyFinish().addErrback(lambda err: self.messageDeliverer._unregisterDeferredAsOutputChannel(response))
        return response



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


class ConnectFailed(Exception):
    pass


class ConnectionLost(Exception):
    pass


CLOSE = u'close'

class ReliableMessageDelivery(object):
    _paused = 0
    _stopped = False

    outgoingAck = -1            # sequence number which has been acknowledged
                                # by this end of the connection.

    outgoingSeq = -1            # sequence number of the next message to be
                                # added to the outgoing queue.

    def __init__(self,
                 livePage,
                 connectTimeout=60, transportlessTimeout=30, idleTimeout=300,
                 connectionLost=None,
                 scheduler=None):
        self.livePage = livePage
        self.messages = []
        self.outputs = []
        self.connectTimeout = connectTimeout
        self.transportlessTimeout = transportlessTimeout
        self.idleTimeout = idleTimeout
        if scheduler is None:
            scheduler = reactor.callLater
        self.scheduler = scheduler
        self._transportlessTimeoutCall = self.scheduler(self.connectTimeout, self._connectTimedOut)
        self.connectionLost = connectionLost


    def _connectTimedOut(self):
        self._transportlessTimeoutCall = None
        self.connectionLost(failure.Failure(ConnectFailed("Timeout")))


    def _transportlessTimedOut(self):
        self._transportlessTimeoutCall = None
        self.connectionLost(failure.Failure(ConnectionLost("Timeout")))


    def _idleTimedOut(self):
        output, timeout = self.outputs.pop(0)
        if not self.outputs:
            self._transportlessTimeoutCall = self.scheduler(self.transportlessTimeout, self._transportlessTimedOut)
        output([self.outgoingAck, []])


    def _sendMessagesToOutput(self, output):
        log.msg(athena_send_messages=True, count=len(self.messages))
        output([self.outgoingAck, self.messages])


    def pause(self):
        self._paused += 1


    def unpause(self):
        self._paused -= 1
        if self._paused == 0:
            if self.messages and self.outputs:
                output, timeout = self.outputs.pop(0)
                timeout.cancel()
                if not self.outputs:
                    self._transportlessTimeoutCall = self.scheduler(self.transportlessTimeout, self._transportlessTimedOut)
                self._sendMessagesToOutput(output)


    def addMessage(self, msg):
        if self._stopped:
            return

        self.outgoingSeq += 1
        self.messages.append((self.outgoingSeq, msg))
        if not self._paused and self.outputs:
            output, timeout = self.outputs.pop(0)
            timeout.cancel()
            if not self.outputs:
                self._transportlessTimeoutCall = self.scheduler(self.transportlessTimeout, self._transportlessTimedOut)
            self._sendMessagesToOutput(output)


    def addOutput(self, output):
        if self._transportlessTimeoutCall is not None:
            self._transportlessTimeoutCall.cancel()
            self._transportlessTimeoutCall = None
        if not self._paused and self.messages:
            self._transportlessTimeoutCall = self.scheduler(self.transportlessTimeout, self._transportlessTimedOut)
            self._sendMessagesToOutput(output)
        else:
            if self._stopped:
                self._sendMessagesToOutput(output)
            else:
                self.outputs.append((output, self.scheduler(self.idleTimeout, self._idleTimedOut)))


    def close(self):
        assert not self._stopped, "Cannot multiply stop ReliableMessageDelivery"
        self.addMessage((CLOSE, []))
        self._stopped = True
        while self.outputs:
            output, timeout = self.outputs.pop(0)
            timeout.cancel()
            self._sendMessagesToOutput(output)
        self.outputs = None
        if self._transportlessTimeoutCall is not None:
            self._transportlessTimeoutCall.cancel()
            self._transportlessTimeoutCall = None


    def _unregisterDeferredAsOutputChannel(self, deferred):
        for i in xrange(len(self.outputs)):
            if self.outputs[i][0].im_self is deferred:
                output, timeout = self.outputs.pop(i)
                timeout.cancel()
                break
        else:
            return
        if not self.outputs:
            self._transportlessTimeoutCall = self.scheduler(self.transportlessTimeout, self._transportlessTimedOut)


    def _registerDeferredAsOutputChannel(self):
        d = defer.Deferred()
        self.addOutput(d.callback)
        return d


    def basketCaseReceived(self, ctx, basketCase):
        """
        This is called when some random JSON data is received from an HTTP
        request.

        A 'basket case' is currently a data structure of the form [ackNum, [[1,
        message], [2, message], [3, message]]]

        Its name is highly informal because unless you are maintaining this
        exact code path, you should not encounter it.  If you do, something has
        gone *badly* wrong.
        """
        ack, incomingMessages = basketCase

        outgoingMessages = self.messages

        # dequeue messages that our client certainly knows about.
        while outgoingMessages and outgoingMessages[0][0] <= ack:
            outgoingMessages.pop(0)

        if incomingMessages:
            log.msg(athena_received_messages=True, count=len(incomingMessages))

            if self.outgoingAck + 1 >= incomingMessages[0][0]:
                lastSentAck = self.outgoingAck
                self.outgoingAck = max(incomingMessages[-1][0], self.outgoingAck)
                self.pause()
                try:
                    for (seq, msg) in incomingMessages:
                        if seq > lastSentAck:
                            self.livePage.liveTransportMessageReceived(ctx, msg)
                        else:
                            log.msg("Athena transport duplicate message, discarding: %r %r" %
                                    (self.livePage.clientID,
                                     seq))
                    d = self._registerDeferredAsOutputChannel()
                finally:
                    self.unpause()
            else:
                d = defer.succeed([self.outgoingAck, []])
                log.msg(
                    "Sequence gap! %r went from %d to %d" %
                    (self.livePage.clientID,
                     self.outgoingAck,
                     incomingMessages[0][0]))
        else:
            d = self._registerDeferredAsOutputChannel()
        return d



class LivePage(rend.Page):
    factory = LivePageFactory()
    _rendered = False
    _didDisconnect = False

    useActiveChannels = True

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

    # Modules needed to bootstrap
    BOOTSTRAP_MODULES = ['Divmod', 'Divmod.Base', 'Divmod.Defer', 'Divmod.Runtime', 'Nevow', 'Nevow.Athena']

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
        self._includedModules = self.BOOTSTRAP_MODULES[:]
        self._disconnectNotifications = []


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
    def _becomeLive(self, location):
        """
        Assign this LivePage a clientID, associate it with a factory, and begin
        tracking its state.  This only occurs when a LivePage is *rendered*,
        not when it is instantiated.
        """
        self.clientID = self.factory.addClient(self)

        if self.jsModuleRoot is None:
            self.jsModuleRoot = location.child(self.clientID).child('jsmodule')

        self._requestIDCounter = itertools.count().next

        self._messageDeliverer = ReliableMessageDelivery(
            self,
            self.TRANSPORTLESS_DISCONNECT_TIMEOUT * 2,
            self.TRANSPORTLESS_DISCONNECT_TIMEOUT,
            self.TRANSPORT_IDLE_TIMEOUT,
            self._disconnected)
        self._remoteCalls = {}

        # Mapping of Object-ID to a Python object that will accept messages
        # from the client.
        self._localObjects = {}

        # Counter for assigning local object IDs
        self._localObjectIDCounter = itertools.count().next

        self.addLocalObject(self)


    def renderHTTP(self, ctx):
        assert not self._rendered, "Cannot render a LivePage more than once"
        assert self.factory is not None, "Cannot render a LivePage without a factory"
        self._rendered = True

        self._becomeLive(
            url.URL.fromString(
                flat.flatten(
                    url.here, ctx)))

        neverEverCache(inevow.IRequest(ctx))
        return rend.Page.renderHTTP(self, ctx)


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


    def addLocalObject(self, obj):
        objID = self._localObjectIDCounter()
        self._localObjects[objID] = obj
        return objID


    def callRemote(self, methodName, *args):
        requestID = u's2c%i' % (self._requestIDCounter(),)
        message = (u'call', (unicode(methodName, 'ascii'), requestID, args))
        resultD = defer.Deferred()
        self._remoteCalls[requestID] = resultD
        self.addMessage(message)
        return resultD


    def addMessage(self, message):
        self._messageDeliverer.addMessage(message)


    def notifyOnDisconnect(self):
        """
        Return a Deferred which will fire or errback when this LivePage is
        no longer connected.

        Note that if a LivePage never establishes a connection in the first
        place, the Deferreds this returns will never fire.

        @rtype: L{defer.Deferred}
        """
        d = defer.Deferred()
        self._disconnectNotifications.append(d)
        return d


    def getJSModuleURL(self, moduleName):
        return self.jsModuleRoot.child(moduleName)


    def getImportStan(self, moduleName):
        var = ''
        if '.' not in moduleName:
            var = 'var '
        moduleDef = '%s%s = {};' % (var, moduleName)
        return [tags.script(type='text/javascript')[tags.raw(moduleDef)],
                tags.script(type='text/javascript', src=self.getJSModuleURL(moduleName))]


    def render_liveglue(self, ctx, data):
        return ctx.tag[
            # Hit jsDeps.getModuleForName to force it to load some plugins :/
            # This really needs to be redesigned.
            [self.getImportStan(jsDeps.getModuleForName(name).name)
             for name
             in self.BOOTSTRAP_MODULES],
            tags.script(type='text/javascript')[tags.raw("""
                Divmod._location = '%(baseURL)s';
                Nevow.Athena.livepageId = '%(clientID)s';
            """ % {'clientID': self.clientID, 'baseURL': flat.flatten(self.transportRoot, ctx)})]
        ]


    def child_jsmodule(self, ctx):
        return JSModules(self.jsModules.mapping)


    _transportResource = None
    def child_transport(self, ctx):
        if self._transportResource is None:
            self._transportResource = LivePageTransport(
                self._messageDeliverer,
                self.useActiveChannels)
        return self._transportResource


    def locateMethod(self, ctx, methodName):
        if methodName in self.iface:
            return getattr(self.rootObject, methodName)
        raise AttributeError(methodName)


    def liveTransportMessageReceived(self, ctx, (action, args)):
        """
        A message was received from the reliable transport layer.  Process it by
        dispatching it first to myself, then later to application code if
        applicable.
        """
        method = getattr(self, 'action_' + action)
        method(ctx, *args)


    def action_call(self, ctx, requestId, method, objectID, args, kwargs):
        """
        Handle a remote call initiated by the client.
        """
        localObj = self._localObjects[objectID]
        try:
            func = localObj.locateMethod(ctx, method)
        except AttributeError:
            result = defer.fail(NoSuchMethod(objectID, method))
        else:
            result = defer.maybeDeferred(func, *args, **kwargs)
        def _cbCall(result):
            success = True
            if isinstance(result, failure.Failure):
                log.msg("Sending error to browser:")
                log.err(result)
                success = False
                if result.check(LivePageError):
                    result = (
                        result.value.jsClass,
                        result.value.args)
                else:
                    result = (
                        u'Divmod.Error',
                        [u'%s: %s' % (
                                result.type.__name__.decode('ascii'),
                                result.getErrorMessage().decode('ascii'))])
            message = (u'respond', (unicode(requestId), success, result))
            self.addMessage(message)
        result.addBoth(_cbCall)


    def action_respond(self, ctx, responseId, success, result):
        """
        Handle the response from the client to a call initiated by the server.
        """
        callDeferred = self._remoteCalls.pop(responseId)
        if success:
            callDeferred.callback(result)
        else:
            callDeferred.errback(getJSFailure(result, self.jsModules.mapping))


    def action_noop(self, ctx):
        """
        Handle noop, used to initialise and ping the live transport.
        """


    def action_close(self, ctx):
        """
        The client is going away.  Clean up after them.
        """
        self._messageDeliverer.close()
        self._disconnected(error.ConnectionDone("Connection closed"))



handler = stan.Proto('athena:handler')
_handlerFormat = "return Nevow.Athena.Widget.handleEvent(this, %(event)s, %(handler)s);"

def _rewriteEventHandlerToAttribute(tag):
    """
    Replace athena:handler children of the given tag with attributes on the tag
    which correspond to those event handlers.
    """
    if isinstance(tag, stan.Tag):
        extraAttributes = {}
        for i in xrange(len(tag.children) - 1, -1, -1):
            if isinstance(tag.children[i], stan.Tag) and tag.children[i].tagName == 'athena:handler':
                info = tag.children.pop(i)
                name = info.attributes['event'].encode('ascii')
                handler = info.attributes['handler']
                extraAttributes[name] = _handlerFormat % {
                    'handler': json.serialize(handler.decode('ascii')),
                    'event': json.serialize(name.decode('ascii'))}
                tag(**extraAttributes)
    return tag


def rewriteEventHandlerNodes(root):
    """
    Replace all the athena:handler nodes in a given document with onfoo
    attributes.
    """
    stan.visit(root, _rewriteEventHandlerToAttribute)
    return root


def _mangleId(oldId):
    """
    Return a consistently mangled form of an id that is unique to the widget
    within which it occurs.
    """
    return ['athenaid:', tags.slot('athena:id'), '-', oldId]


def _rewriteAthenaId(tag):
    """
    Rewrite id attributes to be prefixed with the ID of the widget the node is
    contained by. Also rewrite label "for" attributes which must match the id of
    their form element.
    """
    if isinstance(tag, stan.Tag):
        elementId = tag.attributes.pop('id', None)
        if elementId is not None:
            tag.attributes['id'] = _mangleId(elementId)
        if tag.tagName == "label":
            elementFor = tag.attributes.pop('for', None)
            if elementFor is not None:
                tag.attributes['for'] = _mangleId(elementFor)
        if tag.tagName in ('td', 'th'):
            headers = tag.attributes.pop('headers', None)
            if headers is not None:
                ids = headers.split()
                headers = [_mangleId(headerId) for headerId in ids]
                for n in xrange(len(headers) - 1, 0, -1):
                    headers.insert(n, ' ')
                tag.attributes['headers'] = headers
    return tag


def rewriteAthenaIds(root):
    """
    Rewrite id attributes to be unique to the widget they're in.
    """
    stan.visit(root, _rewriteAthenaId)
    return root


class _LiveMixin(object):
    jsClass = u'Nevow.Athena.Widget'

    preprocessors = [rewriteEventHandlerNodes, rewriteAthenaIds]

    fragmentParent = None

    _page = None

    # Reference to the result of a call to _structured, if one has been made,
    # otherwise None.  This is used to make _structured() idempotent.
    _structuredCache = None

    def __init__(self, *a, **k):
        super(_LiveMixin, self).__init__(*a, **k)
        self.liveFragmentChildren = []

    def page():
        def get(self):
            if self._page is None:
                if self.fragmentParent is not None:
                    self._page = self.fragmentParent.page
            return self._page
        def set(self, value):
            self._page = value
        doc = """
        The L{LivePage} instance which is the topmost container of this
        fragment.
        """
        return get, set, None, doc
    page = property(*page())


    def getInitialArguments(self):
        """
        Return a C{tuple} or C{list} of arguments to be passed to this
        C{LiveFragment}'s client-side Widget.

        This will be called during the rendering process.  Whatever it
        returns will be serialized into the page and passed to the
        C{__init__} method of the widget specified by C{jsClass}.

        @rtype: C{list} or C{tuple}
        """
        return ()


    def rend(self, context, data):
        assert isinstance(self.jsClass, unicode), "jsClass must be a unicode string"

        if self.page is None:
            raise OrphanedFragment(self)
        self._athenaID = self.page.addLocalObject(self)
        context.fillSlots('athena:id', self._athenaID)
        return super(_LiveMixin, self).rend(context, data)


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


    def _getRequiredModules(self):
        """
        Return a list of two-tuples containing module names and URLs at which
        those modules are accessible.  All of these modules must be loaded into
        the page before this Fragment's widget can be instantiated.  modules
        are accessible.
        """
        return [
            (dep.name, self.page.getJSModuleURL(dep.name))
            for dep
            in self._getModuleForClass().allDependencies()
            if self.page._shouldInclude(dep.name)]


    def _structured(self):
        """
        Retrieve an opaque object which may be usable to construct the
        client-side Widgets which correspond to this fragment and all of its
        children.
        """
        if self._structuredCache is not None:
            return self._structuredCache

        children = []
        requiredModules = []

        # Using the context here is terrible but basically necessary given the
        # /current/ architecture of Athena and flattening.  A better
        # implementation which was not tied to the rendering system could avoid
        # this.
        markup = context.call(
            {'children': children,
             'requiredModules': requiredModules},
            flat.flatten, tags.div(xmlns="http://www.w3.org/1999/xhtml")[self]).decode('utf-8')

        del children[0]

        self._structuredCache = {
            u'requiredModules': [(name, flat.flatten(url).decode('utf-8'))
                                 for (name, url) in requiredModules],
            u'class': self.jsClass,
            u'id': self._athenaID,
            u'initArguments': tuple(self.getInitialArguments()),
            u'markup': markup,
            u'children': children}
        return self._structuredCache


    def liveElement(self, request, tag):
        """
        Render framework-level boilerplate for making sure the Widget for this
        Element is created and added to the page properly.
        """
        requiredModules = self._getRequiredModules()

        # Add required attributes to the top widget node
        tag(**{'xmlns:athena': ATHENA_XMLNS_URI,
               'id': 'athena:%d' % self._athenaID,
               'athena:class': self.jsClass})

        # This will only be set if _structured() is being run.
        if context.get('children') is not None:
            context.get('children').append({
                    u'class': self.jsClass,
                    u'id': self._athenaID,
                    u'initArguments': self.getInitialArguments()})
            context.get('requiredModules').extend(requiredModules)
            return tag

        return (
            # Import stuff
            [self.getImportStan(name) for (name, url) in requiredModules],

            # Dump some data for our client-side __init__ into a text area
            # where it can easily be found.
            tags.textarea(id='athena-init-args-' + str(self._athenaID),
                          style="display: none")[
                json.serialize(self.getInitialArguments())],

            # Arrange to be instantiated
            tags.script(type='text/javascript')[
                """
                Nevow.Athena.Widget._widgetNodeAdded(%(athenaID)d);
                """ % {'athenaID': self._athenaID,
                       'pythonClass': self.__class__.__name__}],

            # Okay, application stuff, plus metadata
            tag,
            )
    renderer(liveElement)


    def render_liveFragment(self, ctx, data):
        return self.liveElement(inevow.IRequest(ctx), ctx.tag)


    def getImportStan(self, moduleName):
        return self.page.getImportStan(moduleName)


    def locateMethod(self, ctx, methodName):
        remoteMethod = expose.get(self, methodName, None)
        if remoteMethod is None:
            raise AttributeError(self, methodName)
        return remoteMethod


    def callRemote(self, methodName, *varargs):
        return self.page.callRemote(
            "Nevow.Athena.callByAthenaID",
            self._athenaID,
            unicode(methodName, 'ascii'),
            varargs)



class LiveFragment(_LiveMixin, rend.Fragment):
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

    Methods of the JavaScript widget class can also be bound as event
    handlers using the handler tag type in the Athena namespace:

        <form xmlns:athena="http://divmod.org/ns/athena/0.7">
            <athena:handler event="onsubmit" handler="doFoo" />
        </form>

    This will invoke the C{doFoo} method of the widget which contains the
    form node.

    Because this mechanism sets up error handling and otherwise reduces the
    required boilerplate for handling events, it is preferred and
    recommended over directly including JavaScript in the event handler
    attribute of a node.

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

    C{Nevow.Athena.Widget.callRemote} can be given permission to invoke methods
    on L{LiveFragment} instances by passing the functions which implement those
    methods to L{nevow.athena.expose} in this way::

        class SomeFragment(LiveFragment):
            def someMethod(self, ...):
                ...
            expose(someMethod)

    Only methods exposed in this way will be accessible.

    L{LiveFragment.callRemote} can be used to invoke any method of the widget
    on the client.

    Elements with id attributes will be rewritten so that the id is unique to
    that particular instance. The client-side C{Nevow.Athena.Widget.nodeById}
    API is provided to locate these later on. For example:

        <div id="foo" />

    and then:

        var node = self.nodyById('foo');

    On most platforms, this API will be much faster than similar techniques
    using C{Nevow.Athena.Widget.nodeByAttribute} etc.
    """
    def __init__(self, *a, **kw):
        super(LiveFragment, self).__init__(*a, **kw)
        warnings.warn("[v0.10] LiveFragment has been superceded by LiveElement.",
                      category=PendingDeprecationWarning,
                      stacklevel=2)



class LiveElement(_LiveMixin, Element):
    """
    Base-class for a portion of a LivePage.  When being rendered, a LiveElement
    has a special ID attribute added to its top-level tag.  This attribute is
    used to dispatch calls from the client onto the correct object (this one).

    A LiveElement must use the `liveElement' renderer somewhere in its document
    template.  The node given this renderer will be the node used to construct
    a Widget instance in the browser (where it will be saved as the `node'
    property on the widget object).

    JavaScript handlers for elements inside this node can use
    C{Nevow.Athena.Widget.get} to retrieve the widget associated with this
    LiveElement.  For example:

        <form onsubmit="Nevow.Athena.Widget.get(this).callRemote('foo', bar); return false;">

    Methods of the JavaScript widget class can also be bound as event
    handlers using the handler tag type in the Athena namespace:

        <form xmlns:athena="http://divmod.org/ns/athena/0.7">
            <athena:handler event="onsubmit" handler="doFoo" />
        </form>

    This will invoke the C{doFoo} method of the widget which contains the
    form node.

    Because this mechanism sets up error handling and otherwise reduces the
    required boilerplate for handling events, it is preferred and
    recommended over directly including JavaScript in the event handler
    attribute of a node.

    The C{jsClass} attribute of a LiveElement instance determines the
    JavaScript class used to construct its corresponding Widget.  This appears
    as the 'athena:class' attribute.

    JavaScript modules may import other JavaScript modules by using a special
    comment which Athena recognizes:

        // import Module.Name

    Different imports must be placed on different lines.  No other comment
    style is supported for these directives.  Only one space character must
    appear between the string 'import' and the name of the module to be
    imported.  No trailing whitespace or non-whitespace is allowed.  There must
    be exactly one space between '//' and 'import'.  There must be no
    preceeding whitespace on the line.

    C{Nevow.Athena.Widget.callRemote} can be given permission to invoke methods
    on L{LiveElement} instances by passing the functions which implement those
    methods to L{nevow.athena.expose} in this way::

        class SomeElement(LiveElement):
            def someMethod(self, ...):
                ...
            expose(someMethod)

    Only methods exposed in this way will be accessible.

    L{LiveElement.callRemote} can be used to invoke any method of the widget on
    the client.

    Elements with id attributes will be rewritten so that the id is unique to
    that particular instance. The client-side C{Nevow.Athena.Widget.nodeById}
    API is provided to locate these later on. For example:

        <div id="foo" />

    and then:

        var node = self.nodyById('foo');

    On most platforms, this API will be much faster than similar techniques
    using C{Nevow.Athena.Widget.nodeByAttribute} etc.
    """


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




__all__ = [
    'ATHENA_XMLNS_URI',

    'LivePageError', 'OrphanedFragment', 'ConnectFailed', 'ConnectionLost'

    'JSModules', 'JSModule', 'JSPackage', 'AutoJSPackage', 'allJavascriptPackages',
    'JSDependencies', 'JSException', 'JSCode', 'JSFrame', 'JSTraceback',

    'LivePage', 'LiveFragment', 'LiveElement', 'IntrospectionFragment',

    'expose', 'handler',
    ]
