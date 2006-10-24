// import Nevow.Athena.Test

function makeTestCase() {
    var testCase = {};
    testCase.__class__ = {};
    testCase.__class__.__name__ = 'testcasename';
    return testCase;
};

/**
 * Test running a test with L{Nevow.Athena.Test._TestMethod}.  This only tests
 * that the method is invoked and that startTest and stopTest are called on the
 * reporter.
 */
function test_testMethod() {
    var runArgs = null;
    var runThis = null;
    var testCase = makeTestCase();

    testCase.method = function() {
        assertEqual(runArgs, null, "Test case test method called more than once.");
        runArgs = arguments;
        runThis = this;
    };

    var method = Nevow.Athena.Test._TestMethod(testCase, 'method');
    assertEqual(method.fullyQualifiedName, 'testcasename.method');

    var reporter = {};
    var started = false;
    reporter.startTest = function(testMethod) {
        assertEqual(testMethod, method, "Test method passed to startTest was wrong.");
        started = true;
    };

    var stopped = false;
    reporter.stopTest = function(testMethod) {
        assertEqual(testMethod, method, "Test method passed to stopTest was wrong.");
        stopped = true;
    };

    reporter.addSuccess = function() {};
    reporter.addFailure = function() {};

    method.run(reporter);

    assert(runArgs != null, "Test method not actually run.");
    assert(started, "Reporter was never told the test started.");
    assert(stopped, "Reporter was never told the test stopped.");

    assertEqual(runArgs.length, 0, "Wrong number of arguments passed to run().");
    assertEqual(runThis, testCase, "Wrong execution context when calling run().");
};


/**
 * Test that a synchronously succeeding test results in addSuccess being invoked.
 */
function test_testMethodSynchronousSuccessReporting() {
    var testCase = makeTestCase();
    var success = null;

    testCase.method = function() {
        /*
         * We don't have to do anything in order to succeed.
         */
    };

    var method = Nevow.Athena.Test._TestMethod(testCase, 'method');
    var reporter = {};
    reporter.startTest = function() {};
    reporter.stopTest = function() {};
    reporter.addSuccess = function(testCase) {
        success = testCase;
    };

    method.run(reporter);

    assertEqual(success, method, "Test method not passed to addSuccess().");
};

/**
 * Test that an asynchronously succeeding test results in addSuccess being
 * invoked.
 */
function test_testMethodAsynchronousSuccessReporting() {
    var testCase = makeTestCase();
    var success = null;
    var resultDeferred = Divmod.Defer.Deferred();

    testCase.method = function() {
        return resultDeferred;
    };

    var method = Nevow.Athena.Test._TestMethod(testCase, 'method');
    var reporter = {};
    reporter.startTest = function() {};
    reporter.stopTest = function() {};
    reporter.addSuccess = function(testCase) {
        success = testCase;
    };

    method.run(reporter);

    assertEqual(success, null, "addSuccess() called too early.");

    resultDeferred.callback(null);

    assertEqual(success, method, "Test method not passed to addSuccess().");
};

/**
 * Test that a synchronously failing test results in addFailure being invoked.
 */
function test_testMethodSynchronousFailureReporting() {
    var testCase = makeTestCase();
    var failure = null;

    testCase.method = function() {
        throw new Error("Test failure");
    };

    var method = Nevow.Athena.Test._TestMethod(testCase, 'method');
    var reporter = {};
    reporter.startTest = function() {};
    reporter.stopTest = function() {};
    reporter.addFailure = function(testCase) {
        failure = testCase;
    };

    method.run(reporter);

    assertEqual(failure, method, "Test method not passed to addFailure().");
};

/**
 * Test that an asynchronously failing test results in addFailure being
 * invoked.
 */
function test_testMethodAsynchronousFailureReporting() {
    var testCase = makeTestCase();
    var failure = null;
    var resultDeferred = Divmod.Defer.Deferred();

    testCase.method = function() {
        return resultDeferred;
    };

    var method = Nevow.Athena.Test._TestMethod(testCase, 'method');
    var reporter = {};
    reporter.startTest = function() {};
    reporter.stopTest = function() {};
    reporter.addFailure = function(testCase, error) {
        failure = testCase;
    };

    method.run(reporter);

    assertEqual(failure, null, "addFailure() called too early.");

    resultDeferred.errback(new Error("Test failure"));

    assertEqual(failure, method, "Test method not passed to addFailure().");
};


function test_testCaseMethods() {
    var TestCase = Nevow.Athena.Test.TestCase.subclass('test_livetrial.test_testCaseMethods');
    TestCase.methods(

        /* Override this to avoid doing anything with nodes, which we cannot do
         * in this test harness.
         */
        function __init__() {},

        /* Define a few methods, some of which should be picked up by
         * getTestMethods().
         */
        function test_foo() {},
        function test_bar() {},
        function mumble() {});

    var testCaseInstance = TestCase({});

    var methods = testCaseInstance.getTestMethods();
    methods.sort();
    assertArraysEqual(
        methods,
        ["test_bar", "test_foo"],
        function(a, b, msg) {
            assert(a instanceof Nevow.Athena.Test._TestMethod);
            assertEqual(a.testMethodName, b, msg);
        });
};

var testFunctions = [
    test_testMethod,
    test_testMethodSynchronousSuccessReporting,
    test_testMethodAsynchronousSuccessReporting,
    test_testMethodSynchronousFailureReporting,
    test_testMethodAsynchronousFailureReporting,

    test_testCaseMethods];

runTests(testFunctions);
