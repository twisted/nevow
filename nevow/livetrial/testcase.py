import inspect, types, os

from twisted.trial import runner, unittest

from nevow import athena

class TestCase(athena.LiveFragment, unittest.TestCase):
    def render_liveTest(self, ctx, data):
        ctx.tag(_class='test-unrun')
        return self.render_liveFragment(ctx, data)

    def __repr__(self):
        return object.__repr__(self)

class TestSuite(object):
    def __init__(self, name="Live Tests"):
        self.tests = []
        self.name = name

    def addTest(self, test):
        self.tests.append(test)

class TestLoader(runner.TestLoader):
    modulePrefix = 'livetest_'

    def __init__(self):
        runner.TestLoader.__init__(self)
        self.suiteFactory = TestSuite

    def loadByName(self, name, recurse=False):
        thing = self.findByName(name)
        return self.loadAnything(thing, recurse)

    def loadMethod(self, method):
        raise NotImplementedError, 'livetests must be classes'

    def loadClass(self, klass):
        if not (isinstance(klass, type) or isinstance(klass, types.ClassType)):
            raise TypeError("%r is not a class" % (klass,))
        if not self.isTestCase(klass):
            raise ValueError("%r is not a test case" % (klass,))
        return klass

    def loadModule(self, module):
        if not isinstance(module, types.ModuleType):
            raise TypeError("%r is not a module" % (module,))
        suite = self.suiteFactory(module.__name__)
        for testClass in self._findTestClasses(module):
            suite.addTest(self.loadClass(testClass))
        return suite

    def isTestCase(self, obj):
        return isinstance(obj, (type, types.ClassType)) and issubclass(obj, TestCase) and obj is not TestCase

    def _findTestClasses(self, module):
        classes = []
        for name, val in inspect.getmembers(module):
            if self.isTestCase(val):
                classes.append(val)
        return self.sort(classes)
