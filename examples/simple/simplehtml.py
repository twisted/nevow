from twisted.python import util

from nevow import inevow
from nevow import loaders
from nevow import rend
from nevow import tags

class Simple(rend.Page):    

    addSlash = True
    docFactory = loaders.xmlfile(util.sibpath(__file__, 'simplehtml.html'))

    def render_theTitle(self, context, data):
        return context.tag["Welcome to Nevow world"]
    
    def render_sample(self, context, data):
        request = inevow.IRequest(context)
        session = inevow.ISession(context)
        count = getattr(session, 'count', 1)
        session.count = count + 1
        greeting = ["Welcome, person from ", request.client.host, "! You are using ", 
                        request.getHeader('user-agent'), " and have been here ", 
                        tags.span(id="count")[count], " times."]
        return context.tag[greeting]

    def child_reset(self, context):
        inevow.ISession(context).count = 1
        return '<html><body><span id="reset">Count reset</span></body></html>'
