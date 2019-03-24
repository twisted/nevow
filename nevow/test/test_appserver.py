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
    """
    Perform traversal for C{url} beginning at C{root}.

    @param root: The L{nevow.inevow.IResource} at which to begin.

    @param url: The relative path string of the url of the resource to
        retrieve.
    @type url: L{bytes}

    @return: A L{Deferred} that fires with a L{PageContext} for the discovered
        resource.
    """
    request = testutil.FakeRequest()
    request.postpath = url.split('/')
    ctx = context.RequestContext(tag=request)
    return util.maybeDeferred(
        appserver.NevowSite(root).getPageContextForRequestContext, ctx)

def renderResource(resource, path, method=None):
    """
    Perform a synthetic request for the given resource.

    @param resource: The L{nevow.inevow.IResource} from which to begin
        processing.

    @param path: The path of the url to use in processing.

    @param method: An optional request method to use.

    @return: The return value of L{NevowRequest.process} for this resource,
        path, and method.
    """
    s = appserver.NevowSite(resource)
    channel = DummyChannel()
    channel.site = s
    r = appserver.NevowRequest(channel, True)
    r.path = path
    if method is not None:
        r.method = method
    return r.process()

def renderResourceReturnTransport(resource, path, method):
    """
    Perform a synthetic request for the given resource.  This is like
    L{renderResource} but with a different return value.

    @return: All of the bytes written to the transport as a result of the
        rendering.
    """
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
    """
    Tests for L{OldResourceAdapter}.
    """
    def _deferredResourceTest(self, makeResource, pathSuffix):
        """
        Test the result of rendering some L{DeferredResource}-containing
        hierarchy.

        @param makeResource: A one-argument callable that returns a
            L{twisted.web.resource.IResource} provider to place into the
            resource hierarchy.  There should be a L{DeferredResource}
            somewhere in this hierarchy.  The argument is a byte string which
            should be included in the response to a request for the resource
            targetted by C{pathSuffix}.

        @pathSuffix: An absolute path into the resource returned by
            C{makeResource} identifying the resource to request and test the
            rendering of.

        @raise: A test-failing exception if the resource beneath
            C{makeResource(expected)} identified by C{pathSuffix} does not
            contain C{expected}.
        """
        expected = b"success"
        deferredResource = makeResource(expected)

        rootPage = Page()
        rootPage.child_deferredresource = deferredResource

        actual = self.successResultOf(
            renderResourceReturnTransport(
                rootPage,
                b"/deferredresource" + pathSuffix,
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

    def test_deferredResource(self):
        """
        A L{twisted.web.util.DeferredResource} can be placed into a L{NevowSite}
        resource hierarchy and when requested uses the result of its
        L{Deferred} to render a response.
        """
        def makeResource(expected):
            resource = Data(expected, b"text/plain")
            return DeferredResource(succeed(resource))
        return self._deferredResourceTest(makeResource, b"")

    def test_deferredResourceChild(self):
        """
        A L{twisted.web.util.DeferredResource} can be placed into a L{NevowSite}
        resource hierarchy and when a child of it is requested it uses the
        result of its L{Deferred} for child lookup and the resulting child is
        then rendered.
        """
        def makeResource(expected):
            resource = Data(expected, b"text/plain")
            intermediate = Data(b"incorrect intermediate", b"text/plain")
            intermediate.putChild(b"child", resource)
            return DeferredResource(succeed(intermediate))
        return self._deferredResourceTest(makeResource, b"/child")


@implementer(IRealm)
class OneIResourceAvatarRealm(object):
    """
    An L{IRealm} with a hard-coded L{IResource} avatar that it always returns.

    @ivar _avatar: The avatar.
    """
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

        self.realm = OneIResourceAvatarRealm(self.avatar)
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
