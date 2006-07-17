# -*- test-case-name: nevow.test.test_element -*-

"""
Basic rendering classes for Nevow applications.

API Stability: Completely unstable.
"""

from zope.interface import implements

from nevow.inevow import IRequest, IData, IRenderer, IRendererFactory
from nevow.context import WovenContext
from nevow.tags import invisible
from nevow.errors import MissingRenderMethod, MissingDocumentFactory

from nevow.util import Expose
from nevow.rend import _getPreprocessors

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



class Element(object):
    """
    An Element is an object responsible for rendering part or all of a page.

    Elements provide a way to separate the responsibility for page rendering
    into different units of code.

    Elements implement L{IRendererFactory} to return render methods which are
    registered using L{nevow.page.renderer}.  For example::

        class Menu(Element):
            def items(self, request, tag):
                ....
            renderer(items)

    Render methods are invoked with two arguments: first, the
    L{nevow.inevow.IRequest} being served and second, the tag object which
    "invoked" the render method.

    @ivar docFactory: The L{inevow.IDocFactory} which will be used during
    rendering.
    """
    implements(IRendererFactory, IRenderer)

    docFactory = None
    preprocessors = ()

    def __init__(self, docFactory=None):
        if docFactory is not None:
            self.docFactory = docFactory


    # IRendererFactory
    def renderer(self, context, name):
        renderMethod = renderer.get(self, name, None)
        if renderMethod is None:
            raise MissingRenderMethod(self, name)
        # XXX Hack to avoid passing context and data to the render method.
        # Eventually the rendering system should just not pass these to us.
        return lambda self, ctx, data: renderMethod(IRequest(ctx), ctx.tag)


    # IRenderer
    def rend(self, ctx, data):
        # Unfortunately, we still need a context to make the rest of the
        # rendering process work.  A goal should be to elimate this completely.
        context = WovenContext()

        if self.docFactory is None:
            raise MissingDocumentFactory(self)

        preprocessors = _getPreprocessors(self)

        doc = self.docFactory.load(context, preprocessors)

        context.remember(self, IData)
        context.remember(self, IRenderer)
        context.remember(self, IRendererFactory)
        context.tag = invisible[doc]
        return context


__all__ = [
    'renderer',

    'Element',
    ]
