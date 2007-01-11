// -*- test-case-name: nevow.test.test_javascript.JavaScriptTestSuite.testJSBase

function test_reprString() {
    /**
     * Test L{Divmod.Base.reprString} correctly escapes various whitespace
     * characters.
     */
    var s = '\r\n\f\b\t';
    var repr = Divmod.Base.reprString(s)
    var expected = "\"\\r\\n\\f\\b\\t\"";
    assert(repr == expected, "Expected " + expected + ", got " + repr);
};

function test_serializeJSON() {
    /**
     * Trivial JSON serialization test.  Not nearly comprehensive.  This code
     * is going away soon anyway.
     */
    var expr = [{a: 1, b: "2"}];
    var json = Divmod.Base.serializeJSON(expr);
    var expected = "[{\"a\":1, \"b\":\"2\"}]";
    assert(json == expected, "Expected " + expected + ", got " + json);
};

runTests([test_reprString,
          test_serializeJSON]);
