
// import Divmod
// import Divmod.Base
// import Divmod.Defer


Divmod.Runtime.NodeNotFound = Divmod.Error.subclass("Divmod.Runtime.NodeNotFound");

Divmod.Runtime.TooManyNodes = Divmod.Error.subclass("Divmod.Runtime.TooManyNodes");

Divmod.Runtime.NodeAttributeError = Divmod.Runtime.NodeNotFound.subclass("Divmod.Runtime.NodeAttributeError");
Divmod.Runtime.NodeAttributeError.methods(
    function __init__(self, root, attribute, value) {
        Divmod.Runtime.NodeAttributeError.upcall(self, '__init__');
        self.root = root;
        self.attribute = attribute;
        self.value = value;
    },

    function toString(self) {
        return (
            "Failed to discover node with " + self.attribute +
            " value " + self.value + " beneath " + self.root +
            " (programmer error).");
    });

Divmod.Runtime.Platform = Divmod.Class.subclass("Divmod.Runtime.Platform");

Divmod.Runtime.Platform.DOM_DESCEND = 'Divmod.Runtime.Platform.DOM_DESCEND';
Divmod.Runtime.Platform.DOM_CONTINUE = 'Divmod.Runtime.Platform.DOM_CONTINUE';
Divmod.Runtime.Platform.DOM_TERMINATE = 'Divmod.Runtime.Platform.DOM_TERMINATE';

Divmod.Runtime.Platform.methods(
    function __init__(self, name) {
        self.name = name;
        self.attrNameToMangled = {};
        self._scriptCounter = 0;
        self._scriptDeferreds = {};
    },

    function _nsResolver(self, prefix) {
        var ns;
        switch(prefix) {
            case 'html':
                ns = 'http://www.w3.org/1999/xhtml';
                break;
            case 'athena':
                ns = 'http://divmod.org/ns/athena/0.7';
                break;
            default:
                // this should never happen, but browsers still suck...
                ns = null;
        }
        return ns;
    },

    function _xpathNodeByAttribute(self, attrName, attrValue) {
        var upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
        var lower = upper.toLowerCase();
        return (
            ".//*[@*[translate(name(),'" + upper + "', '" + lower + "')='" +
            attrName + "']='" + attrValue + "'] | .[@*[translate(name(),'" +
            upper + "', '" + lower + "')='" + attrName + "']='" + attrValue +
            "']");
    },

    function firstNodeByAttribute(self, root, attrName, attrValue) {
        /* duplicate this here rather than adding an "onlyOne" arg to
           nodesByAttribute so adding an extra arg accidentally doesn't change
           it's behaviour if called directly
        */
        var xpath = self._xpathNodeByAttribute(attrName, attrValue);
        var node = document.evaluate(
            xpath,
            root,
            null,
            XPathResult.FIRST_ORDERED_NODE_TYPE,
            null
        ).singleNodeValue;
        if (!node) {
            throw Divmod.Runtime.NodeAttributeError(root, attrName, attrValue);
        }
        return node;
    },

    function nodeByAttribute(self, root, attrName, attrValue, /* optional */ defaultNode){
        var xpath = self._xpathNodeByAttribute(attrName, attrValue);
        var nodes = document.evaluate(
            xpath,
            root,
            null,
            XPathResult.UNORDERED_NODE_SNAPSHOT_TYPE,
            null
        );
        if (nodes.snapshotLength > 1) {
            throw new Error("Found too many " + attrName + " = " + attrValue);
        }
        else if (nodes.snapshotLength < 1) {
            if (defaultNode === undefined) {
                throw Divmod.Runtime.NodeAttributeError(root, attrName, attrValue);
            }
            else {
                return defaultNode;
            }
        }
        else {
            var result = nodes.snapshotItem(0);
            return result;
        }
    },

    function nodesByAttribute(self, root, attrName, attrValue) {
        var results = [];
        var xpath = self._xpathNodeByAttribute(attrName, attrValue);
        var nodes = document.evaluate(
            xpath,
            root,
            null,
            XPathResult.ORDERED_NODE_ITERATOR_TYPE,
            null
        );
        var node = nodes.iterateNext();
        while(node){
            results.push(node);
            node = nodes.iterateNext();
        }
        return results;
    },

    /**
     * Calculate the X/Y coordinates of event C{event} on the
     * page in a cross-browser fashion.  If C{event} is not defined,
     * then window.event will be used.
     *
     * @return: object with "x" and "y" slots
     */
    function getEventCoords(self, event) {
        if(!event) {
            event = window.event;
        }
        var x = 0, y = 0;
        if(event.pageX || event.pageY) {
            x = event.pageX;
            y = event.pageY;
        } else if(event.clientX || event.clientY) {
            x = event.clientX +
                document.body.scrollLeft +
                document.documentElement.scrollLeft;
            y = event.clientY +
                document.body.scrollTop +
                document.documentElement.scrollTop;
        }
        return {x: x, y: y};
    },

    /**
     * Find the X position of a node C{node} on the page in a cross-browser
     * fashion
     *
     * @rtype: C{Number}
     */
    function findPosX(self, node) {
        var curleft = 0;
        if (node.offsetParent) {
            while (node.offsetParent) {
                curleft += node.offsetLeft
                node = node.offsetParent;
            }
        } else if (node.x) {
            curleft += node.x;
        }
        return curleft;
    },

    /**
     * Find the Y position of a node C{node} on the page in a cross-browser
     * fashion
     *
     * @rtype: C{Number}
     */
    function findPosY(self, node) {
        var curtop = 0;
        if (node.offsetParent) {
            while (node.offsetParent) {
                curtop += node.offsetTop
                node = node.offsetParent;
            }
        } else if (node.y) {
            curtop += node.y;
        }
        return curtop;
    },

    /**
     * Determine the dimensions of the page (browser viewport).
     * This method only considers the visible portion of the page
     * (i.e. how much of it can fit on the screen at once).
     *
     * @return: object with "w" and "h" attributes
     */
    function getPageSize(self, /* optional */ win) {
        var w, h
        var theWindow = win || window;

        /* slightly modified version of code from
         * http://www.quirksmode.org/viewport/compatibility.html */

        if (theWindow.innerHeight) {
            /* all except Explorer */
            w = theWindow.innerWidth;
            h = theWindow.innerHeight;
        } else if(theWindow.document.documentElement &&
                  theWindow.document.documentElement.clientHeight) {
            /* Explorer 6 Strict Mode */
            w = theWindow.document.documentElement.clientWidth;
            h = theWindow.document.documentElement.clientHeight;
        } else if (theWindow.document.body) {
            /* other Explorers */
            w = theWindow.document.body.clientWidth;
            h = theWindow.document.body.clientHeight;
        }

        return {w: w, h: h};
    },

    /**
     * Calculate the size of the given element, including padding
     * but excluding scrollbars, borders and margins.  If the
     * element is invisible (i.e. display: none) is set, the it
     * will be made visible for the purpose of obtaining its
     * dimensions (sufficiently quickly that the viewport will not
     * update).
     *
     * @return: object with "w" and "h" attributes
     */
    function getElementSize(self, e) {
        var hidden = e.style.display == "none";
        if(hidden) {
            e.style.display = "";
        }
        var size = {w: e.clientWidth, h: e.clientHeight};
        if(hidden) {
            e.style.display = "none";
        }
        return size;
    },

    /**
     * Return all immediate children of C{root} that have tag name C{tagName}
     */
    function getElementsByTagNameShallow(self, root, tagName) {
        var child, result = [];
        for(var i = 0; i < root.childNodes.length; i++) {
            child = root.childNodes[i];
            if(child.tagName && child.tagName.toLowerCase() == tagName) {
                result.push(child);
            }
        }
        return result;
    },

    /**
     * Some browsers rewrite attribute names.  This method is responsible for
     * transforming canonical attribute names into their browser-specific
     * names.  It gets called by L{Divmod.Runtime.Platform.getAttribute} and
     * L{Divmod.Runtime.Platform.setAttribute} when they encounter a
     * namespace-less attribute.
     */
    function _mangleAttributeName(self, localName) {
        if(localName in self.attrNameToMangled) {
            return self.attrNameToMangled[localName];
        }
        return localName;
    },

//     function setAttribute(self, node, localName, namespaceURI, namespaceIdentifier, value) {
//         if (namespaceURI !== undefined && node.setAttributeNS) {
//             node.setAttributeNS(namespaceURI, localName, value);
//         } else if (namespaceIdentifier !== undefined) {
//             node.setAttribute(namespaceIdentifier + ':' + localName, value);
//         } else {
//             node.setAttribute(self._mangleAttributeName(localName), value);
//         }
//     },

    /**
     * This is _the_way_ to get the value of an attribute off of node
     */
    function getAttribute(self, node, localName, namespaceURI, namespaceIdentifier) {
        if(namespaceURI == undefined && namespaceIdentifier == undefined) {
            localName = self._mangleAttributeName(localName);
        }
        if (node.hasAttributeNS) {
            if (node.hasAttributeNS(namespaceURI, localName)) {
                return node.getAttributeNS(namespaceURI, localName);
            } else if (node.hasAttributeNS(namespaceIdentifier, localName)) {
                return node.getAttributeNS(namespaceIdentifier, localName);
            }
        }
        if (node.hasAttribute) {
            var r = (typeof namespaceURI != 'undefined') ? namespaceURI + ':' + localName : localName;
            if (node.hasAttribute(r)) {
                return node.getAttribute(r);
            }
        }
        if (node.getAttribute) {
            var s;
            if(namespaceIdentifier == undefined) {
                s = localName;
            } else {
                s = namespaceIdentifier + ':' + localName;
            }
            try {
                return node.getAttribute(s);
            } catch(err) {
                // IE has a stupid bug where getAttribute throws an error ... on
                // TABLE elements and perhaps other elememnt types!
                // Resort to looking in the attributes.
                var value = node.attributes[s];
                if(value != null) {
                    return value.nodeValue;
                }
            }
        }
        return null;
    },

    function makeHTTPRequest(self) {
        throw new Error("makeHTTPRequest is unimplemented on " + self);
    },

    function _onReadyStateChange(self, req, d) {
        return function() {
            if (d == null) {
                /* We've been here before, and finished everything we needed
                 * to finish.
                 */
                return;
            }
            if (typeof Divmod == 'undefined') {
                /*
                 * If I am invoked _after_ onunload is fired, the JS
                 * environment has been torn down, and there is basically
                 * nothing useful that any callbacks could do.  You can detect
                 * this environment brokenness by looking at a top-level module
                 * object (such as our own, Divmod).
                 *
                 * I also eliminate myself as the onreadystatechange handler of
                 * this request, since at no future point will the execution
                 * context magically be restored to a working state.
                 */
                req.onreadystatechange = null;
                return;
            }
            if (req.readyState == 4) {
                var result = null;
                try {
                    result = {'status': req.status,
                              'response': req.responseText};
                } catch (err) {
                    d.errback(err);
                }
                if (result != null) {
                    d.callback(result);
                }
                d = null;
            }
        };
    },

    function getPage(self, url, /* optional */ args, action, headers, content) {
        if (args == undefined) {
            args = [];
        }
        if (action == undefined) {
            action = 'GET';
        }
        if (headers == undefined) {
            headers = [];
        }
        if (content == undefined) {
            content = null;
        }

        var qargs = [];
        for (var i = 0; i < args.length; ++i) {
            /* encodeURIComponent may not exist on some browsers, I guess.  FF
             * 1.5 and IE 6 have it, anyway.
             */
            qargs.push(args[i][0] + '=' + encodeURIComponent(args[i][1]));
        }

        if (qargs.length) {
            url = url + '?' + qargs.join('&');
        }

        var d = new Divmod.Defer.Deferred();
        var req = self.makeHTTPRequest();

        req.open(action, url, true);

        for (var i = 0; i < headers.length; ++i) {
            req.setRequestHeader(headers[i][0], headers[i][1]);
        }

        req.onreadystatechange = self._onReadyStateChange(req, d);
        req.send(content);
        return [req, d];
    },

    function parseXHTMLString(self, s) {
        throw new Error("parseXHTMLString not implemented on " + self.name);
    },

    function traverse(self, rootNode, visitor) {
        if(rootNode == undefined) {
            throw new Error("traverse() passed bad rootNode");
        }
        var deque = [rootNode];
        while (deque.length != 0) {
            var curnode = deque.pop();
            var visitorResult = visitor(curnode);
            switch (visitorResult) {
            case Divmod.Runtime.Platform.DOM_DESCEND:
                for (var i = curnode.childNodes.length - 1; i > -1 ; i--) {
                    // "maybe you could make me care about how many stop
                    // bits my terminal has!  that would be so retro!"
                    deque.push(curnode.childNodes[i]);
                }
                break;

            case Divmod.Runtime.Platform.DOM_CONTINUE:
                break;

            case Divmod.Runtime.Platform.DOM_TERMINATE:
                return;

            default :
                throw new Error(
                    "traverse() visitor returned illegal value: " + visitorResult);
                break;
            }
        }
    },

    /**
     * Parse the given XHTML 1.0 string and append its top-level node as a
     * child of the given node.
     *
     * @param node: A DOM node.
     * @param innerHTML The XHTML 1.0 string to append.
     */
    function appendNodeContent(self, node, innerHTML) {
        throw new Error("appendNodeContent not implemented on " + self.name);
    },

    /**
     * Parse the given XHTML 1.0 string and use its top-level node to replace
     * all of the given node's children.
     *
     * @param node: A DOM node.
     * @param innerHTML The XHTML 1.0 string to append.
     */
    function setNodeContent(self, node, innerHTML) {
        while (node.childNodes.length) {
            node.removeChild(node.firstChild);
        }
        self.appendNodeContent(node, innerHTML);
    },

    /**
     * Load the JavaScript module at the given URL.
     *
     * The manner in which the JavaScript is evaluated is implementation
     * dependent.
     *
     * @return: A Deferred which fires when the contents of the module have
     * been evaluated.
     */
    function loadScript(self, location) {
        self._scriptCounter += 1;
        self._scriptDeferreds[self._scriptCounter] = Divmod.Defer.Deferred();

        var language = '"text/javascript"';
        var onload = '"Divmod.Runtime.theRuntime._scriptLoaded(' + self._scriptCounter + ')"';
        var src = '"' + location + '"';
        var id = '"__athena_runtime_script_loader_' + self._scriptCounter + '__"';
        var xmlns = '"http://www.w3.org/1999/xhtml"';
        var script = (
            '<span ' +
            'style="display: none" ' +
            'xmlns=' + xmlns + ' ' +
            'id=' + id + '>' +
            '<script ' +
            'type=' + language + ' ' +
            'onload=' + onload + ' ' +
            'src=' + src + '>' +
            '</script>' +
            '</span>');

        self.appendNodeContent(document.body, script);

        return self._scriptDeferreds[self._scriptCounter];
    },

    function _scriptLoaded(self, which) {
        var script = document.getElementById('__athena_runtime_script_loader_' + which + '__');
        script.parentNode.removeChild(script);

        var loaded = self._scriptDeferreds[which];
        delete self._scriptDeferreds[which];
        loaded.callback(null);
    },

    /**
     * Simulate the functionality of the DOM Level 2 Document.importNode
     * method, used on the browser document.
     *
     * @param node: A DOM Node to import.
     * @param deep: A boolean indicating whether children should be imported.
     * @returns: The imported Node.
     */
    function importNode(self, node, deep) {
        return document.importNode(node, deep);
    },

    /**
     * Retrieve an element from the document by id, where the element is
     * expected to be the child of a particular node (typically a widget's
     * top-most node). Note that this method does not enforce that the element
     * ultimately located is, in fact, a child of the node passed in; the API
     * is merely to allow for platfom-specific workarounds for certain edge
     * cases.
     */
    function getElementByIdWithNode(self, node, id) {
        var foundNode = node.ownerDocument.getElementById(id);
        if (foundNode == null) {
            throw Divmod.Runtime.NodeNotFound('Node with id ' + id + ' not found');
        }
        return foundNode;
    });

Divmod.Runtime.Firefox = Divmod.Runtime.Platform.subclass('Divmod.Runtime.Firefox');

Divmod.Runtime.Firefox.isThisTheOne = function isThisTheOne() {
    try {
        return navigator.appName == "Netscape";
    } catch (err) {
        if (err instanceof ReferenceError) {
            return false;
        } else {
            throw err;
        }
    }
};

Divmod.Runtime.Firefox.methods(
    function __init__(self) {
        Divmod.Runtime.Firefox.upcall(self, '__init__', 'Firefox');
        self.dp = new DOMParser();
        self.ds = new XMLSerializer();
    },

    function makeHTML(self, element) {
        throw new Error("This sucks don't use it");

        var HTML_ELEMENT;

        if (element.nodeName.charAt(0) == '#') {
            HTML_ELEMENT = document.createTextNode(element.nodeValue);
        } else {
            HTML_ELEMENT = document.createElement(element.nodeName);
        }

        if (element.attributes != undefined) {
            for (var i = 0; i < element.attributes.length; ++i) {
                attr = element.attributes[i];
                HTML_ELEMENT.setAttribute(attr.nodeName, attr.nodeValue);
            }
        }

        for (var i = 0; i < element.childNodes.length; ++i) {
            HTML_ELEMENT.appendChild(MAKE_HTML(element.childNodes[i]));
        }
        return HTML_ELEMENT;
    },

    function parseXHTMLString(self, s) {
        var doc = self.dp.parseFromString(s, "application/xml");
        if (doc.documentElement.namespaceURI != "http://www.w3.org/1999/xhtml") {
            throw new Error("Unknown namespace used with parseXHTMLString - only XHTML 1.0 is supported.");
        }
        return doc;
    },

    function appendNodeContent(self, node, innerHTML) {
        var xpath = "//html:script";
        var doc = self.parseXHTMLString(innerHTML);
        var scripts = doc.evaluate(
            xpath,
            doc,
            self._nsResolver,
            XPathResult.UNORDERED_NODE_SNAPSHOT_TYPE, null
        );
        var oldScript;
        var newScript;
        var newAttr;
        for (var i = 0; i < scripts.snapshotLength; ++i) {
            oldScript = scripts.snapshotItem(i);
            newScript = document.createElement('script');
            for (var j = 0; j < oldScript.attributes.length; ++j) {
                newAttr = oldScript.attributes[j];
                newScript.setAttribute(newAttr.name, newAttr.value);
            }
            for (var j = 0; j < oldScript.childNodes.length; ++j) {
                newScript.appendChild(oldScript.childNodes[j].cloneNode(true));
            }
            if (oldScript.parentNode) {
                oldScript.parentNode.removeChild(oldScript);
            }
            node.appendChild(newScript);
        }
        node.appendChild(document.importNode(doc.documentElement, true));
    },

    function makeHTTPRequest(self) {
        return new XMLHttpRequest();
    });

Divmod.Runtime.InternetExplorer = Divmod.Runtime.Platform.subclass("Divmod.Runtime.InternetExplorer");

Divmod.Runtime.InternetExplorer.isThisTheOne = function isThisTheOne() {
    try {
        return navigator.appName == "Microsoft Internet Explorer";
    } catch (err) {
        if (err instanceof ReferenceError) {
            return false;
        } else {
            throw err;
        }
    }
};

Divmod.Runtime.InternetExplorer.methods(
    function __init__(self) {
        Divmod.Runtime.InternetExplorer.upcall(self, '__init__', 'Internet Explorer');
        // IE has no equivalent to the stacktrace that FF provides, so this
        // JSON adapter will provide a dummy object to make Athena happy when
        // it tries to send exceptions from the client to the server
        Divmod.Base.registerJSON(
            'Error',
            function(obj) {
                return obj instanceof Error;
            },
            function(obj) {
                return {
                    'name': obj.name,
                    'message': obj.message,
                    'stack': 'No stacktrace available\n'
                };
            }
        );

        /* IE rewrites attributes with names matching these
           keys to their corresponding values.
           e.g. class -> className, etc
         */
        self.attrNameToMangled = {"class": "className",
                                  "checked": "defaultChecked",
                                  "usemap": "useMap",
                                  "for": "htmlFor"};
    },

    function parseXHTMLString(self, s) {
        var xmldoc = new ActiveXObject("MSXML.DOMDocument");
        xmldoc.async = false;

        if(!xmldoc.loadXML(s)){
            throw new Error('XML parsing error: ' + xmldoc.parseError.reason);
        }
        return xmldoc;
    },

    function appendNodeContent(self, node, innerHTML) {
        var head = document.getElementsByTagName('head').item(0);
        var doc = self.parseXHTMLString(innerHTML);
        var scripts = doc.getElementsByTagName('script');

        for(var i = 0;i < scripts.length;i++){
            var oldScript = scripts[i].parentNode.removeChild(scripts[i]);
            var src = oldScript.getAttribute('src');
            var text = oldScript.text;
            var script = document.createElement('script');
            script.type = 'text/javascript';
            if(src != '' && src != null){
                script.src = src;
            }
            else if(text != '' && text != null){
                script.text = text;
            }
            head.appendChild(script);
        }

        node.innerHTML += doc.xml;
    },

    function makeHTTPRequest(self) {
        if (!self._xmlhttpname) {
            var names = ["Msxml2.XMLHTTP", "Microsoft.XMLHTTP", "Msxml2.XMLHTTP.4.0"];
            while (names.length) {
                self._xmlhttpname = names.shift();
                try {
                    return self.makeHTTPRequest();
                } catch (e) {
                    // pass
                }
            }
            self._xmlhttpname = null;
            throw new Error("No support XML HTTP Request thingy on this platform");
        } else {
            return new ActiveXObject(self._xmlhttpname);
        }
    },

    function firstNodeByAttribute(self, root, attrName, attrValue) {
        /* duplicate this here rather than adding an "onlyOne" arg to
           nodesByAttribute so adding an extra arg accidentally doesn't change
           it's behaviour if called directly
        */
        var descend = Divmod.Runtime.Platform.DOM_DESCEND;
        var terminate = Divmod.Runtime.Platform.DOM_TERMINATE;

        var result = null;
        self.traverse(
            root,
            function(node) {
                if (self.getAttribute(node, attrName) == attrValue) {
                    result = node;
                    return terminate;
                }
                return descend;
            });
        if (result === null) {
            throw new Error("Failed to discover node with " + attrName +
                            " value " + attrValue + " beneath " + root +
                            " (programmer error).");
        }
        return result;
    },

    function nodesByAttribute(self, root, attrName, attrValue) {
        var descend = Divmod.Runtime.Platform.DOM_DESCEND;
        var results = [];
        self.traverse(
            root,
            function(node) {
                if (self.getAttribute(node, attrName) == attrValue) {
                    results.push(node);
                }
                return descend;
            });
        return results;
    },

    function nodeByAttribute(self, root, attrName, attrValue, /* optional */ defaultNode) {
        var nodes = self.nodesByAttribute(root, attrName, attrValue);
        if (nodes.length > 1) {
            throw new Error("Found too many " + attrName + " = " + attrValue);
        } else if (nodes.length < 1) {
            if (defaultNode === undefined) {
                throw new Error("Failed to discover node with class value " +
                                attrValue + " beneath " + root +
                                " (programmer error).");
            } else {
                return defaultNode;
            }

        } else {
            var result = nodes[0];
            return result;
        }
    },

    function loadScript(self, location) {
        // The <script> tricks the base implementation uses produce
        // spectacularly bizarre behaviour in IE, so we just use getPage/eval
        // here.

        var req = Divmod.Runtime.theRuntime.getPage(location);
        var d = req[1];
        d.addCallback(
            function (result) {
                eval(result['response']);
            });
        return d;
    },

    /**
     * Simulate importNode by rebuilding the node contents in a node created in
     * the browser document; IE doesn't support DOM Level 2, and importNode in
     * particular.
     */
    function importNode(self, node, deep) {
        var nodeXML = node.xml || node.outerHTML;
        if (!nodeXML) {
            // This probably isn't a node at all, but some other junk
            throw new Error('Unable to retrieve XML content of node');
        }

        var tmpNode = document.createElement('div');
        tmpNode.innerHTML = nodeXML;
        return tmpNode.firstChild.cloneNode(deep);
    },

    function getElementByIdWithNode(self, node, id) {
        var foundNode = node.ownerDocument.getElementById(id);
        if (foundNode == null) {
            // We didn't find it, maybe we need a workaround.

            // Let's find the root node of the hierarchy.
            var root = node;
            while (root.parentNode != null) {
                root = root.parentNode;
            }

            var DOCUMENT_FRAGMENT_NODE = 11;
            if (root.nodeType == DOCUMENT_FRAGMENT_NODE) {
                // We're in a DocumentFragment, and thus getElementById won't
                // find any of our children. Let's insert ourselves into the
                // document temporarily.
                var currentParent = node.parentNode;
                var nextSibling = node.nextSibling;
                currentParent.removeChild(node);
                document.documentElement.appendChild(node);

                // Try again
                foundNode = node.ownerDocument.getElementById(id);

                // And now put us back where we used to be.
                node.parentNode.removeChild(node);
                currentParent.insertBefore(node, nextSibling);
            }
        }

        if (foundNode == null) {
            throw Divmod.Runtime.NodeNotFound('Node with id ' + id + ' not found');
        }

        return foundNode;
    });


Divmod.Runtime.Opera = Divmod.Runtime.Platform.subclass("Divmod.Runtime.Opera");

Divmod.Runtime.Opera.isThisTheOne = function isThisTheOne() {
    try {
        return navigator.userAgent.indexOf('Opera') != -1;
    } catch (err) {
        if (err instanceof ReferenceError) {
            return false;
        } else {
            throw err;
        }
    }
};

Divmod.Runtime.Opera.methods(
    function __init__(self) {
        Divmod.Runtime.Opera.upcall(self, '__init__', 'Opera');
        self.lp = document.implementation.createLSParser(DOMImplementationLS.MODE_SYNCHRONOUS, null);
        self.ls = document.implementation.createLSSerializer();

        // Provide a JSON adapter for client-side errors, to make Athena happy
        // when it tries to send exceptions from the client to the server

        // TODO: Convert Opera's backtrace string to FF's stacktrace format
        Divmod.Base.registerJSON(
            'Error',
            function(obj) {
                return obj instanceof Error;
            },
            function(obj) {
                var stack = 'No stacktrace available\n';
                var message = obj.message;
                var backtrace = message.indexOf('Backtrace:');
                if(backtrace != -1) {
                    stack = message.slice(backtrace);
                    message = message.slice(0, backtrace);
                }
                return {
                    'name': obj.name,
                    'message': message,
                    'stack': stack
                };
            }
        );
    },

    function parseXHTMLString(self, s) {
        var lsi = document.implementation.createLSInput();
        lsi.stringData = s;
        return self.lp.parse(lsi);
    },

    function appendNodeContent(self, node, innerHTML) {
        var doc = self.parseXHTMLString(innerHTML);
        node.appendChild(document.importNode(doc.documentElement, true));
    },

    function makeHTTPRequest(self) {
        return new XMLHttpRequest();
    });


Divmod.Runtime.SpidermonkeyStandalone = Divmod.Class.subclass();
Divmod.Runtime.SpidermonkeyStandalone.isThisTheOne = function() {
    try {
        navigator;
    } catch (err) {
        if (!(err instanceof ReferenceError)) {
            throw err;
        }
        try {
            document;
        } catch (err) {
            if (!(err instanceof ReferenceError)) {
                throw err;
            }
            try {
                window;
            } catch (err) {
                if (!(err instanceof ReferenceError)) {
                    throw err;
                }
                return true;
            }
        }
    }
    return false;
};

Divmod.Runtime.Platform.determinePlatform = function determinePlatform() {
    var platforms = [
        Divmod.Runtime.Firefox,
        Divmod.Runtime.InternetExplorer,
        Divmod.Runtime.Opera,
        Divmod.Runtime.SpidermonkeyStandalone];
    for (var cls = 0; cls < platforms.length; ++cls) {
        if (platforms[cls].isThisTheOne()) {
            return platforms[cls];
        }
    }
    throw new Error("Unsupported platform");
};

Divmod.Runtime.theRuntimeType = Divmod.Runtime.Platform.determinePlatform();
Divmod.Runtime.theRuntime = new Divmod.Runtime.theRuntimeType;
