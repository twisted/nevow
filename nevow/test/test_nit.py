from twisted.application import app
from twisted.trial.unittest import TestCase
from twisted.python.reflect import prefixedMethods
from twisted.python.failure import Failure

from nevow.testutil import FragmentWrapper, renderLivePage
from nevow.livetrial.testcase import TestSuite, TestError
from nevow.scripts import nit

MESSAGE = u'I am an error'



class _DummyErrorHolder(object):
    """
    A dummy object that implements the parts of the ErrorHolder API we use,
    supplying an appropriate Failure.
    """

    def createFailure(self):
        """Create a Failure with traceback and all."""
        try:
            raise Exception(MESSAGE)
        except Exception:
            return Failure()


    def run(self, thing):
        thing.addError(self, self.createFailure())



class _DummySuite(TestSuite):
    """A dummy test suite containing a dummy Failure holder."""

    holderType = _DummyErrorHolder

    def __init__(self):
        self.name = 'Dummy Suite'
        holder = _DummyErrorHolder()
        self.tests = [holder]



class NevowInteractiveTesterTest(TestCase):

    def testGatherError(self):
        """
        Attempt collection of tests in the presence of an Failure that has
        occurred during trial's collection.
        """
        suite = _DummySuite()
        instances = suite.gatherInstances()
        te = instances[0]
        self.assertIdentical(type(te), TestError)


    def testErrorRendering(self):
        te = TestError(_DummyErrorHolder())
        return renderLivePage(FragmentWrapper(te)).addCallback(
            lambda output: self.assertIn(MESSAGE, output))



class MockNitOptions(nit.Options):
    """
    Version of L{nit.Options} that won't do anything dangerous such as trying
    to start an application or initialize logs.
    """

    def _startApplication(self):
        pass

    def _startLogging(self):
        pass



class NitTest(TestCase):
    """
    Tests for the C{nit} script.
    """

    # app methods
    def app_runReactorWithLogging(self, *a):
        pass


    def app_installReactor(self, name):
        self.log.append(name)


    # XXX - duplicated from axiom.test.test_axiomatic
    def _replaceAppMethods(self):
        """
        Mask over methods in the L{app} module with methods from this class
        that start with 'app_'.
        """
        prefix = 'app_'
        replacedMethods = {}
        for method in prefixedMethods(self, 'app_'):
            name = method.__name__[len(prefix):]
            replacedMethods[name] = getattr(app, name)
            setattr(app, name, method)
        return replacedMethods


    # XXX - duplicated from axiom.test.test_axiomatic
    def _restoreAppMethods(self, methods):
        """
        Replace any methods in L{app} with methods from parameter C{methods}.
        """
        for name, method in methods.iteritems():
            setattr(app, name, method)


    def setUp(self):
        self.options = MockNitOptions()
        self.log = []
        self._oldMethods = self._replaceAppMethods()


    def tearDown(self):
        self._restoreAppMethods(self._oldMethods)


    def test_noReactorSpecified(self):
        """
        Check that no reactor is installed if no reactor is specified.
        """
        self.options.parseOptions([])
        self.assertEqual(self.log, [])


    def test_reactorSpecified(self):
        """
        Check that a reactor is installed if it is specified.
        """
        self.options.parseOptions(['--reactor', 'select'])
        self.assertEqual(self.log, ['select'])
