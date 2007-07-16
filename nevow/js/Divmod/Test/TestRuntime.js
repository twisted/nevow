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
     * Node.appendChild should accept a TextNode and add it to the childNodes
     * array.
     */
    function test_appendTextNode(self) {
        var words = 'words';
        var node = document.createElement('span');
        var text = document.createTextNode(words);
        node.appendChild(text);
        self.assertIdentical(node.childNodes.length, 1);
        self.assertIdentical(node.childNodes[0].nodeValue, words);
    },

    /**
     * When a node is removed from its parent with removeChild, the parentNode
     * property of the removed node should be set to null.
     */
    function test_removeChildClearsParent(self) {
        var parent = document.createElement('span');
        var child = document.createElement('span');
        parent.appendChild(child);
        parent.removeChild(child);
        self.assertIdentical(child.parentNode, null);
    },

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
    },

    /**
     * It should be possible to find a node with a particular id starting from
     * a node with implements the DOM API.
     *
     * Elements are documented here:
     *
     * http://www.w3.org/TR/REC-DOM-Level-1/level-one-core.html#ID-745549614
     */
    function test_getElementByIdWithNode(self) {
        var id = 'right';
        var node;
        var child;

        node = document.createElement('a');
        node.id = id;
        document.body.appendChild(node);
        self.assertIdentical(
            Divmod.Runtime.theRuntime.getElementByIdWithNode(node, id),
            node);

        self.assertThrows(
            Divmod.Runtime.NodeNotFound,
            function() {
                Divmod.Runtime.theRuntime.getElementByIdWithNode(
                    node, 'wrong');
            });

        node = document.createElement('a');
        child = document.createElement('b');
        child.id = 'wrong';
        node.appendChild(child);
        child = document.createElement('c');
        child.id = id;
        node.appendChild(child);
        document.body.appendChild(node);

        self.assertIdentical(
            Divmod.Runtime.theRuntime.getElementByIdWithNode(node, id).id,
            id)
    });
