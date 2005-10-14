from nevow import inevow
from nevow import loaders
from nevow import rend

from nevow import tags as T

class Simple(rend.Page):
    
    addSlash = True

    def render_theTitle(self, context, data):
        return [x * 5 for x in "title"]

    def render_sample(self, context, data):
        request = inevow.IRequest(context)
        session = inevow.ISession(context)
        count = getattr(session, 'count', 1)
        session.count = count + 1
        return ["Welcome, person from ", request.client.host, "! You are using ",
            request.getHeader('user-agent'), " and have been here ", 
            T.span(id="count")[count], " times."]

    def child_reset(self, context):
        inevow.ISession(context).count = 1
        return '<html><body><span id="reset">Count reset</span></body></html>'

    docFactory = loaders.stan(
        T.html[
            T.head[
                T.title[render_theTitle]
            ],
            T.body[
                T.h1["Hello."],
                render_sample,
            ]
        ])
