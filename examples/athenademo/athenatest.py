
from twisted.trial import unittest

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
    var d = r.callRemote('test', 1, 1.5, 'Hello world', L, O);
    d.addCallback(function(result) {
        alert('Success.');
    });
    d.addErrback(function(err) {
        alert('Failure: ' + err);
    });
};
"""

    docFactory = loaders.stan([
        tags.form(action='#', onsubmit='test_ClientToServerArgumentSerialization(this); return false;')[
            tags.input(type='submit', value='Test Client To Server Argument Serialization'),
            ]])

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


class ClientToServerResultSerialization(athena.LiveFragment, unittest.TestCase):
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
        alert('Success.');
    });
    d.addErrback(function (err) {
        alert(err);
    });
};
"""

    docFactory = loaders.stan([
        tags.form(action='#', onsubmit='test_ClientToServerResultSerialization(this); return false;')[
            tags.input(type='submit', value='Test Client To Server Result Serialization'),
            ]])

    allowedMethods = {'test': True}
    def test(self, i, f, s, l, d):
        return (i, f, s, l, d)

class AthenaTests(athena.LivePage):
    docFactory = loaders.stan(tags.html[
        tags.head[
            tags.invisible(render=tags.directive('liveglue')),
            tags.script(type='text/javascript')["""
            function assertEquals(a, b) {
                if (!(a == b)) {
                    throw new Error('Failure: ' + a + ' != ' + b);
                }
            }
            """],
            tags.slot('methods')],
        tags.body[
            tags.slot('tests')]])

    addSlash = True

    tests = [
        ClientToServerArgumentSerialization,
        ClientToServerResultSerialization,
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
