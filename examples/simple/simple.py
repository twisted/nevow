from nevow import inevow
from nevow import loaders
from nevow import rend, page

from nevow import tags as T


class Simple(page.Page):
    
    addSlash = True

    def theTitle(self, context, data):
        return [x * 5 for x in "title"]
    page.renderer(theTitle)

    def sample(self, request, data):
        session = request.getSession()
        count = getattr(session, 'count', 1)
        session.count = count + 1
        return ["Welcome, person from ", request.client.host, "! You are using ",
            request.getHeader('user-agent'), " and have been here ", 
            T.span(id="count")[count], " times."]
    page.renderer(sample)

    def reset(self, request):
        request.getSession().count = 1
        return '<html><body><span id="reset">Count reset</span></body></html>'
    page.child(reset)

    docFactory = loaders.stan(
        T.html[
            T.head[
                T.title[theTitle]
            ],
            T.body[
                T.h1["Hello."],
                sample,
            ]
        ])
