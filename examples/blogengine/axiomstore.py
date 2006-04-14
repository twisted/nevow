from iblogengine import IBlog
from zope.interface import implements
from axiom import item, store, attributes, sequence
from epsilon.extime import Time

class Post(item.Item):
    typeName = "BlogenginePost"
    schemaVersion = 1

    id = attributes.integer(indexed=True, allowNone=False)
    created = attributes.timestamp(indexed=True)
    modified = attributes.timestamp(indexed=True)
    title = attributes.text(indexed=True, allowNone=False)
    author = attributes.text(indexed=True, allowNone=False)
    category = attributes.text(indexed=True)
    content = attributes.text(indexed=True)

    def __init__(self, **kw):
        now = Time()
        kw.update({'created':now,
                   'modified':now})
        super(Post, self).__init__(**kw)

    def setModified(self):
        self.modified = Time()

class Blog(item.Item, item.InstallableMixin):
    implements(IBlog)

    typeName = "BlogengineBlog"
    schemaVersion = 1

    posts = attributes.reference()
    next_id = attributes.integer(default=0)
    
    def __init__(self, **kw):
        super(Blog, self).__init__(**kw)
        self.posts = sequence.List(store=self.store)
        post = Post(store=self.store,
                    id=self.getNextId(),
                    author=u'mike',
                    title=u'FIRST POST!!!!',
                    category=u'Test',
                    content=u'I guess it worked.')
        self.addNewPost(post)

    def installOn(self, other):
        super(Blog, self).installOn(other)
        other.powerUp(self, IBlog)

    def addNewPost(self, post):
        # Why even let posts manage their own ids?  Oh well.
        assert post.id == self.next_id,\
               "Bad post ID; is %r, should be %r" % (post.id, self.next_id)
        self.posts.append(post)
        self.next_id += 1

    def getPosts(self, how_many = None):
        """Return the latest 'how_many' posts, in reverse database order.

        XXX Really, it should be based on modtime.  Which is broken.
        """
        if how_many is None or how_many > self.next_id:
            how_many = self.next_id
        return (self.getOne(self.next_id-id-1) for id in range(how_many))

    def getOne(self, id):
        return self.posts[id]

    def getNextId(self):
        return self.next_id
    
def initialize(storename):
    s = store.Store(storename)
    s.findOrCreate(Blog).installOn(s)
    return s
