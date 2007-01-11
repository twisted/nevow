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
};


/**
 * Test that Divmod.Class subclasses have a __name__ attribute which gives
 * their name.
 */
function test_className(self) {
    var cls = Divmod.Class.subclass("test_object.test_className.cls");
    assertEqual(cls.__name__, "test_object.test_className.cls");

    /* Make sure subclasses don't inherit __name__ from their superclass.
     */
    var subcls = cls.subclass("test_object.test_className.subcls");
    assertEqual(subcls.__name__, "test_object.test_className.subcls");
};

/**
 * Test that instances of Divmod.Class have a __class__ attribute which refers
 * to their class.
 */
function test_instanceClassReference() {
    var cls = Divmod.Class.subclass("test_object.test_instanceClassReference.cls");
    var instance;

    instance = cls();
    assertEqual(instance.__class__, cls);

    instance = new cls();
    assertEqual(instance.__class__, cls);

    instance = cls.apply(null, []);
    assertEqual(instance.__class__, cls);

    instance = cls.call(null);
    assertEqual(instance.__class__, cls);
};

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

/**
 * Test that L{Divmod.objectify} properly zips two lists into an object with
 * properties from the first list bound to the objects from the second.
 */
function test_objectify() {
    var keys = ["one", "two", "red", "blue"];
    var values = [1, 2, [255, 0, 0], [0, 0, 255]];
    var obj = Divmod.objectify(keys, values);
    assertEqual(obj.one, 1);
    assertEqual(obj.two, 2);
    assertArraysEqual(obj.red, [255, 0, 0]);
    assertArraysEqual(obj.blue, [0, 0, 255]);

    /*
     * Test that it fails loudly on invalid input, too.
     */
    var msg = "Lengths of keys and values must be the same.";
    var error;

    error = assertThrows(Error, function() { Divmod.objectify([], ["foo"]); });
    assertEqual(error.message, msg);

    error = assertThrows(Error, function() { Divmod.objectify(["foo"], []); });
    assertEqual(error.message, msg);
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
    test_className,
    test_instanceClassReference,
    testNewlessInstantiation,
    testUtil,
    test_objectify,
    testMethod,
    testLogger];

runTests(testFunctions);
