from nevow import compy


class IPasting(compy.Interface):

    def getLatestVersion(self):
        """Return the latest version"""

    def getVersion(self, version):
        """Get a specific version"""

    def getHistory(self):
        """Get the history of the pasting as a list of (version, author, time) tuples."""


class IVersion(compy.Interface):
    
    def getAuthor(self):
        pass

    def getText(self):
        pass

    def getTime(self):
        pass
