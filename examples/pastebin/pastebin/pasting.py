from zope.interface import Interface


class IPasting(Interface):

    def getLatestVersion():
        """Return the latest version"""

    def getVersion(version):
        """Get a specific version"""

    def getHistory():
        """Get the history of the pasting as a list of (version, author, time) tuples."""


class IVersion(Interface):
    
    def getAuthor():
        pass

    def getText():
        pass

    def getTime():
        pass
