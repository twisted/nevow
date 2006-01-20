
from twisted.trial import unittest
from twisted.internet import defer

from nevow import athena, loaders, tags, util

TEST = 'return Nevow.Athena.Widget.get(this).test();'

class AthenaTestMixin:
    jsModules = {
        u'AthenaTest': util.resource_filename('athenademo', 'athenatest.js')}


class ImportBeforeLiteralJavaScript(AthenaTestMixin, athena.LiveFragment):

    jsClass = u'AthenaTest.ImportBeforeLiteralJavaScript'

    docFactory = loaders.stan(tags.p(render=tags.directive('liveFragment'))[
        tags.button(onclick=TEST)['Test Import Before Literal JavaScript'],
        tags.div[
            tags.script(type="text/javascript")["""
            var importBeforeLiteralJavaScriptResult;
            if (typeof Nevow.Athena.Widget == 'undefined') {
                importBeforeLiteralJavaScriptResult = false;
            } else {
                importBeforeLiteralJavaScriptResult = true;
            }
            """]]])



class ClientToServerArgumentSerialization(athena.LiveFragment, unittest.TestCase):
    """
    Tests that arguments passed to a method on the server are properly
    received.
    """

    jsClass = u'AthenaTest.ClientToServerArgumentSerialization'

    docFactory = loaders.stan(tags.div(render=tags.directive('liveFragment'))[
        tags.form(action='#', onsubmit=TEST)[
            tags.input(type='submit', value='Test Client To Server Argument Serialization')]])

    allowedMethods = {'test': True}
    def test(self, i, f, s, l, d):
        self.assertEquals(i, 1)
        self.assertEquals(f, 1.5)
        self.failUnless(isinstance(s, unicode))
        self.assertEquals(s, u'Hello world')
        self.failUnless(isinstance(l[2], unicode))
        self.assertEquals(l, [1, 1.5, u'Hello world'])
        self.assertEquals(d, {u'hello world': u'object value'})
        self.failUnless(isinstance(d.keys()[0], unicode))
        self.failUnless(isinstance(d.values()[0], unicode))



class ClientToServerResultSerialization(athena.LiveFragment):
    """
    Tests that the return value from a method on the server is
    properly received by the client.
    """

    jsClass = u'AthenaTest.ClientToServerResultSerialization'

    docFactory = loaders.stan(tags.div(render=tags.directive('liveFragment'))[
        tags.form(action='#', onsubmit=TEST)[
            tags.input(type='submit', value='Test Client To Server Result Serialization')]])

    allowedMethods = {'test': True}
    def test(self, i, f, s, l, d):
        return (i, f, s, l, d)


class ClientToServerExceptionResult(athena.LiveFragment):
    """
    Tests that when a method on the server raises an exception, the
    client properly receives an error.
    """

    jsClass = u'AthenaTest.ClientToServerExceptionResult'

    docFactory = loaders.stan(tags.div(render=tags.directive('liveFragment'))[
        tags.form(action='#', onsubmit='return Nevow.Athena.Widget.get(this).test(true);')[
            tags.input(type='submit', value='Test Client To Server Synchronous Exception Result')],
        tags.form(action='#', onsubmit='return Nevow.Athena.Widget.get(this).test(false);')[
            tags.input(type='submit', value='Test Client To Server Asynchronous Exception Result')]])


    allowedMethods = {'testSync': True, 'testAsync': True}
    def testSync(self, s):
        raise Exception(s)

    def testAsync(self, s):
        return defer.fail(Exception(s))


class ServerToClientArgumentSerialization(athena.LiveFragment):
    """
    Tests that a method invoked on the client by the server is passed
    the correct arguments.
    """

    jsClass = u'AthenaTest.ServerToClientArgumentSerialization'

    docFactory = loaders.stan(tags.div(render=tags.directive('liveFragment'))[
        tags.form(action='#', onsubmit=TEST)[
            tags.input(type='submit', value='Test Server To Client Argument Serialization')]])

    allowedMethods = {'test': True}
    def test(self):
        return self.callRemote('reverse', 1, 1.5, u'hello', {u'world': u'value'});

class ServerToClientResultSerialization(athena.LiveFragment, unittest.TestCase):
    """
    Tests that the result returned by a method invoked on the client
    by the server is correct.
    """

    jsClass = u'AthenaTest.ServerToClientResultSerialization'

    docFactory = loaders.stan(tags.div(render=tags.directive('liveFragment'))[
        tags.form(action='#', onsubmit=TEST)[
            tags.input(type='submit', value='Test Server To Client Result Serialization')]])

    allowedMethods = {'test': True}
    def test(self):
        def cbResults(result):
            self.assertEquals(result[0], 1)
            self.assertEquals(result[1], 1.5)
            self.assertEquals(result[2], u'hello')
            self.assertEquals(result[3], {u'world': u'value'})
        d = self.callRemote('reverse')
        d.addCallback(cbResults)
        return d



class WidgetInATable(AthenaTestMixin, athena.LiveFragment):
    jsClass = u"AthenaTest.WidgetInATable"

    docFactory = loaders.stan(tags.table[
        tags.tbody[
            tags.tr[
                tags.td(render=tags.directive('liveFragment'))[
                    tags.button(onclick=TEST)[
                        'Test Widget In A Table']]]]])



class WidgetIsATable(AthenaTestMixin, athena.LiveFragment):
    jsClass = u"AthenaTest.WidgetIsATable"

    docFactory = loaders.stan(tags.table(render=tags.directive('liveFragment'))[
        tags.tbody[
            tags.tr[
                tags.td[
                    tags.button(onclick=TEST)[
                        'Test Widget Is A Table']]]]])



class ParentChildRelationshipTest(AthenaTestMixin, athena.LiveFragment):
    jsClass = u"AthenaTest.ChildParentRelationshipTest"

    docFactory = loaders.stan(tags.div(render=tags.directive('liveFragment'))[
        tags.button(onclick=TEST)['Test Parent Child Relationships'],
        tags.div(render=tags.directive('childrenWidgets'))])


    def render_childrenWidgets(self, ctx, data):
        for i in xrange(3):
            yield ChildFragment(self.page, i)


    allowedMethods = {'getChildCount': True}
    def getChildCount(self):
        return 3



class ChildFragment(athena.LiveFragment):
    jsClass = u'AthenaTest.ChildParentRelationshipTest'

    docFactory = loaders.stan(tags.div(render=tags.directive('liveFragment'))[
        tags.div(render=tags.directive('childrenWidgets')),
        'child'])

    def __init__(self, page, childCount):
        super(ChildFragment, self).__init__()
        self.page = page
        self.childCount = childCount


    def render_childrenWidgets(self, ctx, data):
        # yield tags.div['There are ', self.childCount, 'children']
        for i in xrange(self.childCount):
            yield ChildFragment(self.page, self.childCount - 1)


    allowedMethods = {'getChildCount': True}
    def getChildCount(self):
        return self.childCount



class AutomaticClass(AthenaTestMixin, athena.LiveFragment):
    jsClass = u'AthenaTest.AutomaticClass'

    docFactory = loaders.stan(tags.div(render=tags.directive('liveFragment'))[
        tags.button(onclick=TEST)['Automatic athena:class attribute']])



class AthenaTests(athena.LivePage):
    docFactory = loaders.stan([
        tags.xml('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'),
        tags.html(**{'xmlns:nevow': 'http://nevow.com/ns/nevow/0.1'})[
            tags.head[
                tags.invisible(render=tags.directive('liveglue'))],
            tags.body[
                tags.slot('tests'),
                tags.invisible(render=tags.directive('introspection'))]]])

    addSlash = True

    tests = [
        # ImportBeforeLiteralJavascript _must_ be the first test.
        ImportBeforeLiteralJavaScript,

        ClientToServerArgumentSerialization,
        ClientToServerResultSerialization,
        ClientToServerExceptionResult,
        ServerToClientArgumentSerialization,
        ServerToClientResultSerialization,
        WidgetInATable,
        WidgetIsATable,
        AutomaticClass,
        ParentChildRelationshipTest,
        ]


    def renderTests(self):
        for frgClass in self.tests:
            frg = frgClass()
            self.jsModules.mapping.update(getattr(frg, 'jsModules', {}))
            frg.page = self
            yield frg


    def beforeRender(self, ctx):
        ctx.fillSlots('tests', self.renderTests())


    def render_introspection(self, ctx, data):
        f = athena.IntrospectionFragment()
        f.setFragmentParent(self)
        return ctx.tag[f]
