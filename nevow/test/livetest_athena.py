# Copyright (c) 2004-2007 Divmod.
# See LICENSE for details.

"""
Browser integration tests for Athena.
"""

from zope.interface import implements

from twisted.internet import defer

from nevow.inevow import IAthenaTransportable
from nevow import loaders, tags, athena
from nevow.page import Element, renderer
from nevow.athena import expose, LiveElement
from nevow.livetrial import testcase
from nevow.test import test_json
from nevow.testutil import CSSModuleTestMixin

class WidgetInitializerArguments(testcase.TestCase):
    """
    Test that the arguments represented by the list returned by
    getInitialArguments are properly passed to the widget class's __init__
    method.
    """
    jsClass = 'Nevow.Athena.Tests.WidgetInitializerArguments'

    _args = [1, "two", [3.0 for four in range(5)]]

    def getInitialArguments(self):
        return self._args

    def test(self, args):
        self.assertEqual(self._args, args)
    expose(test)



class CallRemoteTestCase(testcase.TestCase):
    """
    Test the callRemote method of Widgets.
    """
    jsClass = 'Nevow.Athena.Tests.CallRemoteTestCase'



class ClientToServerArgumentSerialization(testcase.TestCase):
    """
    Tests that arguments passed to a method on the server are properly
    received.
    """

    jsClass = 'Nevow.Athena.Tests.ClientToServerArgumentSerialization'

    def test(self, i, f, s, l, d):
        self.assertEqual(i, 1)
        self.assertEqual(f, 1.5)
        self.assertTrue(isinstance(s, str))
        self.assertEqual(s, 'Hello world')
        self.assertTrue(isinstance(l[2], str))
        self.assertEqual(l, [1, 1.5, 'Hello world'])
        self.assertEqual(d, {'hello world': 'object value'})
        self.assertTrue(isinstance(list(d.keys())[0], str))
        self.assertTrue(isinstance(list(d.values())[0], str))
    expose(test)


class ClientToServerResultSerialization(testcase.TestCase):
    """
    Tests that the return value from a method on the server is properly
    received by the client.
    """

    jsClass = 'Nevow.Athena.Tests.ClientToServerResultSerialization'

    def test(self, i, f, s, l, d):
        return (i, f, s, l, d)
    expose(test)



class JSONRoundtrip(testcase.TestCase):
    """
    Test that all test cases from nevow.test.test_json roundtrip correctly
    through the real client implementation, too.
    """

    jsClass = 'Nevow.Athena.Tests.JSONRoundtrip'

    def test(self):
        cases = test_json.TEST_OBJECTS + test_json.TEST_STRINGLIKE_OBJECTS
        def _verifyRoundtrip(_cases):
            for v1, v2 in zip(cases, _cases):
                self.assertEqual(v1, v2)
        return self.callRemote('identity', cases).addCallback(_verifyRoundtrip)
    expose(test)



class ExceptionFromServer(testcase.TestCase):
    """
    Tests that when a method on the server raises an exception, the client
    properly receives an error.
    """

    jsClass = 'Nevow.Athena.Tests.ExceptionFromServer'

    def testSync(self, s):
        raise Exception(s)
    expose(testSync)



class AsyncExceptionFromServer(testcase.TestCase):
    """
    Tests that when a method on the server raises an exception asynchronously,
    the client properly receives an error.
    """

    jsClass = 'Nevow.Athena.Tests.AsyncExceptionFromServer'

    def testAsync(self, s):
        return defer.fail(Exception(s))
    expose(testAsync)



class ExceptionFromClient(testcase.TestCase):
    """
    Tests that when a method on the client raises an exception, the server
    properly receives an error.
    """

    jsClass = 'Nevow.Athena.Tests.ExceptionFromClient'

    def loopbackError(self):
        return self.callRemote('generateError').addErrback(self.checkError)
    expose(loopbackError)


    def checkError(self, f):
        f.trap(athena.JSException)
        if 'This is a test exception' in f.value.args[0]:
            return True
        else:
            raise f



class AsyncExceptionFromClient(testcase.TestCase):
    """
    Tests that when a method on the client raises an exception asynchronously,
    the server properly receives an error.
    """

    jsClass = 'Nevow.Athena.Tests.AsyncExceptionFromClient'

    def loopbackError(self):
        return self.callRemote('generateError').addErrback(self.checkError)
    expose(loopbackError)


    def checkError(self, f):
        f.trap(athena.JSException)
        if 'This is a deferred test exception' in f.value.args[0]:
            return True
        else:
            raise f


class CustomTransportable(object):
    """
    A simple transportable object used to verify customization is possible.
    """
    implements(IAthenaTransportable)

    jsClass = 'Nevow.Athena.Tests.CustomTransportable'

    def getInitialArguments(self):
        return ("Hello", 5, "world")



class ServerToClientArgumentSerialization(testcase.TestCase):
    """
    Tests that a method invoked on the client by the server is passed the
    correct arguments.
    """

    jsClass = 'Nevow.Athena.Tests.ServerToClientArgumentSerialization'

    def test(self):
        return self.callRemote(
            'reverse', 1, 1.5, 'hello', {'world': 'value'},
            CustomTransportable())
    expose(test)



class ServerToClientResultSerialization(testcase.TestCase):
    """
    Tests that the result returned by a method invoked on the client by the
    server is correct.
    """

    jsClass = 'Nevow.Athena.Tests.ServerToClientResultSerialization'

    def test(self):
        def cbResults(result):
            self.assertEqual(result[0], 1)
            self.assertEqual(result[1], 1.5)
            self.assertEqual(result[2], 'hello')
            self.assertEqual(result[3], {'world': 'value'})
        d = self.callRemote('reverse')
        d.addCallback(cbResults)
        return d
    expose(test)



class WidgetInATable(testcase.TestCase):
    jsClass = "Nevow.Athena.Tests.WidgetInATable"

    def getTestContainer(self):
        return tags.table[tags.tbody[tags.tr[tags.td[tags.slot('widget')]]]]



class WidgetIsATable(testcase.TestCase):
    jsClass = "Nevow.Athena.Tests.WidgetIsATable"

    def getWidgetTag(self):
        """
        Make this widget's top-level node a table node.
        """
        return tags.table


    def getWidgetDocument(self):
        """
        Create a body for the table node at the top of this widget.  Put a row
        and a column in it.
        """
        return tags.tbody[tags.tr[tags.td]]



class ParentChildRelationshipTest(testcase.TestCase):
    jsClass = "Nevow.Athena.Tests.ChildParentRelationshipTest"

    def getWidgetDocument(self):
        """
        Return a tag which will have numerous children rendered beneath it.
        """
        return tags.div(render=tags.directive('childrenWidgets'))


    def render_childrenWidgets(self, ctx, data):
        """
        Put some children into this widget.  The client portion of this test
        will assert things about their presence in C{Widget.childWidgets}.
        """
        for i in range(3):
            yield ChildFragment(self.page, i)


    def getChildCount(self):
        return 3
    expose(getChildCount)



class ChildFragment(athena.LiveFragment):
    jsClass = 'Nevow.Athena.Tests.ChildParentRelationshipTest'

    docFactory = loaders.stan(tags.div(render=tags.directive('liveFragment'))[
        tags.div(render=tags.directive('childrenWidgets')),
        'child'])

    def __init__(self, page, childCount):
        super(ChildFragment, self).__init__()
        self.page = page
        self.childCount = childCount


    def render_childrenWidgets(self, ctx, data):
        # yield tags.div['There are ', self.childCount, 'children']
        for i in range(self.childCount):
            yield ChildFragment(self.page, self.childCount - 1)


    def getChildCount(self):
        return self.childCount
    expose(getChildCount)



class AutomaticClass(testcase.TestCase):
    jsClass = 'Nevow.Athena.Tests.AutomaticClass'
    docFactory = loaders.stan(tags.div(render=tags.directive('liveTest')))



class ButtonElement(Element):
    """
    A button with an automatic Athena event handler.
    """
    preprocessors = LiveElement.preprocessors
    docFactory = loaders.stan(
        tags.button[
            athena.handler(event='onclick', handler='handler')])



class AthenaHandler(testcase.TestCase):
    jsClass = 'Nevow.Athena.Tests.AthenaHandler'

    def getWidgetDocument(self):
        """
        Return a button with an automatic athena handler attached to its
        onclick event.
        """
        return ButtonElement()



class NodeLocationSubElement1(LiveElement):
    docFactory = loaders.stan(
        tags.div(render=tags.directive('liveElement'))[
            tags.invisible(render=tags.directive('bar')),
            tags.label(_class='foo', _for="username"),
            tags.input(_class='foo', id='username')])

    def bar(self, req, tag):
        e = NodeLocationSubElement2()
        e.setFragmentParent(self)
        return e
    renderer(bar)



class NodeLocationSubElement2(LiveElement):
    docFactory = loaders.stan(
        tags.div(render=tags.directive('liveElement'))[
            tags.label(_class='bar', _for="username"),
            tags.input(_class='bar', id='username')])


    def getDynamicWidget(self):
        """
        Return a widget dynamically for us to have more fun with.
        """
        e = NodeLocationSubElement1()
        e.setFragmentParent(self)
        return e
    expose(getDynamicWidget)


    def getNodeInsertedHelper(self):
        """
        Return a dynamically instantiated NodeInsertedHelper to play with.
        """
        e = NodeInsertedHelper()
        e.setFragmentParent(self)
        return e
    expose(getNodeInsertedHelper)



class NodeInsertedHelper(LiveElement):
    """
    Simple widget to be dynamically instatiated for testing nodeInserted
    behaviour on client side.
    """
    jsClass = 'Nevow.Athena.Tests.NodeInsertedHelper'
    docFactory = loaders.stan(
        tags.div(render=tags.directive('liveElement')))



class NodeLocation(testcase.TestCase):
    jsClass = 'Nevow.Athena.Tests.NodeLocation'

    def getWidgetDocument(self):
        """
        Return some child elements for us to search in.
        """
        e = NodeLocationSubElement1()
        e.setFragmentParent(self)
        e2 = NodeLocationSubElement2()
        e2.setFragmentParent(self)
        return [e, e2]



class WidgetRequiresImport(LiveElement):
    """
    Widget which has no behavior, but which has a JavaScript class which will
    require a dynamic import.
    """
    jsClass = 'Nevow.Athena.Tests.Resources.ImportWidget'
    docFactory = loaders.stan(tags.div(render=tags.directive('liveElement')))



class DynamicWidgetInstantiation(testcase.TestCase):
    jsClass = 'Nevow.Athena.Tests.DynamicWidgetInstantiation'


    def makeDynamicWidget(self):
        """
        Return a newly created LiveFragment with no parent.
        """
        class DynamicFragment(athena.LiveFragment):
            docFactory = loaders.stan(tags.div(render=tags.directive('liveFragment')))
            jsClass = 'Nevow.Athena.Tests.DynamicWidgetClass'

            def someMethod(self):
                return 'foo'
            expose(someMethod)
        return DynamicFragment()


    def getDynamicWidget(self):
        """
        Return a newly created LiveFragment with this LiveFragment as its
        parent.
        """
        f = self.makeDynamicWidget()
        f.setFragmentParent(self)
        return f
    expose(getDynamicWidget)


    def getDynamicWidgetLater(self):
        """
        Make a s->c call with a LiveFragment as an argument.  This tests
        that widgets are reliably serialized when they appear as function
        arguments.
        """
        class DynamicFragment(athena.LiveFragment):
            docFactory = loaders.stan(tags.div(render=tags.directive('liveFragment')))
            jsClass = 'Nevow.Athena.Tests.DynamicWidgetClass'

            def someMethod(self):
                return 'foo'
            expose(someMethod)

        f = DynamicFragment()
        f.setFragmentParent(self)
        return self.callRemote("sendWidgetAsArgument", f)
    expose(getDynamicWidgetLater)


    def getDynamicWidgetInfo(self):
        """
        Return a dictionary containing structured information about a newly
        created Fragment which is a child of this test case.
        """
        f = self.getDynamicWidget()

        # Force it to have an ID and to become part of the page and other
        # grotty filthy things.
        #
        # XXX Make an actual API, maybe.
        widgetInfo = f._structured()

        return {
            'id': widgetInfo['id'],
            'klass': widgetInfo['class']}
    expose(getDynamicWidgetInfo)


    def getWidgetWithImports(self):
        """
        Return a Widget which requires a module import.
        """
        f = WidgetRequiresImport()
        f.setFragmentParent(self)
        return f
    expose(getWidgetWithImports)

    def getNonXHTMLWidget(self):
        """
        @return: a widget with a namespace that is not XHTML so a test can
        verify that the namespace is preserved.
        """
        class NonXHTMLFragment(athena.LiveFragment):
            circle = tags.Proto("circle")
            docFactory = loaders.stan(
                    circle(xmlns="http://www.w3.org/2000/svg",
                           render=tags.directive("liveFragment")))

        f = NonXHTMLFragment()
        f.setFragmentParent(self)
        return f
    expose(getNonXHTMLWidget)


    def getAndRememberDynamicWidget(self):
        """
        Call and return the result of L{getDynamicWidget}, but also save the
        result as an attribute on self for later inspection.
        """
        self.savedWidget = self.getDynamicWidget()
        return self.savedWidget
    expose(getAndRememberDynamicWidget)


    def getAndSaveDynamicWidgetWithChild(self):
        """
        Return a LiveFragment which is a child of this widget and which has a
        child.
        """
        childFragment = self.makeDynamicWidget()
        class DynamicFragment(athena.LiveFragment):
            docFactory = loaders.stan(
                tags.div(render=tags.directive('liveFragment'))[
                    tags.div(render=tags.directive('child'))])
            jsClass = 'Nevow.Athena.Tests.DynamicWidgetClass'

            def render_child(self, ctx):
                childFragment.setFragmentParent(self)
                return childFragment

        f = DynamicFragment()
        f.setFragmentParent(self)
        return f
    expose(getAndSaveDynamicWidgetWithChild)


    def assertSavedWidgetRemoved(self):
        """
        Verify that the saved widget is no longer a child of this fragment.
        """
        self.assertNotIn(self.savedWidget, self.liveFragmentChildren)
    expose(assertSavedWidgetRemoved)


    def detachSavedDynamicWidget(self):
        """
        Initiate a server-side detach on the saved widget.
        """
        return self.savedWidget.detach()
    expose(detachSavedDynamicWidget)



class GettingWidgetlessNodeRaisesException(testcase.TestCase):
    jsClass = 'Nevow.Athena.Tests.GettingWidgetlessNodeRaisesException'



class RemoteMethodErrorShowsDialog(testcase.TestCase):
    jsClass = 'Nevow.Athena.Tests.RemoteMethodErrorShowsDialog'

    def raiseValueError(self):
        raise ValueError('hi')
    athena.expose(raiseValueError)



class DelayedCallTests(testcase.TestCase):
    """
    Tests for the behavior of scheduling timed calls in the client.
    """
    jsClass = 'Nevow.Athena.Tests.DelayedCallTests'



class DynamicStylesheetFetching(testcase.TestCase, CSSModuleTestMixin):
    """
    Tests for stylesheet fetching when dynamic widget instantiation is
    involved.
    """
    jsClass = 'Nevow.Athena.Tests.DynamicStylesheetFetching'
    # lala we want to use TestCase.mktemp
    _testMethodName = 'DynamicStylesheetFetching'

    def getWidgetWithCSSDependencies(self):
        """
        Return a widget which depends on some CSS.
        """
        self.page.cssModules = self._makeCSSRegistry()

        element = athena.LiveElement()
        element.cssModule = 'TestCSSModuleDependencies.Dependor'
        element.setFragmentParent(self)
        element.docFactory = loaders.stan(
            tags.div(render=tags.directive('liveElement')))

        return (
            element,
            [str(self.page.getCSSModuleURL(n))
                for n in ('TestCSSModuleDependencies',
                          'TestCSSModuleDependencies.Dependee',
                          'TestCSSModuleDependencies.Dependor')])
    expose(getWidgetWithCSSDependencies)
