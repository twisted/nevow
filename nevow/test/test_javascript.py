
from twisted.trial import unittest
from twisted.internet import reactor, protocol, error, defer
from twisted.python import procutils, filepath

class _JavaScriptTestSuiteProtocol(protocol.ProcessProtocol):
    finished = None

    def connectionMade(self):
        self.out = []
        self.err = []

    def outReceived(self, out):
        self.out.append(out)

    def errReceived(self, err):
        self.err.append(err)

    def processEnded(self, reason):
        if reason.check(error.ProcessTerminated):
            self.finished.errback(Exception(reason.getErrorMessage(), ''.join(self.out), ''.join(self.err)))
        elif self.err:
            self.finished.errback(Exception(''.join(self.out), ''.join(self.err)))
        else:
            self.finished.callback(''.join(self.out))



class JavaScriptTestSuite(unittest.TestCase):

    javascriptInterpreter = None

    def testAllJavaScript(self):
        p = _JavaScriptTestSuiteProtocol()
        d = p.finished = defer.Deferred()
        reactor.spawnProcess(
            p,
            self.javascriptInterpreter,
            ("js", filepath.FilePath(__file__).parent().child('test_object.js').path),
            path=filepath.FilePath(__file__).parent().path)

        def finished(output):
            lines = output.splitlines()
            self.assertEquals(lines[-1], 'SUCCESS')

        return d.addCallback(finished)



_jsInterps = procutils.which('smjs')
if _jsInterps:
    JavaScriptTestSuite.javascriptInterpreter = _jsInterps[0]
else:
    JavaScriptTestSuite.skip = "No JavaScript interpreter available."
del _jsInterps

