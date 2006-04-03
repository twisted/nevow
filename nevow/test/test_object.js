#!/usr/bin/smjs

load("testsupport.js");

// import Divmod

/*
 *  Unit tests.
 * These don't work in any browser yet
 *on account of the smjs 'print' and 'load'
 builtins
 */

function testClass() {
    var Eater = Divmod.Class.subclass('Eater');

    Eater.methods(
        function __init__(self, foodFactory) {
            self.food = foodFactory();
        },

        function doEat(self) {
            return self.food + 1;
        });

    Eater.classCounter = 0;

    Eater.classIncr = function() {
        this.classCounter += 1;
    };

    var BetterEater = Eater.subclass('BetterEater');

    BetterEater.methods(
        function __init__(self, foodFactory) {
            BetterEater.upcall(self, "__init__", foodFactory);
            self.food += 10;
        });

    var makeFood = function() {
        return 100;
    };

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

function testNewlessInstantiation() {
    /*
     * Test that Divmod.Class subclasses can be instantiated without using
     * `new', as well as using .apply() and .call().
     */
    var SomeClass = Divmod.Class.subclass("SomeClass");
    SomeClass.methods(
        function __init__(self, x, y) {
            self.x = x;
            self.y = y;
        });

    var a = SomeClass(1, 2);
    assert(a.x == 1, "Normal instantiation without new lost an argument");
    assert(a.y == 2, "Normal instantiation without new lost an argument");

    var b = SomeClass.apply(null, [1, 2]);
    assert(b.x == 1, ".apply() instantiation lost an argument");
    assert(b.y == 2, ".apply() instantiation lost an argument");

    var c = SomeClass.call(null, 1, 2);
    assert(c.x == 1, ".call() instantiation lost an argument");
    assert(c.y == 2, ".call() instantiation lost an argument");
}

function testUtil() {
    /* Divmod.namedAny
     */
    assert(Divmod.namedAny('not.a.real.package.or.name') == undefined);
    assert(Divmod.namedAny('Divmod') == Divmod);
    assert(Divmod.namedAny('Divmod.namedAny') == Divmod.namedAny);

    var path = [];
    assert(Divmod.namedAny('Divmod', path) == Divmod);
    assert(path.length == 0);

    assert(Divmod.namedAny('Divmod.namedAny', path) == Divmod.namedAny);
    assert(path.length == 1);
    assert(path[0] == Divmod);
}

function testMethod() {
    var MethodClassTest = Divmod.Class.subclass('MethodClassTest');

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

    MethodClassTest.methods(
        function quux(self) {
            return function() { return self; };
        },
        function corge(self) {
            return function() { return self; };
        }
    );

    var mct = new MethodClassTest();

    assert(mct.foo()() === mct);
    assert(mct.bar()() === mct);
    assert(mct.quux()() === mct);
    assert(mct.corge()() === mct);
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
    testNewlessInstantiation,
    testUtil,
    testMethod,
    testLogger];

runTests(testFunctions);
