
from twisted.internet import reactor
from twisted.internet.defer import succeed

from nevow.appserver import NevowSite

from nevow.rend import Page, Fragment
from nevow.page import Element, renderer
from nevow.loaders import stan
from nevow.tags import directive, div, span


class Static:
    docFactory = stan("Hello, world.  " * 100)



class StaticFragment(Static, Fragment):
    pass



class StaticElement(Static, Element):
    pass



class Tiny:
    docFactory = stan(div(render=directive("foo")))



class TinyFragment(Tiny, Fragment):
    def render_foo(self, ctx, data):
        return ctx.tag[span["result"]]



class TinyElement(Tiny, Element):
    def foo(self, request, tag):
        return tag[span["result"]]
    renderer(foo)



class Huge:
    docFactory = stan(div[[
        div(render=directive("foo"))
        for x in range(100)]])



class HugeFragment(Huge, Fragment):
    def render_foo(self, ctx, data):
        return ctx.tag[span["Hello, ", "world", "!"]]



class HugeElement(Huge, Element):
    def foo(self, request, tag):
        return tag[span["Hello, ", "world", "!"]]
    renderer(foo)



class Nested:
    docFactory = stan(div(render=directive("foo")))

    def __init__(self, count=6):
        self.count = count



class NestedFragment(Nested, Fragment):
    def render_foo(self, ctx, data):
        if self.count:
            return span[NestedFragment(self.count - 1)]
        return ctx.tag["Hello"]



class NestedElement(Nested, Element):
    def foo(self, request, tag):
        if self.count:
            return span[NestedFragment(self.count - 1)]
        return tag["Hello"]
    renderer(foo)



class Deferred:
    docFactory = stan(div(render=directive('foo')))



class DeferredFragment(Deferred, Fragment):
    def render_foo(self, ctx, data):
        return ctx.tag[succeed("foo")]



class DeferredElement(Deferred, Element):
    def foo(self, request, tag):
        return tag[succeed("foo")]
    renderer(foo)



class Compare(Page):
    def __init__(self, fragment, element):
        self.fragment = fragment
        self.element = element

    def child_fragment(self, ctx):
        return Page(docFactory=stan(self.fragment))


    def child_element(self, ctx):
        return Page(docFactory=stan(self.element))



class Root(Page):
    def child_static(self, ctx):
        return Compare(StaticFragment(), StaticElement())


    def child_tiny(self, ctx):
        return Compare(TinyFragment(), TinyElement())


    def child_huge(self, ctx):
        return Compare(HugeFragment(), HugeElement())


    def child_nested(self, ctx):
        return Compare(NestedFragment(), NestedElement())


    def child_deferred(self, ctx):
        return Compare(DeferredFragment(), DeferredElement())



if __name__ == '__main__':
    reactor.listenTCP(8080, NevowSite(Root()))
    reactor.run()
