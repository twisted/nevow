from twisted.python.filepath import FilePath
from nevow.testutil import JavaScriptTestSuite, setJavascriptInterpreterOrSkip

class NevowJavaScriptTestSuite(JavaScriptTestSuite):
    """
    Run all the nevow javascript tests
    """
    path = FilePath(__file__).parent()

    def testJSDeferred(self):
        return self.onetest('test_deferred.js')


    def testJSObject(self):
        return self.onetest('test_object.js')


    def testJSBase(self):
        return self.onetest('test_base.js')


    def testJSInspect(self):
        return self.onetest('test_inspect.js')


    def testJSLivetrial(self):
        return self.onetest('test_livetrial.js')

setJavascriptInterpreterOrSkip(NevowJavaScriptTestSuite)
