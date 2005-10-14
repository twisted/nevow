

import atexit, pickle
from nevow import loaders, tags, livepage, inevow


class node:
    def __init__(self, question, positive=None, negative=None):
        self.question = question
        self.positive = positive
        self.negative = negative

    def clone(self):
        return self.__class__(**vars(self))

    def isLeaf(self):
        return not (self.positive or self.negative)


win = 'winnar'
lose = lambda: node("I give up. What is the animal, and what question describes it?")


def guess(animal):
    return node("Is it " + animal + "?", win, lose())


try:
    knowledge = pickle.load(file('knowledge', 'rb'))
except:
    knowledge = lose()
atexit.register(lambda: pickle.dump(knowledge, file('knowledge', 'wb')))


class AnimalPage(livepage.LivePage):
    addSlash = True
    def locateChild(self, ctx, segments):
        if ctx.arg('fresh') is not None:
            global knowledge
            knowledge = lose()
        return super(AnimalPage, self).locateChild(ctx, segments)

    def goingLive(self, ctx, client):
        client.oldNode = knowledge
        client.node = knowledge
        client.send(self.handle_updateDom(ctx))

    docFactory = loaders.stan(
        tags.html[
            tags.head[
                tags.directive('liveglue')],
            tags.body[
                tags.h1["Live Animal"],
                tags.div(id='question')[""],
                tags.div(id='answer-inputs')[
                    tags.form(
                        name='new-question',
                        pattern="leaf",
                        onsubmit=[
                            livepage.server.handle(
                                'newquestion',
                                livepage.get('animal').value,
                                livepage.get('new-question').value),
                            livepage.stop])[
                        tags.input(name='animal', id='animal'),
                        tags.input(name='new-question', id='new-question'),
                        tags.button['Submit']],
                    tags.invisible(pattern='branch')[
                        tags.button(
                            id="yes-response",
                            onclick=livepage.server.handle('positiveResponse'))['Yes'],
                        tags.button(
                            id="no-response",
                                onclick=livepage.server.handle('negativeResponse'))['No']]]]])

    def handle_updateDom(self, ctx):
        client = livepage.IClientHandle(ctx)
        yield livepage.set('question', client.node.question), livepage.eol
        if client.node.isLeaf():
            yield livepage.set('answer-inputs', inevow.IQ(AnimalPage.docFactory).onePattern('leaf')), livepage.eol
        else:
            yield livepage.set('answer-inputs', inevow.IQ(AnimalPage.docFactory).onePattern('branch')), livepage.eol

    def handle_newquestion(self, ctx, animal, question):
        client = livepage.IClientHandle(ctx)
        newNegative = client.oldNode.clone()
    
        client.oldNode.question = question
        client.oldNode.positive = guess(animal)
        client.oldNode.negative = newNegative
    
        client.node = knowledge
        return self.handle_updateDom(ctx)

    def handle_positiveResponse(self, ctx):
        client = livepage.IClientHandle(ctx)
        client.oldNode = client.node
        client.node = client.node.positive
        if client.node == win:
            client.node = knowledge
            yield livepage.set('question', "I win!"), livepage.eol
            yield livepage.set(
                'answer-inputs',
                tags.button(
                    id="start-over",
                    onclick=livepage.server.handle('updateDom'))["Start over"]), livepage.eol
        else:
            yield self.handle_updateDom(ctx), livepage.eol
    
    def handle_negativeResponse(self, ctx):
        client = livepage.IClientHandle(ctx)
        client.oldNode = client.node
        client.node = client.node.negative
        return self.handle_updateDom(ctx)


def createResource():
    return AnimalPage()


