from twisted.python import util
from nevow import rend, tags as t, loaders

import itertools
counter1 = itertools.count()
counter2 = itertools.count()

inside_counter = itertools.count()

class Base(rend.Page):
    docFactory = loaders.xmlfile(util.sibpath(__file__, 'main.html'), ignoreDocType=True)
    def render_advice(self, ctx, data):
        return ctx.tag[
            t.p["This counter has been called:"],
            t.p(style="text-align: center")["===>",t.strong[inside_counter.next()+1],"<==="]
        ]

class Root(Base):
    addSlash = True
    
    def macro_content(self, ctx):
        return t.invisible[
                   t.p["This macro has been called ",
                       counter1.next()+1,
                       " time(s)"],
                   loaders.xmlfile(util.sibpath(__file__,'root_macro.html'), ignoreDocType=True).load()
               ]

    def childFactory(self, ctx, segment):
        if segment == 'child':
            return Child()

class Child(Base):
    addSlash=True
    def macro_content(self, ctx):
        return t.invisible[
                   t.p["This macro has been called ",
                       counter2.next()+1,
                       " time(s)"],
                   loaders.xmlfile(util.sibpath(__file__,'child_macro.html'), ignoreDocType=True).load()
            ]
