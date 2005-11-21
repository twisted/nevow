
from nevow import rend, url, static, loaders, tags, athena, appserver
from twisted.application import service, internet

class CooperativeAthenaFragments(athena.LivePage):
    docFactory = loaders.stan(tags.html[
        tags.head[
            tags.invisible(render=tags.directive('liveglue')),
            tags.script(type="text/javascript", src="/app/js")],
        tags.body[
            tags.invisible(render=tags.directive('foo')),
            tags.invisible(render=tags.directive('bar'))]])

    def child_js(self, ctx):
        return static.Data("""
            function submitIt(node, name) {
                var d = Nevow.Athena.refByDOM(node).callRemote(name);
                d.addCallback(function(result) {
                    alert(result + ' is a success.');
                });
            }
        """, type="text/javascript")

    def render_foo(self, ctx, data):
        return CooperativeFrag("foo", self)

    def render_bar(self, ctx, data):
        return CooperativeFrag("bar", self)

class CooperativeFrag(athena.LiveFragment):
    docFactory = loaders.stan(tags.div[
        tags.div[
            "This is a Fragment of the First Kind"],
        tags.form(action="#", onsubmit=tags.directive('submit'))[
            tags.input(type="submit")]])

    def __init__(self, label, *a, **kw):
        super(CooperativeFrag, self).__init__(*a, **kw)
        self.allowedMethods = {label: True}
        setattr(self, label, lambda: unicode(label))

    def render_submit(self, ctx, data):
        return "submitIt(this, '%s'); return false;" % (self.allowedMethods.keys()[0],)

class Root(rend.Page):
    def child_(self, ctx):
        return url.URL.fromString('/app')

    def child_app(self, ctx):
        return CooperativeAthenaFragments()

application = service.Application("Cooperative Athena Fragments")
internet.TCPServer(8999, appserver.NevowSite(Root())).setServiceParent(application)
