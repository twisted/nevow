"""
Simple example of how child resources are located.
"""

from nevow import loaders
from nevow import rend
from nevow import tags as T
from nevow import url


class ChildPage(rend.Page):

    def __init__(self, name):
        rend.Page.__init__(self)
        self.name = name

    def child_childOfChild(self, context):
        return ChildOfChildPage(self.name)

    def render_name(self, context, data):
        return self.name

    docFactory = loaders.stan(
        T.html[
            T.body[
                T.h1['ChildPage'],
                T.p['My name is: ', T.span(id="name")[render_name]],
                T.p[
                    'I have child too: ',
                    T.a(id="child", href=url.here.child('childOfChild'))['my child']
                    ],
                ]
            ]
        )


class ChildOfChildPage(rend.Page):

    def __init__(self, parentName):
        rend.Page.__init__(self)
        self.parentName = parentName

    def render_parentName(self, context, data):
        return self.parentName

    docFactory = loaders.stan(
        T.html[
            T.body[
                T.h1['ChildOfChildPage'],
                T.p['My parent is the ChildPage called: ', T.span(id="parentName")[render_parentName]]
                ]
            ]
        )


class RootPage(rend.Page):

    addSlash = True

    # A resource that is always called 'foo' and only needs to be created once
    child_foo = ChildPage('foo')

    def child_bar(self, context):
        """A resource that is always called 'bar' but is created per-request
        """
        return ChildPage('bar')

    def childFactory(self, ctx, name):
        """Create and return a child resource where the name is dynamic
        """
        if name in ['1', '2', '3']:
            return ChildPage(name)

    def locateChild(self, ctx, segments):
        """Create and return a dynamically named child resource if child_ or
        childFactory didn't help. However, this time we get the chance to
        consume multiple path segments (inluding the childOfChild link).
        
        Note: locateChild is actually the main resource location API (see
        inevow.IReource) and it is actually rend.Page's implementation of the
        method that provides the child_ and childFactory functionality.
        """

        # Let parent class have a go first
        # WARNING: This 3 lines work well until you use formless in this page
        # because formless will make locateChild return only one return value
        # (a deferred) on which you should add a callback that accepts a resource and 
        # an empty tuple that represents no remaining segments.
        child, remainingSegments = rend.Page.locateChild(self, ctx, segments)
        if child:
            return child, remainingSegments

        # Consume all remaining path segments for the name
        return ChildPage('/'.join(segments)), []
    
    docFactory = loaders.stan(
        T.html[
            T.body[
                T.h1['RootPage'],
                T.p['Fixed name, singleton resource: ', T.a(id="foo", href=url.here.child('foo'))['foo']],
                T.p['Fixed name, created per-request: ', T.a(id="bar", href=url.here.child('bar'))['bar']],
                T.p[
                    'Dynamically named resources, located via childFactory: ',
                    [(T.a(id=("d", n), href=url.here.child(n))[n],' ') for n in ['1', '2', '3']]
                    ],
                T.p[
                    'Dynamically named resources, located via locateChild: ',
                    [(T.a(id=("d", n), href=url.here.child(n))[n],' ') for n in ['4', '5', '6/7']]
                    ],
                ]
            ]
        )

