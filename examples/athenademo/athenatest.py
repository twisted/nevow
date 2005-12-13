
from twisted.trial import unittest
from twisted.internet import defer

from nevow import athena, loaders, tags

class ClientToServerArgumentSerialization(athena.LiveFragment, unittest.TestCase):
    """
    Tests that arguments passed to a method on the server are properly
    received.
    """

    javascriptTest = """\
function test_ClientToServerArgumentSerialization(node) {
    var r = Nevow.Athena.refByDOM(node);
    var L = [1, 1.5, 'Hello world'];
    var O = {'hello world': 'object value'};
    return r.callRemote('test', 1, 1.5, 'Hello world', L, O);
};
"""

    docFactory = loaders.stan(tags.div(**athena.liveFragmentID)[
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
    var r = Nevow.Athena.refByDOM(node);
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

    docFactory = loaders.stan(tags.div(**athena.liveFragmentID)[
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
    var r = Nevow.Athena.refByDOM(node);
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

    docFactory = loaders.stan(tags.div(**athena.liveFragmentID)[
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
    return Nevow.Athena.refByDOM(node).callRemote('test');
}

function test_Reverse_ServerToClientArgumentSerialization(i, f, s, o) {
    assertEquals(i, 1);
    assertEquals(f, 1.5);
    assertEquals(s, 'hello');
    assertEquals(o['world'], 'value');
}
"""

    docFactory = loaders.stan(tags.div(**athena.liveFragmentID)[
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
    return Nevow.Athena.refByDOM(node).callRemote('test');
}

function test_Reverse_ServerToClientResultSerialization(i, f, s, o) {
    return [1, 1.5, 'hello', {'world': 'value'}];
}
"""

    docFactory = loaders.stan(tags.div(**athena.liveFragmentID)[
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

class WidgetInATable(athena.LiveFragment):
    template = """
    <table xmlns:n="http://nevow.com/ns/nevow/0.1" xmlns:athena="http://divmod.org/ns/athena/0.7">
      <tbody>
        <tr>
          <td>
            <n:attr name="athena:id"><n:slot name="athena:id"/></n:attr>
            <n:attr name="athena:class">WidgetInATable</n:attr>
            <button onclick="test_WidgetInATable(this)">Test Widget In A Table</button>
          </td>
        </tr>
      </tbody>
    </table>
    """
    javascriptTest = """
    test_WidgetInATable = function(node) {
        try {
            Nevow.Athena.Widget.get(node).test();
            alert("Success!");
        } catch(err) {
            alert("Failure: " + err.message);
        }
    }
    WidgetInATable = Nevow.Athena.Widget.subclass();
    WidgetInATable.prototype.test = function() {
    }
    """
    docFactory = loaders.xmlstr(template)

class WidgetIsATable(athena.LiveFragment):
    template = """
    <table xmlns:n="http://nevow.com/ns/nevow/0.1" xmlns:athena="http://divmod.org/ns/athena/0.7">
      <n:attr name="athena:id"><n:slot name="athena:id"/></n:attr>
      <n:attr name="athena:class">WidgetIsATable</n:attr>
      <tbody>
        <tr>
          <td>
            <button onclick="test_WidgetIsATable(this)">Test Widget Is A Table</button>
          </td>
        </tr>
      </tbody>
    </table>
    """
    javascriptTest = """
    test_WidgetIsATable = function(node) {
        try {
            Nevow.Athena.Widget.get(node).test();
            alert("Success!");
        } catch(err) {
            alert("Failure: " + err.message);
        }
    }
    WidgetIsATable = Nevow.Athena.Widget.subclass();
    WidgetIsATable.prototype.test = function() {
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
                    deferred.addCallback(function (result) {
                        alert('Success!');
                    });
                    deferred.addErrback(function (err) {
                        alert('Failure: ' + err.message);
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
        ClientToServerArgumentSerialization,
        ClientToServerResultSerialization,
        ClientToServerExceptionResult,
        ServerToClientArgumentSerialization,
        ServerToClientResultSerialization,
        WidgetInATable,
        WidgetIsATable,
        ]

    def renderTests(self):
        for frgClass in self.tests:
            frg = frgClass()
            frg.page = self
            yield frg

    def renderMethods(self):
        for frgClass in self.tests:
            yield tags.script(type='text/javascript')[frgClass.javascriptTest]

    def beforeRender(self, ctx):
        ctx.fillSlots('tests', self.renderTests())
        ctx.fillSlots('methods', self.renderMethods())
