from nevow import url
from aip import base

class Login(base.Generic):
    template = 'login.html'

    def render_action(self, ctx, data):
        here = url.URL.fromContext(ctx).clear()
        return ctx.tag(action='/__login__/'+here.path)

    def childFactory(self, ctx, segment):
        return Login()
