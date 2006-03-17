
import sys

from twisted.trial import unittest
from twisted.internet import reactor, protocol, error, defer
from twisted.python import procutils, filepath

from twisted.python.util import untilConcludes

class _JavaScriptTestSuiteProtocol(protocol.ProcessProtocol):

    # XXX TODO: integrate this with Trial somehow, to report results of
    # individual JS tests.

    finished = None

    def connectionMade(self):
        self.out = []
        self.err = []

    def outReceived(self, out):
        untilConcludes(sys.stdout.write, out)
        untilConcludes(sys.stdout.flush)
        self.out.append(out)

    def errReceived(self, err):
        untilConcludes(sys.stdout.write, err)
        untilConcludes(sys.stdout.flush)
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

    def onetest(self, jsfile):
        p = _JavaScriptTestSuiteProtocol()
        d = p.finished = defer.Deferred()
        reactor.spawnProcess(
            p,
            self.javascriptInterpreter,
            ("js", filepath.FilePath(__file__).parent().child(jsfile).path),
            path=filepath.FilePath(__file__).parent().path)

        return d


    def testJSDeferred(self):
        return self.onetest('test_deferred.js')


    def testJSObject(self):
        return self.onetest('test_object.js')



_jsInterps = procutils.which('smjs')
if _jsInterps:
    JavaScriptTestSuite.javascriptInterpreter = _jsInterps[0]
else:
    JavaScriptTestSuite.skip = "No JavaScript interpreter available."
del _jsInterps

