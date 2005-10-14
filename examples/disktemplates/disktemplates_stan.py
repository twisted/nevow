import random

from twisted.application import service
from twisted.application import internet

from nevow import inevow
from nevow import appserver
from nevow import loaders
from nevow import rend
from nevow import tags as T
from nevow.stan import directive


class Mine(rend.Page):

    addSlash = True
    docFactory = loaders.stan(
        T.html[
            T.head[
                T.title["This is title"]
            ],
            T.body[
                T.h1(id="header")["Welcome"],
                T.ol(data=directive("theList"), render=directive("sequence"))[
                    T.span(pattern="header")["HEADER"],
                    T.li(pattern="item")["Stuff: ",T.span(render=directive("string")), "!"],
                    T.span(pattern="divider")["-----"],
                    T.div(pattern="empty")["Nothing."],
                    T.span(pattern="footer")["FOOTER"],
                ],
                T.ol(data=directive("empty"), render=directive("sequence"))[
                    T.span(pattern="header")["HEADER"],
                    T.li(pattern="item")["Stuff: ",T.span(render=directive("string")), "!"],
                    T.span(pattern="divider")["-----"],
                    T.div(pattern="empty")["Nothing."],
                    T.span(pattern="footer")["FOOTER"],
                ],
                T.span(render=directive("foo"))[
                    "This entire node, including the span tag, will be replaced by \
                    a randomly chosen node from below:",
                    T.div(pattern="one", style="color: red")["one"],
                    
                    T.table(pattern="two")[
                        T.tr[T.td["two"],T.td["two"],T.td["two"]]
                    ],
                    
                    T.ol(pattern="three")[
                        T.li["three"],
                        T.li["three"],
                        T.li["three"],
                    ]
                ]
            ]
        ]
    )
        

    def render_foo(self, context, data):
        return inevow.IQ(context).onePattern(random.choice(['one', 'two', 'three']))

    def data_theList(self, context, data):
        return [random.randint(0, 5000) for x in range(random.randint(0, 10))]

    def data_empty(self, context, data):
        return []


application = service.Application("disktemplates")
internet.TCPServer(
    8080, 
    appserver.NevowSite(
        Mine()
    )
).setServiceParent(application)
