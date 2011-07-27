
import time, os

from twisted.internet import task
from twisted.python import log, util

from nevow import athena, loaders, static

class Clock(athena.LiveFragment):
    jsClass = u"WidgetDemo.Clock"

    docFactory = loaders.xmlstr('''\
<div xmlns:nevow="http://nevow.com/ns/nevow/0.1"
     xmlns:athena="http://divmod.org/ns/athena/0.7"
     nevow:render="liveFragment">
    <div>
        <a href="#"><athena:handler event="onclick" handler="start" />
            Start
        </a>
        <a href="#"><athena:handler event="onclick" handler="stop" />
            Stop
        </a>
    </div>
    <div class="clock-time" />
</div>
''')

    running = False

    def start(self):
        if self.running:
            return
        self.loop = task.LoopingCall(self.updateTime)
        self.loop.start(1)
        self.running = True
    athena.expose(start)

    def stop(self):
        if not self.running:
            return
        self.loop.stop()
        self.running = False
    athena.expose(stop)

    def _oops(self, err):
        log.err(err)
        if self.running:
            self.loop.stop()
            self.running = False

    def updateTime(self):
        self.callRemote('setTime', unicode(time.ctime(), 'ascii')).addErrback(self._oops)

class WidgetPage(athena.LivePage):
    docFactory = loaders.xmlstr("""\
<html xmlns:nevow="http://nevow.com/ns/nevow/0.1">
    <head>
        <nevow:invisible nevow:render="liveglue" />
    </head>
    <body>
        <div nevow:render="clock">
            First Clock
        </div>
        <div nevow:render="clock">
            Second Clock
        </div>
        <div nevow:render="debug" />
    </body>
</html>
""")

    addSlash = True

    def __init__(self, *a, **kw):
        super(WidgetPage, self).__init__(*a, **kw)
        self.jsModules.mapping[u'WidgetDemo'] = util.sibpath(__file__, 'widgets.js')

    def childFactory(self, ctx, name):
        ch = super(WidgetPage, self).childFactory(ctx, name)
        if ch is None:
            p = util.sibpath(__file__, name)
            if os.path.exists(p):
                ch = static.File(file(p))
        return ch

    def render_clock(self, ctx, data):
        c = Clock()
        c.page = self
        return ctx.tag[c]

    def render_debug(self, ctx, data):
        f = athena.IntrospectionFragment()
        f.setFragmentParent(self)
        return ctx.tag[f]
