
"""
Tests for L{nevow.page.Page}
"""

from twisted.trial.unittest import TestCase

from nevow import appserver

from nevow.testutil import FakeRequest
from nevow.context import RequestContext
from nevow.loaders import stan
from nevow.tags import directive, p, div, invisible
from nevow.page import renderer, child, Page, Element
from nevow.util import maybeDeferred, Deferred


class PageTestCase(TestCase):
    """
    Tests for the new page.Page class
    """

    def getResourceFor(self, root, url):
        ctx = RequestContext(tag=FakeRequest(uri=url))
        return maybeDeferred(
            appserver.NevowSite(root).getPageContextForRequestContext, ctx)

    def _render(self, page):
        """
        Test helper which tries to render the given page.
        """
        defres = FakeRequest()
        defres.d = Deferred()
        d = maybeDeferred(page.renderHTTP, defres)

        def done(result):
            if isinstance(result, str):
                defres.write(result)
            defres.d.callback(defres.v)
            return result
        d.addCallback(done)
        return defres.d

    def test_simpleRendering(self):
        """
        Testing that the simple rendering without dynamic elements results in
        the expected result.
        """
        class NewPage(Page):
            pass
        pag = NewPage(docFactory=stan(p["Hello, world."]))
        return self._render(pag).addCallback(
            self.assertEquals, "<p>Hello, world.</p>")

    def test_simpleRenderString(self):
        """
        Testing that the simple rendering using L{nevow.page.Page.renderString}
        method actually works.
        """
        class NewPage(Page):
            pass
        pag = NewPage(docFactory=stan(p["Hello, world."]))
        return pag.renderString().addCallback(
            self.assertEquals, "<p>Hello, world.</p>")

    def test_lookup(self):
        """
        Testing that the child decorator works as expected and that the result
        output is what was expected.
        """
        class Root(Page):
            def cool(self, request):
                return Cool(docFactory=stan(p["Hello, from Cool."]))
            child(cool)
        class Cool(Page):
            pass
        r = Root()
        def _cb(result):
            self.assert_(isinstance(result.tag, Cool))
            d = self._render(result.tag)
            d.addCallback(self.assertEquals, "<p>Hello, from Cool.</p>")
            return d
        return self.getResourceFor(r, '/cool').addCallback(_cb)

    def test_childFactory(self):
        """
        Testing that childFactory method returns the expected object with the
        right segment passed to the method.
        """
        class Root(Page):
            def childFactory(self, request, segment):
                return Cool(docFactory=stan(p["Hello, from %s." % segment]))
        class Cool(Page):
            pass
        r = Root()
        return self.getResourceFor(r, '/cool').addCallback(
                lambda result: self._render(result.tag)
            ).addCallback(
                self.assertEquals, "<p>Hello, from cool.</p>")

    def test_dynamicRendering(self):
        """
        Testing that dynamic rendering on Page objects works as expected.
        """
        class Root(Page):
            def item(self, request, tag):
                for item in ["Foo1", "Foo2"]:
                    tag[p[item]]
                return tag
            renderer(item)
        r = Root(docFactory=stan(invisible(render=directive("item"))))
        return self._render(r).addCallback(
            self.assertEquals, "<p>Foo1</p><p>Foo2</p>")

    def test_elementRendering(self):
        """
        Testing that an L{nevow.page.Element} included in a L{nevow.page.Page}
        is rendered properly.
        """
        class Content(Element):
            docFactory = stan(
                p(render=directive("inside"))
            )
            def inside(self, request, tag):
                return tag["Hello, from Content."]
            renderer(inside)
        class Main(Page):
            docFactory = stan(
                div(render=directive("content"))
            )
            def content(self, request, tag):
                return tag[Content()]
            renderer(content)
        r = Main()
        return self._render(r).addCallback(
            self.assertEquals, "<div><p>Hello, from Content.</p></div>")

    def test_macroRendering(self):
        """
        Testing that a macro actually works as expected in the new Page object.
        """
        import itertools
        class MasterPage(Page):
            docFactory = stan(
                div(macro=directive("content"))
            )
            counter = itertools.count()
            incounter = itertools.count()
            def content(self, tag):
                return tag[stan(div[p[self.counter.next()], p(render=directive("innerCounter"))]).load()]
            macro(content)
            def innerCounter(self, request, tag):
                return tag[self.incounter.next()]
            renderer(innerCounter)
        r = MasterPage()
        return self._render(r).addCallback(
            self.assertEquals, "<div><div><p>0</p><p>0</p></div></div>"
            ).addCallback(
            lambda _: self._render(r)
            ).addCallback(
            self.assertEquals, "<div><div><p>0</p><p>1</p></div></div>"
            )
    test_macroRendering.skip = "implement macros later"

    def test_buffered(self):
        """
        Testing that rendering works when buffering is active.
        """
        class Root(Page):
            buffered = True

        r = Root(docFactory=stan(p["test"]))
        return self._render(r).addCallback(
            self.assertEquals, '<p>test</p>')

