import signal, subprocess
from StringIO import StringIO

try:
    import subunit
except ImportError:
    subunit = None

from twisted.python import procutils
from twisted.trial import unittest

from nevow.scripts import consolejstest


class NotSupported(Exception):
    """
    Raised by the L{TestCase} if the installation lacks a certain required
    feature.
    """


class JavaScriptTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        self.testMethod = getattr(self, methodName)


    def checkDependencies(self):
        """
        Check that all the dependencies of the test are satisfied.

        @raise NotSupported: If any one of the dependencies is not satisfied.
        """
        js = consolejstest.findJavascriptInterpreter()
        if js is None:
            raise NotSupported("Could not find JavaScript interpreter")
        if subunit is None:
            raise NotSupported("Could not import 'subunit'")


    def _writeToTemp(self, contents):
        fname = self.mktemp()
        fd = file(fname, 'w')
        try:
            fd.write(contents)
        finally:
            fd.close()
        return fname


    def makeScript(self, testModule):
        js = """
// import Divmod.UnitTest
// import %(module)s

Divmod.UnitTest.runRemote(Divmod.UnitTest.loadFromModule(%(module)s));
""" % {'module': testModule}
        jsfile = self._writeToTemp(js)
        scriptFile = self._writeToTemp(consolejstest.generateTestScript(jsfile))
        return scriptFile


    def _runWithSigchild(self, f, *a, **kw):
        """
        Run the given function with an alternative SIGCHLD handler.
        """
        oldHandler = signal.signal(signal.SIGCHLD, signal.SIG_DFL)
        try:
            return f(*a, **kw)
        finally:
            signal.signal(signal.SIGCHLD, oldHandler)


    def run(self, result):
        try:
            self.checkDependencies()
        except NotSupported, e:
            result.startTest(self)
            result.addSkip(self, str(e))
            result.stopTest(self)
            return
        js = consolejstest.findJavascriptInterpreter()
        script = self.makeScript(self.testMethod())
        def runTests():
            protocol = subunit.TestProtocolServer(result)
            output = subprocess.Popen([js, script],
                                      stdout=subprocess.PIPE).communicate()[0]
            protocol.readFrom(StringIO(output))
        self._runWithSigchild(runTests)



class JSUnitTests(JavaScriptTestCase):
    def test_jsunit(self):
        return 'Divmod.Test.TestUnitTest'


    def test_deferred(self):
        return 'Divmod.Test.TestDeferred'


    def test_base(self):
        return 'Divmod.Test.TestBase'


    def test_livetrial(self):
        return 'Divmod.Test.TestLivetrial'


    def test_inspect(self):
        return 'Divmod.Test.TestInspect'


    def test_object(self):
        return 'Divmod.Test.TestObject'
