// -*- test-case-name: nevow.test.test_javascript.JSUnitTests.test_runtime -*-
/**
 * Unit Tests for Divmod.Runtime.
 *
 * There are not enough tests here, because the unit test framework for
 * Javascript, and perhaps more importantly the mock browser document
 * implementation, were added long after the Runtime module was introduced.
 * However, as any functionality is changed or updated or bugs are fixed,
 * tests should be added here to verify various behaviors of the runtime.  Any
 * necessary functionality should be added to MockBrowser to facilitate those
 * tests.
 */

// import Divmod.UnitTest
// import Divmod.Runtime

Divmod.Test.TestRuntime.RuntimeTests = Divmod.UnitTest.TestCase.subclass(
    'Divmod.Test.TestRuntime.RuntimeTests');
Divmod.Test.TestRuntime.RuntimeTests.methods(
    /**
     * Verify that traversal of nested nodes will result in retrieving all the
     * nodes in depth-first order.
     */
    function test_traverse(self) {
        var d = document;

        var firstNode = d.createElement('firstNode');
        var secondNode = d.createElement('secondNode');
        var thirdNode = d.createElement('thirdNode');
        var fourthNode = d.createElement('fourthNode');

        secondNode.appendChild(thirdNode);
        firstNode.appendChild(secondNode);
        firstNode.appendChild(fourthNode);
        var nodes = [];
        Divmod.Runtime.theRuntime.traverse(firstNode, function (aNode) {
            nodes.push(aNode);
            return Divmod.Runtime.Platform.DOM_DESCEND;
        });

        self.assertIdentical(nodes.length, 4);
        self.assertIdentical(nodes[0], firstNode);
        self.assertIdentical(nodes[1], secondNode);
        self.assertIdentical(nodes[2], thirdNode);
        self.assertIdentical(nodes[3], fourthNode);
    });
