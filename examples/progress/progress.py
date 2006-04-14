from twisted.internet import task
from nevow import loaders, livepage, tags as t
from nevow.taglibrary.livetags import component, componentGlue
from nevow.taglibrary.progressbar import progressBar, progressBarGlue


class Progressbar(livepage.LivePage):
    addSlash = True

    progress = {
        'bar1': 0,
        'bar2': 20,
        'bar3': 30,
        'bar4': 50,
        }
    
    def data_bar1(self, ctx, data):
        return { 'name': 'bar1' }
    def data_bar2(self, ctx, data):
        return { 'name': 'bar2', 'percent': self.progress['bar2'] }
    def data_bar3(self, ctx, data):
        return { 'name': 'bar3', 'percent': self.progress['bar3'] }
    def data_bar4(self, ctx, data):
        return { 'name': 'bar4', 'percent': self.progress['bar4'] }

    def goingLive(self, ctx, client):
        self.progress = self.progress.copy()

    def handle_click(self, ctx, value):
        def send():
            if self.progress[value] >= 100:
                t.stop()
            else:
                self.progress[value] += 1
                livepage.IClientHandle(ctx).send(component[value].setPercent(str(self.progress[value])))
        t = task.LoopingCall(send)
        t.start(1)

    docFactory = loaders.stan(
        t.html[
            t.head[
                t.title["ProgressBar Example"],
                livepage.glue,
                componentGlue.inlineGlue,
                progressBarGlue.inlineGlue,
            ],
            t.body[
                t.invisible(data=t.directive('bar1'), render=progressBar),
                t.p[ t.a(href="", onclick=[livepage.server.handle('click', 'bar1'), livepage.stop])['Start meter'] ],
                t.invisible(data=t.directive('bar2'), render=progressBar),
                t.p[ t.a(href="", onclick=[livepage.server.handle('click', 'bar2'), livepage.stop])['Start meter'] ],
                t.invisible(data=t.directive('bar3'), render=progressBar),
                t.p[ t.a(href="", onclick=[livepage.server.handle('click', 'bar3'), livepage.stop])['Start meter'] ],
                t.invisible(data=t.directive('bar4'), render=progressBar),
                t.p[ t.a(href="", onclick=[livepage.server.handle('click', 'bar4'), livepage.stop])['Start meter'] ],
            ]
        ]
    )
 
def createResource():
    return Progressbar()
