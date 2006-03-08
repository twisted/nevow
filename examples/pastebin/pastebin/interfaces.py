from zope.interface import Interface

class IPasteBin(Interface):

    def getListOfPastings(limit=None):
        """
        (oid, author, time) tuples
        """
        pass

    def getPasting(oid):
        pass

    def addPasting(author, text):
        pass

    def updatePasting(oid, author, text):
        pass
