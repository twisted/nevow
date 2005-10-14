from nevow import rend
import itodo
import controller

# All this is only useful to dynamically update the web page code
# without restarting the server each time. As you can see below, you can 
# disable this by putting a false value in the Env object.

class Dispatch(rend.Page):
    def locateChild(self, ctx, segments):
        if itodo.IEnv(ctx).development:
            reload(controller)
        return controller.root.locateChild(ctx,segments)
