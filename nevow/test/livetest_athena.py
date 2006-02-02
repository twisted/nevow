from twisted.internet import defer

from nevow import loaders, tags, athena
from nevow.livetrial import testcase

class ClientToServerArgumentSerialization(testcase.TestCase):
    """
    Tests that arguments passed to a method on the server are properly
    received.
    """

    jsClass = u'Nevow.Athena.Tests.ClientToServerArgumentSerialization'

    docFactory = loaders.stan(tags.div(render=tags.directive('liveTest'))['ClientToServerArgumentSerialization'])

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

class ClientToServerResultSerialization(testcase.TestCase):
    """
    Tests that the return value from a method on the server is
    properly received by the client.
    """

    jsClass = u'Nevow.Athena.Tests.ClientToServerResultSerialization'

    docFactory = loaders.stan(tags.div(render=tags.directive('liveTest'))['ClientToServerResultSerialization'])

    allowedMethods = {'test': True}
    def test(self, i, f, s, l, d):
        return (i, f, s, l, d)

class ClientToServerExceptionResult(testcase.TestCase):
    """
    Tests that when a method on the server raises an exception, the
    client properly receives an error.
    """

    jsClass = u'Nevow.Athena.Tests.ClientToServerExceptionResult'

    docFactory = loaders.stan(tags.div(render=tags.directive('liveTest'))['ClientToServerExceptionResult'])

    allowedMethods = {'testSync': True}
    def testSync(self, s):
        raise Exception(s)

class ClientToServerAsyncExceptionResult(testcase.TestCase):
    """
    Tests that when a method on the server raises an exception asynchronously,
    the client properly receives an error.
    """

    jsClass = u'Nevow.Athena.Tests.ClientToServerAsyncExceptionResult'

    docFactory = loaders.stan(tags.div(render=tags.directive('liveTest'))['ClientToServerAsyncExceptionResult'])

    allowedMethods = {'testAsync': True}
    def testAsync(self, s):
        return defer.fail(Exception(s))

class ServerToClientArgumentSerialization(testcase.TestCase):
    """
    Tests that a method invoked on the client by the server is passed
    the correct arguments.
    """

    jsClass = u'Nevow.Athena.Tests.ServerToClientArgumentSerialization'

    docFactory = loaders.stan(tags.div(render=tags.directive('liveTest'))['ServerToClientArgumentSerialization'])

    allowedMethods = {'test': True}
    def test(self):
        return self.callRemote('reverse', 1, 1.5, u'hello', {u'world': u'value'});

class ServerToClientResultSerialization(testcase.TestCase):
    """
    Tests that the result returned by a method invoked on the client
    by the server is correct.
    """

    jsClass = u'Nevow.Athena.Tests.ServerToClientResultSerialization'

    docFactory = loaders.stan(tags.div(render=tags.directive('liveTest'))['ServerToClientResultSerialization'])

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

class WidgetInATable(testcase.TestCase):
    jsClass = u"Nevow.Athena.Tests.WidgetInATable"

    docFactory = loaders.stan(tags.table[
        tags.tbody[
            tags.tr[
                tags.td(render=tags.directive('liveTest'))[
                    'Test Widget In A Table']]]])

class WidgetIsATable(testcase.TestCase):
    jsClass = u"Nevow.Athena.Tests.WidgetIsATable"

    docFactory = loaders.stan(tags.table(render=tags.directive('liveTest'))[
        tags.tbody[
            tags.tr[
                tags.td[
                    'Test Widget Is A Table']]]])

class ParentChildRelationshipTest(testcase.TestCase):
    jsClass = u"Nevow.Athena.Tests.ChildParentRelationshipTest"

    docFactory = loaders.stan(tags.div(render=tags.directive('liveTest'))[
        'ParentChildRelationshipTest',
        tags.div(render=tags.directive('childrenWidgets'))])


    def render_childrenWidgets(self, ctx, data):
        for i in xrange(3):
            yield ChildFragment(self.page, i)


    allowedMethods = {'getChildCount': True}
    def getChildCount(self):
        return 3

class ChildFragment(athena.LiveFragment):
    jsClass = u'Nevow.Athena.Tests.ChildParentRelationshipTest'

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

class AutomaticClass(testcase.TestCase):
    jsClass = u'Nevow.Athena.Tests.AutomaticClass'

    docFactory = loaders.stan(tags.div(render=tags.directive('liveTest'))['AutomaticClass'])
