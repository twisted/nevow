from nevow.compy import Interface

class IStore(Interface):
    """ Interface used to remember the store in the site object """
    
class IBlog(Interface):
    """ Represents the Blog Powerup in the Store """
    def addNewPost(self, post):
        """ Add the user provided post instance to the blog """
    def getPosts(self, how_many = None):
        """ Get the last X posts, if how_many is not specified, gets all of them """

    def getOne(self, id):
        """ Get the post with the corresponding id from the store """

    def getNextId(self):
        """ Get the next free id in the store """