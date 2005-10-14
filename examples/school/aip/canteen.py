from nevow import static

from aip import base

class Canteen(base.Generic):
    template = 'canteen.html'

    child_provider = lambda self, ctx: Provider()
    child_menu = lambda self, ctx: Menu()
    child_canteen_pics = lambda self, ctx: CanteenPics()

class Provider(base.Generic):
    template = 'canteen_provider.html'

class Menu(base.Generic):
    template = 'canteen_menu.html'

class CanteenPics(base.Generic):
    template = 'canteen_pics.html'

    child_pics = static.File('documents/canteen_pics/')
