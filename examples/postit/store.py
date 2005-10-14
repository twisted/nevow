from zope.interface import implements

from atop.store import Store, referenced, Pool, Item, indexed #functions, classes
from atop.store import NameIndex, UIDIndex, StringIndex, DateIndex #Indexes
from atop.powerup import Storeup, IPowerStation #PowerUps

from nevow import compy

class ContentIndex(StringIndex): pass
class AuthorIndex(StringIndex): pass

class Post(Item):
    
    content = indexed(ContentIndex)
    author = indexed(AuthorIndex)
    
    def __init__(self, store, author, title, url, content=None):
        Item.__init__(self, store, name = title)

        self.author = author
        self.title = title
        self.url = url
        self.content = content

class IPostit(compy.Interface):
    pass

class Postit(Storeup):
    implements(IPostit)
    
    powerupName = "postit"
    postsPool = referenced
    
    def setUpPools(self, store):
        self.postsPool = Pool(store)
        addI = self.postsPool.addIndex
        addI(NameIndex)
        addI(DateIndex)
        addI(ContentIndex)
        addI(AuthorIndex)
        
        post = Post(store, 'dialtone', 'Cool',
                    'http://www.python.org/',
                    'Hi boys and girls, this is just my first post in here')
        self.addNewPost(post)
        store.setComponent(IPostit, self)
        
    def addNewPost(self, post):
        id = self.getNextId()
        self.postsPool.addItem(post)
        self.touch()        
        return id
    
    def getPosts(self, how_many = None):
        posts_num = self.getNextId()
        if how_many:
            return self.postsPool.queryIndex(UIDIndex, startKey=posts_num-1, endKey=posts_num-how_many, backwards=True)
        else:
            return self.postsPool.queryIndex(UIDIndex, startKey=posts_num-1, endKey=0, backwards=True)
            
    
    def getOne(self, id):
        return self.postsPool.getIndexItem(UIDIndex, id)
            
    def getNextId(self):
        # This is different from nextUID since I need this to enumerate ONLY posts in the pool
        return self.postsPool.nextUID(allocate=False)
            
def initialize(dbname='db', fsname='fs'):
    s = Store(dbname, fsname)
    ps = IPowerStation(s)
    def _(s, ps):
        ps.installPowerup(Postit)
    s.transact(_, s, ps)
    return s

num = 100000
def populate():
    # Don't run me from this module, run populate.py instead
    # it takes some time to populate the database with 100.000 elements
    # the final database size should be around 175MB.
    s = initialize('db', 'fs')

    def createPost(s):
        global num
        po = IPostit(s)
        newPost = Post(s, 'dialtone', 'Title: %s' % (100000-num,), 
                       'bench','This is the test number %s' % (num)) 
        po.addNewPost(newPost)
        num -= 1
        if num <= 0:
            print "Finished"
            return True
        return False    

    def createPosts(s):
        postsCreated = s.batch(createPost, s)
        return postsCreated

    def factory(s):
        postsCreated = 0
        while 1:
            postsCreated += s.transact(createPosts, s)
            if postsCreated >= 100000:
                break
    
    factory(s)
