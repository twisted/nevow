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
        throw new Error("Test Failure: "+err);
    }
}

function test() {
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

test();
print("SUCCESS");
