from zope.interface import implements

from axiom import store, item, attributes

from nevow import compy

class Book(item.Item):
    typeName = 'book'
    schemaVersion = 1

    title = attributes.text()
    description = attributes.text()

class ILibrary(compy.Interface):
    pass

class Library(item.Item):
    implements(ILibrary)
    
    typeName = 'library'
    schemaVersion = 1

    name = attributes.text()
    
    def install(self):
        self.store.powerUp(self, ILibrary)

    def addNewBook(self, title):
        newBook = Book(store=self.store, title=title)
    
    def getBookByTitle(self, title):
        books = self.store.query(Book, Book.title == unicode(title))
        for book in books:
            return book
        
def initialize(dbdir):
    # This is store initialization. 
    s = store.Store(dbdir)
    l = Library(store=s, name=u"Great Library")
    l.install()
    descr = u"""This book is totally useless, in fact nobody would
    borrow it"""
    Book(store=s, title=u"Title: 1", description=descr)
    return s
