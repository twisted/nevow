
"""
Tests for L{nevow.page.Element}
"""

from twisted.trial.unittest import TestCase

from nevow.rend import Page
from nevow.inevow import IRequest
from nevow.testutil import FakeRequest
from nevow.context import WovenContext
from nevow.loaders import stan, xmlstr
from nevow.tags import directive, p
from nevow.errors import MissingRenderMethod, MissingDocumentFactory
from nevow.page import renderer, Element

class ElementTestCase(TestCase):
    """
    Tests for the awesome new Element class.
    """

    def _render(self, fragment):
        """
        Test helper which tries to render the given fragment.
        """
        ctx = WovenContext()
        req = FakeRequest()
        ctx.remember(req, IRequest)
        return Page(docFactory=stan(fragment)).renderString(ctx)


    def test_missingDocumentFactory(self):
        """
        Test that rendering a Element without a docFactory attribute raises
        the appropriate exception.
        """
        f = Element()
        return self.assertFailure(self._render(f), MissingDocumentFactory)


    def test_missingRenderMethod(self):
        """
        Test that rendering a Element and using a render directive in its
        document factory fails if there is no available render method to
        satisfy that directive.
        """
        f = Element(docFactory=stan(directive('renderMethod')))
        return self.assertFailure(self._render(f), MissingRenderMethod)


    def test_missingDocumentFactoryRepr(self):
        """
        Test that a L{MissingDocumentFactory} instance can be repr()'d without
        error.
        """
        class PrettyReprElement(Element):
            def __repr__(self):
                return 'Pretty Repr Element'
        self.assertIn('Pretty Repr Element',
                      repr(MissingDocumentFactory(PrettyReprElement())))


    def test_missingRenderMethodRepr(self):
        """
        Test that a L{MissingRenderMethod} instance can be repr()'d without
        error.
        """
        class PrettyReprElement(Element):
            def __repr__(self):
                return 'Pretty Repr Element'
        s = repr(MissingRenderMethod(PrettyReprElement(),
                                     'expectedMethod'))
        self.assertIn('Pretty Repr Element', s)
        self.assertIn('expectedMethod', s)


    def test_simpleStanRendering(self):
        """
        Test that a Element with a simple, static stan document factory
        renders correctly.
        """
        f = Element(docFactory=stan(p["Hello, world."]))
        return self._render(f).addCallback(
            self.assertEquals, "<p>Hello, world.</p>")


    def test_docFactoryClassAttribute(self):
        """
        Test that if there is a non-None docFactory attribute on the class
        of an Element instance but none on the instance itself, the class
        attribute is used.
        """
        class SubElement(Element):
            docFactory = stan(p["Hello, world."])
        return self._render(SubElement()).addCallback(
            self.assertEquals, "<p>Hello, world.</p>")


    def test_simpleXHTMLRendering(self):
        """
        Test that a Element with a simple, static xhtml document factory
        renders correctly.
        """
        f = Element(docFactory=xmlstr("<p>Hello, world.</p>"))
        return self._render(f).addCallback(
            self.assertEquals, "<p>Hello, world.</p>")


    def test_stanDirectiveRendering(self):
        """
        Test that a Element with a valid render directive has that directive
        invoked and the result added to the output.
        """
        class RenderfulElement(Element):
            def renderMethod(self, request, tag):
                return tag["Hello, world."]
            renderer(renderMethod)
        f = RenderfulElement(
            docFactory=stan(p(render=directive('renderMethod'))))
        return self._render(f).addCallback(
            self.assertEquals, "<p>Hello, world.</p>")


    def test_stanDirectiveRenderingOmittingTag(self):
        """
        Test that a Element with a render method which omits the containing
        tag successfully removes that tag from the output.
        """
        class RenderfulElement(Element):
            def renderMethod(self, request, tag):
                return "Hello, world."
            renderer(renderMethod)
        f = RenderfulElement(
            docFactory=stan(p(render=directive('renderMethod'))[
                    "Goodbye, world."]))
        return self._render(f).addCallback(
            self.assertEquals, "Hello, world.")


    def test_elementContainingStaticElement(self):
        """
        Test that a Element which is returned by the render method of another
        Element is rendered properly.
        """
        class RenderfulElement(Element):
            def renderMethod(self, request, tag):
                return tag[Element(docFactory=stan("Hello, world."))]
            renderer(renderMethod)
        f = RenderfulElement(
            docFactory=stan(p(render=directive('renderMethod'))))
        return self._render(f).addCallback(
            self.assertEquals, "<p>Hello, world.</p>")


    def test_elementContainingDynamicElement(self):
        """
        Test that directives in the document factory of a Element returned from a
        render method of another Element are satisfied from the correct object:
        the "inner" Element.
        """
        class OuterElement(Element):
            def outerMethod(self, request, tag):
                return tag[InnerElement(docFactory=stan(directive("innerMethod")))]
            renderer(outerMethod)
        class InnerElement(Element):
            def innerMethod(self, request, tag):
                return "Hello, world."
            renderer(innerMethod)
        f = OuterElement(
            docFactory=stan(p(render=directive('outerMethod'))))
        return self._render(f).addCallback(
            self.assertEquals, "<p>Hello, world.</p>")
