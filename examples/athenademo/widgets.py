
import time

from twisted.internet import task
from twisted.python import log, filepath

from nevow import athena, loaders, static

class Clock(athena.LiveFragment):
    docFactory = loaders.xmlstr("""\
<div xmlns:nevow="http://nevow.com/ns/nevow/0.1"
     xmlns:athena="xxx"
     nevow:render="athenaID"
     athena:class="WidgetDemo.Clock">
    <div>
        <a href="" onclick="WidgetDemo.Clock.get(this).start(); return false;">
            Start
        </a>
        <a href="" onclick="WidgetDemo.Clock.get(this).stop(); return false;">
            Stop
        </a>
    </div>
    <div class="clock-time" />
</div>
""")

    running = False

    allowedMethods = {'start': True, 'stop': True}
    def start(self):
        if self.running:
            return
        self.loop = task.LoopingCall(self.updateTime)
        self.loop.start(1)
        self.running = True

    def stop(self):
        if not self.running:
            return
        self.loop.stop()
        self.running = False

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
        <script type="text/javascript" src="widgets.js" />
    </head>
    <body>
        <div nevow:render="clock">
            First Clock
        </div>
        <div nevow:render="clock">
            Second Clock
        </div>
        <div id="nevow-log" />
    </body>
</html>
""")

    addSlash = True

    def childFactory(self, ctx, name):
        ch = super(WidgetPage, self).childFactory(ctx, name)
        if ch is None:
            ch = static.File(filepath.FilePath(__file__).parent().child(name).path)
        return ch

    def render_clock(self, ctx, data):
        c = Clock()
        c.page = self
        return ctx.tag[c]
