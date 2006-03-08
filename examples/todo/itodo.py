from zope.interface import Interface

class ITimer(Interface):
    """ """

class IEnv(Interface):
    """ """

class ITodos(Interface):
    """ """
    def add(description, done):
        pass
    def delete(id):
        pass
    def edit(id, description, done):
        pass
