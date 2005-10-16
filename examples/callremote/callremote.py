
import random

from twisted.internet import reactor, defer

from nevow import athena, loaders, util

class CallRemote(athena.LivePage):
    docFactory = loaders.xmlfile(util.resource_filename('callremote', 'callremote.html'))
    addSlash = True

    def remote_live(self, ctx):
        print 'A client lives!'
        self.notifyOnDisconnect().addCallbacks(self.connectionClosed, self.connectionLost)

    def connectionClosed(self, ignored):
        print 'A client peacefully retires.'

    def connectionLost(self, reason):
        print 'A client dies!', reason

    def remote_slowEcho(self, ctx, text):
        d = defer.Deferred()
        reactor.callLater(random.randrange(2, 5), d.callback, text)
        return d
