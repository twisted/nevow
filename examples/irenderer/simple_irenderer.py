from zope.interface import implements

from twisted.python.components import registerAdapter, Adapter

from nevow import inevow
from nevow import loaders
from nevow import rend
from nevow import tags as T

##  Let's start from the beginning (apart from the various imports):

##  We are provided 2 different classes, Person and Bookmark which contain some information (maybe built from a RDBMS 
##  or directly from an OODB).

##  Then the hard stuff begins (I'm not going to explain extensively how adaptation works since there's not enough room, 
##  but I'm going to give you just a fast overview of how objects and adapter relate to each other):

##  We need 2 different adapters since Person and Bookmark are not directly renderable and need some extra 
##  transformations. What we do here with PersonView and BookmarkView is to define a class that inherits from
##  Adapter and define a rend method.

##  What is Adapter? Basically it is a class that accepts an argument in the constructor which is the object that 
##  needs to be adapted to some other interface. Obviously the adapter will implement the interface we need (ie: inevow.
##  IRenderer).

##  Why do we need to implement IRenderer? An object that implements IRenderer is an object upon which a rend() method
##  can be called safely. Since Nevow rendering pipeline uses rend() to serialize objects to html (remember that html tags 
##  are objects too in Nevow) we need to implement that interface, which is built-in. The adapters we wrote, directly 
##  implement IRenderer thus we can use them inside the rendering pipeline. Also each adapter holds a reference to the 
##  corresponding object in self.original.

##  Then 2 interesting lines:

##  registerAdapter(PersonView, Person, inevow.IRenderer)
##  registerAdapter(BookmarkView, Bookmark, inevow.IRenderer)

##  Basically we are registering in Nevow object space, that PersonView and BookmarkView are the adapters for classes/
##  objects Person and Bookmark to inevow.IRenderer. What does this mean? It means that when we will call inevow.
##  IRenderer() interface [later in the Page class] with an instance of Person or Bookmark as argument we will receive the 
##  right adapter as a result. Without these 2 lines, Nevow doesn't know anything about the way your objects are adapted 
##  or referenced by each other.

##  Then as usual we are creating a bunch of example objects in a list.

##  And, last, but not least, we wrote a Page class that uses stan to render the objects list.

############################################################################
# Define some simple classes for out application data.

class Person:
    def __init__(self, firstName, lastName, nickname):
        self.firstName = firstName
        self.lastName = lastName
        self.nickname = nickname

class Bookmark:
    def __init__(self, name, url):
        self.name = name
        self.url = url

class PersonView(Adapter):
    """Render a full view of a Person.
    """
    implements(inevow.IRenderer)
    def rend(self, data):
        attrs = ['firstName', 'lastName', 'nickname']
        return T.div(_class="View person")[
            T.p['Person'],
            T.dl[
                [(T.dt[attr], T.dd[getattr(self.original, attr)])
                    for attr in attrs]
                ]
            ]

class BookmarkView(Adapter):
    """Render a full view of a Bookmark.
    """
    implements(inevow.IRenderer)
    def rend(self, data):
        attrs = ['name', 'url']
        return T.div(_class="View bookmark")[
            T.p['Bookmark'],
            T.dl[
                [(T.dt[attr], T.dd[getattr(self.original, attr)])
                    for attr in attrs]
                ]
            ]
    

############################################################################
# Register the rendering adapters. Note, these could easily be defined in
# a text file and registered by name rather than class object.

registerAdapter(PersonView, Person, inevow.IRenderer)
registerAdapter(BookmarkView, Bookmark, inevow.IRenderer)

############################################################################
# Create some data for the application to do something with.

objs = [
    Person('Valetino', 'Volonghi', 'dialtone'),
    Person('Matt', 'Goodall', 'mg'),
    Bookmark('Nevow', 'http://www.nevow.com'),
    Person('Somebody', 'Else', 'Nevow2004'),
    Bookmark('Twisted', 'http://twistedmatrix.com/'),
    Bookmark('Python', 'http://www.python.org'),
    ]

############################################################################
# PSimple Page that renders objs list

class Page(rend.Page):
    
    addSlash = True

    def render_item(self, ctx, data):
        return inevow.IRenderer(data)

    docFactory = loaders.stan(
        T.html[
            T.body[
                T.ul(data=objs, render=rend.sequence)[
                T.li(pattern='item')[render_item]
                    ],
                ],
            ]
        )
