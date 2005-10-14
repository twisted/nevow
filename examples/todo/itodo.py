from nevow import compy

class ITimer(compy.Interface):
    """ """

class IEnv(compy.Interface):
    """ """

class ITodos(compy.Interface):
    """ """
    def add(self, description, done):
        pass
    def delete(self, id):
        pass
    def edit(self, id, description, done):
        pass
