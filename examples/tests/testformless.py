
from twisted.internet import defer

from formless import annotate, webform

from nevow import rend, loaders, tags, livetest, url, livepage


"""WWWWizard functionality!
"""


test_suite = [
    ('visit', '/formpost/', ''),
    ('value', 'foo-foo', '5'),
    ('post', 'foo', {'foo-foo': 'asdf'}),
    ('assert', livetest.xpath('//form[@id="foo"]//div[@class="freeform-form-error"]'), "'asdf' is not an integer."),
    ## Check to make sure we repopulate the user's input with the erronious input
    ('value', 'foo-foo', 'asdf'),
    ('post', 'foo', {'foo-foo': '10'}),
    ('value', 'foo-foo', '10'),
    ]


test_suite += [
    ('visit', '/formpost2/', ''),
    ('post', 'bar', {'bar-baz': '5', 'bar-slam': '5', 'bar-ham': 'efgh', 'bar-custom': '1'}),
    ## XXX TODO: Can't post a radio button, so there is "None" below
    ('assert', livetest.xpath('//h3'), "You called bar! 5 5 efgh None {'stuff': 1234, 'name': 'One'}")
]

test_suite += [
    ('visit', '/testformless', ''),
    ('post', 'name', {'name-name': 'Fred'}),
    ('post', 'quest', {'quest-quest': 'Find the Grail'}),
    ('post', 'speed', {'speed-speed': '123'}),
    ('assert', 'body', "Thanks for taking our survey! You said: 'Fred' 'Find the Grail' 123")]


class NameWizard(rend.Page):
    docFactory = loaders.stan(tags.html[tags.h1["What is your name"], webform.renderForms()])

    def bind_name(self, ctx):
        return [('name', annotate.String())]

    def name(self, name):
        return QuestWizard(name)


class QuestWizard(rend.Page):
    docFactory = loaders.stan(tags.html[tags.h1["What is your quest"], webform.renderForms()])

    def bind_quest(self, ctx):
        return [('quest', annotate.Choice(['Find the Grail', 'Get laid', 'Earn twenty bucks', 'Destroy the sun']))]

    def quest(self, quest):
        return FinalWizard((self.original, quest))


class FinalWizard(rend.Page):
    docFactory = loaders.stan(tags.html[tags.h1["What is the airspeed velocity of an unladen swallow"], webform.renderForms()])

    def bind_speed(self, ctx):
        return [('speed', annotate.Integer())]

    def speed(self, speed):
        return rend.Page(
            docFactory=loaders.stan(
                tags.html[
                    tags.body(id='body')[
                        "Thanks for taking our survey! You said: %r %r %r" % (
                            self.original[0], self.original[1], speed)]]))


def checkLocation(client):
    d = defer.Deferred()
    def gotResult(ctx, location):
        from urlparse import urlparse
        if urlparse(location)[2] == '/':
            d.callback(None)
        else:
            d.errback(None)
    client.send(client.transient(gotResult, livepage.js.testFrameNode.contentDocument.location))
    return d


test_suite += [
    ('visit', '/formless_redirector', ''),
    ('post', 'goHome', {}),
    ('call', checkLocation, ())]


class Redirector(rend.Page):
    docFactory = loaders.stan(tags.html[tags.body[webform.renderForms()]])

    def bind_goHome(self, ctx):
        return []

    def goHome(self):
        return url.root


formless_tests = livetest.Tester(test_suite)


