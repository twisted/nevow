from nevow import static

from aip import base

class Logistics(base.Generic):
    template = 'logistics.html'

    child_map = lambda self, ctx: Map()

class Map(base.Generic):
    template = 'logistics_map.html'

    child_logistics_pics = static.File('documents/logistics_pics/')
