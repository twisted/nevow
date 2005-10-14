import time

from zope.interface import implements

from atop.store import Store, referenced, Pool, Item, indexed #functions, classes
from atop.store import NameIndex, UIDIndex, DateIndex, StringIndex, IntIndex #Indexes
from atop.powerup import Storeup, IPowerStation #PowerUps

from iblogengine import IBlog

class ContentIndex(StringIndex): pass
class CategoryIndex(StringIndex): pass
class ModificationIndex(DateIndex): pass
class AuthorIndex(StringIndex): pass
class PostIndex(IntIndex): pass

def updateTime(item, value):
    item.last_mod = time.gmtime(time.time())    

class Post(Item):
    
    id = indexed(PostIndex, updateTime)
    modification = indexed(ModificationIndex, updateTime)
    content = indexed(ContentIndex, updateTime)
    category = indexed(CategoryIndex, updateTime)
    author = indexed(AuthorIndex, updateTime)
    
    exists = False
    
    def __init__(self, store, id, author, title, category=None, content=None):
        Item.__init__(self, store, name = title)
        self.id = id
        self.author = author
        self.title = title
        self.last_mod = self.dateCreated
        self.category = category
        self.content = content
        self.exists = True

class Blog(Storeup):
    implements(IBlog)
    
    powerupName = "blogengine"
    id = 0
    postsPool = referenced
    
    def setUpPools(self, store):
        self.postsPool = Pool(store)
        addI = self.postsPool.addIndex
        addI(NameIndex)
        addI(DateIndex)
        addI(ModificationIndex)
        addI(ContentIndex)
        addI(CategoryIndex)
        addI(AuthorIndex)
        addI(PostIndex)
        
        post = Post(store, self.getNextId(), 'dialtone', 'This is the first post','Hobby',
                    'Hi boys and girls, this is just my first post in here')
        self.addNewPost(post)
        store.setComponent(IBlog, self)
        
    def addNewPost(self, post):
        self.postsPool.addItem(post)
        self.id = self.id + 1
        self.touch()
    
    def getPosts(self, how_many = None):
        posts_num = self.postsPool.nextUID(allocate=False)
        if how_many:
            return self.postsPool.queryIndex(UIDIndex, startKey=posts_num-1, endKey=posts_num-how_many, backwards=True)
        else:
            return self.postsPool.queryIndex(UIDIndex, startKey=posts_num-1, endKey=0, backwards=True)
            
    
    def getOne(self, id):
        return self.postsPool.getIndexItem(PostIndex, id)
            
    def getNextId(self):
        # This is different from nextUID since I need this to enumerate ONLY posts in the pool
        return self.id
            
def initialize(dbname='db', fsname='fs'):
    s = Store(dbname, fsname)
    ps = IPowerStation(s)
    def _(s, ps):
        ps.installPowerup(Blog)
    s.transact(_, s, ps)
    return s

num = 10000
def populate():
    # Don't run me from this module, run populate.py instead
    # it takes some time to populate the database with 10.000 elements
    # the final database size should be around 20MB with 40MB of logs.
    s = initialize('db', 'fs')

    def createPost(s):
        global num
        po = IBlog(s)
        newPost = Post(s, po.getNextId(), 'dialtone', 'Title: %s' % (10000-num,), 
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
            if postsCreated >= 10000:
                break
    
    factory(s)
