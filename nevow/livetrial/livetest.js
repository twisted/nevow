
// import Divmod.Inspect
// import Divmod.Defer
// import Nevow.Athena

/**
 * Represent one test method from one test case.
 *
 * @ivar testCase: The instance of L{Nevow.Athena.Test.TestCase} to which this
 * test method belongs.
 *
 * @ivar testMethodName: A string naming the method from C{testCase} to run.
 *
 * @ivar fullyQualifiedName: A string naming both the class from which this
 * test method comes as well as the individual method itself.  For example,
 * "Nevow.Athena.Test.TestStuff.test_fooBar".
 */
Nevow.Athena.Test._TestMethod = Divmod.Class.subclass('Nevow.Athena.Test._TestMethod');
Nevow.Athena.Test._TestMethod.methods(
    function __init__(self, testCase, testMethodName) {
        self.testCase = testCase;
        self.testMethodName = testMethodName;
        self.fullyQualifiedName = self.testCase.__class__.__name__ + '.' + self.testMethodName;
    },

    function toString(self) {
        return 'TestMethod(' + self.fullyQualifiedName + ')';
    },

    /**
     * Execute this test method and report its results to the given reporter.
     *
     * @param reporter: An L{IReporter} provider to which the outcome of this
     * test run will be reported.
     *
     * @return: A L{Divmod.Defer.Deferred} which will be called back when this
     * test has completed, whether it succeeds or fails.
     */
    function run(self, reporter) {
        var failed;
        var result;
        var testMethod = self.testCase[self.testMethodName];

        reporter.startTest(self);
        try {
            failed = false;
            result = testMethod.call(self.testCase);
        } catch (err) {
            failed = true;
            result = Divmod.Defer.fail(err);
        }
        if (!failed) {
            if (!(result instanceof Divmod.Defer.Deferred)) {
                result = Divmod.Defer.succeed(result);
            }
        }
        result.addCallback(function(result) {
                reporter.addSuccess(self);
            });
        result.addErrback(function(error) {
                reporter.addFailure(self, error);
            });
        result.addCallback(function(ignored) {
                reporter.stopTest(self);
            });
        return result;
    });


Nevow.Athena.Test.TestCase = Nevow.Athena.Widget.subclass('Nevow.Athena.Test.TestCase');
Nevow.Athena.Test.TestCase.methods(
    function fail(self, msg) {
        throw new Error('Test Failure: ' + msg);
    },

    function assertEquals(self, a, b, msg) {
        if (!(a == b)) {
            if(msg == undefined) {
                msg = a + ' != ' + b;
            }
            self.fail(msg);
        }
    },

    function failUnless(self, a, msg) {
        if(!a) {
            if(msg == undefined) {
                msg = a;
            }
            self.fail(msg);
        }
    },

    /**
     * Return an Array of ITestMethod providers.
     */
    function getTestMethods(self) {
        var tests = [];
        var methods = Divmod.Inspect.methods(self.__class__);
        for (var i = 0; i < methods.length; ++i) {
            if (methods[i].slice(0, 4) == "test") {
                tests.push(Nevow.Athena.Test._TestMethod(self, methods[i]));
            }
        }

        /*
         * A bit of backwards compatibility
         */
        if (self['run'] != undefined) {
            Divmod.msg("TestCase.run() is deprecated: define methods with a 'test' prefix.");
            tests.push(Nevow.Athena.Test._TestMethod(self, 'run'));
        }
        return tests;
    });


Nevow.Athena.Test.TestRunner = Nevow.Athena.Widget.subclass('Nevow.Athena.Test.TestRunner');
Nevow.Athena.Test.TestRunner.methods(
    function __init__(self, node) {
        Nevow.Athena.Test.TestRunner.upcall(self, '__init__', node);
        self._successNode = self.nodeByAttribute('class', 'test-success-count');
        self._failureNode = self.nodeByAttribute('class', 'test-failure-count');
        self._timingNode = self.nodeByAttribute('class', 'test-time');
        self._resultsNode = self.nodeByAttribute('class', 'test-results');
    },

    /* ITestSuite */

    /**
     * Return an Array of all the test methods of all the ITestSuites which are
     * children of this widget.
     */
    function getTestMethods(self) {
        var widget;
        var methods = [];
        for (var i = 0; i < self.childWidgets.length; ++i) {
            widget = self.childWidgets[i];
            if (widget.getTestMethods) {
                methods = methods.concat(widget.getTestMethods());
            }
        }
        return methods;
    },

    function setRunTime(self, started, finished) {
        var difference = finished.getTime() - started.getTime();
        self._timingNode.innerHTML = difference / 1000.0 + ' seconds';
    },

    function _clear(self, node) {
        while (node.firstChild != null) {
            node.removeChild(node.firstChild);
        }
    },

    /**
     * Run the test suite represented by by the TestCases which exist as
     * children of this Widget's node using a default visitor controller and
     * reporter.
     *
     * @return: C{false}
     */
    function runWithDefaults(self) {
        self._clear(self._successNode);
        self._clear(self._failureNode);
        self._clear(self._timingNode);
        self._clear(self._resultsNode);

        var started = new Date();
        var completionDeferred = self.run(
            Nevow.Athena.Test.ConcurrentVisitor(),
            Nevow.Athena.Test.TestReporter(
                self._successNode,
                self._failureNode,
                self._timingNode,
                self._resultsNode),
            self);
        completionDeferred.addCallback(
            function(ignored) {
                var finished = new Date();
                self.setRunTime(started, finished);
            });
        completionDeferred.addErrback(
            function(error) {
                alert(error);
            });
        return false;
    },

    /**
     * Run a suite of tests, visiting them as directed by a C{controller}
     * and passing results to C{reporter}.
     *
     * @param controller: An L{IVisitController} provider (L{ConcurrentVisitor}
     * or L{SerialVisitor}).
     *
     * @param reporter: An L{IReporter} provider (L{TestReporter}).
     *
     * @param suite: An L{ITestSuite} provider (L{TestCase}).
     *
     * @return: A L{Deferred} which fires when the suite has been run to
     * completion.
     */
    function run(self, controller, reporter, suite) {
        return controller.traverse(
            function(testMethod) {
                Divmod.msg("Running " + testMethod);
                var result;
                var failed;
                try {
                    failed = false;
                    result = testMethod.run(reporter);
                } catch (err) {
                    failed = true;
                    result = Divmod.Defer.fail(err);
                }
                if (!failed) {
                    if (!result instanceof Divmod.Defer.Deferred) {
                        result = Divmod.Defer.succeed(result);
                    }
                }
                return result;
            }, suite);
    });


/**
 * Represent the running or completed state of a single test method.
 *
 * @ivar node: A DOM node which will be manipulated to reflect the state of
 * this result.
 *
 * @ivar testMethodName: A string naming the test method for which this
 * represents the results.
 */
Nevow.Athena.Test.TestResult = Divmod.Class.subclass('Nevow.Athean.Test.TestResult');
Nevow.Athena.Test.TestResult.methods(
    function __init__(self, node, testMethodName) {
        self.node = node;
        self.testMethodName = testMethodName;

        self._initializeNode(self.node);
    },

    function _createLabel(self, text) {
        return document.createTextNode(text);
    },

    function _createTraceback(self, text) {
        var tb = document.createTextNode(text);
        var container = document.createElement('pre');
        container.appendChild(tb);
        return container;
    },

    function _initializeNode(self, node) {
        node.appendChild(self._createLabel(self.testMethodName));
    },

    function startTest(self) {
        self.node.setAttribute('class', 'test-running');
    },

    function testSucceeded(self) {
        self.node.setAttribute('class', 'test-success');
    },

    function testFailed(self, failure) {
        self.node.setAttribute('class', 'test-failure');
        self.node.appendChild(
            self._createTraceback(
                failure.error.message + '\n' + failure.error.stack + '\n'));
    });


/**
 * Report the results of a number of test runs using a document in this page.
 * (This is the de-facto definition of IReporter for now).
 *
 * @implements: IReporter
 *
 * @ivar successCountNode: A DOM node which will be manipulated to reflect the
 * number of tests which have succeeded.
 *
 * @ivar successCountNode: A DOM node which will be manipulated to reflect the
 * number of tests which have failed.
 *
 * @ivar successCountNode: A DOM node which will be manipulated to report the
 * total runtime of the test suite.
 *
 * @ivar resultsNode: The DOM node beneath which test results will be reported.
 *
 * @ivar _knownTestMethods: A mapping of test method names to
 * L{Nevow.Athena.Test.TestResult} instances representing the current reporting
 * state.
 *
 */
Nevow.Athena.Test.TestReporter = Divmod.Class.subclass('Nevow.Athena.Test.TestReporter');
Nevow.Athena.Test.TestReporter.methods(
    function __init__(self, successCountNode, failureCountNode, timingNode, resultsNode) {
        self.successCountNode = successCountNode;
        self.failureCountNode = failureCountNode;
        self.timingNode = timingNode;
        self.resultsNode = resultsNode;
        self._knownTestMethods = {};
    },

    /**
     * Create a DOM node suitable for use by a TestResult.
     */
    function _createResultNode(self, testMethod) {
        return document.createElement('div');
    },

    function _increment(self, node) {
        var currentValue = parseInt(node.innerHTML);
        if (isNaN(currentValue)) {
            currentValue = 0;
        }
        node.innerHTML = String(currentValue + 1);
    },

    function startTest(self, testMethod) {
        if (testMethod.fullyQualifiedName in self._knownTestMethods) {
            throw new Error("Completely invalid duplicate testMethod: " + testMethod.fullyQualifiedName);
        }
        var node = self._createResultNode(testMethod);
        self.resultsNode.appendChild(node);
        var result = Nevow.Athena.Test.TestResult(node, testMethod.fullyQualifiedName);
        self._knownTestMethods[testMethod.fullyQualifiedName] = result;
        result.startTest();
    },

    function stopTest(self, testMethod) {
    },

    function addSuccess(self, testMethod) {
        self._increment(self.successCountNode);
        self._knownTestMethods[testMethod.fullyQualifiedName].testSucceeded()
    },

    function addFailure(self, testMethod, failure) {
        self._increment(self.failureCountNode);
        self._knownTestMethods[testMethod.fullyQualifiedName].testFailed(failure)
    });


/**
 * A visit-controller which applies a specified visitor to the methods of a
 * suite without waiting for the Deferred from a visit to fire before
 * proceeding to the next method.
 */
Nevow.Athena.Test.ConcurrentVisitor = Divmod.Class.subclass('Nevow.Athena.Test.ConcurrentVisitor');
Nevow.Athena.Test.ConcurrentVisitor.methods(
    function traverse(self, visitor, suite) {
        var deferreds = [];
        var methods = suite.getTestMethods();
        Divmod.msg("Running " + methods.length + " methods.");
        for (var i = 0; i < methods.length; ++i) {
            deferreds.push(visitor(methods[i]));
        }
        Divmod.msg("DeferredList(" + deferreds + ")");
        return Divmod.Defer.DeferredList(deferreds);
    });


/**
 * A visit-controller which applies a specified visitor to the methods of a
 * suite, waiting for the Deferred from a visit to fire before proceeding to
 * the next method.
 */
Nevow.Athena.Test.SerialVisitor = Divmod.Class.subclass('Nevow.Athena.Test.SerialVisitor');
Nevow.Athena.Test.SerialVisitor.methods(
    function traverse(self, visitor, suite) {
        return self._traverse(visitor, suite.getTestMethods());
    },

    function _traverse(self, visitor, methods) {
        var method;
        var result;
        if (methods.length) {
            method = methods.shift();
            result = visitor(method);
            result.addCallback(function(ignored) {
                    self._traverse(visitor, methods);
                });
            return result;
        }
        return Divmod.Defer.succeed(null);
    });
