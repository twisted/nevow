from zope.interface import implements, Interface

from axiom import item, store
from axiom.attributes import text, timestamp
from epsilon.extime import Time

class IPostit(Interface):
    def getPosts(how_many):
        """Retrieve 'how_many' posts from the database."""
    
    def getPost(id):
        """Retrieve the post 'id' from the database"""

class Post(item.Item):
    title = text()
    url = text()
    content = text()
    author = text()
    created = timestamp()

class Application(item.Item, item.InstallableMixin):
    implements(IPostit)

    name = text()

    def installOn(self, other):
        super(Application, self).installOn(other)
        other.powerUp(self, IPostit)

    def getPosts(self, how_many = None):
        return self.store.query(Post, limit=how_many, sort=Post.created.descending)

    def getOne(self, id):
        return self.store.getItemByID(id)

def initialize():
    s = store.Store('postit.axiom')
    postit = IPostit(s, None)
    if not postit:
        Application(store=s, name=u'Postit').installOn(s)
        Post(store=s, 
             title=u"This is the title",
             url=u"http://www.divmod.org",
             content=u"Here is the content for the link",
             author=u"dialtone",
             created=Time())
    return s
