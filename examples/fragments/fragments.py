from twisted.python import util
from nevow import inevow, rend, tags as t, loaders

class Root(rend.Page):
    addSlash = True
    docFactory = loaders.xmlfile(util.sibpath(__file__, 'main.html'))

    def data_ip(self, ctx, data):
        return inevow.IRequest(ctx).client.host

    def render_header(self, ctx, data):
        return ctx.tag[Header(data)]

    def render_sidebar(self, ctx, data):
        # This is only a different way of using a Fragment
        # you can either fill a slot or return it from a
        # render_* method
        ctx.tag.fillSlots('main_sidebar', SideBar())
        return ctx.tag

    def render_content(self, ctx, data):
        return ctx.tag[Content()]

class Header(rend.Fragment):
    docFactory = loaders.stan(
        t.invisible[
            t.p(render=t.directive("ip"))["Welcome IP: "]
        ]
    )

    def render_ip(self, ctx, data):
        return ctx.tag[data]
            
class SideBar(rend.Fragment):
    docFactory = loaders.stan(
        t.ul[
            t.li["Menuitem 1"],
            t.li["Menuitem 2"],
            t.li["Menuitem 3"],
        ]
    )

class Content(rend.Fragment):
    docFactory = loaders.stan(
        t.p["""Hi, this page is composed thanks to Fragments.
A Fragment allows the programmer to dispatch the composition of the
page to many different objects that represent a logical entity inside
the page. The Fragment can be used just like any other piece of stan
plus it understands render_* and data_* methods.

For additional questions come in #twisted.web"""]
    )
