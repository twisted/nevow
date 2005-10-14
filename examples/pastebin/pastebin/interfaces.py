from nevow import compy

class IPasteBin(compy.Interface):

    def getListOfPastings(self, limit=None):
        """
        (oid, author, time) tuples
        """
        pass

    def getPasting(self, oid):
        pass

    def addPasting(self, author, text):
        pass

    def updatePasting(self, oid, author, text):
        pass
