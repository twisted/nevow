from nevow import loaders
from aip import iaip, base

class Index(base.Generic):
    addSlash = True
    template = 'index.html'

    child_founder = lambda self, ctx: IndexFounder()
    child_dedicated = lambda self, ctx: IndexDedicated()

class IndexFounder(base.Generic):
    template = 'index_founder.html'

class IndexDedicated(base.Generic):
    template = 'index_dedicated_to.html'
