
import os, sets
from itertools import izip
from xml.dom.minidom import parseString

from twisted.trial import unittest
from twisted.python import util
from twisted.internet.defer import Deferred
from twisted.application.service import IServiceMaker
from twisted.application.internet import TCPServer
from twisted.python.reflect import qual
from twisted.python.usage import UsageError
from twisted.plugin import IPlugin

from nevow import athena, rend, tags, flat, loaders
from nevow.loaders import stan
from nevow.athena import LiveElement
from nevow.appserver import NevowSite
from nevow.inevow import IRequest
from nevow.context import WovenContext
from nevow.testutil import FakeRequest, renderLivePage
from nevow._widget_plugin import ElementRenderingLivePage

from twisted.plugins.nevow_widget import widgetServiceMaker


class _TestJSModule(athena.JSModule):
    extractCounter = 0

    def _extractImports(self, *a, **kw):
        self.extractCounter += 1
        return super(_TestJSModule, self)._extractImports(*a, **kw)


class Utilities(unittest.TestCase):

    testModuleImpl = '''\
lalal this is javascript honest
// uh oh!  a comment!  gee I wish javascript had an import system
// import ExampleModule
here is some more javascript code
// import Another
// import Module
the end
'''


    def testJavaScriptModule(self):
        testModuleFilename = self.mktemp()
        testModule = file(testModuleFilename, 'w')
        testModule.write(self.testModuleImpl)
        testModule.close()

        modules = {'testmodule': testModuleFilename}
        m1 = athena.JSModule.getOrCreate('testmodule', modules)
        m2 = athena.JSModule.getOrCreate('testmodule', modules)
        self.assertEquals(m1.name, 'testmodule')

        self.assertIdentical(m1, m2)

        modules['Another'] = self.mktemp()
        anotherModule = file(modules['Another'], 'w')
        anotherModule.write('// import SecondaryDependency\n')
        anotherModule.close()

        modules['ExampleModule'] = self.mktemp()
        exampleModule = file(modules['ExampleModule'], 'w')
        exampleModule.write('// import ExampleDependency\n')
        exampleModule.close()

        modules['Module'] = self.mktemp()
        moduleModule = file(modules['Module'], 'w')
        moduleModule.close()

        # Stub these out with an empty file
        modules['SecondaryDependency'] = modules['Module']
        modules['ExampleDependency'] = modules['Module']

        deps = [d.name for d in m1.dependencies()]
        deps.sort()
        self.assertEquals(deps, ['Another', 'ExampleModule', 'Module'])

        depgraph = {
            'Another': ['SecondaryDependency'],
            'ExampleModule': ['ExampleDependency'],
            'Module': [],
            'testmodule': ['Another', 'ExampleModule', 'Module'],
            'SecondaryDependency': [],
            'ExampleDependency': []}

        allDeps = [d.name for d in m1.allDependencies()]
        for m in allDeps:
            modDeps = depgraph[m]
            for d in modDeps:
                # All dependencies should be loaded before the module
                # that depends upon them.
                self.assertIn(d, allDeps)
                self.assertIn(m, allDeps)
                self.failUnless(allDeps.index(d) < allDeps.index(m))


    def test_dependencyCaching(self):
        """
        Test that dependency caching works as expected.
        """
        testModuleFilename = self.mktemp()
        testModule = file(testModuleFilename, 'w')
        testModule.write('')
        testModule.close()

        modules = {'testmodule': testModuleFilename}
        m = _TestJSModule('testmodule', modules)

        deps = list(m.dependencies())
        self.assertEquals(m.extractCounter, 1)

        deps2 = list(m.dependencies())
        self.assertEquals(m.extractCounter, 1)

        newTime = m.lastModified
        os.utime(testModuleFilename, (newTime + 1, newTime + 1))
        deps3 = list(m.dependencies())
        self.assertEquals(m.extractCounter, 2)

    def test_renderJavascriptModules(self):
        """
        The parent of the javascript modules is not renderable itself.  Make
        sure it's a 404.
        """
        m = athena.JSModules({})
        self.failUnless(isinstance(m.renderHTTP(None), rend.FourOhFour))


    def test_lookupNonExistentJavascriptModule(self):
        """
        Test that the parent resource for all JavaScript modules returns the
        correct thing when asked for a module.
        """
        m = athena.JSModules({'name': 'value'})
        self.assertEquals(m.locateChild(None, ('key',)), rend.NotFound)


    def test_lookupJavascriptModule(self):
        """
        Test that retrieving a JavaScript module which actually exists returns
        whatever the resourceFactory method produces.
        """
        m = athena.JSModules({'name': 'value'})
        m.resourceFactory = sets.Set
        resource, segments = m.locateChild(None, ('name',))
        self.assertEquals(segments, [])
        self.assertEquals(resource, sets.Set('value'))


    def testPackage(self):
        baseDir = util.sibpath(__file__, 'test_package')
        package = athena.AutoJSPackage(baseDir)

        def _f(*sib):
            return os.path.join(baseDir, *sib)

        expected = {u'Foo': _f('Foo', '__init__.js'),
                    u'Foo.Bar': _f('Foo', 'Bar.js'),
                    u'Foo.Baz': util.sibpath(athena.__file__, 'empty.js'),
                    u'Foo.Baz.Quux': _f('Foo', 'Baz', 'Quux.js')}

        for module, path in expected.iteritems():
            self.assertIn(module, package.mapping)
            self.assertEquals(package.mapping[module], path)


    def testPackageDeps(self):
        modules = {u'Foo': self.mktemp(), u'Foo.Bar': self.mktemp()}
        file(modules[u'Foo'], 'wb').close()
        file(modules[u'Foo.Bar'], 'wb').close()
        foo = athena.JSModule.getOrCreate(u'Foo', modules)
        bar = athena.JSModule.getOrCreate(u'Foo.Bar', modules)
        self.assertIn(foo, bar.allDependencies())



    def test_preprocessorCollection(self):
        """
        Test that preprocessors from all the base classes of an instance are
        found, and that a preprocessor instance attribute overrides all of
        these.
        """
        a, b, c = object(), object(), object()

        class Base(object):
            preprocessors = [a]

        class OtherBase(object):
            preprocessors = [b]

        class Derived(Base, OtherBase):
            preprocessors = [c]

        inst = Derived()
        self.assertEqual(
            rend._getPreprocessors(inst),
            [a, b, c])

        d = object()
        inst.preprocessors = [d]
        self.assertEqual(
            rend._getPreprocessors(inst),
            [d])


    def test_handlerMacro(self):
        """
        Test that the handler macro rewrites athena:handler nodes to the
        appropriate JavaScript.
        """
        expectedOutput = (
            'return Nevow.Athena.Widget.handleEvent('
            'this, &quot;onclick&quot;, &quot;bar&quot;);')
        tag = tags.span[athena.handler(event='onclick', handler='bar')]
        mutated = athena._rewriteEventHandlerToAttribute(tag)
        output = flat.flatten(mutated)
        self.assertEquals(
            output,
            '<span onclick="' + expectedOutput + '"></span>')


    def test_handlerMacroAgainstList(self):
        """
        Macros need to be runnable on lists of things.  Make sure the handler
        macro is.
        """
        tag = ["hello", " ", "world"]
        self.assertEquals(
            athena._rewriteEventHandlerToAttribute(tag),
            tag)


    def test_athenaIdRewriting(self):
        """
        Test that IDs are correctly rewritten in id, for, and headers
        attributes.
        """
        tag = [tags.label(_for='foo'),
               tags.input(id='foo'),
               tags.th(headers=''),
               tags.th(headers='foo'),
               tags.td(headers='foo bar'),
               tags.td(headers='foo bar baz')]
        element = athena.LiveElement(docFactory=loaders.stan(tag))
        page = athena.LivePage(docFactory=loaders.stan(element))
        element.setFragmentParent(page)

        def _verifyRendering(result):
            self.assertIn('<input id="athenaid:%s-foo"' % (element._athenaID,), result)
            self.assertIn('<label for="athenaid:%s-foo"' % (element._athenaID,), result)
            self.assertIn('<th headers=""', result)
            self.assertIn('<th headers="athenaid:%s-foo"' % (
                element._athenaID,), result)
            self.assertIn('<td headers="athenaid:%s-foo athenaid:%s-bar"' % (
                element._athenaID, element._athenaID), result)
            self.assertIn('<td headers="athenaid:%s-foo athenaid:%s-bar athenaid:%s-baz"' % (
                element._athenaID, element._athenaID, element._athenaID), result)

        return renderLivePage(page).addCallback(_verifyRendering)


    def _render(self, page):
        """
        Test helper which tries to render the given page.
        """
        ctx = WovenContext()
        req = FakeRequest()
        ctx.remember(req, IRequest)
        return page.renderHTTP(ctx).addCallback(lambda ign: req.v)


    def test_elementPreprocessors(self):
        """
        Make sure that LiveElements have their preprocessors applied to their
        document.
        """
        preprocessed = []

        tag = tags.span
        element = athena.LiveElement(docFactory=loaders.stan(tag))
        page = athena.LivePage(docFactory=loaders.stan(element))
        element.preprocessors = [preprocessed.append]
        element.setFragmentParent(page)
        renderDeferred = self._render(page)
        def rendered(result):
            page.action_close(None)
            self.assertEquals(preprocessed, [[tag]])
        renderDeferred.addCallback(rendered)
        return renderDeferred



class StandardLibraryTestCase(unittest.TestCase):
    """
    Test all the Nevow JavaScript "standard library" modules.
    """
    def setUp(self):
        self.deps = athena.JSDependencies()


    def _importTest(self, moduleName):
        mod = self.deps.getModuleForName(moduleName)
        inspect = [dep for dep in mod.allDependencies() if dep.name == moduleName]
        self.failUnless(inspect)


    def test_divmodImport(self):
        """
        Test that Divmod can be imported.
        """
        return self._importTest('Divmod')


    def test_baseImport(self):
        """
        Test that Divmod.Base can be imported.
        """
        return self._importTest('Divmod.Base')


    def test_deferImport(self):
        """
        Test that Divmod.Defer can be imported.
        """
        return self._importTest('Divmod.Defer')


    def test_inspectImport(self):
        """
        Test that Divmod.Inspect can be imported.
        """
        return self._importTest('Divmod.Inspect')


    def test_runtimeImport(self):
        """
        Test that Divmod.Runtime can be imported.
        """
        return self._importTest('Divmod.Runtime')


    def test_xmlImport(self):
        """
        Test that Divmod.XML can be imported.
        """
        return self._importTest('Divmod.XML')


    def test_nevowImport(self):
        """
        Test that Nevow can be imported.
        """
        return self._importTest('Nevow')


    def test_athenaImport(self):
        """
        Test that Nevow.Athena can be imported.
        """
        return self._importTest('Nevow.Athena')


    def test_testImport(self):
        """
        Test that Nevow.Athena can be imported.
        """
        return self._importTest('Nevow.Athena.Test')


    def test_tagLibraryImport(self):
        """
        Test that Nevow.TagLibrary can be imported.
        """
        return self._importTest('Nevow.TagLibrary')


    def test_tabbedPaneImport(self):
        """
        Test that Nevow.TagLibrary.TabbedPane can be imported.
        """
        return self._importTest('Nevow.TagLibrary.TabbedPane')



class TestFragment(athena.LiveFragment):
    pass

class Nesting(unittest.TestCase):

    def testFragmentNesting(self):
        lp = athena.LivePage()
        tf1 = TestFragment()
        tf2 = TestFragment()

        tf1.setFragmentParent(lp)
        tf2.setFragmentParent(tf1)

        self.assertEquals(lp.liveFragmentChildren, [tf1])
        self.assertEquals(tf1.liveFragmentChildren, [tf2])
        self.assertEquals(tf2.liveFragmentChildren, [])
        self.assertEquals(tf2.fragmentParent, tf1)
        self.assertEquals(tf1.fragmentParent, lp)

        self.assertEquals(tf2.page, lp)
        self.assertEquals(tf1.page, lp)


    def testInsideOutFragmentNesting(self):
        """
        Test that even if LiveFragments have their parents assigned from the
        inside out, parent/child relationships still end up correct.
        """
        innerFragment = TestFragment()
        outerFragment = TestFragment()
        page = athena.LivePage()

        innerFragment.setFragmentParent(outerFragment)
        outerFragment.setFragmentParent(page)

        self.assertEquals(page.liveFragmentChildren, [outerFragment])
        self.assertEquals(outerFragment.fragmentParent, page)
        self.assertEquals(outerFragment.page, page)

        self.assertEquals(outerFragment.liveFragmentChildren, [innerFragment])
        self.assertEquals(innerFragment.fragmentParent, outerFragment)
        self.assertEquals(innerFragment.page, page)



class Tracebacks(unittest.TestCase):
    frames = (('Error()', '', 0),
              ('someFunction()', 'http://somesite.com:8080/someFile', 42),
              ('anotherFunction([object Object])', 'http://user:pass@somesite.com:8080/someOtherFile', 69))

    stack = '\n'.join(['%s@%s:%d' % frame for frame in frames])

    exc = {u'name': 'SomeError',
           u'message': 'An error occurred.',
           u'stack': stack}

    def testStackParsing(self):
        p = athena.parseStack(self.stack)
        for iframe, oframe in izip(self.frames[::-1], p):
            self.assertEquals(oframe, iframe)

    def testStackLengthAndOrder(self):
        f = athena.getJSFailure(self.exc, {})
        self.assertEqual(len(f.frames), len(self.frames))
        self.assertEqual(f.frames[0][0], self.frames[-1][0])



class _DelayedCall(object):
    def __init__(self, container, element):
        self.container = container
        self.element = element

    def cancel(self):
        self.container.remove(self.element)


def mappend(transport):
    def send((ack, messages)):
        transport.append(messages[:])
    return send

class Transport(unittest.TestCase):
    """
    Test the various states and events which can occur that are related to the
    server's ability to convey a message to the client.

    This includes things such as the receipt of a new request or the depletion
    of an existing request.
    """

    theMessage = "Immediately Send This Message"

    connectTimeout = 1
    transportlessTimeout = 2
    idleTimeout = 3

    clientID = 'FAKE ATHENA PAGE'

    def liveTransportMessageReceived(self, ctx, outgoingMessage):
        self.outgoingMessages.append((ctx, outgoingMessage))

    def setUp(self):
        self.transport = []
        self.scheduled = []
        self.events = []
        self.outgoingMessages = []
        self.rdm = athena.ReliableMessageDelivery(
            self,
            connectTimeout=self.connectTimeout,
            transportlessTimeout=self.transportlessTimeout,
            idleTimeout=self.idleTimeout,
            connectionLost=lambda reason: self.events.append(reason),
            scheduler=self._schedule)


    def _schedule(self, n, f, *a, **kw):
        """
        Deterministic, rigidly controlled stand-in for reactor.callLater().
        """
        t = (n, f, a, kw)
        self.scheduled.append(t)
        return _DelayedCall(self.scheduled, t)


    def testSendMessageImmediately(self):
        """
        Test that if there is an output channel for messages, trying to send a
        message immediately does so, consuming the output channel.
        """
        self.rdm.addOutput(mappend(self.transport))
        self.rdm.addMessage(self.theMessage)
        self.assertEquals(self.transport, [[(0, self.theMessage)]])
        self.rdm.addMessage(self.theMessage)
        self.assertEquals(self.transport, [[(0, self.theMessage)]])


    def testSendMessageQueued(self):
        """
        Test that if there is no output channel when a message is sent, it will
        be sent once an output channel becomes available.
        """
        self.rdm.addMessage(self.theMessage)
        self.rdm.addOutput(mappend(self.transport))
        self.assertEquals(self.transport, [[(0, self.theMessage)]])


    def testMultipleQueuedMessages(self):
        """
        Test that if there are several messages queued they are all sent at
        once when an output channel becomes available.
        """
        self.rdm.addMessage(self.theMessage)
        self.rdm.addMessage(self.theMessage.encode('hex'))
        self.rdm.addOutput(mappend(self.transport))
        self.assertEquals(self.transport, [[(0, self.theMessage), (1, self.theMessage.encode('hex'))]])


    def testMultipleQueuedOutputs(self):
        """
        Test that if there are several output channels available, each message
        only consumes the first of them.
        """
        secondTransport = []
        self.rdm.addOutput(mappend(self.transport))
        self.rdm.addOutput(mappend(secondTransport))
        self.rdm.addMessage(self.theMessage)
        self.assertEquals(self.transport, [[(0, self.theMessage)]])
        self.assertEquals(secondTransport, [])


    def testMessageRedelivery(self):
        """
        Test that outputs added while there are unacknowledged messages result
        in re-transmits of those messages.
        """
        secondMessage = self.theMessage + '-2'
        secondTransport = []
        thirdTransport = []
        fourthTransport = []
        self.rdm.addMessage(self.theMessage)
        self.rdm.addMessage(secondMessage)
        self.rdm.addOutput(mappend(self.transport))
        self.assertEquals(self.transport, [[(0, self.theMessage), (1, secondMessage)]])
        self.rdm.addOutput(mappend(secondTransport))
        self.assertEquals(secondTransport, [[(0, self.theMessage), (1, secondMessage)]])
        self.rdm.basketCaseReceived(None, [0, []])
        self.rdm.addOutput(mappend(thirdTransport))
        self.assertEquals(thirdTransport, [[(1, secondMessage)]])
        self.rdm.basketCaseReceived(None, [1, []])
        self.rdm.addOutput(mappend(fourthTransport))
        self.assertEquals(fourthTransport, [])


    def testConnectTimeout(self):
        """
        Test that a connection timeout is set up which, if allowed to expire,
        will cause notification of the fact that the connection was never
        established.
        """
        n, f, a, kw = self.scheduled.pop()
        self.failIf(self.scheduled, "Too many tasks scheduled.")

        self.assertEquals(n, self.connectTimeout)
        f(*a, **kw)

        self.assertEquals(len(self.events), 1)
        self.events[0].trap(athena.ConnectFailed)

        self.failIf(self.scheduled, "Unexpected task scheduled after connect failed.")


    def testConnectSucceeds(self):
        """
        Test that the connection timeout is cancelled when an output channel is
        added.
        """
        self.failUnless(self.scheduled, "No connect timeout scheduled.") # Sanity check
        self.rdm.addOutput(mappend(self.transport))
        n, f, a, kw = self.scheduled.pop()
        self.assertEquals(n, self.idleTimeout)
        self.failIf(self.scheduled, "Output channel added but there is still a task pending.")
        self.assertEquals(self.transport, [], "Received unexpected output.")


    def testOutputConsumedMessageTimeout(self):
        """
        Test that a timeout is set up when the last output is used and that if
        it expires, notification of the connection being lost is delivered.  In
        particular, test that if there is a message waiting and a new output is
        added, the timeout behavior is correct.
        """
        self.rdm.addMessage(self.theMessage)
        self.rdm.addOutput(mappend(self.transport))

        n, f, a, kw = self.scheduled.pop()
        self.failIf(self.scheduled, "Too many tasks scheduled.")

        self.assertEquals(n, self.transportlessTimeout)
        f(*a, **kw)

        self.assertEquals(len(self.events), 1)
        self.events[0].trap(athena.ConnectionLost)

        self.failIf(self.scheduled, "Unexpected task scheduled after connection lost.")


    def testMessageConsumedOutputTimeout(self):
        """
        Very similar to testOutputConsumedMessageTimeout, but test the case
        where there is an existing output and a message is added, causing it
        to be used.
        """
        self.rdm.addOutput(mappend(self.transport))
        self.rdm.addMessage(self.theMessage)

        n, f, a, kw = self.scheduled.pop()
        self.failIf(self.scheduled, "Too many tasks scheduled.")

        self.assertEquals(n, self.transportlessTimeout)
        f(*a, **kw)

        self.assertEquals(len(self.events), 1)
        self.events[0].trap(athena.ConnectionLost)

        self.failIf(self.scheduled, "Unexpected task scheduled after connection lost.")


    def testOutputConnectionAdded(self):
        """
        Test that the timeout created when the last output is used is cancelled
        when a new output is added.
        """
        self.rdm.addMessage(self.theMessage)
        self.rdm.addOutput(mappend(self.transport))

        self.assertEquals(len(self.scheduled), 1, "Transportless timeout not created.")
        n, f, a, kw = self.scheduled[0]
        self.assertEquals(n, self.transportlessTimeout, "Unexpected task still scheduled after output added.")

        self.rdm.basketCaseReceived(None, [0, []])

        n, f, a, kw = self.scheduled.pop()
        self.assertEquals(n, self.idleTimeout)

        self.failIf(self.scheduled, "Unexpected task still scheduled after output added.")
        self.failIf(self.events, "Unexpectedly received some kind of event.")


    def testIdleOutputTimeout(self):
        """
        Test that outputs are discarded with an empty message list if they are
        not used within the specified interval.
        """
        self.rdm.addOutput(mappend(self.transport))

        n, f, a, kw = self.scheduled.pop()
        self.assertEquals(n, self.idleTimeout)
        self.failIf(self.scheduled, "Unexpected tasks still scheduled in addition to idle timeout task.")

        f(*a, **kw)

        self.assertEquals(self.transport, [[]])


    def testIdleTimeoutStartsOutputlessTimeout(self):
        """
        Test that if the last output is removed due to idleness that another
        timeout for the lack of any outputs is started.
        """
        self.rdm.addOutput(mappend(self.transport))

        n, f, a, kw = self.scheduled.pop()
        self.assertEquals(n, self.idleTimeout)
        f(*a, **kw)

        self.failIf(self.events, "Unexpectedly received some events.")

        n, f, a, kw = self.scheduled.pop()
        self.assertEquals(n, self.transportlessTimeout)
        f(*a, **kw)

        self.assertEquals(len(self.events), 1)
        self.events[0].trap(athena.ConnectionLost)


    def testPreConnectPause(self):
        """
        Test that no outputs are used while the reliable message
        deliverer is paused before the first connection is made.
        """
        self.rdm.pause()
        self.rdm.addOutput(mappend(self.transport))

        # The connection timeout should have been cancelled and
        # replaced with an idle timeout.
        self.assertEquals(len(self.scheduled), 1)
        n, f, a, kw = self.scheduled[0]
        self.assertEquals(n, self.idleTimeout)

        self.rdm.addMessage(self.theMessage)
        self.assertEquals(self.transport, [])

        self.rdm.unpause()
        self.assertEquals(self.transport, [[(0, self.theMessage)]])


    def testTransportlessPause(self):
        """
        Test that if the message deliverer is paused while it has no
        transports, it remains so and does not use an output which is
        added to it.
        """
        self.rdm.addOutput(mappend(self.transport))

        self.rdm.pause()
        self.rdm.addMessage(self.theMessage)
        self.assertEquals(self.transport, [])

        self.rdm.unpause()
        self.assertEquals(self.transport, [[(0, self.theMessage)]])


    def testMessagelessPause(self):
        """
        Test that if the message deliverer is paused while it has no
        messages, it remains so and does not use an output when a
        message is added.
        """
        self.rdm.addOutput(mappend(self.transport))

        self.rdm.pause()
        self.rdm.addMessage(self.theMessage)
        self.assertEquals(self.transport, [])

        self.rdm.unpause()
        self.assertEquals(self.transport, [[(0, self.theMessage)]])


    def testStaleMessages(self):
        """
        Test that if an older basket case with fewer messages in it arrives
        after a more recent, complete basket case is processed, that it is
        properly disregarded.
        """
        self.rdm.basketCaseReceived(
            None,
            [-1, [[0, self.theMessage],
                  [1, self.theMessage + "-1"],
                  [2, self.theMessage + "-2"]]])
        self.assertEquals(
            self.outgoingMessages,
            [(None, self.theMessage),
             (None, self.theMessage + "-1"),
             (None, self.theMessage + "-2")])
        self.outgoingMessages = []

        self.rdm.basketCaseReceived(
            None,
            [-1, [[1, self.theMessage + "-1"]]])
        self.assertEquals(
            self.outgoingMessages,
            [])

        self.rdm.basketCaseReceived(
            None,
            [-1, [[2, self.theMessage + "-2"]]])
        self.assertEquals(
            self.outgoingMessages,
            [])


    def testClosing(self):
        """
        Test that closing a reliable message deliverer causes all of outs
        remaining outputs to be used up with a close message and that any
        future outputs added to it are immediately used in a similar
        manner.
        """
        self.rdm.addOutput(mappend(self.transport))
        self.rdm.addOutput(mappend(self.transport))
        self.rdm.close()
        self.assertEquals(self.transport, [[(0, (athena.CLOSE, []))], [(0, (athena.CLOSE, []))]])

        self.transport = []
        self.rdm.addOutput(mappend(self.transport))
        self.assertEquals(self.transport, [[(0, (athena.CLOSE, []))]])


    def testCloseBeforeConnect(self):
        """
        Test that closing the reliable message deliverer before a connection is
        ever established properly cleans up any timeouts.
        """
        self.rdm.close()
        self.failIf(self.scheduled, "Expected no scheduled calls.")


class LiveMixinTestsMixin:
    """
    Test-method defining mixin class for L{LiveElement} and L{LiveFragment} testing.

    @ivar elementFactory: No-argument callable which returns an object against
    which tests will be run.
    """
    def elementFactory(self):
        raise NotImplementedError("%s did not implement elementFactory" % (self,))


    def test_localDetach(self):
        """
        Verify that L{_athenaDetachServer} removes the element from its parent
        and disassociates it from the page locally.
        """
        page = athena.LivePage()
        element = self.elementFactory()
        element.setFragmentParent(page)
        element._athenaDetachServer()
        self.assertNotIn(element, page.liveFragmentChildren)
        self.assertIdentical(element.fragmentParent, None)
        self.assertIdentical(element.page, None)


    def test_localDetachWithChildren(self):
        """
        Similar to L{test_localDetach}, but cover the case where the removed
        element has a child of its own and verify that that child is also
        detached.
        """
        page = athena.LivePage()
        element = self.elementFactory()
        element.setFragmentParent(page)
        child = self.elementFactory()
        child.setFragmentParent(element)
        element._athenaDetachServer()
        self.assertNotIn(element, page.liveFragmentChildren)
        self.assertIdentical(element.fragmentParent, None)
        self.assertIdentical(element.page, None)
        self.assertNotIn(child, element.liveFragmentChildren)
        self.assertIdentical(child.fragmentParent, None)
        self.assertIdentical(child.page, None)


    def test_detach(self):
        """
        Verify that L{detach} informs the client of the event and returns a
        Deferred which fires when the client acknowledges this.
        """
        page = athena.LivePage()
        element = self.elementFactory()
        element.setFragmentParent(page)

        calls = []
        def callRemote(methodName):
            d = Deferred()
            calls.append((methodName, d))
            return d
        element.callRemote = callRemote

        d = element.detach()
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], '_athenaDetachClient')
        calls[0][1].callback(None)
        self.assertNotIn(element, page.liveFragmentChildren)
        self.assertIdentical(element.fragmentParent, None)
        self.assertIdentical(element.page, None)


    def test_detachWithChildren(self):
        """
        Similar to L{test_detach}, but cover the case where the removed element
        has a child of its own and verify that that child is also detached.
        """
        page = athena.LivePage()
        element = self.elementFactory()
        element.setFragmentParent(page)
        child = self.elementFactory()
        child.setFragmentParent(element)

        calls = []
        def callRemote(methodName):
            d = Deferred()
            calls.append((methodName, d))
            return d
        element.callRemote = callRemote
        child.callRemote = callRemote

        d = element.detach()
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], '_athenaDetachClient')
        calls[0][1].callback(None)
        self.assertNotIn(element, page.liveFragmentChildren)
        self.assertIdentical(element.fragmentParent, None)
        self.assertIdentical(element.page, None)
        self.assertNotIn(child, element.liveFragmentChildren)
        self.assertIdentical(child.fragmentParent, None)
        self.assertIdentical(child.page, None)


    def test_localDetachCallback(self):
        """
        Verify that C{detached} is called when C{_athenaDetachServer} is
        called.
        """
        page = athena.LivePage()
        element = self.elementFactory()
        element.setFragmentParent(page)

        detachCall = []
        def detached():
            detachCall.append((element.fragmentParent, element.page))
        element.detached = detached

        element._athenaDetachServer()
        self.assertEqual(detachCall, [(None, None)])


    def test_detachCallback(self):
        """
        Verify that C{detached} is called C{detach} is called locally.
        """
        page = athena.LivePage()
        element = self.elementFactory()
        element.setFragmentParent(page)

        detachCall = []
        def detached():
            detachCall.append((element.fragmentParent, element.page))
        element.detached = detached

        calls = []
        def callRemote(methodName):
            d = Deferred()
            calls.append(d)
            return d
        element.callRemote = callRemote

        d = element.detach()

        self.assertEqual(detachCall, [])
        calls[0].callback(None)
        self.assertEqual(detachCall, [(None, None)])



class LiveElementTests(LiveMixinTestsMixin, unittest.TestCase):
    """
    Tests for L{nevow.athena.LiveElement}.
    """
    elementFactory = athena.LiveElement



class LiveFragmentTests(LiveMixinTestsMixin, unittest.TestCase):
    """
    Tests for L{nevow.athena.LiveFragment}.
    """
    elementFactory = athena.LiveFragment



class DummyLiveElement(LiveElement):
    """
    Behaviorless Athena element used to test C{makeService}.
    """



class WidgetSubcommandTests(unittest.TestCase):
    """
    Test the twistd subcommand which runs a server to render a single Athena
    widget.
    """
    def test_portOption(self):
        """
        Verify that the --port option adds an integer to the Options' port key.
        """
        options = widgetServiceMaker.options()
        options['element'] = DummyLiveElement()
        options.parseOptions(['--port', '3874'])
        self.assertEqual(options['port'], 3874)
        options.parseOptions(['--port', '65535'])
        self.assertEqual(options['port'], 65535)


    def test_invalidPortOption(self):
        """
        Verify that non-integer and out-of-range port numbers are rejected.
        """
        options = widgetServiceMaker.options()
        options['element'] = DummyLiveElement()
        self.assertRaises(UsageError, options.parseOptions, ['--port', 'hello world'])
        self.assertRaises(UsageError, options.parseOptions, ['--port', '-7'])
        self.assertRaises(UsageError, options.parseOptions, ['--port', '70000'])
        self.assertRaises(UsageError, options.parseOptions, ['--port', '65536'])


    def test_widgetOption(self):
        """
        Verify that the --element option adds a class to the Options' element
        key.
        """
        options = widgetServiceMaker.options()
        options.parseOptions(['--element', qual(DummyLiveElement)])
        self.failUnless(isinstance(options['element'], DummyLiveElement))


    def test_invalidWidgetOption(self):
        """
        Verify that specifying a non-existent class is rejected.
        """
        options = widgetServiceMaker.options()
        self.assertRaises(
            UsageError,
            options.parseOptions, ['--element', qual(DummyLiveElement) + 'xxx'])
        self.assertRaises(
            UsageError,
            options.parseOptions, ['--element', '-'])



    def test_invalidMissingWidget(self):
        """
        Verify that a missing widget class is rejected.
        """
        options = widgetServiceMaker.options()
        self.assertRaises(UsageError, options.parseOptions, [])


    def test_defaultPort(self):
        """
        Verify that the default port number is 8080.
        """
        options = widgetServiceMaker.options()
        options['element'] = DummyLiveElement()
        options.parseOptions([])
        self.assertEqual(options['port'], 8080)


    def test_providesInterfaces(self):
        """
        Verify that the necessary interfaces for the object to be found as a
        twistd subcommand plugin are provided.
        """
        self.failUnless(IPlugin.providedBy(widgetServiceMaker))
        self.failUnless(IServiceMaker.providedBy(widgetServiceMaker))


    def test_makeService(self):
        """
        Verify that the L{IService} creation function returns a service which
        will run a Nevow site.
        """
        service = widgetServiceMaker.makeService({
                'element': DummyLiveElement(),
                'port': 8080,
                })
        self.failUnless(isinstance(service, TCPServer))
        self.assertEqual(service.args[0], 8080)
        self.failUnless(isinstance(service.args[1], NevowSite))
        self.failUnless(isinstance(service.args[1].resource, ElementRenderingLivePage))
        self.failUnless(isinstance(service.args[1].resource.element, DummyLiveElement))


    def test_livePageRendering(self):
        """
        Verify that an L{ElementRenderingLivePage} instantiated with a
        particular LiveElement properly renders that element.
        """
        element = DummyLiveElement()
        element.jsClass = u'Dummy.ClassName'
        element.docFactory = stan('the element')
        page = ElementRenderingLivePage(element)
        renderDeferred = renderLivePage(page)
        def cbRendered(result):
            document = parseString(result)
            titles = document.getElementsByTagName('title')
            self.assertEqual(len(titles), 1)
            self.assertEqual(titles[0].firstChild.nodeValue, DummyLiveElement.__name__)
            divs = document.getElementsByTagName('div')
            self.assertEqual(len(divs), 1)
            self.assertEqual(divs[0].firstChild.nodeValue, 'the element')
        renderDeferred.addCallback(cbRendered)
        return renderDeferred
