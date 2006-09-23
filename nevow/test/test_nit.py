from twisted.trial.unittest import TestCase
from twisted.python.failure import Failure

from nevow.testutil import FragmentWrapper, renderLivePage
from nevow.livetrial.testcase import TestSuite, TestError

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
