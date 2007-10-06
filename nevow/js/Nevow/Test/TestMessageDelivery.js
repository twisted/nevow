// -*- test-case-name: nevow.test.test_javascript.JSUnitTests.test_rdm -*-

// import Divmod
// import Divmod.UnitTest
// import Divmod.Defer
// import Divmod.Test.TestRuntime
// import Nevow.Athena

Nevow.Test.TestMessageDelivery.ReliableMessageDeliveryTests = Divmod.UnitTest.TestCase.subclass(
    "Nevow.Test.TestMessageDelivery.ReliableMessageDeliveryTests");

Nevow.Test.TestMessageDelivery.ReliableMessageDeliveryTests.methods(
    /**
     * Create a ReliableMessageDelivery with a mock output factory and
     * connection lost notification that record the associated information
     * with the calls on this test case.
     */
    function setUp(self) {
        self.requests = [];
        self.lostConnection = false;
        self.channel = Nevow.Athena.ReliableMessageDelivery(
            function (synchronous) {
                if (synchronous === undefined) {
                    synchronous = false;
                }
                var d = Divmod.Defer.Deferred();
                var output = {
                  send: function (ack, messages) {
                        var theReq = {
                          // things expected by interface
                          abort: function () {
                                this.aborted = true;
                            },
                          deferred: d,
                          aborted: false,
                          // things we want to check on
                          synchronous: synchronous,
                          ack: ack,
                          messages: messages.slice()
                        };
                        self.requests.push(theReq);
                        return theReq;
                    }
                };
                return output;
            },
            function () {
                self.lostConnection = true;
            });
        // Used for testing 'call' method dispatching.
        Nevow.Test.TestMessageDelivery.TEMPORARY_GLOBAL = self;
    },

    function tearDown(self) {
        delete Nevow.Test.TestMessageDelivery.TEMPORARY_GLOBAL;
    },

    /**
     * Verify that starting the channel sets the 'running' attribute to true,
     * and will make an outgoing request with no payload.  This request is
     * provided so that the server can send notifications.
     */
    function test_startChannel(self) {
        // Sanity check.
        self.assertIdentical(self.requests.length, 0);
        self.assertIdentical(self.channel.running, false);
        self.channel.start();
        self.assertIdentical(self.channel.running, true);
        self.assertIdentical(self.requests.length, 1);
        var r = self.requests[0];
        self.assertArraysEqual(r.messages, []);
    },

    /**
     * Verify that adding a message to a ReliableMessageDelivery will make an
     * outgoing request that will be queued until that request completes
     * successfully.
     */
    function test_addMessage(self) {
        self.channel.start();
        var MESSAGE = "A message that the test is sending";
        self.channel.addMessage(MESSAGE);

        self.assertIdentical(self.requests.length, 2);
        var r = self.requests[1];
        self.assertIdentical(r.messages.length, 1);
        self.assertArraysEqual(r.messages[0], [0, MESSAGE]);
        self.assertIdentical(self.channel.messages.length,
                             1);
        self.assertArraysEqual(self.channel.messages[0], [0, MESSAGE]);
        // Now, have the server acknowledge the message in a noop.
        r.deferred.callback([0, [[0, ["noop", []]]]]);
        self.assertArraysEqual(self.channel.messages, []);
        // Only the "live" connection should remain.
        self.assertArraysEqual(self.channel.requests, [self.requests[0]]);
    },

    /**
     * When the server answers the last outstanding request, the reliable
     * message delivery should create a new one.
     */
    function test_answeringLastRequest(self) {
        self.channel.start();
        self.requests[0].deferred.callback([-1, [[0, ["noop", []]]]]);
        self.assertIdentical(self.requests.length, 2);
        self.assertIdentical(self.channel.requests.length, 1);
    },

    /**
     * Verify that messages from the server are sent to an action_ method on
     * the reliable message delivery object.
     */
    function test_messageDispatch(self) {
        self.channel.start();
        var checkA = 3;
        var checkB = "stuff";
        var checkC = {other: "stuff"};
        var called = true;
        var gotA = null;
        var gotB = null;
        var gotC = null;
        var checkThis = null;
        self.channel.action_testaction = function (a, b, c) {
            checkThis = this;
            gotA = a;
            gotB = b;
            gotC = c;
        }
        self.requests[0].deferred.callback(
            [-1, [[0, ["testaction", [checkA, checkB, checkC]]]]]);
        self.assertIdentical(gotA, checkA);
        self.assertIdentical(gotB, checkB);
        self.assertIdentical(gotC, checkC);
        self.assertIdentical(checkThis, self.channel);
    },

    /**
     * Messages with the same sequence number should only be processed once.
     */
    function test_sequenceChecking(self) {
        var dupcount = 0;
        self.channel.action_duplicate = function () {
            dupcount++;
        };
        self.channel.messageReceived([[0, ["duplicate", []]]]);
        self.assertIdentical(dupcount, 1);
        self.channel.messageReceived([[0, ["duplicate", []]]]);
        self.assertIdentical(dupcount, 1);
        self.channel.messageReceived([[1, ["duplicate", []]]]);
        self.assertIdentical(dupcount, 2);
    },

    /**
     * Test that the 'noop' action does nothing, so the server can ping us.
     */
    function test_noopAction(self) {
        self.channel.action_noop();
    },

    /**
     * A test for a call action.
     *
     * @param toReturn: a 2-arg function which takes the expected return value
     * and may return it, raise an exception, or return a Deferred that wraps
     * it (or fails).  The second argument to is is a 1-arg function which
     * changes the return value to expect.
     *
     * @param: expectSuccess: a boolean, whether the test should expect the
     * method to succeed.
     */
    function callActionTest(self, toReturn, expectSuccess) {
        var innerThis = null;
        var innerArg = null;
        var TEST_ARG = "test argument";
        var OPAQUE_ID = 'opaque-identifier';
        var RESULT = 'resulting value';
        var expected = RESULT;
        self.tempMethod = function (arg) {
            innerThis = this;
            innerArg = arg;
            return toReturn(RESULT, function (arg) {
                expected = arg;
            });
        };
        self.channel.action_call(
            'Nevow.Test.TestMessageDelivery.TEMPORARY_GLOBAL.tempMethod',
            OPAQUE_ID, [TEST_ARG]);
        self.assertIdentical(innerArg, TEST_ARG);
        self.assertIdentical(innerThis, self);
        var msg = self.channel.messages[0][1];
        var args = msg[1];
        self.assertIdentical(msg[0], "respond");
        self.assertArraysEqual(args, [OPAQUE_ID, expectSuccess, expected]);
    },

    /**
     * The 'call' action should invoke a given global function and return its
     * value to the server along with a flag indicating it succeed by adding a
     * new message.
     */
    function test_callAction(self) {
        self.callActionTest(function (value) {
            return value;
        }, true);
    },

    /**
     * The 'call' action should invoke a given global function and, if that
     * function raises an exception, serialize that exception along with a
     * flag indicating it failed by adding a new message.
     */
    function test_callActionFail(self) {
        self.callActionTest(function (value, expect) {
            var e = new Error();
            expect(e);
            throw e;
        }, false);
    },

    /**
     * The 'call' action should invoke a given global function and return the
     * result of its deferred to the server along with a flag indicating it
     * succeed by adding a new message.
     */
    function test_callActionDeferred(self) {
        self.callActionTest(function (value, expect) {
            var d = Divmod.Defer.succeed(value);
            expect(value);
            return d;
        }, true);
    },

    /**
     * The 'call' action should invoke a given global function and return the
     * failure from its deferred to the server along with a flag indicating it
     * failed by adding a new message.
     */
    function test_callActionDeferredFail(self) {
        self.callActionTest(function (value, expect) {
            var e = new Error();
            expect(e);
            return Divmod.Defer.fail(e);
        }, false);
    },

    /**
     * The 'respond' action should look up a Deferred in the remoteCalls
     * object and delete it.
     */
    function test_respondAction(self) {
        var OPAQUE_ID = "opaque test remote call id";
        var RESULT = "opaque test result";
        var d = Divmod.Defer.Deferred();
        var innerResult = null;
        d.addCallback(function (result) {
            innerResult = result;
        });
        Nevow.Athena.remoteCalls[OPAQUE_ID] = d;
        self.channel.action_respond(OPAQUE_ID, true, RESULT);
        self.assert(!(OPAQUE_ID in Nevow.Athena.remoteCalls));
        self.assertIdentical(innerResult, RESULT);
    },

    /**
     * The 'close' action should stop the reliable message delivery channel.
     */
    function test_closeAction(self) {
        self.channel.action_close();
        self.assertIdentical(self.channel.running, false);
        self.assertIdentical(self.lostConnection, true);
    },

    /**
     * When the reliable message delivery channel is closed, it must be done
     * in a few steps:
     *
     *  - terminate all current asynchronous reqeusts
     *    (The page would shut them down in a moment anyway, and forcing them
     *    to tear down while the environment is still under our control will
     *    allow everything to shut down gracefully, and will, for example,
     *    avoid tickling bugs in firebug.)
     *
     * - make one synchronous request containing a single message telling the
     *   server that the connection has been terminated.
     *
     * This technique is documented here:
     *
     * http://www.hunlock.com/blogs/Mastering_The_Back_Button_With_Javascript#quickIDX6
     *
     * This is really sub-optimal, and we shouldn't *need* any page tear-down
     * at all; the message queue should be structured such that the server can
     * notice connections have gone away.
     */
    function test_sendCloseMessage(self) {
        self.channel.start();
        self.channel.addMessage("message1");
        self.channel.sendCloseMessage();
        self.assertIdentical(self.requests.length, 3);
        // created by 'start'
        self.assertIdentical(self.requests[0].synchronous, false);
        self.assertIdentical(self.requests[0].aborted, true);
        // created by 'message1'
        self.assertIdentical(self.requests[1].synchronous, false);
        self.assertIdentical(self.requests[1].aborted, true);
        // created by 'sendCloseMessage'
        self.assertIdentical(self.requests[2].synchronous, true);
        self.assertIdentical(self.requests[2].aborted, false);
        self.assertIdentical(self.requests[2].ack, -1);
        // Check for the special sequence number
        self.assertIdentical(self.requests[2].messages[0][0], "unload");
        // the command
        self.assertIdentical(self.requests[2].messages[0][1][0], "close");
        // the command's arguments
        self.assertArraysEqual(self.requests[2].messages[0][1][1], []);
    });

/**
 * Tests to ensure that global state is set up properly.
 */
Nevow.Test.TestMessageDelivery.GlobalSetupTests = Divmod.UnitTest.TestCase.subclass(
    "Nevow.Test.TestMessageDelivery.GlobalSetupTests");

Nevow.Test.TestMessageDelivery.GlobalSetupTests.methods(

    /**
     * Set up a list of objects which were mocked so they can be restored in
     * tearDown.
     */
    function setUp(self) {
        self._mocks = [];
    },

    /**
     * Safely replace an attribute for the duration of the test, such that it will
     * be restored in tearDown.
     */
    function mockForTest(self, name, newValue, parent /* = Divmod._global */) {
        if (parent === undefined) {
            parent = Divmod._global;
        }
        self._mocks.push({parent: parent,
                name: name,
                original: parent[name]});
        parent[name] = newValue;
    },

    /**
     * Put back all objects which were mocked for the duration of this test.
     */
    function tearDown(self) {
        for (var i = 0; i < self._mocks.length; i++) {
            var mock = self._mocks[i];
            mock.parent[mock.name] = mock.original;
        }
    },

    /**
     * Verify that the _createMessageDelivery function creates a
     * MessageDelivery object that creates HTTPRequestOutput objects for its
     * outputFactory, and will invoke Nevow.Athena._connectionLost when its
     * connection is lost.
     */
    function test_createMessageDelivery(self) {
        self.mockForTest("window", {location: "http://unittest.example.com/"})
        var testRDM = Nevow.Athena._createMessageDelivery();
        var asyncfactory = testRDM.outputFactory();
        self.assert(asyncfactory instanceof Nevow.Athena.HTTPRequestOutput);
        self.assertIdentical(asyncfactory.synchronous, false);
        var syncfactory = testRDM.outputFactory(true);
        self.assertIdentical(syncfactory.synchronous, true);
        self.assertIdentical(testRDM.connectionLost, Nevow.Athena._connectionLost);
    },

    /**
     * Verify that the HTTPRequestOutput sends the appropriate request via the
     * runtime.
     */
    function test_outputSend(self) {
        var reqs = [];
        self.mockForTest("makeHTTPRequest",
                         function () {
                             var fr = Divmod.Test.TestRuntime.FakeRequest();
                             reqs.push(fr);
                             return fr;
                         },
                         Divmod.Runtime.theRuntime);
        var reqOut = Nevow.Athena.HTTPRequestOutput(
            "http://unittest.example.com/",
            [["test", "arg"]],
            [['header', 'value']],
            true);
        reqOut.send(5, ["hello"]);
        self.assertIdentical(reqs.length, 1);
        self.assertArraysEqual(reqs[0].opened, ["POST", "http://unittest.example.com/?test=arg", false]);
        self.assertArraysEqual(reqs[0].sent, ['[5, ["hello"]]']);
    });
