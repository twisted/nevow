from zope.interface import implements

from nevow import inevow

##
## How does a request come to the Page?
##
## or How to use Nevow without all the fancy automations
##

# This is a simple Root page object, the inevow.IResource interface
# tells us that it must implement 2 methods:
# locateChild and renderHTTP.
# locateChild is used to find children of the current page, it must return a 
# tuple of (page, remaining_segments)
# if there is no page, and you want to display a 404 page, you will need to return
# a None, () tuple.
class Root(object):
    implements(inevow.IResource)

    def locateChild(self, ctx, segments):
        # This locateChild is 'stupid' since it can only work if the tree of
        # pages is static. Anyway it will work for our simple example
        if segments[0] == '':
            # If the server is looking for the root page segments will be ('',)
            # then renderHTTP will be called on self
            return self, ()
        elif segments[0] == 'foo':
            # Now we received a request whose segments had in the first position
            # the string foo
            # like http://example.org/foo/baz/ -> ('foo', 'baz')
            # after the page has been located we return it with the remaining segments
            # ('baz')
            return self.foo, segments[1:]
        else:
            return None, ()
        
    def renderHTTP(self, ctx):
        # When the server needs to return a response to the request it will call
        # the renderHTTP method that will return a string of what needs to be sent.
        return """<html><body>Hello world!<br />
        <a href="./foo" id="foo">foo</a></body></html>
"""

class Foo(object):
    implements(inevow.IResource)
    
    def locateChild(self, ctx, segments):
        # segments is the remaining segments returned by the root locateChild
        # see segments[1:]
        if segments[0] == 'baz':
            return self.baz, segments[1:]
        else:
            return None, ()
    
    def renderHTTP(self, ctx):
        return """<html><body><h1 id="heading">You are in Foo</h1>
        <a href="./foo/baz" id="baz">baz</a></body></html>
"""

class Baz(object):
    implements(inevow.IResource)
    def locateChild(self, ctx, segments):
        return None, ()
    def renderHTTP(self, ctx):
        return '<html><body><h1 id="heading">You are in Baz</h1></body></html>'

# We are adding children to the pages.
# This could also happen inside the class.
root = Root()
root.foo = Foo()
root.foo.baz = Baz()
