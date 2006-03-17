from zope.interface import implements

from nevow import rend, loaders, tags as t
from formless import annotate, webform
from time import time as now
import itodo

class ITodo(annotate.TypedInterface):
    def insert(ctx=annotate.Context(),
               description=annotate.String(required=True,
                                           requiredFailMessage="Description Missing")
               ):
        pass
    insert = annotate.autocallable(insert, action="New Todo")
    def delete(ctx=annotate.Context(), id=annotate.Integer()):
        pass
    delete = annotate.autocallable(delete, invisible=True)
    def update(ctx=annotate.Context(), 
               id=annotate.Integer(), 
               oldstate=annotate.Integer()):
        pass
    update = annotate.autocallable(update, invisible=True)

class Root(rend.Page):
    implements(ITodo)
    
    child_css = webform.defaultCSS
    
    docFactory = loaders.stan(
        t.html(render=t.directive("time"))[
            t.head[
                t.title['todo'],
                t.style(type="text/css")[".done { color: #dddddd; }"],
                t.style(type="text/css")["@import url(/css);"]
                ],
            t.body[
                webform.renderForms(),
                t.ul(data=t.directive("findAll"),
                     render=t.directive("sequence"))[
                         t.li(pattern="item",render=t.directive('todo')),
                         t.li(pattern="empty",render=t.directive('empty')),
                ],
                t.p(render=t.directive("end"))
            ]
        ]
    )
    
    def insert(self, ctx, description):
        return itodo.ITodos(ctx).add(description, 0)
    
    def delete(self, ctx, id):
        return itodo.ITodos(ctx).delete(id)

    def update(self, ctx, id, oldstate):
        newstate = [1, 0][oldstate]
        return itodo.ITodos(ctx).update(id, newstate)
        
    def data_findAll(self, ctx, data):
        return itodo.ITodos(ctx).findAll()

    def render_todo(self, ctx, data):
        deluri = "freeform_post!!delete?id="+str(data[0])
        updateuri = "freeform_post!!update?id="+str(data[0])+"&oldstate="+str(data[2])
        state = [" Done", " To Do"][int(data[2])==0]
        tag = ctx.tag
        if data[2]:
            tag = ctx.tag(_class="done")
        return tag[data[1]+" - ",
                   t.a(href=deluri)["Delete"], " / ",
                   t.a(href=updateuri)[("Mark Done", "Mark Undone")[data[2]]],
                   state]

    def render_empty(self, ctx, data):
        return ctx.tag["No Todos"]
    
    def render_time(self, ctx, data):
        ctx.remember(now(), itodo.ITimer)
        return ctx.tag
        
    def render_end(self, ctx, data):
        return ctx.tag["%.3f"%(now()-itodo.ITimer(ctx))]

root = Root()
