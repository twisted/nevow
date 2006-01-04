
from twisted.trial import unittest
from twisted.internet import defer

from nevow import athena, loaders, tags, util

class ClientToServerArgumentSerialization(athena.LiveFragment, unittest.TestCase):
    """
    Tests that arguments passed to a method on the server are properly
    received.
    """

    javascriptTest = """\
function test_ClientToServerArgumentSerialization(node) {
    var r = Nevow.Athena.Widget.get(node);
    var L = [1, 1.5, 'Hello world'];
    var O = {'hello world': 'object value'};
    return r.callRemote('test', 1, 1.5, 'Hello world', L, O);
};
"""

    docFactory = loaders.stan(tags.div(render=tags.directive('liveFragment'))[
        tags.form(action='#', onsubmit='return test(test_ClientToServerArgumentSerialization(this));')[
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

    javascriptTest = """\
function test_ClientToServerResultSerialization(node) {
    var r = Nevow.Athena.Widget.get(node);
    var L = [1, 1.5, 'Hello world'];
    var O = {'hello world': 'object value'};
    var d = r.callRemote('test', 1, 1.5, 'Hello world', L, O);
    d.addCallback(function(result) {
        assertEquals(result[0], 1);
        assertEquals(result[1], 1.5);
        assertEquals(result[2], 'Hello world');
        assertEquals(result[3][0], 1);
        assertEquals(result[3][1], 1.5);
        assertEquals(result[3][2], 'Hello world');
        assertEquals(result[4]['hello world'], 'object value');
    });
    return d;
};
"""

    docFactory = loaders.stan(tags.div(render=tags.directive('liveFragment'))[
        tags.form(action='#', onsubmit='return test(test_ClientToServerResultSerialization(this));')[
            tags.input(type='submit', value='Test Client To Server Result Serialization')]])

    allowedMethods = {'test': True}
    def test(self, i, f, s, l, d):
        return (i, f, s, l, d)

class ClientToServerExceptionResult(athena.LiveFragment):
    """
    Tests that when a method on the server raises an exception, the
    client properly receives an error.
    """

    javascriptTest = """\
function test_ClientToServerExceptionResult(node, sync) {
    var r = Nevow.Athena.Widget.get(node);
    var d;
    var s = 'This exception should appear on the client.';
    if (sync) {
        d = r.callRemote('testSync', s);
    } else {
        d = r.callRemote('testAsync', s);
    }
    d.addCallbacks(function(result) {
        fail('Erroneously received a result: ' + result);
    }, function(err) {
        var idx = err.message.indexOf(s);
        if (idx == -1) {
            fail('Did not find expected message in error message: ' + err);
        }
    });
    return d;
}
"""

    docFactory = loaders.stan(tags.div(render=tags.directive('liveFragment'))[
        tags.form(action='#', onsubmit='return test(test_ClientToServerExceptionResult(this, true));')[
            tags.input(type='submit', value='Test Client To Server Synchronous Exception Result')],
        tags.form(action='#', onsubmit='return test(test_ClientToServerExceptionResult(this, false));')[
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

    javascriptTest = """\
function test_ServerToClientArgumentSerialization(node) {
    return Nevow.Athena.Widget.get(node).callRemote('test');
}

function test_Reverse_ServerToClientArgumentSerialization(i, f, s, o) {
    assertEquals(i, 1);
    assertEquals(f, 1.5);
    assertEquals(s, 'hello');
    assertEquals(o['world'], 'value');
}
"""

    docFactory = loaders.stan(tags.div(render=tags.directive('liveFragment'))[
        tags.form(action='#', onsubmit='return test(test_ServerToClientArgumentSerialization(this));')[
            tags.input(type='submit', value='Test Server To Client Argument Serialization')]])

    allowedMethods = {'test': True}
    def test(self):
        return self.page.callRemote('test_Reverse_ServerToClientArgumentSerialization', 1, 1.5, u'hello', {u'world': u'value'});

class ServerToClientResultSerialization(athena.LiveFragment, unittest.TestCase):
    """
    Tests that the result returned by a method invoked on the client
    by the server is correct.
    """

    javascriptTest = """\
function test_ServerToClientResultSerialization(node) {
    return Nevow.Athena.Widget.get(node).callRemote('test');
}

function test_Reverse_ServerToClientResultSerialization(i, f, s, o) {
    return [1, 1.5, 'hello', {'world': 'value'}];
}
"""

    docFactory = loaders.stan(tags.div(render=tags.directive('liveFragment'))[
        tags.form(action='#', onsubmit='return test(test_ServerToClientResultSerialization(this));')[
            tags.input(type='submit', value='Test Server To Client Result Serialization')]])

    allowedMethods = {'test': True}
    def test(self):
        def cbResults(result):
            self.assertEquals(result[0], 1)
            self.assertEquals(result[1], 1.5)
            self.assertEquals(result[2], u'hello')
            self.assertEquals(result[3], {u'world': u'value'})
        d = self.page.callRemote('test_Reverse_ServerToClientResultSerialization')
        d.addCallback(cbResults)
        return d



class AthenaTestMixin:
    jsModules = {
        u'AthenaTest': util.resource_filename('athenademo', 'athenatest.js')}

    javascriptTest = ''



class WidgetInATable(AthenaTestMixin, athena.LiveFragment):
    jsClass = u"AthenaTest.WidgetInATable"

    template = """
    <table xmlns:n='http://nevow.com/ns/nevow/0.1'>
      <tbody>
        <tr>
          <td n:render='liveFragment'>
            <button onclick='test(test_WidgetInATable(this))'>Test Widget In A Table</button>
          </td>
        </tr>
      </tbody>
    </table>
    """

    javascriptTest = """
    test_WidgetInATable = function(node) {
        Nevow.Athena.Widget.get(node).test();
    }
    """
    docFactory = loaders.xmlstr(template)



class WidgetIsATable(AthenaTestMixin, athena.LiveFragment):
    jsClass = u"AthenaTest.WidgetIsATable"

    template = """
    <table xmlns:n="http://nevow.com/ns/nevow/0.1" n:render="liveFragment">
      <tbody>
        <tr>
          <td>
            <button onclick="test(test_WidgetIsATable(this))">Test Widget Is A Table</button>
          </td>
        </tr>
      </tbody>
    </table>
    """

    javascriptTest = """
    test_WidgetIsATable = function(node) {
        Nevow.Athena.Widget.get(node).test();
    }
    """
    docFactory = loaders.xmlstr(template)



class ParentChildRelationshipTest(AthenaTestMixin, athena.LiveFragment):
    jsClass = u"AthenaTest.ChildParent"

    template = """
    <div xmlns:n='http://nevow.com/ns/nevow/0.1' n:render='liveFragment'>
        <button onclick='test(Nevow.Athena.Widget.get(this).test())'>
        Test Parent Child Relationships
        </button>
        <div n:render='childrenWidgets' />
    </div>
    """

    docFactory = loaders.xmlstr(template)

    def render_childrenWidgets(self, ctx, data):
        for i in xrange(3):
            yield ChildFragment(self.page, i)


    allowedMethods = {'getChildCount': True}
    def getChildCount(self):
        return 3



class ChildFragment(athena.LiveFragment):
    jsClass = u'AthenaTest.ChildParent'

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

    javascriptTest = ''

    docFactory = loaders.stan(tags.div(render=tags.directive('liveFragment'))[
        tags.button(onclick='test(Nevow.Athena.Widget.get(this).clicked())')[
            'Automatic athena:class attribute']])

class ImportBeforeLiteralJavascript(AthenaTestMixin, athena.LiveFragment):

    template = """
    <p xmlns:n="http://nevow.com/ns/nevow/0.1">
      <button onclick="test(test_ImportBeforeLiteralJavascript())">Test Import Before Literal Javascript</button>
      <div n:render="liveFragment">
        <script type="text/javascript">
          var ibljResult;
          if (typeof Nevow.Athena.Widget == undefined) {
              ibljResult = 0;
          } else {
              ibljResult = 1;
          }
        </script>
      </div>
    </p>
    """

    javascriptTest = """
    test_ImportBeforeLiteralJavascript = function() {
        if (ibljResult) {
            return MochiKit.Async.succeed(null);
        } else {
            return MochiKit.Async.fail(null);
        }
    }
    """

    docFactory = loaders.xmlstr(template)


class AthenaTests(athena.LivePage):
    docFactory = loaders.stan([
        tags.xml('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'),
        tags.html(**{'xmlns:nevow': 'http://nevow.com/ns/nevow/0.1'})[
            tags.head[
                tags.invisible(render=tags.directive('liveglue')),
                tags.script(type='text/javascript')["""
                function test(deferred) {
                    if (deferred == undefined || !deferred.addCallback || !deferred.addErrback) {
                        deferred = new MochiKit.Async.succeed(deferred);
                    }

                    deferred.addCallback(function (result) {
                        Divmod.log('test', 'Success!');
                    });
                    deferred.addErrback(function (err) {
                        Divmod.log('test', 'Failure: ' + err.message);
                    });
                    return false;
                }

                function fail(msg) {
                    throw new Error('Test Failure: ' + msg);
                }

                function assertEquals(a, b) {
                    if (!(a == b)) {
                        fail(a + ' != ' + b);
                    }
                }
                """],
                tags.slot('methods')],
            tags.body[
                tags.slot('tests'), tags.div(id='nevow-log')]]])

    addSlash = True

    tests = [
        # ImportBeforeLiteralJavascript _must_ be the first test.
        ImportBeforeLiteralJavascript,

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


    def renderMethods(self):
        for frgClass in self.tests:
            yield tags.script(type='text/javascript')[frgClass.javascriptTest]


    def beforeRender(self, ctx):
        ctx.fillSlots('tests', self.renderTests())
        ctx.fillSlots('methods', self.renderMethods())
