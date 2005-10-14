

# chatola.py
# a simple chat engine

import os, random, time

from nevow import inevow, loaders, livepage
from nevow.livepage import set, assign, append, js, document, eol


chatolaDir = os.path.split(os.path.abspath(__file__))[0]


if os.path.exists('/usr/share/dict/words'):
    WORDS = open('/usr/share/dict/words').readlines()
else:
    WORDS = open(os.path.join(
        os.path.split(
            chatolaDir)[0], 'files', 'words')).readlines()


class Chatola(livepage.LivePage):
    addSlash = True
    docFactory = loaders.xmlfile(os.path.join(chatolaDir, 'Chatola.html'))
    messagePattern = inevow.IQ(docFactory).patternGenerator('message')
    userPattern = inevow.IQ(docFactory).patternGenerator('user')
    topic = "Welcome to Chatola"

    def __init__(self):
        self.clients = []
        self.events = []
        self.sendEvent(
            None,
            set('topic', self.topic), eol,
            assign(document.topicForm.topic.value, self.topic), eol)

        livepage.LivePage.__init__(self)

    def goingLive(self, ctx, client):
        client.notifyOnClose().addBoth(self.userLeft, client)

        client.userId = random.choice(WORDS).strip()
        client.send(
            assign(document.nickForm.nick.value, client.userId))

        addUserlistEntry = append('userlist', self.userPattern.fillSlots('user-id', client.userId)), eol
        self.sendEvent(
            client, addUserlistEntry, self.content(client, 'has joined.'))

        ## Catch the user up with the previous events
        client.send([(event, eol) for source, event in self.events])

        self.clients.append(client)

    def userLeft(self, _, client):
        self.clients.remove(client)
        self.sendEvent(
            client,
            js.removeNode('user-list-%s' % (client.userId, )), eol,
            self.content(client, 'has left.'))

    def sendEvent(self, source, *event):
        self.events.append((source, event))
        for target in self.clients:
            if target is not source:
                target.send(event)
        return event

    def content(self, sender, message):
        return append(
            'content',
            self.messagePattern.fillSlots(
                'timestamp', time.strftime("%H:%M %d/%m/%y")
            ).fillSlots(
                'userid', sender.userId
            ).fillSlots(
                'message', message)), eol, js.scrollDown()

    def handle_sendInput(self, ctx, inputLine):
        sender = livepage.IClientHandle(ctx)
        return self.sendEvent(sender, self.content(sender, inputLine)), eol, js.focusInput()

    def handle_changeTopic(self, ctx, topic):
        changer = livepage.IClientHandle(ctx)
        return self.sendEvent(
            changer,
            set('topic', topic), eol, 
            assign(document.topicForm.topic.value, topic), eol,
            self.content(changer, 'changed the topic to %r.' % (topic, )))

    def handle_changeNick(self, ctx, nick):
        changer = livepage.IClientHandle(ctx)
        rv = self.sendEvent(
            changer,
            set('user-list-%s' % (changer.userId, ), nick), eol,
            js.changeId('user-list-%s' % (changer.userId, ), 'user-list-%s' % (nick, )), eol,
            self.content(changer, 'changed nick to %r.' % (nick, )))

        changer.userId = nick
        return rv


def createResource():
    return Chatola()


