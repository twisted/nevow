// -*- test-case-name: nevow.test.test_javascript.JavaScriptTestSuite.testJSInspect

// import Divmod.Inspect

/**
 * Test that L{Divmod.Inspect.methods} returns all the methods of a class
 * object.
 */
function test_methods() {

    /* Divmod.Class has no visible toString method for some reason.  If this
     * ever changes, feel free to change this test.
     */
    assertArraysEqual(
        Divmod.Inspect.methods(Divmod.Class),
        ["__init__"]);

    var TestClass = Divmod.Class.subclass("test_inspect.test_methods.TestClass");
    TestClass.methods(function method() {});

    /* Subclasses get two methods automagically, __init__ and toString.  If
     * this ever changes, feel free to change this test.
     */
    assertArraysEqual(
        Divmod.Inspect.methods(TestClass),
        ["__init__", "method", "toString"]);


    var TestSubclass = TestClass.subclass("test_inspect.test_methods.TestSubclass");
    TestSubclass.methods(function anotherMethod() {});

    assertArraysEqual(
        Divmod.Inspect.methods(TestSubclass),
        ["__init__", "anotherMethod", "method", "toString"]);
};

/**
 * Test that an appropriate exception is raised if the methods of an instance
 * are requested.
 */
function test_methodsAgainstInstance() {
    var msg = "Only classes have methods.";
    var error;

    error = assertThrows(
        Error,
        function() {
            return Divmod.Inspect.methods([]);
        });
    assertEqual(error.message, msg);

    error = assertThrows(
        Error,
        function() {
            return Divmod.Inspect.methods({});
        });
    assertEqual(error.message, msg);

    error = assertThrows(
        Error,
        function() {
            return Divmod.Inspect.methods(0);
        });
    assertEqual(error.message, msg);

    error = assertThrows(
        Error,
        function() {
            return Divmod.Inspect.methods("");
        });
    assertEqual(error.message, msg);

    error = assertThrows(
        Error,
        function() {
            return Divmod.Inspect.methods(Divmod.Class());
        });
    assertEqual(error.message, msg);
};

runTests([test_methods,
          test_methodsAgainstInstance]);
