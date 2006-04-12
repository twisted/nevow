

function runTests(testFunctions) {
    var testFailures = 0;
    print("(JS)...");
    for (var i = 0; i < testFunctions.length; ++i) {
        try {
            testFunctions[i]();
            print("  " + testFunctions[i].name + "... [OK]");
        } catch (e) {
            print("  " + testFunctions[i].name + "... [FAIL]");
            print(e.message);
            print(e.stack);
            testFailures++;
        }
    }
    if (testFailures > 0) {
        throw new Error("***** FAILED *****");
    }
}

function assert (cond, err) {
    if (!cond) {
        throw new Error("Test Failure: " + err);
    }
}


MochiKit = {};
MochiKit.DOM = {};
MochiKit.DOM.addLoadEvent = function () {};

_testsupportDummyScheduler = [];
function setTimeout(f, n) {
    _testsupportDummyScheduler.push([n, f]);
}

/*
 * XXX TODO: actually parse //import lines, don't always import everything.
 */


var Divmod = {};
load("../divmod.js");

Divmod.Defer = {};
load("../defer.js");

var Nevow = {};
load("../nevow.js");
