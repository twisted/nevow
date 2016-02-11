from zope.interface import implementer, Interface

from axiom import store, item
from axiom.attributes import text, bytes

class IImages(Interface):
    pass

class Image(item.Item):
    title = text()
    author = text()
    image = bytes()
    hash = text()

@implementer(IImages)
class Application(item.Item, item.InstallableMixin):

    name = text()

    def installOn(self, other):
        super(Application, self).installOn(other)
        other.powerUp(self, IImages)

    def getImages(self, how_many=None):
        return self.store.query(Image, limit=how_many, sort=Image.storeID.descending)

    def getOne(self, hash):
        return self.store.findUnique(Image, Image.hash==hash)

def initialize():
   s = store.Store('imagination.axiom')
   images = IImages(s, None)
   if not images:
       Application(store=s, name='Imagination').installOn(s)
   return s
