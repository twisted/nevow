from twisted.python.util import sibpath
from nevow.athena import LiveElement, expose
from nevow.loaders import xmlfile

class EchoElement(LiveElement):

    docFactory = xmlfile(sibpath(__file__, 'template.html'))
    jsClass = u'EchoThing.EchoWidget'

    def say(self, message):
        self.callRemote('addText', message)
    say = expose(say)
