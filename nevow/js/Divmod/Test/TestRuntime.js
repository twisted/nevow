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
     * Verify that C{insertBefore} sticks the new node at the right place in
     * the C{childNodes} array, and sets the appropriate parent.
     */
    function test_insertBefore(self) {
        var top = document.createElement('div');
        var reference = document.createElement('div');
        top.appendChild(reference);
        var toInsert = document.createElement('div');
        top.insertBefore(toInsert, reference);
        self.assertIdentical(toInsert.parentNode, top);
        self.assertIdentical(top.childNodes[0], toInsert);
        self.assertIdentical(top.childNodes[1], reference);
        self.assertIdentical(top.childNodes.length, 2);
    },

    /**
     * Verify that C{insertBefore} returns the inserted node.
     */
    function test_insertBeforeReturnValue(self) {
        var top = document.createElement('div');
        var reference = document.createElement('div');
        top.appendChild(reference);
        var toInsert = document.createElement('div');
        self.assertIdentical(top.insertBefore(toInsert, reference), toInsert);
    },

    /**
     * Verify that C{insertBefore} returns the inserted node when the
     * reference node is C{null}.
     */
    function test_insertBeforeReturnValueNoReference(self) {
        var top = document.createElement('div');
        var toInsert = document.createElement('div');
        self.assertIdentical(top.insertBefore(toInsert, null), toInsert);
    },

    /**
     * Verify that C{insertBefore} appends the node to its child array when
     * the reference node is C{null}.
     */
     function test_insertBeforeNoReference(self) {
        var top = document.createElement('div');
        var toInsert = document.createElement('div');
        top.insertBefore(toInsert, null);
        self.assertIdentical(toInsert.parentNode, top);
        self.assertIdentical(top.childNodes.length, 1);
        self.assertIdentical(top.childNodes[0], toInsert);
    },

    /**
     * C{insertBefore} should throw a C{DOMError} if its passed a non C{null}
     * reference node which is not one of its child nodes.
     */
    function test_insertBeforeBadReference(self) {
        self.assertThrows(
            DOMException,
            function() {
                document.createElement('div').insertBefore(
                    document.createElement('div'),
                    document.createElement('div'));
            });
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
            id);
    },

    /**
     * I{firstNodeByAttribute} should return the highest, left-most node in the
     * DOM with a matching attribute value.
     */
    function test_firstNodeByAttribute(self) {
        /*
         * Save some typing.
         */
        function find(root, attrName, attrValue) {
            return Divmod.Runtime.theRuntime.firstNodeByAttribute(
                root, attrName, attrValue);
        }
        var root = document.createElement('div');
        root.setAttribute('foo', 'bar');
        self.assertIdentical(find(root, 'foo', 'bar'), root);

        var childA = document.createElement('h1');
        childA.setAttribute('foo', 'bar');
        childA.setAttribute('baz', 'quux');
        root.appendChild(childA);
        self.assertIdentical(find(root, 'foo', 'bar'), root);
        self.assertIdentical(find(root, 'baz', 'quux'), childA);

        var childB = document.createElement('h2');
        childB.setAttribute('foo', 'bar');
        childB.setAttribute('baz', 'quux');
        root.appendChild(childB);
        self.assertIdentical(find(root, 'foo', 'bar'), root);
        self.assertIdentical(find(root, 'baz', 'quux'), childA);

        var childC = document.createElement('h3');
        childC.setAttribute('foo', 'bar');
        childC.setAttribute('baz', 'quux');
        childA.appendChild(childC);
        self.assertIdentical(find(root, 'foo', 'bar'), root);
        self.assertIdentical(find(root, 'baz', 'quux'), childA);

        var childD = document.createElement('h4');
        childD.setAttribute('corge', 'grault');
        childB.appendChild(childD);
        self.assertIdentical(find(root, 'corge', 'grault'), childD);
    },

    /**
     * I{firstNodeByAttribute} should throw an error if no node matches the
     * attribute name and value supplied.
     */
    function test_firstNodeByAttributeThrows(self) {
        var root = document.createElement('span');
        self.assertThrows(
            Error,
            function() {
                return Divmod.Runtime.theRuntime.firstNodeByAttribute(
                    root, 'foo', 'bar');
            });

        root.setAttribute('foo', 'quux');
        self.assertThrows(
            Error,
            function() {
                return Divmod.Runtime.theRuntime.firstNodeByAttribute(
                    root, 'foo', 'bar');
            });

        root.setAttribute('baz', 'bar');
        self.assertThrows(
            Error,
            function() {
                return Divmod.Runtime.theRuntime.firstNodeByAttribute(
                    root, 'foo', 'bar');
            });
    },

    /**
     * I{nodeByAttribute} should return the single node which matches the
     * attribute name and value supplied.
     */
    function test_nodeByAttribute(self) {
        function find(root, attrName, attrValue) {
            return Divmod.Runtime.theRuntime.nodeByAttribute(
                root, attrName, attrValue);
        };
        var root = document.createElement('div');
        root.setAttribute('foo', 'bar');
        self.assertIdentical(find(root, 'foo', 'bar'), root);

        root.setAttribute('foo', '');
        var childA = document.createElement('span');
        childA.setAttribute('foo', 'bar');
        root.appendChild(childA);
        self.assertIdentical(find(root, 'foo', 'bar'), childA);

        childA.setAttribute('foo', '');
        var childB = document.createElement('span');
        childB.setAttribute('foo', 'bar');
        root.appendChild(childB);
        self.assertIdentical(find(root, 'foo', 'bar'), childB);

        childB.setAttribute('foo', '');
        var childC = document.createElement('span');
        childC.setAttribute('foo', 'bar');
        childA.appendChild(childC);
        self.assertIdentical(find(root, 'foo', 'bar'), childC);

        childC.setAttribute('foo', '');
        var childD = document.createElement('span');
        childD.setAttribute('foo', 'bar');
        childB.appendChild(childD);
        self.assertIdentical(find(root, 'foo', 'bar'), childD);
    },

    /**
     * I{nodeByAttribute} should throw an error if more than one node matches
     * the specified attribute name and value.
     */
    function test_nodeByAttributeThrowsOnMultiple(self) {
        function find(root, attrName, attrValue) {
            return Divmod.Runtime.theRuntime.nodeByAttribute(
                root, attrName, attrValue);
        };

        var root = document.createElement('div');
        root.setAttribute('foo', 'bar');
        var childA = document.createElement('span');
        childA.setAttribute('foo', 'bar');
        root.appendChild(childA);
        self.assertThrows(
            Error,
            function() {
                return find(root, 'foo', 'bar');
            });

        childA.setAttribute('foo', '');
        var childB = document.createElement('span');
        childB.setAttribute('foo', 'bar');
        root.appendChild(childB);
        self.assertThrows(
            Error,
            function() {
                return find(root, 'foo', 'bar');
            });

        childB.setAttribute('foo', '');
        var childC = document.createElement('span');
        childC.setAttribute('foo', 'bar');
        childA.appendChild(childC);
        self.assertThrows(
            Error,
            function() {
                return find(root, 'foo', 'bar');
            });

        childC.setAttribute('foo', '');
        var childD = document.createElement('span');
        childD.setAttribute('foo', 'bar');
        childB.appendChild(childD);
        self.assertThrows(
            Error,
            function() {
                return find(root, 'foo', 'bar');
            });

        root.setAttribute('foo', '');
        childC.setAttribute('foo', 'bar');
        self.assertThrows(
            Error,
            function() {
                return find(root, 'foo', 'bar');
            });
    },

    /**
     * I{nodeByAttribute} should throw an error if no nodes match the specified
     * attribute name and value.
     */
    function test_nodeByAttributeThrowsOnMissing(self) {
        var root = document.createElement('span');
        self.assertThrows(
            Error,
            function() {
                return Divmod.Runtime.theRuntime.nodeByAttribute(
                    root, 'foo', 'bar');
            });

        root.setAttribute('foo', 'quux');
        self.assertThrows(
            Error,
            function() {
                return Divmod.Runtime.theRuntime.nodeByAttribute(
                    root, 'foo', 'bar');
            });

        root.setAttribute('baz', 'bar');
        self.assertThrows(
            Error,
            function() {
                return Divmod.Runtime.theRuntime.nodeByAttribute(
                    root, 'foo', 'bar');
            });
    },

    /**
     * I{nodesByAttribute} should return an array of all nodes which have
     * matching values for the specified attribute.
     */
    function test_nodesByAttribute(self) {
        var root = document.createElement('div');
        root.setAttribute('foo', 'bar');
        var childA = document.createElement('span');
        var childB = document.createElement('span');
        childB.setAttribute('foo', 'bar');
        root.appendChild(childA);
        root.appendChild(childB);

        var nodes = Divmod.Runtime.theRuntime.nodesByAttribute(
            root, 'foo', 'bar');
        self.assertIdentical(nodes.length, 2);
        self.assertIdentical(nodes[0], root);
        self.assertIdentical(nodes[1], childB);

        nodes = Divmod.Runtime.theRuntime.nodesByAttribute(
            root, 'baz', 'quux');
        self.assertIdentical(nodes.length, 0);
    },

    /**
     * I{firstNodeByClass} should find nodes with multiple classes.
     */
    function test_firstNodeByClass(self) {
        var target = document.createElement('div');
        Divmod.Runtime.theRuntime.setAttribute(target, 'class', 'foo bar');
        var ringer = document.createElement('div');
        Divmod.Runtime.theRuntime.setAttribute(ringer, 'clas', 'foobar');
        target.appendChild(ringer);
        var found = Divmod.Runtime.theRuntime.firstNodeByClass(target,
                'bar');
        self.assertIdentical(
            Divmod.Runtime.theRuntime.getAttribute(found, 'class'),
            'foo bar');
    },

    /**
     * I{firstNodeByClass} for a missing node must throw the right exception.
     */
    function test_firstNodeByClassMissing(self) {
        var target = document.createElement('div');
        var ringer = document.createElement('div');
        Divmod.Runtime.theRuntime.setAttribute(ringer, 'clas', 'foobar');
        target.appendChild(ringer);
        var error = self.assertThrows(
            Divmod.Runtime.NodeAttributeError,
            function() {
                Divmod.Runtime.theRuntime.firstNodeByClass(
                    target, 'bar');
            });
        self.assertIdentical(error.root, target);
        self.assertIdentical(error.attribute, 'class');
        self.assertIdentical(error.value, 'bar');
    },

    /**
     * I{nodesByClass} should return an array of all nodes which have the
     * matching class.
     */
    function test_nodesByClass(self) {
        var root = document.createElement('div');
        var childA = document.createElement('span');
        var childB = document.createElement('span');
        var childC = document.createElement('span');
        root.appendChild(childA);
        root.appendChild(childB);
        root.appendChild(childC);
        childB.setAttribute('class', 'foo bar');
        childC.setAttribute('class', 'bar');

        var nodes = Divmod.Runtime.theRuntime.nodesByClass(
            root, 'bar');
        self.assertIdentical(nodes.length, 2);
        self.assertIdentical(nodes[0], childB);
        self.assertIdentical(nodes[1], childC);
    });
