############################################################################
# Example of registering rendering adapters for object types so that
# the page doesn't have to know anything about about the objects, only
# that it wants to render some particular view of the object.
############################################################################


import random
from zope.interface import implements, Interface
from twisted.python.components import registerAdapter, Adapter

from nevow import inevow
from nevow import loaders
from nevow import rend
from nevow import tags as T


############################################################################
# Define some simple classes for out application data.

class Person:
    def __init__(self, firstName, lastName, email):
        self.firstName = firstName
        self.lastName = lastName
        self.email = email

class Bookmark:
    def __init__(self, name, url):
        self.name = name
        self.url = url


############################################################################
# Create interfaces for the different views of application objects.
# These are nothing but marker interfaces to register a rendering adapt
# for simplicity sake you can consider them to be named views.

class ISummaryView(Interface):
    """Render a summary of an object.
    """

class IFullView(Interface):
    """Full view of the object.
    """


############################################################################
# Define the rendering adapters that do the real work of rendering an
# object.

class PersonSummaryView(Adapter):
    """Render a summary of a Person.
    """
    implements(inevow.IRenderer, ISummaryView)
    def rend(self, data):
        return T.div(_class="summaryView person")[
            T.a(href=['mailto:',self.original.email])[
                self.original.firstName, ' ', self.original.lastName
                ]
            ]

class PersonFullView(Adapter):
    """Render a full view of a Person.
    """
    implements(inevow.IRenderer, IFullView)
    def rend(self, data):
        attrs = ['firstName', 'lastName', 'email']
        return T.div(_class="fullView person")[
            T.p['Person'],
            T.dl[
                [(T.dt[attr], T.dd[getattr(self.original, attr)])
                for attr in attrs]
                ]
            ]
    
class BookmarkSummaryView(Adapter):
    """Render a summary of a Person.
    """
    implements(inevow.IRenderer, ISummaryView)
    def rend(self, data):
        return T.div(_class="summaryView bookmark")[
            T.a(href=self.original.url)[self.original.name]
            ]
    
class BookmarkFullView(Adapter):
    """Render a full view of a Bookmark.
    """
    implements(inevow.IRenderer, IFullView)
    def rend(self, data):
        attrs = ['name', 'url']
        return T.div(_class="fullView bookmark")[
            T.p['Bookmark'],
            T.dl[
                [(T.dt[attr], T.dd[getattr(self.original, attr)])
                for attr in attrs]
                ]
            ]
    

############################################################################
# Register the rendering adapters. Note, these could easily be defined in
# a text file and registered by name rather than class object.

registerAdapter(PersonSummaryView, Person, ISummaryView)
registerAdapter(PersonFullView, Person, IFullView)
registerAdapter(BookmarkSummaryView, Bookmark, ISummaryView)
registerAdapter(BookmarkFullView, Bookmark, IFullView)


############################################################################
# Create some data for the application to do something with.

objs = [
    Person('Matt', 'Goodall', 'matt@pollenation.net'),
    Bookmark('Nevow', 'http://www.nevow.com'),
    Person('Somebody', 'Else', 'somebody@else.net'),
    Bookmark('Twisted', 'http://twistedmatrix.com/'),
    Bookmark('Python', 'http://www.python.org'),
    ]


############################################################################
# Page that simply renders a summary of the objects and chooses one at
# random to display a full view of.

class Page(rend.Page):

    addSlash = True

    def render_one(self, ctx, data):
        return IFullView(random.choice(objs))

    docFactory = loaders.stan(
        T.html[
            T.body[
                T.ul(data=objs, render=rend.sequence)[
                T.li(pattern='item')[lambda c,d: ISummaryView(d)]
                    ],
                T.hr,
                render_one,
                ],
            ]
        )
