# -*- test-case-name: nevow.test.test_page -*-

"""
Basic rendering classes for Nevow applications.

API Stability: Completely unstable.
"""

from cStringIO import StringIO
from zope.interface import implements

from nevow.inevow import (
    IRequest, IRenderable, IRendererFactory, IData, IRenderer)
from nevow import flat
from nevow.inevow import IResource
from nevow.context import WovenContext
from nevow.tags import invisible
from nevow.errors import MissingRenderMethod, MissingDocumentFactory
from nevow.util import Expose, maybeDeferred, log

from nevow.rend import _getPreprocessors

from nevow.flat.ten import registerFlattener
from nevow._flat import _OldRendererFactory, _ctxForRequest
from nevow._flat import deferflatten, FlattenerError
FlattenerError                  # see below in __all__


renderer = Expose(
    """
    Allow one or more methods to be used to satisfy template render
    directives::

    | class Foo(Element):
    |     def twiddle(self, request, tag):
    |         return tag['Hello, world.']
    |     renderer(twiddle)

    | <div xmlns:nevow="http://nevow.com/ns/nevow/0.1">
    |     <span nevow:render="twiddle" />
    | </div>

    Will result in this final output:

    | <div>
    |     <span>Hello, world.</span>
    | </div>
    """)



child = Expose(
    """
    Allow one or more methods to be used to create a child page of the current
    one::

    | class Root(Page):
    |     def bar(self, request):
    |         return Bar()
    |     child(bar)

    Accessing an url like: http://example.com/bar/ will result in returning
    the new L{nevow.page.Page} object Bar.
    """)



class Element(object):
    """
    Base for classes which can render part of a page.

    An Element is a renderer that can be embedded in a stan document and can
    hook its template (from the docFactory) up to render methods.

    An Element might be used to encapsulate the rendering of a complex piece of
    data which is to be displayed in multiple different contexts.  The Element
    allows the rendering logic to be easily re-used in different ways.

    Element implements L{IRenderable.renderer} to return render methods which
    are registered using L{nevow.page.renderer}.  For example::

        class Menu(Element):
            def items(self, request, tag):
                ....
            renderer(items)

    Render methods are invoked with two arguments: first, the
    L{nevow.inevow.IRequest} being served and second, the tag object which
    "invoked" the render method.

    Element implements L{IRenderable.render} to load C{docFactory} and return
    the result.

    @type docFactory: L{IDocFactory} provider
    @ivar docFactory: The factory which will be used to load documents to
        return from C{render}.
    """
    implements(IRenderable)

    docFactory = None
    preprocessors = ()

    def __init__(self, docFactory=None):
        if docFactory is not None:
            self.docFactory = docFactory


    def renderer(self, name):
        """
        Get the named render method using C{nevow.page.renderer}.
        """
        method = renderer.get(self, name, None)
        if method is None:
            raise MissingRenderMethod(self, name)
        return method


    def render(self, request):
        """
        Load and return C{self.docFactory}.
        """
        rend = self.rend
        if rend.im_func is not Element.__dict__['rend']:
            context = _ctxForRequest(request, [], self, False)
            return rend(context, None)

        docFactory = self.docFactory
        if docFactory is None:
            raise MissingDocumentFactory(self)
        return docFactory.load(None, _getPreprocessors(self))


    def rend(self, context, data):
        """
        Backwards compatibility stub.  This is only here so that derived
        classes can upcall to it.  It is not otherwise used in the rendering
        process.
        """
        context.remember(_OldRendererFactory(self), IRendererFactory)
        docFactory = self.docFactory
        if docFactory is None:
            raise MissingDocumentFactory(self)
        return docFactory.load(None, _getPreprocessors(self))

    def _rememberStuff(self, context):
        context.remember(self, IData)
        context.remember(self, IRenderer)
        context.remember(self, IRendererFactory)



def _flattenElement(element, ctx):
    """
    Use the new flattener implementation to flatten the given L{IRenderable} in
    a manner appropriate for the specified context.
    """
    if ctx.precompile:
        return element

    synchronous = []
    accumulator = []
    request = IRequest(ctx, None) # XXX None case is DEPRECATED
    finished = deferflatten(request, element, ctx.isAttrib, True, accumulator.append)
    def cbFinished(ignored):
        if synchronous is not None:
            synchronous.append(None)
        return accumulator
    def ebFinished(err):
        if synchronous is not None:
            synchronous.append(err)
        else:
            return err
    finished.addCallbacks(cbFinished, ebFinished)
    if synchronous:
        if synchronous[0] is None:
            return accumulator
        synchronous[0].raiseException()
    synchronous = None
    return finished

registerFlattener(_flattenElement, Element)



class Page(Element):
    implements(IResource)

    buffered = False
    children = None
    beforeRender = None
    afterRender = None
    addSlash = False

    def locateChild(self, request, segments):
        """
        Locate a child page of this one. request is a
        L{nevow.appserver.NevowRequest}, and segments is a tuple of each
        element in the URI. An tuple (page, segments) should be returned,
        where page is an instance of L{nevow.page.Page} and segments a tuple
        representing the remaining segments of the URI. If the child is not
        found, return NotFound instead.

        locateChild is designed to be easily overridden to perform fancy
        lookup tricks. However, the default locateChild is useful, and looks
        for children in three places, in this order:

         - in a dictionary, self.children
         - a member of self decorated with L{nevow.page.child}. This can be
           either an attribute or a method. If an attribute, it should be an
           object which can be adapted to IResource. If a method, it should
           take the request and return an object which can be adapted to
           IResource.
         - by calling self.childFactory(request, name). Name is a single
           string instead of a tuple of strings. This should return an object
           that can be adapted to IResource.
        """

        request = IRequest(request)

        if self.children is not None:
            r = self.children.get(segments[0], None)
            if r is not None:
                return r, segments[1:]

        if segments[0] == '':
            if self.addSlash and len(request.postpath) == 1:
                return self, segments[1:]

        childPage = child.get(self, segments[0], None)
        if childPage is not None:
            if IResource(childPage, None) is not None:
                return childPage, segments[1:]
            res = childPage(request)
            if res is not None:
                return res, segments[1:]

        res = self.childFactory(request, segments[0])
        if res is not None:
            return res, segments[1:]
        return None, ()

    def childFactory(self, request, segment):
        """
        Used by locateChild to return children which are generated
        dynamically. Note that higher level interfaces use only locateChild,
        and only nevow.page.Page.locateChild uses this.

        segment is a string represnting one element of the URI. request is a
        nevow.appserver.NevowRequest.

        The default implementation of this always returns None; it is
        intended to be overridden.
        """
        return None

    def renderHTTP(self, request):
        if self.addSlash and request.prepath[-1] != '':
            request.redirect(request.URLPath().child(''))
            return ''

        if self.beforeRender is not None:
            return maybeDeferred(self.beforeRender, request
                ).addCallback(lambda result, request: self._renderHTTP(request), request)
        return self._renderHTTP(request)

    def _renderHTTP(self, request):
        log.msg(http_render=None, uri=request.uri)

        context = WovenContext()
        self._rememberStuff(context)
        context.remember(request, IRequest)

        def finishRequest():
            if self.afterRender is not None:
                return maybeDeferred(self.afterRender, request)

        def doFinish(result):
            print 'Finishin it up lool'
            return maybeDeferred(finishRequest).addCallback(lambda r: result)

        def doWriteAndFinish(result):
            print 'Writin teh valuez'
            request.write(io.getvalue())
            return doFinish(result)

        if self.buffered:
            io = StringIO()
            writer = io.write
            finisher = doWriteAndFinish
        else:
            writer = request.write
            finisher = doFinish

        doc = self.docFactory.load(context)
        context.tag = invisible[doc]
        # XXX this is wrong, it won't support Deferreds.
        return ''.join(_flattenElement(self, context))


    def _rememberStuff(self, context):
        super(Page, self)._rememberStuff(context)
        context.remember(self, IResource)


    def renderString(self, request=None):
        """
        Render this page outside of a web request, returning a Deferred which
        will result in a string.
        """
        io = StringIO()
        writer = io.write

        def finisher(result):
            return io.getvalue()

        context = WovenContext()
        if request is not None:
            context.remember(request, IRequest)

        self._rememberStuff(context)
        doc = self.docFactory.load(context)

        context.tag = invisible[doc]
        return flat.flattenFactory(doc, context, writer, finisher)


__all__ = [
    'FlattenerError',
    'child',
    'Element',
    'renderer', 'deferflatten',
    'Page',
    ]
