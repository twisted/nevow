// -*- test-case-name: nevow.test.test_javascript -*-

load("testsupport.js");

// import Divmod
// import Divmod.Defer

function succeedDeferred() {
    var result = null;
    var error = null;
    var d = Divmod.Defer.succeed("success");
    d.addCallback(function(res) {
        result = res;
    });
    d.addErrback(function(err) {
        error = err;
    });
    assert(result == "success", "Result was not success but instead: " + result);
    assert(error == null, "Error was not null but instead: " + error);
}

function failDeferred() {
    var result = null;
    var error = null;
    var d = Divmod.Defer.fail(Error("failure"));
    d.addCallback(function(res) {
        result = res;
    });
    d.addErrback(function(err) {
        error = err;
    });
    assert(result == null, "Result was not null but instead: " + result);
    assert(error.error.message == "failure", "Error message was not failure but instead: " + error.error.message);
}

function callThisDontCallThat() {
    var thisCalled = false;
    var thatCalled = false;
    var thisCaller = function (rlst) { thisCalled = true; }
    var thatCaller = function (err) { thatCalled = true; }

    var d = new Divmod.Defer.Deferred();

    d.addCallbacks(thisCaller, thatCaller);
    d.callback(true);

    assert(thisCalled);
    assert(!thatCalled);

    thisCalled = thatCalled = false;

    d = new Divmod.Defer.Deferred();
    d.addCallbacks(thisCaller, thatCaller);
    d.errback(new Divmod.Defer.Failure(Error("Test error for errback testing")));

    assert(!thisCalled);
    assert(thatCalled);
}

function callbackResultPassedToNextCallback() {
    var interimResult = null;
    var finalResult = null;

    var d = new Divmod.Defer.Deferred();
    d.addCallback(function(result) {
            interimResult = result;
            return "final result";
        });
    d.addCallback(function(result) {
            finalResult = result;
        });
    d.callback("interim result");

    assert(interimResult == "interim result", "Incorrect interim result: " + interimResult);
    assert(finalResult == "final result", "Incorrect final result: " + finalResult);
}

function addCallbacksAfterResult() {
    var callbackResult = null;
    var d = new Divmod.Defer.Deferred();
    d.callback("callback");
    d.addCallbacks(
        function(result) {
            callbackResult = result;
        });

    assert(callbackResult == "callback", "Callback result was " + callbackResult);
}

function deferredReturnedFromCallback() {
    var theResult = null;
    var interimDeferred = new Divmod.Defer.Deferred();
    var outerDeferred = new Divmod.Defer.Deferred();

    outerDeferred.addCallback(
        function(ignored) {
            return interimDeferred;
        });
    outerDeferred.addCallback(
        function(result) {
            theResult = result;
        });

    outerDeferred.callback("callback");

    assert(theResult == null, "theResult got value too soon: " + theResult);

    interimDeferred.callback("final result");

    assert(theResult == "final result", "theResult did not get final result: " + theResult);
}

function deferredList() {
    var defr1 = new Divmod.Defer.Deferred();
    var defr2 = new Divmod.Defer.Deferred();
    var defr3 = new Divmod.Defer.Deferred();
    var dl = new Divmod.Defer.DeferredList([defr1, defr2, defr3]);

    var result;
    function cb(resultList) {
        result = resultList;
    };

    dl.addCallback(cb);
    defr1.callback("1");
    defr2.errback(new Error("2"));
    defr3.callback("3");

    assert(result.length == 3);
    assert(result[0].length == 2);
    assert(result[0][0]);
    assert(result[0][1] == "1");
    assert(result[1].length == 2);
    assert(!result[1][0]);
    assert(result[1][1] instanceof Divmod.Defer.Failure);
    assert(result[1][1].error.message == "2");
    assert(result[2].length == 2);
    assert(result[2][0]);
    assert(result[2][1] == "3");
};

function emptyDeferredList() {
    var result = null;
    var dl = new Divmod.Defer.DeferredList([]).addCallback(function(res) {
        result = res;
    });
    assert(result instanceof Array);
    assert(result.length == 0);
};

function fireOnOneCallback() {
    var result = null;
    var dl = new Divmod.Defer.DeferredList(
        [new Divmod.Defer.Deferred(), Divmod.Defer.succeed("success")],
        true, false, false);
    dl.addCallback(function(res) {
        result = res;
    });
    assert(result instanceof Array);
    assert(result.length == 2);
    assert(result[0] == "success");
    assert(result[1] == 1);
};

function fireOnOneErrback() {
    var result = null;
    var dl = new Divmod.Defer.DeferredList(
        [new Divmod.Defer.Deferred(), Divmod.Defer.fail(new Error("failure"))],
        false, true, false);
    dl.addErrback(function(err) {
        result = err;
    });
    assert(result instanceof Divmod.Defer.Failure);
    assert(result.error instanceof Divmod.Defer.FirstError);
};

function gatherResults() {
    var result = null;
    var dl = Divmod.Defer.gatherResults([Divmod.Defer.succeed("1"),
                                         Divmod.Defer.succeed("2")]);
    dl.addCallback(function(res) {
        result = res;
    });
    assert(result instanceof Array);
    assert(result.length == 2);
    assert(result[0] == "1");
    assert(result[1] == "2");
};

runTests([succeedDeferred,
          failDeferred,
          callThisDontCallThat,
          callbackResultPassedToNextCallback,
          addCallbacksAfterResult,
          deferredReturnedFromCallback,
          deferredList,
          emptyDeferredList,
          fireOnOneCallback,
          fireOnOneErrback,
          gatherResults]);
