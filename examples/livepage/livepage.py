"""
A short LivePage server.  Text inputted into the input box on the page is
routed to the server, and the server echoes it back in an alert box.
"""

from twisted.internet import reactor

from nevow import livepage, tags, loaders, appserver

class LiveExamplePage(livepage.LivePage):
    docFactory = loaders.stan(
        tags.html[
            tags.head[
                livepage.glue],
            tags.body[
                tags.input(
                    type="text",
                    onchange="server.handle('change', this.value)")]])

    def handle_change(self, ctx, value):
        return livepage.alert(value)

site = appserver.NevowSite(LiveExamplePage())
reactor.listenTCP(8080, site)
reactor.run()
