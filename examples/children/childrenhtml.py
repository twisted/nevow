"""
Simple example of how child resources are located.
"""

from twisted.application import internet
from twisted.application import service

from twisted.python import util

from nevow import appserver
from nevow import loaders
from nevow import rend
from nevow import url


class ChildPage(rend.Page):

    docFactory = loaders.xmlfile(util.sibpath(__file__, "childrenhtml_ChildPage.html"))

    def __init__(self, name):
        rend.Page.__init__(self)
        self.name = name

    def child_childOfChild(self, context):
        print "istanzaaa"
        return ChildOfChildPage(self.name)

    def render_name(self, context, data):
        return context.tag[self.name]
    
    def render_link(self, context, data):
        context.fillSlots('childLink', url.here.child('childOfChild'))
        return context.tag


class ChildOfChildPage(rend.Page):

    docFactory = loaders.xmlfile(util.sibpath(__file__, "childrenhtml_ChildOfChildPage.html"))

    def __init__(self, parentName):
        rend.Page.__init__(self)
        self.parentName = parentName

    def render_parentName(self, context, data):
        return context.tag[self.parentName]


class RootPage(rend.Page):

    addSlash = True

    docFactory = loaders.xmlfile(util.sibpath(__file__, "childrenhtml_RootPage.html"))

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
        child, remainingSegments = rend.Page.locateChild(self, ctx, segments)
        if child:
            return child, remainingSegments

        # Consume all remaining path segments for the name
        return ChildPage('/'.join(segments)), []


application = service.Application('children')
internet.TCPServer(8080, appserver.NevowSite(RootPage())).setServiceParent(application)
