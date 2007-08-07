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
     * Assert that the various *_NODE attributes are present with the correct
     * values.
     *
     * Note: Actually, there should be quite a few other attributes as well.
     * See
     * <http://www.w3.org/TR/REC-DOM-Level-1/level-one-core.html#ID-1950641247>.
     * Feel free to add them as necessary.
     */
    function _attributesTest(self, node) {
        self.assertIdentical(node.ELEMENT_NODE, 1);
        self.assertIdentical(node.TEXT_NODE, 3);
        self.assertIdentical(node.DOCUMENT_NODE, 9);
    },

    /**
     * Nodes should have L{ELEMENT_NODE} and L{TEXT_NODE} attributes.
     */
    function test_nodeAttributes(self) {
        var node = document.createElement('span');
        self._attributesTest(node);
    },

    /**
     * Documents should have L{ELEMENT_NODE} and L{TEXT_NODE} attributes.
     */
    function test_documentAttributes(self) {
        self._attributesTest(document);
    },

    /**
     * The nodeType property of a Document should be C{DOCUMENT_NODE}.
     */
    function test_documentNodeType(self) {
        self.assertIdentical(document.nodeType, document.DOCUMENT_NODE);
    },

    /**
     * The nodeType property of an element should be C{ELEMENT_NODE}.
     */
    function test_elementNodeType(self) {
        var node = document.createElement('span');
        self.assertIdentical(node.nodeType, document.ELEMENT_NODE);
    },

    /**
     * The nodeType property of a text node should be C{TEXT_NODE}.
     */
    function test_textNodeNodeType(self) {
        var node = document.createTextNode('foo');
        self.assertIdentical(node.nodeType, document.TEXT_NODE);
    },

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
     * A node can be replaced in its parent's children list with the parent's
     * C{replaceNode} method.  C{replaceNode} returns the node which was
     * replaced.
     */
    function test_replaceChild(self) {
        var parent = document.createElement('SPAN');
        var oldChild = document.createElement('A');
        var newChild = document.createElement('B');

        parent.appendChild(document.createElement('BEFORE'));
        parent.appendChild(oldChild);
        parent.appendChild(document.createElement('AFTER'));

        var returned = parent.replaceChild(newChild, oldChild);
        self.assertIdentical(returned, oldChild);

        self.assertIdentical(parent.childNodes.length, 3);
        self.assertIdentical(parent.childNodes[0].tagName, 'BEFORE');
        self.assertIdentical(parent.childNodes[1].tagName, 'B');
        self.assertIdentical(parent.childNodes[2].tagName, 'AFTER');

        self.assertIdentical(oldChild.parentNode, null);
        self.assertIdentical(newChild.parentNode, parent);
    },

    /**
     * L{Element.replaceChild} should throw a L{DOMError} when invoked with an
     * old child argument which is not a child of the node.
     */
    function test_replaceChildThrows(self) {
        var parent = document.createElement('SPAN');
        var nonChild = document.createElement('A');
        var newChild = document.createElement('B');

        self.assertThrows(
            DOMException,
            function() {
                parent.replaceChild(newChild, nonChild);
            });
        self.assertIdentical(parent.childNodes.length, 0);
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
