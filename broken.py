
from nevow import athena, loaders

class XMLHTTP(athena.LivePage):
    docFactory = loaders.xmlstr("""
<html xmlns:nevow="http://nevow.com/ns/nevow/0.1">
    <head>
        <nevow:invisible nevow:render="liveglue" />
        <script type="text/javascript" src="app" />
    </head>
    <body onload="doit();">
    </body>
</html>
""")

    factory = athena.LivePageFactory(None)

    def remote_ping(self, ctx):
        from twisted.internet import defer, reactor
        d = defer.Deferred()
        reactor.callLater(10, d.callback, 'boo')
        reactor.callLater(2, reactor.stop)
        return d

    def child_mochikit(self, ctx):
        return file('/home/exarkun/Projects/Nevow/branches/exarkun/callRemote-2/nevow/MochiKit.js').read()

    def child_app(self, ctx):
        return ("""
function doit() {
    server.callRemote('ping').addCallbacks(
        function(ign) {
            alert('This code is broken.');
            document.write('This code is broken');
        },
        function(err) {
            alert('This code works!  ' + new String(err));
            document.write('This code works.');
        });
}
""")

from twisted.internet import reactor
from nevow import appserver

import sys
from twisted.python import log
log.startLogging(sys.stdout)

reactor.listenTCP(9000, appserver.NevowSite(XMLHTTP()))
reactor.run()
