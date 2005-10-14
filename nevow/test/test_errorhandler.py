from cStringIO import StringIO
from zope.interface import implements
from twisted.internet import defer
from twisted.trial import unittest
from twisted.python import log
from nevow import appserver, context, flat, inevow, loaders, rend, tags as T, testutil


class Root(rend.Page):
    docFactory = loaders.stan(T.html[T.p['Root']])
        
        
class NotFoundHandler(object):
    implements(inevow.ICanHandleNotFound)
    html = 'NotFoundHandler'
    def renderHTTP_notFound(self, ctx):
        return self.html
        

class BadNotFoundHandler(object):
    implements(inevow.ICanHandleNotFound)
    html = 'NotFoundHandler'
    exceptionType = Exception
    exceptionMessage ='Error from BadNotFoundHandler'
    def __init__(self, exceptionType=None):
        if exceptionType is not None:
            self.exceptionType = exceptionType
    def renderHTTP_notFound(self, ctx):
        raise self.exceptionType(self.exceptionMessage)
        

def result(obj):
    d = defer.succeed(None)
    d.addCallback(lambda spam: obj)
    return unittest.deferredResult(d)
    

def getResource(root, path):
    ctx = context.RequestContext(tag=testutil.FakeRequest(uri=path))
    ctx = result(appserver.NevowSite(root).getPageContextForRequestContext(ctx))
    return ctx.tag
    
    
def renderResource(uri, notFoundHandler=None):
    """Render a resource at some uri and return the response code and html.
    """

    root = Root()
    if notFoundHandler is not None:
        root.remember(notFoundHandler, inevow.ICanHandleNotFound)
    site = appserver.NevowSite(root)
    ctx = context.SiteContext(tag=site)

    request = testutil.FakeRequest(uri=uri)
    ctx = context.RequestContext(parent=ctx, tag=request)
    ctx = result(site.getPageContextForRequestContext(ctx))
    html = result(ctx.tag.renderHTTP(ctx))

    return request.code, html


class Test404(testutil.TestCase):
    
    def test_standard404(self):
        """Test the standard 404 handler.
        """
        root = Root()
        resource = getResource(root, '/foo')
        self.failUnless(isinstance(resource, rend.FourOhFour))
        code, html = renderResource('/foo')
        self.assertEquals(rend.FourOhFour.notFound, html)
        self.assertEquals(code, 404)
        
    def test_remembered404Handler(self):
        code, html = renderResource('/foo', notFoundHandler=NotFoundHandler())
        self.assertEquals(html, NotFoundHandler.html)
        self.assertEquals(code, 404)
        
    def test_keyErroringNotFoundHandler(self):
        io = StringIO()
        def observer(ed):
            io.write(str(ed['message']))
        log.addObserver(observer)
        code, html = renderResource('/foo', notFoundHandler=BadNotFoundHandler())
        log.removeObserver(observer)
        self.assertIn(BadNotFoundHandler.exceptionMessage, io.getvalue())
        self.assertEquals(rend.FourOhFour.notFound, html)
        self.assertEquals(code, 404)
    test_keyErroringNotFoundHandler.skip = 'Log capture not working.'
    
