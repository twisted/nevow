# Copyright (c) 2004-2007 Divmod.
# See LICENSE for details.

"""
Tests for L{nevow.appserver}.
"""

from zope.interface import implementer

from io import BytesIO
from shlex import split

from twisted.trial.unittest import TestCase
from twisted.internet.defer import Deferred
from twisted.web.test.requesthelper import DummyChannel

from nevow import inevow
from nevow import appserver
from nevow import context
from nevow import testutil
from nevow import util

from nevow.appserver import NevowSite
from nevow.context import RequestContext
from nevow.rend import Page
from nevow.testutil import FakeRequest


@implementer(inevow.IResource)
class Render:

    rendered = False

    def locateChild(self, context, segs):
        return self, ()

    def renderHTTP(self, context):
        self.rendered = True
        return ''


class TestLookup(testutil.TestCase):
    def getResourceFor(self, root, url):
        r = testutil.FakeRequest()
        self.request = r
        r.postpath = url.split('/')
        ctx = context.RequestContext(tag=self.request)
        return util.maybeDeferred(
            appserver.NevowSite(root).getPageContextForRequestContext, ctx)

    def test_leafIsRoot(self):
        root = Render()
        self.getResourceFor(root, 'foo/bar/baz').addCallback(
            lambda result: self.assertIdentical(result.tag, root))

    def test_children(self):
        class FirstTwo(Render):
            def locateChild(self, context, segs):
                return LastOne(), segs[2:]

        class LastOne(Render):
            def locateChild(self, context, segs):
                return Render(), segs[1:]

        return self.getResourceFor(FirstTwo(), 'foo/bar/baz').addCallback(
            lambda result: self.assertIdentical(result.tag.__class__, Render))

    def test_oldresource(self):
        from twisted.web import resource
        r = resource.Resource()
        r.putChild('foo', r)
        return self.getResourceFor(r, 'foo').addCallback(
            lambda result: self.assertIdentical(r, result.tag.original))

    def test_deferredChild(self):
        class Deferreder(Render):
            def locateChild(self, context, segs):
                d = util.succeed((self, segs[1:]))
                return d

        r = Deferreder()
        return self.getResourceFor(r, 'foo').addCallback(
            lambda result: self.assertIdentical(r, result.tag))

    def test_cycle(self):
        @implementer(inevow.IResource)
        class Resource(object):
            def locateChild(self, ctx, segments):
                if segments[0] == 'self':
                    return self, segments
                return self, segments[1:]
        root = Resource()

        def asserterr(f):
            f.trap(AssertionError)
            return self.getResourceFor(root, 'notself')
        self.getResourceFor(root, 'self').addCallbacks(
            lambda : self.fail(),
            asserterr)



class TestSiteAndRequest(testutil.TestCase):
    def renderResource(self, resource, path):
        s = appserver.NevowSite(resource)
        channel = DummyChannel()
        channel.site = s
        r = appserver.NevowRequest(channel, True)
        r.path = path
        return r.process()

    def test_deferredRender(self):
        class Deferreder(Render):
            def renderHTTP(self, context):
                return util.succeed("hello")

        return self.renderResource(Deferreder(), b'foo').addCallback(
            lambda result: self.assertEqual(result, "hello"))

    def test_regularRender(self):
        class Regular(Render):
            def renderHTTP(self, context):
                return "world"

        return self.renderResource(Regular(), b'bar').addCallback(
            lambda result: self.assertEqual(result, 'world'))

    def test_returnsResource(self):
        class Res2(Render):
            def renderHTTP(self, ctx):
                return "world"

        class Res1(Render):
            def renderHTTP(self, ctx):
                return Res2()

        return self.renderResource(Res1(), b'bar').addCallback(
            lambda result: self.assertEqual(result, 'world'))

    def test_connectionLost(self):
        """
        L{Request.finish} is not called when the connection is lost before
        rendering has finished.
        """
        rendering = Deferred()
        class Res(Render):
            def renderHTTP(self, ctx):
                return rendering
        site = appserver.NevowSite(Res())
        channel = DummyChannel()
        channel.site = site
        request = appserver.NevowRequest(channel, True)
        request.connectionLost(Exception("Just Testing"))
        rendering.callback(b"finished")

        self.assertFalse(
            request.finished, "Request was incorrectly marked as finished.")


    def test_renderPOST(self):
        """
        A POST request with form data has the form data parsed into
        C{request.fields}.
        """
        class Res(Render):
            def renderHTTP(self, ctx):
                return b''

        s = appserver.NevowSite(Res())
        channel = DummyChannel()
        channel.site = s
        r = appserver.NevowRequest(channel, True)
        r.method = b'POST'
        r.path = b'/'
        r.content = BytesIO(b'foo=bar')
        self.successResultOf(r.process())
        self.assertEqual(r.fields['foo'].value, 'bar')



from twisted.internet import protocol, address

class FakeTransport(protocol.FileWrapper):
    disconnecting = False
    disconnect_done = False
    def __init__(self, addr, peerAddr):
        self.data = BytesIO()
        protocol.FileWrapper.__init__(self, self.data)
        self.addr = addr
        self.peerAddr = peerAddr
    def getHost(self):
        return self.addr
    def getPeer(self):
        return self.peerAddr
    def loseConnection(self):
        self.disconnecting = True

class Logging(testutil.TestCase):
    def setUp(self):
        class Res1(Render):
            def renderHTTP(self, ctx):
                return "boring"
        self.site = appserver.NevowSite(Res1())
        self.site.startFactory()
        self.addCleanup(self.site.stopFactory)
        self.site.logFile = BytesIO()


    def renderResource(self, path):
        """@todo: share me"""
        path = path.encode("utf-8")
        proto = self.site.buildProtocol(
            address.IPv4Address('TCP', 'fakeaddress', 42))
        transport = FakeTransport(
            address.IPv4Address('TCP', 'fakeaddress1', 42),
            address.IPv4Address('TCP', 'fakeaddress2', 42))
        proto.makeConnection(transport)
        proto.dataReceived(b'\r\n'.join([b'GET %b HTTP/1.0' % path,
                                        b'ReFeReR: fakerefer',
                                        b'uSeR-AgEnt: fakeagent',
                                        b'', b'']))
        assert transport.disconnecting
        return proto


    def setSiteTime(self, when):
        """
        Forcibly override the current time as known by C{self.site}.

        This relies on knowledge of private details of
        L{twisted.web.server.Site}.  It would be nice if there were an API on
        that class for doing this more properly, to facilitate testing.
        """
        self.site._logDateTime = when


    def test_oldStyle(self):
        self.setSiteTime('faketime')
        proto = self.renderResource('/foo')
        logLines = proto.site.logFile.getvalue().splitlines()
        self.assertEqual(len(logLines), 1)
        self.assertEqual(
            split(logLines[0].decode("utf-8")),
            ['fakeaddress2', '-', '-', 'faketime', 'GET /foo HTTP/1.0', '200', '6',
             'fakerefer', 'fakeagent'])


    def test_newStyle(self):
        class FakeLogger(object):
            logged = []
            def log(self, ctx):
                request = inevow.IRequest(ctx)
                self.logged.append(('fakeLog',
                                    request.getClientIP(),
                                    request.method.decode("utf-8"),
                                    request.uri.decode("utf-8"),
                                    request.clientproto.decode("utf-8"),
                                    request.code,
                                    request.sentLength))

        myLog = FakeLogger()
        self.site.remember(myLog, inevow.ILogger)
        proto = self.renderResource('/foo')
        logLines = proto.site.logFile.getvalue().splitlines()
        self.assertEqual(len(logLines), 0)
        self.assertEqual(myLog.logged,
                          [
            ('fakeLog', 'fakeaddress2', 'GET', '/foo', 'HTTP/1.0', 200, 6),
            ])



class HandleSegment(TestCase):
    """
    Tests for L{NevowSite.handleSegment}.

    L{NevowSite.handleSegment} interprets the return value of a single call to
    L{IResource.locateChild} and makes subsequent calls to that API or returns
    a context object which will render a resource.
    """
    def test_emptyPostPath(self):
        """
        If more path segments are consumed than remain in the request's
        I{postpath}, L{NevowSite.handleSegment} should silently not update
        I{prepath}.
        """
        request = FakeRequest(currentSegments=('',))
        context = RequestContext(tag=request)
        rootResource = Page()
        childResource = Page()
        site = NevowSite(rootResource)
        result = site.handleSegment(
            (childResource, ()), request, ('foo', 'bar'), context)
        self.assertEqual(request.prepath, [''])
        self.assertEqual(request.postpath, [])
