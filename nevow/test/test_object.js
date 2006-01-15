#!/usr/bin/smjs

/*
 *  Unit tests.
 * These don't work in any browser yet
 *on account of the smjs 'print' and 'load'
 builtins
 */

load("../MochiKit/Base.js");
load("../MochiKit/Async.js");
MochiKit.DOM = {};
MochiKit.DOM.addLoadEvent = function () {}
load("../athena.js");

function assert (cond, err) {
    if (!cond) {
        throw new Error("Test Failure: " + err);
    }
}

function testClass() {
    var Eater = Divmod.Class.subclass();

    Eater.prototype.__init__ = function (foodFactory) {
        this.food = foodFactory();
    };

    Eater.classCounter = 0;

    Eater.classIncr = function() {
        this.classCounter += 1;
    };

    Eater.prototype.doEat = function() {
        return this.food + 1;
    };

    var BetterEater = Eater.subclass();

    BetterEater.prototype.__init__ = function(foodFactory) {
        BetterEater.upcall(this, "__init__", foodFactory);
        this.food += 10;
    };

    var makeFood = function() {
        return 100;
    }

    var be = new BetterEater(makeFood);

    Eater.classIncr();
    Eater.classIncr();
    Eater.classIncr();
    BetterEater.classIncr();
    BetterEater.classIncr();

    assert(be.doEat() == 111, "explode");

    assert(Eater.classCounter == 3, 'classmethod fuckup');
    assert(BetterEater.classCounter == 2, 'classmethod fuckup');
}

function testUtil() {
    /* Divmod.namedAny
     */
    assert(Divmod.namedAny('not.a.real.package.or.name') == undefined);
    assert(Divmod.namedAny('Divmod') == Divmod);
    assert(Divmod.namedAny('Divmod.namedAny') == Divmod.namedAny);
}

function testMethod() {
    var MethodClassTest = Divmod.Class.subclass();

    /* Backwards compatibility test - this usage is deprecated
     */
    MethodClassTest.method(
	"foo", function(self) {
	    return function () {
		return self;
	    };
	});

    /* This is the real way to do it
     */
    MethodClassTest.method(function bar(self) {
        return function() {
            return self;
        };
    });

    var mct = new MethodClassTest();

    assert(mct.foo()() === mct);
    assert(mct.bar()() === mct);
}

function testLogger() {
    var logEvents = [];

    var removeObserver = Divmod.logger.addObserver(function(event) { logEvents.push(event); });

    var logmsg = "(logging system test error) Hello, world";
    Divmod.msg(logmsg);

    assert(logEvents.length == 1);
    assert(logEvents[0].isError == false);
    assert(logEvents[0].message == logmsg);

    logEvents = [];

    var logerr = "(logging system test error) Doom, world.";
    Divmod.err(new Error(logerr), logmsg);

    assert(logEvents.length == 1);
    assert(logEvents[0].isError == true);
    assert(logEvents[0].error instanceof Error);
    assert(logEvents[0].error.message == logerr);
    assert(logEvents[0].message == logmsg);

    removeObserver();
    logEvents = [];
    Divmod.msg(logmsg);
    assert(logEvents.length == 0);

    var observererr = "(logging system test error) Observer had a bug.";
    Divmod.logger.addObserver(function(event) { throw new Error(observererr); });
    Divmod.logger.addObserver(function(event) { logEvents.push(event); });

    Divmod.msg(logmsg);
    Divmod.msg(logerr);
    assert(logEvents.length == 3, "Incorrect number of events logged");
    assert(logEvents[0].isError == false, "First event should not have been an error");
    assert(logEvents[0].message == logmsg, "First event had wrong message");
    assert(logEvents[1].isError == true, "Second event should have been an error");
    assert(logEvents[1].error.message == observererr, "Second event had wrong message");
    assert(logEvents[2].isError == false, "Third event should not have been an error");
    assert(logEvents[2].message == logerr, "Third event had wrong message");

}

Divmod.logger.addObserver(function(event) {
    if (event['isError']) {
        print(event['error']);
    }
});

var testFunctions = [
    testClass,
    testUtil,
    testMethod,
    testLogger];

for (var i = 0; i < testFunctions.length; ++i) {
    testFunctions[i]();
}
print("SUCCESS");
