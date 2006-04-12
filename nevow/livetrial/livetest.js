
// import Nevow.Athena

Nevow.Athena.Test.TestCase = Nevow.Athena.Widget.subclass('Nevow.Athena.Test.TestCase');
Nevow.Athena.Test.TestCase.methods(
    function fail(self, msg) {
        throw new Error('Test Failure: ' + msg);
    },

    function assertEquals(self, a, b) {
        if (!(a == b)) {
            self.fail(a + ' != ' + b);
        }
    },

    function _run(self, reporter) {
        self.node.setAttribute('class', 'test-running');
        try {
            var result = self.run();
        } catch (err) {
            self._failure(err, reporter);
            return;
        }
        if (typeof result == 'object' && result.addCallback && result.addErrback) {
            result.addCallback(function(result) { self._success(reporter); });
            result.addErrback(function(err) { self._failure(err.error, reporter); });
            return result;
        } else {
            self._success(reporter);
        }
    },

    function _failure(self, err, reporter) {
        self.node.setAttribute('class', 'test-failure');

        var error = document.createElement('pre');
        error.setAttribute('class', 'test-failure-message');
        error.appendChild(document.createTextNode(err.name + ': ' + err.message + '\n\n' + err.stack));
        self.node.appendChild(error);

        reporter.reportFailure(err);
    },

    function _success(self, reporter) {
        self.node.setAttribute('class', 'test-success');
        reporter.reportSuccess();
    });

Nevow.Athena.Test.TestSuite = Nevow.Athena.Widget.subclass('Nevow.Athena.Test.TestSuite');
Nevow.Athena.Test.TestSuite.methods(
    function __init__(self, node) {
        Nevow.Athena.Test.TestSuite.upcall(self, '__init__', node);
    },

    function _run(self, reporter) {
        var allTests = [];
        for (var i = 0; i < self.childWidgets.length; ++i) {
            var widget = self.childWidgets[i];
            if (widget._run) {
                var result = widget._run(reporter);
                if (result instanceof Divmod.Defer.Deferred) {
                    allTests.push(result);
                }
            }
        }
        return Divmod.Defer.DeferredList(allTests);
    });

Nevow.Athena.Test.TestRunner = Nevow.Athena.Test.TestSuite.subclass('Nevow.Athena.Test.TestRunner');
Nevow.Athena.Test.TestRunner.methods(
    function __init__(self, node) {
        Nevow.Athena.Test.TestRunner.upcall(self, '__init__', node);
        self._successNode = self.nodeByAttribute('class', 'test-success-count');
        self._failureNode = self.nodeByAttribute('class', 'test-failure-count');
        self._timingNode = self.nodeByAttribute('class', 'test-time');
    },

    function run(self) {
        self._successCount = 0;
        self._failureCount = 0;
        var testsStarted = new Date();
        self._timingNode.innerHTML = '-';
        var d = self._run(self);
        d.addCallback(function(result) {
            var now = new Date();
            self._timingNode.innerHTML = (now.getTime() - testsStarted.getTime()) / 1000.0 + ' seconds';
        });
        return false;
    },

    function reportSuccess(self) {
        self._successCount += 1;
        self._successNode.innerHTML = self._successCount;
    },

    function reportFailure(self, err) {
        self._failureCount += 1;
        self._failureNode.innerHTML = self._failureCount;
        Divmod.log('test-result', err.message);
    });
