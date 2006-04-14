from twisted.python.components import registerAdapter
from nevow import rend, loaders, tags as t, inevow, accessors

class Edge(object):
    pass

class Vertex(object):
    def __init__(self, name):
        self.name = name
        self.edges = []

v1 = Vertex('v1')
v2 = Vertex('v2')
v3 = Vertex('v3')
v1.edges = [Edge(), Edge(), Edge(), Edge()]
v2.edges = [Edge(), Edge(), Edge(), Edge()]
v3.edges = [Edge(), Edge(), Edge(), Edge()]

class Root(rend.Page):
    addSlash = True
    docFactory = loaders.stan(
        t.html[
            t.head[t.title["Nested Sequence"]],
            t.body[
                t.ul(data=t.directive("vertexes"), render=t.directive("sequence"))[
                    t.li(pattern="item")[
                        t.span(data=t.directive("name"), render=t.directive("string")),
                        t.ul(data=t.directive('edges'), render=t.directive("sequence"))[
                            t.li(pattern="item", render=t.directive("string"))
                            ]
                        ]
                    ]
                ]
            ]
        )
    
    def data_vertexes(self, ctx, data):
        return [v1, v2, v3]

registerAdapter(accessors.ObjectContainer, Vertex, inevow.IContainer)
