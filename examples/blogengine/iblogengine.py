from zope.interface import Interface

class IStore(Interface):
    """ Interface used to remember the store in the site object """
    
class IBlog(Interface):
    """ Represents the Blog Powerup in the Store """
    def addNewPost(post):
        """ Add the user provided post instance to the blog """
    def getPosts(how_many = None):
        """ Get the last X posts, if how_many is not specified, gets all of them """

    def getOne(id):
        """ Get the post with the corresponding id from the store """

    def getNextId():
        """ Get the next free id in the store """
