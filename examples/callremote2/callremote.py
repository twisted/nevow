
import sys, random

from twisted.internet import reactor, defer
from twisted.python import log

from nevow import athena, appserver, loaders, tags as T

class NewLPTest(athena.LivePage):
    addSlash = True

    docFactory = loaders.stan(T.html[
            T.head[
                T.directive('liveglue'),
                T.script(type='text/javascript')[
                    "function sayHello() { alert('The server says hello.'); return 'hello'; }",
                    "function updateStatus(n) { document.getElementById('status').innerHTML = new String(n); }"]],
            T.body(onload="server.callRemote('live')")[
                T.form(onsubmit=
                       "var a = this.firstChild.value;"
                       "var b = this.firstChild.nextSibling.value;"
                       "d = server.callRemote('huzzah', a, b);"
                       "d.addBoth(function(result) { document.getElementById('output').innerHTML = result; });"
                       "return false;")[
                    T.input(type='text'),
                    T.input(type='text'),
                    T.input(type='submit')],
                T.div["Update in ", T.span(id="status"), " seconds."],
                T.div(id="output"),
                T.div(id="notify"),
                T.button(onclick='LogConsole.show()')['*']]])

    def remote_huzzah(self, ctx, x, y):
        def update(n, d):
            if n == 0:
                d.callback(x + y)
            else:
                self.callRemote('updateStatus', n - 1).addBoth(lambda result: log.msg('Status updated: ' + str(result)))
                reactor.callLater(1, update, n - 1, d)
        d = defer.Deferred()
        n = random.randrange(5, 15)
        update(n, d)
        return d

    def goingLive(self, ctx):
        print "*****LIVE****"
        def _ok(hello):
            print "** OK:", repr(hello)
        def _ko(err):
            print "** KO:"
            log.err(err)
        self.callRemote('sayHello').addCallbacks(_ok, _ko)
