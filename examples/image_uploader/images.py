from zope.interface import implements

from atop.store import Store, referenced, Pool, Item, indexed #functions, classes
from atop.store import UIDIndex, StringIndex #Indexes
from atop.powerup import Storeup, IPowerStation #PowerUps

from nevow import compy

import random
from string import ascii_letters as alpha # ohhh...
 
alphaDigit = alpha + '0123456789'
 
 
def label(length=None): 
   """
   Return one of 183,123,959,522,816 possible labels.
   """
 
   first = random.choice(alpha)
   rest = [random.choice(alphaDigit) for i in xrange(length or 7)]
   newLabel = first + ''.join(rest)
   return newLabel

class AuthorIndex(StringIndex): pass
class FileNameIndex(StringIndex): pass

class Image(Item):
   
   filename = indexed(FileNameIndex)

   def __init__(self, store, image, author=None, title=None):
      filename = label()
      self.title = title or filename
      Item.__init__(self, store, name = self.title)
      
      self.author = author
      self.image = image
      f = self.store.newSubFileForItem(self)
      f.write(image)
      self.filename = f.close(filename).path
      self.touch()
      
   def getImage(self):
      try:
         f = open(self.filename, "r")
         return f.read()
      finally:
         if f:
            f.close()

class IImages(compy.Interface):
   pass

class Images(Storeup):
   implements(IImages)
   
   powerupName = "imagination"
   imagesPool = referenced
    
   def setUpPools(self, store):
      self.imagesPool = Pool(store)
      addI = self.imagesPool.addIndex
      addI(FileNameIndex)
      addI(UIDIndex)
      
      store.setComponent(IImages, self)
      
   def addImage(self, image):
      id = self.getNextId()
      self.imagesPool.addItem(image)
      self.touch()        
      return id
    
   def getImages(self, how_many=None):
      posts_num = self.getNextId()
      if how_many:
         return self.imagesPool.queryIndex(UIDIndex, startKey=posts_num, endKey=posts_num-how_many, backwards=True)
      else:
         return self.imagesPool.queryIndex(UIDIndex, startKey=posts_num-1, endKey=0, backwards=True)
            
    
   def getOne(self, name):
      return self.imagesPool.getIndexItem(FileNameIndex, name)
            
   def getNextId(self):
      return self.imagesPool.nextUID(allocate=False)
        
    
def initialize(dbname='db', fsname='fs'):
   s = Store(dbname, fsname)
   ps = IPowerStation(s)
   def _(s, ps):
      ps.installPowerup(Images)
   s.transact(_, s, ps)
   return s
