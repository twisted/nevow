from zope.interface import implementer, Interface

from axiom import store, item, attributes

class Book(item.Item):
    typeName = 'book'
    schemaVersion = 1

    title = attributes.text()
    description = attributes.text()

class ILibrary(Interface):
    pass

@implementer(ILibrary)
class Library(item.Item, item.InstallableMixin):
    
    typeName = 'library'
    schemaVersion = 1

    name = attributes.text()
    
    def installOn(self, other):
        super(Library, self).installOn(other)
        other.powerUp(self, ILibrary)

    def addNewBook(self, title):
        newBook = Book(store=self.store, title=title)
    
    def getBookByTitle(self, title):
        books = self.store.query(Book, Book.title == str(title))
        for book in books:
            return book
        
def initialize(dbdir):
    # This is store initialization. 
    s = store.Store(dbdir)
    l = Library(store=s, name="Great Library")
    l.installOn(s)
    descr = """This book is totally useless, in fact nobody would
    borrow it"""
    Book(store=s, title="Title: 1", description=descr)
    return s
