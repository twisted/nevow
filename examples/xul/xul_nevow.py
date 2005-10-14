from twisted.python import util
from nevow import rend, loaders, inevow, livepage


getValue = livepage.js('getValue')
changeLabel = livepage.js('changeLabel')


def onCommand(client, text):
    client.sendScript(changeLabel(text))


class XulApp(livepage.LivePage):
    addSlash = True
    docFactory = loaders.xmlfile(util.sibpath(__file__, 'xul_example.xul'))

    def locateChild(self, ctx, segments):
        inevow.IRequest(ctx).setHeader("Content-Type", "application/vnd.mozilla.xul+xml; charset=UTF-8")
        return rend.Page.locateChild(self, ctx, segments)

    def render_btn(self, ctx, data):
        return ctx.tag(oncommand=livepage.server.handle('onCommand', getValue('some-text')))

    def handle_onCommand(self, ctx, text):
        return changeLabel(text)


def createResource():
    return XulApp()

