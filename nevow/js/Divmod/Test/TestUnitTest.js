/**
 * Tests for Divmod.UnitTest, the Javascript unit-testing framework.
 * Uses mock test cases provided by Divmod.Test.Mock.
 */

// import Divmod.UnitTest
// import Divmod.Test.Mock


/**
 * A mock L{TestResult} object that we use to test that L{startTest} and L{stopTest}
 * are called appropriately.
 */
Divmod.Test.TestUnitTest.MockResult = Divmod.Class.subclass('Divmod.Test.TestUnitTest.MockResult');
Divmod.Test.TestUnitTest.MockResult.methods(
    function __init__(self) {
        self.log = '';
    },

    function startTest(self, test) {
        self.log += 'startTest ' + test.id();
    },

    function addSuccess(self, test) {
        self.log += ' addSuccess ' + test.id();
    },

    function stopTest(self, test) {
        self.log += ' stopTest ' + test.id();
    });



/**
 * Tests for assertions in L{Divmod.UnitTest.TestCase}.
 */
Divmod.Test.TestUnitTest.AssertionTests = Divmod.UnitTest.TestCase.subclass('Divmod.Test.TestUnitTest.AssertionTests');
Divmod.Test.TestUnitTest.AssertionTests.methods(
    /**
     * Test that L{assert} raises an exception if its expression is false.
     */
    function test_assert(self) {
        self.assertThrows(Divmod.UnitTest.AssertionError,
                          function () { self.assert(false, "message"); })
    },


    /**
     * Test that L{assertThrows} doesn't raise an exception if its callable
     * raises the excepted error.
     */
    function test_assertThrowsPositive(self) {
        try {
            self.assertThrows(Divmod.UnitTest.AssertionError,
                              function () {
                                  throw Divmod.UnitTest.AssertionError();
                              });
        } catch (e) {
            self.fail("assertThrows should have passed: " + e.message);
        }
    },


    /**
     * Test that L{assertThrows} raises an exception if its callable does
     * I{not} raise an exception.
     */
    function test_assertThrowsNoException(self) {
        var raised = true;
        try {
            self.assertThrows(Divmod.UnitTest.AssertionError,
                              function () { });
            raised = false;
        } catch (e) {
            if (!(e instanceof Divmod.UnitTest.AssertionError)) {
                self.fail("assertThrows should have thrown AssertionError");
            }
        }
        if (!raised) {
            self.fail("assertThrows did not raise an error");
        }
    },


    /**
     * Test that L{assertThrows} raises an exception if its callable raises
     * the wrong kind of exception.
     */
    function test_assertThrowsWrongException(self) {
        var raised = true;
        try {
            self.assertThrows(Divmod.UnitTest.AssertionError,
                              function () { throw Divmod.IndexError(); });
            raised = false;
        } catch (e) {
            if (!(e instanceof Divmod.UnitTest.AssertionError)) {
                self.fail("assertThrows should have thrown AssertionError");
            }
        }
        if (!raised) {
            self.fail("assertThrows did not raise an error");
        }
    },


    /**
     * Test that L{compare} does not raise an exception if its callable
     * returns C{true}.
     */
    function test_comparePositive(self) {
        self.compare(function () { return true; });
    },


    /**
     * Test that L{compare} raises an error if its callable returns C{false}.
     */
    function test_compareNegative(self) {
        self.assertThrows(Divmod.UnitTest.AssertionError,
                          function () {
                              self.compare(
                                  function (a, b) { return a === b; },
                                  "!==", "a", "b");
                          });
    },


    /**
     * Test that the message of L{compare}'s AssertionError describes the
     * failed the comparison based on its parameters.
     */
    function test_compareDefaultMessage(self) {
        try {
            self.compare(function () {return false;}, "<->", "a", "b");
        } catch (e) {
            self.assertIdentical(e.message, 'a <-> b');
        }
    },


    /**
     * Test that the L{compare}'s AssertionError includes the optional
     * message if it is provided.
     */
    function test_compareWithMessage(self) {
        try {
            self.compare(function () {return false;}, "<->", "a", "b",
                         "Hello");
        } catch (e) {
            self.assertIdentical(e.message, 'a <-> b: Hello');
        }
    },


    /**
     * Test that L{assertIdentical} raises an exception if its arguments are
     * unequal, and that the message of the raised exception contains the
     * arguments.
     */
    function test_assertIdenticalNegative(self) {
        var e = self.assertThrows(Divmod.UnitTest.AssertionError,
                                  function () {
                                      self.assertIdentical('apple', 'orange');
                                  });
        self.assert(e.message === 'apple !== orange', e.message);
    },


    /**
     * If L{assertIdentical} is given a message as an optional third argument,
     * that message should appear in the raised exception's message. Test this.
     */
    function test_assertIdenticalNegativeWithMessage(self) {
        try {
            self.assertIdentical('apple', 'orange', 'some message');
        } catch (e) {
            self.assert(e.message === 'apple !== orange: some message');
        }
    },


    /**
     * Test that L{assertIdentical} doesn't raise an exception if its
     * arguments are equal.
     */
    function test_assertIdenticalPositive(self) {
        self.assertIdentical('apple', 'apple');
    },


    /**
     * Test that L{assertIdentical} thinks that 1 and '1' are unequal.
     */
    function test_assertIdenticalDifferentTypes(self) {
        var raised = true;
        var e = self.assertThrows(Divmod.UnitTest.AssertionError,
                                  function () {
                                      self.assertIdentical(1, '1');
                                  });
        self.assert(e.message === '1 !== 1');
    },


    /**
     * Test that L{assertArraysEqual} doesn't raise an exception if it is
     * passed that two 'equal' arrays.
     */
    function test_assertArraysEqualPositive(self) {
        self.assertArraysEqual([], []);
        self.assertArraysEqual([1, 2], [1, 2]);
    },


    /**
     * Test that L{assertArraysEqual} raises exceptions if it is passed two unequal
     * arrays.
     */
    function test_assertArraysEqualNegative(self) {
        self.assertThrows(Divmod.UnitTest.AssertionError,
                          function () {
                              self.assertArraysEqual([1, 2], [1, 2, 3]);
                          });
        self.assertThrows(Divmod.UnitTest.AssertionError,
                          function () {
                              self.assertArraysEqual({'foo': 2}, [2]);
                          });
        self.assertThrows(Divmod.UnitTest.AssertionError,
                          function () {
                              self.assertArraysEqual(1, [1]);
                          });
        self.assertThrows(Divmod.UnitTest.AssertionError,
                          function () {
                              self.assertArraysEqual(function () { return 1; },
                                                     function () { return 2; });
                          });
        self.assertThrows(Divmod.UnitTest.AssertionError,
                          function () {
                              self.assertArraysEqual(function () { },
                                                     function () { });
                          });
    },


    /**
     * Test that two equal arrays are not identical, and that an object is
     * identical to itself.
     */
    function test_assertIdentical(self) {
        var foo = [1, 2];
        self.assertIdentical(foo, foo);
        self.assertThrows(Divmod.UnitTest.AssertionError,
                          function () { self.assertIdentical(foo, [1, 2]); });
    });



/**
 * Tests for L{TestCase}.
 */
Divmod.Test.TestUnitTest.TestCaseTest = Divmod.UnitTest.TestCase.subclass('Divmod.Test.TestUnitTest.TestCaseTest');
Divmod.Test.TestUnitTest.TestCaseTest.methods(
    function setUp(self) {
        self.result = Divmod.UnitTest.TestResult();
    },

    /**
     * Test that when a test is run, C{setUp} is called first, then the test
     * method, then L{tearDown}.
     */
    function test_wasRun(self) {
        var test = Divmod.Test.Mock._WasRun("test_good");
        self.assertIdentical(test.log, '');
        test.run(self.result);
        self.assertIdentical(test.log, 'setUp test tearDown');
    },

    /**
     * Test that C{tearDown} still gets called, even when the test fails.
     */
    function test_tearDownCalled(self) {
        var test = Divmod.Test.Mock._WasRun("test_bad");
        test.run(self.result);
        self.assertIdentical(test.log, 'setUp tearDown');
    },

    /**
     * Test that C{run} takes a L{TestResult} that we can use to see whether
     * the test passed.
     */
    function test_goodResult(self) {
        var test = Divmod.Test.Mock._WasRun('test_good');
        test.run(self.result);
        self.assertArraysEqual(self.result.getSummary(), [1, 0, 0]);
        self.assert(self.result.wasSuccessful());
    },


    /**
     * Test that C{run} takes a L{TestResult} that we can use to see whether
     * test test failed.
     */
    function test_badResult(self) {
        var test = Divmod.Test.Mock._WasRun('test_bad');
        test.run(self.result);
        self.assertArraysEqual(self.result.getSummary(), [1, 1, 0]);
        self.assert(!self.result.wasSuccessful());
    },


    /**
     * Test that the L{TestResult} distinguishes between failed assertions
     * and general errors.
     */
    function test_errorResult(self) {
        var test = Divmod.Test.Mock._WasRun('test_error');
        test.run(self.result);
        self.assertArraysEqual(self.result.getSummary(), [1, 0, 1]);
        self.assert(!self.result.wasSuccessful());
    },


    /**
     * Test that we can find out which tests had which errors and which tests
     * succeeded.
     */
    function test_resultAccumulation(self) {
        var suite = Divmod.UnitTest.TestSuite();
        var bad = Divmod.Test.Mock._WasRun('test_bad');
        var good = Divmod.Test.Mock._WasRun('test_good');
        var error = Divmod.Test.Mock._WasRun('test_error');
        suite.addTests([bad, good, error]);
        suite.run(self.result);
        self.assertArraysEqual(self.result.getSummary(), [3, 1, 1]);
        // check the failure
        self.assertIdentical(self.result.failures[0].length, 2);
        self.assertIdentical(self.result.failures[0][0], bad);
        self.assert(self.result.failures[0][1]
                    instanceof Divmod.UnitTest.AssertionError);
        self.assertIdentical(self.result.failures[0][1].message,
                             "fail this test deliberately");
        // check the error
        self.assertIdentical(self.result.errors[0].length, 2);
        self.assertIdentical(self.result.errors[0][0], error);
        self.assert(self.result.errors[0][1] instanceof Divmod.Error);
        self.assertIdentical(self.result.errors[0][1].message, "error");
        self.assertArraysEqual(self.result.successes, [good]);
    },


    /**
     * Test that neither L{tearDown} nor the test method is called when
     * L{setUp} fails.
     */
    function test_failureInSetUp(self) {
        var test = Divmod.Test.Mock._BadSetUp('test_method');
        self.assertIdentical(test.log, '');
        test.run(self.result);
        self.assertIdentical(test.log, '');
    },


    /**
     * Test that failures in L{setUp} are reported to the L{TestResult}
     * object.
     */
    function test_failureInSetUpReported(self) {
        var test = Divmod.Test.Mock._BadSetUp('test_method');
        test.run(self.result);
        self.assertArraysEqual(self.result.getSummary(), [1, 0, 1]);
    },


    /**
     * Test that failures in L{tearDown} are reported to the L{TestResult}
     * object.
     */
    function test_failureInTearDownReported(self) {
        var test = Divmod.Test.Mock._BadTearDown('test_method');
        test.run(self.result);
        self.assertArraysEqual(self.result.getSummary(), [1, 0, 1]);
    },


    /**
     * Test that a test which fails in L{tearDown} does *not* get added as
     * a success.
     */
    function test_badTearDownNotSuccess(self) {
        var test = Divmod.Test.Mock._BadTearDown('test_method');
        test.run(self.result);
        self.assertIdentical(self.result.successes.length, 0);
    },


    /**
     * Test that L{TestCase.run} calls L{TestResult.startTest} and
     * L{TestResult.stopTest}.
     */
    function test_startAndStopTest(self) {
        var test = Divmod.Test.Mock._WasRun('test_good');
        var id = test.id();
        var result = Divmod.Test.TestUnitTest.MockResult();
        test.run(result);
        self.assertIdentical(
            result.log,
            'startTest ' + id + ' addSuccess ' + id + ' stopTest ' + id);
    },


    /**
     * Test that we can create a L{TestSuite}, add tests to it, run it and
     * get the results of all of the tests.
     */
    function test_testSuite(self) {
        var suite = Divmod.UnitTest.TestSuite();
        suite.addTest(Divmod.Test.Mock._WasRun('test_good'));
        suite.addTest(Divmod.Test.Mock._WasRun('test_bad'));
        suite.run(self.result);
        self.assertArraysEqual(self.result.getSummary(), [2, 1, 0]);
        self.assert(!self.result.wasSuccessful());
    },


    /**
     * Check that C{countTestCases} returns 0 for an empty suite, 1 for a test,
     * and n for a suite with n tests.
     */
    function test_countTestCases(self) {
        self.assertIdentical(self.countTestCases(), 1);
        var suite = Divmod.UnitTest.TestSuite();
        self.assertIdentical(suite.countTestCases(), 0);
        suite.addTest(self);
        self.assertIdentical(suite.countTestCases(), 1);
        suite.addTest(Divmod.Test.Mock._WasRun('good'));
        self.assertIdentical(suite.countTestCases(), 2);
    },


    /**
     * Test that C{id} returns the fully-qualified name of the test.
     */
    function test_id(self) {
        var test = Divmod.Test.Mock._WasRun('test_good');
        self.assertIdentical(test.id(), 'Divmod.Test.Mock._WasRun.test_good');
    },


    /**
     * Test that C{visit} calls the visitor with the test case.
     */
    function test_visitCase(self) {
        var log = [];
        function visitor(test) {
            log.push(test);
        }
        self.visit(visitor);
        self.assertArraysEqual(log, [self]);
    },


    /**
     * Test that C{visit} calls the visitor for each test case in a suite.
     */
    function test_visitSuite(self) {
        var log = [];
        function visitor(test) {
            log.push(test);
        }
        Divmod.UnitTest.TestSuite().visit(visitor);
        self.assertArraysEqual(log, []);
        var tests = [self, Divmod.Test.Mock._WasRun('test_good')];
        var suite = Divmod.UnitTest.TestSuite(tests);
        suite.visit(visitor);
        self.assertArraysEqual(log, tests);
    },


    /**
     * Check that issubclass returns true when the first parameter is a subclass
     * of the second, and false otherwise.
     */
    function test_issubclass(self) {
        self.assert(self.__class__.subclassOf(self.__class__),
                    "Thing should subclass itself");
        self.assert(self.__class__.subclassOf(Divmod.UnitTest.TestCase));
        self.assert(!Divmod.UnitTest.TestCase.subclassOf(self.__class__));
    });



Divmod.Test.TestUnitTest.LoaderTests = Divmod.UnitTest.TestCase.subclass("Divmod.Test.TestUnitTest.LoaderTests");
Divmod.Test.TestUnitTest.LoaderTests.methods(
    /**
     * Return a list containing the id() of each test in a suite.
     */
    function getTestIDs(self, suite) {
        var ids = [];
        suite.visit(function (test) { ids.push(test.id()); });
        return ids;
    },


    /**
     * Test that C{loadFromClass} returns an empty suite when given a
     * C{TestCase} subclass that contains no tests.
     */
    function test_loadFromClassEmpty(self) {
        var suite = Divmod.UnitTest.loadFromClass(Divmod.UnitTest.TestCase);
        self.assertArraysEqual(self.getTestIDs(suite), []);
    },


    /**
     * Test that C{loadFromClass} returns a suite which contains all the
     * test methods in a given C{TestCase} subclass.
     */
    function test_loadFromClass(self) {
        var suite = Divmod.UnitTest.loadFromClass(Divmod.Test.Mock._WasRun);
        self.assertArraysEqual(self.getTestIDs(suite),
                               ['Divmod.Test.Mock._WasRun.test_bad',
                                'Divmod.Test.Mock._WasRun.test_error',
                                'Divmod.Test.Mock._WasRun.test_good']);
    },


    /**
     * Test that C{loadFromModule} returns an empty suite when given a module
     * with no unit tests.
     */
    function test_loadFromModuleEmpty(self) {
        var module = {};
        var suite = Divmod.UnitTest.loadFromModule(module);
        self.assertIdentical(suite.countTestCases(), 0);
    },


    /**
     * Test that C{loadFromModule} returns a suite which contains all the
     * test methods in a given module.
     */
    function test_loadFromModule(self) {
        var Mock = {};
        Mock.SomeTestCase = Divmod.UnitTest.TestCase.subclass('Mock.SomeTestCase');
        Mock.SomeTestCase.methods(function test_method(self) {});
        suite = Divmod.UnitTest.loadFromModule(Mock);
        self.assertArraysEqual(self.getTestIDs(suite),
                               ['Mock.SomeTestCase.test_method']);
    });


Divmod.Test.TestUnitTest.RunnerTest = Divmod.UnitTest.TestCase.subclass('Divmod.Test.TestUnitTest.RunnerTest');
Divmod.Test.TestUnitTest.RunnerTest.methods(
    function setUp(self) {
        self.result = Divmod.UnitTest.TestResult();
    },


    /**
     * Test that the summary of an empty result object indicates the 'test run'
     * passed, and that no tests were run.
     */
    function test_formatSummaryEmpty(self) {
        self.assertIdentical(Divmod.UnitTest.formatSummary(self.result),
                             "PASSED (tests=0)");
    },


    /**
     * Test that the summary of a result object from a successful test run
     * indicates that the run was successful along with the number of tests in
     * the run.
     */
    function test_formatSummaryOK(self) {
        var test = Divmod.Test.Mock._WasRun('test_good');
        test.run(self.result);
        self.assertIdentical(Divmod.UnitTest.formatSummary(self.result),
                             "PASSED (tests=1)");
    },


    /**
     * Test that the summary of a result object from a test run with failures
     * indicates an overall failure as well as the number of test failures.
     */
    function test_formatSummaryFailed(self) {
        var test = Divmod.Test.Mock._WasRun('test_bad');
        test.run(self.result);
        self.assertIdentical(Divmod.UnitTest.formatSummary(self.result),
                             "FAILED (tests=1, failures=1)");
    },


    /**
     * As L{test_formatSummaryFailed}, but for errors instead of failures.
     */
    function test_formatSummaryError(self) {
        var test = Divmod.Test.Mock._WasRun('test_error');
        test.run(self.result);
        self.assertIdentical(Divmod.UnitTest.formatSummary(self.result),
                             "FAILED (tests=1, errors=1)");
    },


    /**
     * Sanity test added to make sure the summary makes sense when a suite
     * has both failed and errored tests.
     */
    function test_formatSummaryMultiple(self) {
        var test = Divmod.UnitTest.loadFromClass(Divmod.Test.Mock._WasRun);
        test.run(self.result);
        self.assertIdentical(Divmod.UnitTest.formatSummary(self.result),
                             "FAILED (tests=3, errors=1, failures=1)");
    },


    /**
     * Check that L{formatErrors} returns an empty string for an empty result.
     */
    function test_formatErrorsEmpty(self) {
        self.assertIdentical(Divmod.UnitTest.formatErrors(self.result), '');
    },


    /**
     * Check that L{formatErrors} returns an empty string for a successful result.
     */
    function test_formatErrorsOK(self) {
        var test = Divmod.Test.Mock._WasRun('test_good');
        test.run(self.result);
        self.assertIdentical(Divmod.UnitTest.formatErrors(self.result), '');
    },


    /**
     * Check that the L{formatError} returns a nicely formatted representation
     * of a failed/errored test.
     */
    function test_formatError(self) {
        var test = Divmod.Test.Mock._WasRun('test_bad');
        var error, failure;
        try {
            throw Divmod.Error("error-message");
        } catch (e) {
            error = e;
            failure = Divmod.Defer.Failure(error);
        }
        self.assertIdentical(
            Divmod.UnitTest.formatError('FAILURE', test, error),
            '[FAILURE] Divmod.Test.Mock._WasRun.test_bad: error-message\n'
            + failure.toPrettyText(failure.filteredParseStack()) + '\n');
    },


    /**
     * Check that L{formatErrors} returns a string that contains all of the
     * errors and failures from the result, formatted using L{formatError}.
     */
    function test_formatErrors(self) {
        var test = Divmod.UnitTest.loadFromClass(Divmod.Test.Mock._WasRun);
        test.run(self.result);
        var expected = '';
        for (var i = 0; i < self.result.errors.length; ++i) {
            expected += Divmod.UnitTest.formatError('ERROR',
                                                self.result.errors[i][0],
                                                self.result.errors[i][1]);
        }
        for (var i = 0; i < self.result.failures.length; ++i) {
            expected += Divmod.UnitTest.formatError('FAILURE',
                                                self.result.failures[i][0],
                                                self.result.failures[i][1]);
        }
        var observed = Divmod.UnitTest.formatErrors(self.result);
        self.assertIdentical(observed, expected);
    });
