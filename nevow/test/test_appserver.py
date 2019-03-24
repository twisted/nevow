# Copyright (c) 2004-2007 Divmod.
# See LICENSE for details.

"""
Tests for L{nevow.appserver}.
"""

from zope.interface import implements, implementer

from cStringIO import StringIO
from shlex import split

from twisted.trial.unittest import TestCase
from twisted.internet.defer import Deferred
from twisted.web.test.requesthelper import DummyChannel
from twisted.web.util import DeferredResource
from twisted.internet.defer import succeed
from twisted.cred.portal import (
    Portal,
    IRealm,
)
from twisted.cred.checkers import (
    AllowAnonymousAccess,
)
from twisted.web.resource import (
    IResource,
)
from twisted.web.static import (
    Data,
)
from twisted.web.guard import (
    HTTPAuthSessionWrapper,
    BasicCredentialFactory,
)

from nevow import inevow
from nevow import appserver
from nevow import context
from nevow import testutil
from nevow import util

from nevow.appserver import NevowSite
from nevow.context import RequestContext
from nevow.rend import Page
from nevow.testutil import FakeRequest


class Render:
    implements(inevow.IResource)

    rendered = False

    def locateChild(self, context, segs):
        return self, ()

    def renderHTTP(self, context):
        self.rendered = True
        return ''


def getResourceFor(root, url):
    request = testutil.FakeRequest()
    request.postpath = url.split('/')
    ctx = context.RequestContext(tag=request)
    return util.maybeDeferred(
        appserver.NevowSite(root).getPageContextForRequestContext, ctx)

def renderResource(resource, path, method=None):
    s = appserver.NevowSite(resource)
    channel = DummyChannel()
    channel.site = s
    r = appserver.NevowRequest(channel, True)
    r.path = path
    if method is not None:
        r.method = method
    return r.process()

def renderResourceReturnTransport(resource, path, method):
    s = appserver.NevowSite(resource)
    channel = DummyChannel()
    channel.site = s
    r = appserver.NevowRequest(channel, True)
    r.path = path
    if method is not None:
        r.method = method
    d = r.process()
    d.addCallback(lambda ignored: channel.transport.written.getvalue())
    return d

class TestLookup(testutil.TestCase):
    def getResourceFor(self, root, url):
        return getResourceFor(root, url)

    def test_leafIsRoot(self):
        root = Render()
        return self.getResourceFor(root, 'foo/bar/baz').addCallback(
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
        class Resource(object):
            implements(inevow.IResource)
            def locateChild(self, ctx, segments):
                if segments[0] == 'self':
                    return self, segments
                return self, segments[1:]
        root = Resource()

        def asserterr(f):
            f.trap(AssertionError)
            return self.getResourceFor(root, 'notself')
        return self.getResourceFor(root, 'self').addCallbacks(
            lambda : self.fail(),
            asserterr)



class TestSiteAndRequest(testutil.TestCase):
    def renderResource(self, resource, path):
        return renderResource(resource, path)

    def test_deferredRender(self):
        class Deferreder(Render):
            def renderHTTP(self, context):
                return util.succeed("hello")

        return self.renderResource(Deferreder(), 'foo').addCallback(
            lambda result: self.assertEquals(result, "hello"))

    def test_regularRender(self):
        class Regular(Render):
            def renderHTTP(self, context):
                return "world"

        return self.renderResource(Regular(), 'bar').addCallback(
            lambda result: self.assertEquals(result, 'world'))

    def test_returnsResource(self):
        class Res2(Render):
            def renderHTTP(self, ctx):
                return "world"

        class Res1(Render):
            def renderHTTP(self, ctx):
                return Res2()

        return self.renderResource(Res1(), 'bar').addCallback(
            lambda result: self.assertEquals(result, 'world'))

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
        r.content = StringIO(b'foo=bar')
        self.successResultOf(r.process())
        self.assertEquals(r.fields[b'foo'].value, b'bar')



from twisted.internet import protocol, address

class FakeTransport(protocol.FileWrapper):
    disconnecting = False
    disconnect_done = False
    def __init__(self, addr, peerAddr):
        self.data = StringIO()
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
        self.site.logFile = StringIO()


    def renderResource(self, path):
        """@todo: share me"""
        proto = self.site.buildProtocol(
            address.IPv4Address('TCP', 'fakeaddress', 42))
        transport = FakeTransport(
            address.IPv4Address('TCP', 'fakeaddress1', 42),
            address.IPv4Address('TCP', 'fakeaddress2', 42))
        proto.makeConnection(transport)
        proto.dataReceived('\r\n'.join(['GET %s HTTP/1.0' % path,
                                        'ReFeReR: fakerefer',
                                        'uSeR-AgEnt: fakeagent',
                                        '', '']))
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
        self.assertEquals(len(logLines), 1)
        self.assertEqual(
            split(logLines[0]),
            ['fakeaddress2', '-', '-', 'faketime', 'GET /foo HTTP/1.0', '200', '6',
             'fakerefer', 'fakeagent'])


    def test_newStyle(self):
        class FakeLogger(object):
            logged = []
            def log(self, ctx):
                request = inevow.IRequest(ctx)
                self.logged.append(('fakeLog',
                                    request.getClientIP(),
                                    request.method,
                                    request.uri,
                                    request.clientproto,
                                    request.code,
                                    request.sentLength))

        myLog = FakeLogger()
        self.site.remember(myLog, inevow.ILogger)
        proto = self.renderResource('/foo')
        logLines = proto.site.logFile.getvalue().splitlines()
        self.assertEquals(len(logLines), 0)
        self.assertEquals(myLog.logged,
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


class OldResourceAdapterTests(TestCase):
    def test_deferredResource(self):
        expected = b"success"
        resource = Data(expected, b"text/plain")
        deferredResource = DeferredResource(succeed(resource))

        rootPage = Page()
        rootPage.child_deferredresource = deferredResource

        actual = self.successResultOf(
            renderResourceReturnTransport(
                rootPage,
                b"/deferredresource",
                b"GET",
            ),
        )
        self.assertTrue(
            actual.endswith(b"\r\n\r\n" + expected),
            "{!r} did not include expected response body {!r}".format(
                actual,
                expected,
            )
        )

    def test_deferredResourceChild(self):
        expected = b"success"
        resource = Data(expected, b"text/plain")
        intermediate = Data(b"incorrect intermediate", b"text/plain")
        intermediate.putChild(b"child", resource)
        deferredResource = DeferredResource(succeed(intermediate))

        rootPage = Page()
        rootPage.child_deferredresource = deferredResource

        actual = self.successResultOf(
            renderResourceReturnTransport(
                rootPage,
                b"/deferredresource/child",
                b"GET",
            ),
        )
        self.assertTrue(
            actual.endswith(b"\r\n\r\n" + expected),
            "{!r} did not include expected response body {!r}".format(
                actual,
                expected,
            )
        )

@implementer(IRealm)
class Realm(object):
    def __init__(self, avatar):
        self._avatar = avatar

    def requestAvatar(self, avatarId, mind, *interfaces):
        if IResource in interfaces:
            return IResource, self._avatar, lambda: None
        raise NotImplementedError("Only IResource")

class GuardTests(TestCase):
    """
    Tests for interaction with L{twisted.web.guard}.
    """
    def setUp(self):
        self.avatar_content = b"avatar content"
        self.child_content = b"child content"
        self.grandchild_content = b"grandchild content"

        grandchild = Data(self.grandchild_content, b"text/plain")

        child = Data(self.child_content, b"text/plain")
        child.putChild(b"grandchild", grandchild)

        self.avatar = Data(self.avatar_content, b"text/plain")
        self.avatar.putChild(b"child", child)

        self.realm = Realm(self.avatar)
        self.portal = Portal(
            self.realm,
            [AllowAnonymousAccess()],
        )
        self.guard = HTTPAuthSessionWrapper(
            self.portal,
            [BasicCredentialFactory("example.com")],
        )

    def test_avatar(self):
        """
        A request for exactly the guarded resource results in the avatar returned
        by cred.
        """
        root = Page()
        root.child_guarded = self.guard

        actual = self.successResultOf(
            renderResourceReturnTransport(
                root,
                b"/guarded",
                b"GET",
            ),
        )
        self.assertIn(self.avatar_content, actual)

    def test_child(self):
        """
        A request for a direct child of the guarded resource results in that child
        of the avatar returned by cred.
        """
        root = Page()
        root.child_guarded = self.guard

        actual = self.successResultOf(
            renderResourceReturnTransport(
                root,
                b"/guarded/child",
                b"GET",
            ),
        )
        self.assertIn(self.child_content, actual)

    def test_grandchild(self):
        """
        A request for a grandchild of the guarded resource results in that
        grandchild of the avatar returned by cred.

        Ideally this test would be redundant with L{test_child} but the
        implementation of L{IResource} support results in different codepaths
        for the 1st descendant vs the Nth descendant.
        """
        root = Page()
        root.child_guarded = self.guard

        actual = self.successResultOf(
            renderResourceReturnTransport(
                root,
                b"/guarded/child/grandchild",
                b"GET",
            ),
        )
        self.assertIn(self.grandchild_content, actual)
