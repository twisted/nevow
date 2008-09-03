from twisted.python.util import sibpath
from nevow.loaders import xmlfile
from nevow.athena import LiveElement, expose

class ChatRoom(object):

    def __init__(self):
        self.chatters = []

    def wall(self, message):
        for chatter in self.chatters:
            chatter.wall(message)

    def tellEverybody(self, who, what):
        for chatter in self.chatters:
            chatter.hear(who.username, what)

    def makeChatter(self):
        elem = ChatterElement(self)
        self.chatters.append(elem)
        return elem

# element to be run with twistd
chat = ChatRoom().makeChatter

class ChatterElement(LiveElement):

    docFactory = xmlfile(sibpath(__file__, 'template.html'))
    jsClass = u'ChatThing.ChatterWidget'

    def __init__(self, room):
        self.room = room

    def setUsername(self, username):
        self.username = username
        message = ' * user '+username+' has joined the room'
        self.room.wall(message)
    setUsername = expose(setUsername)

    def say(self, message):
        self.room.tellEverybody(self, message)
    say = expose(say)

    def wall(self, message):
        self.callRemote('displayMessage', message)

    def hear(self, username, what):
        self.callRemote('displayUserMessage', username, what)
