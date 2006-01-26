
// import Divmod

Divmod.Runtime = new Divmod.Module('Divmod.Runtime');

Divmod.Runtime.Platform = Divmod.Class.subclass("Divmod.Runtime.Platform");

Divmod.Runtime.Platform.DOM_DESCEND = 'Divmod.Runtime.Platform.DOM_DESCEND';
Divmod.Runtime.Platform.DOM_CONTINUE = 'Divmod.Runtime.Platform.DOM_CONTINUE';

Divmod.Runtime.Platform.method(
    function __init__(self, name) {
        self.name = name;
    });

Divmod.Runtime.Platform.method(
    function requestHTTP(self, url) {
        throw new Error("requestHTTP not implemented on " + self.name);
    });

Divmod.Runtime.Platform.method(
    function parseXHTMLString(self, s) {
        throw new Error("parseXHTMLString not implemented on " + self.name);
    });

Divmod.Runtime.Platform.method(
    function traverse(self, rootNode, visitor) {
        var deque = [rootNode];
        while (deque.length != 0) {
            var curnode = deque.shift();
            var visitorResult = visitor(curnode);
            switch (visitorResult) {
            case self.DOM_DESCEND:
                for (var i = 0; i < curnode.childNodes.length; i++) {
                    // "maybe you could make me care about how many stop
                    // bits my terminal has!  that would be so retro!"
                    deque.push(curnode.childNodes[i]);
                }
                break;

            case self.DOM_CONTINUE:
                break;

            default :
                throw new Error(
                    "traverse() visitor returned illegal value: " + visitorResult);
                break;
            }
        }
    });

Divmod.Runtime.Platform.method(
    function appendNodeContent(self, node, innerHTML) {
        throw new Error("appendNode content not implemented on " + self.name);
    });

Divmod.Runtime.Platform.method(
    function setNodeContent(self, node, innerHTML) {
        while (node.childNodes.length) {
            node.removeChild(node.firstChild);
        }
        self.appendNodeContent(node, innerHTML);
    });

Divmod.Runtime.Firefox = Divmod.Runtime.Platform.subclass('Divmod.Runtime.Firefox');

Divmod.Runtime.Firefox.isThisTheOne = function isThisTheOne() {
    return navigator.appName == "Netscape";
};

Divmod.Runtime.Firefox.method(
    function __init__(self) {
        Divmod.Runtime.Firefox.upcall(self, '__init__', 'Firefox');
        self.dp = new DOMParser();
        self.ds = new XMLSerializer();
    });

Divmod.Runtime.Firefox.method(
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
    });

Divmod.Runtime.Firefox.method(
    function parseXHTMLString(self, s) {
        var doc = self.dp.parseFromString(s, "application/xml");
        if (doc.documentElement.namespaceURI != "http://www.w3.org/1999/xhtml") {
            throw new Error("Unknown namespace used with parseXHTMLString - only XHTML 1.0 is supported.");
        }
        return doc;
    });

Divmod.Runtime.Firefox.method(
    function appendNodeContent(self, node, innerHTML) {
        var doc = self.parseXHTMLString(innerHTML);
        var scripts = [];

        self.traverse(
            doc.documentElement,
            function(node) {
                if (node.tagName == 'script') {
                    scripts.push(node);
                }
                return Divmod.Runtime.theRuntime.DOM_DESCEND;
            });

        var oldScript;
        var newScript;
        var newAttr;

        for (var i = 0; i < scripts.length; ++i) {
            oldScript = scripts[i];
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
        node.appendChild(doc.documentElement);
    });

Divmod.Runtime.Firefox.method(
    function setNodeContent(self, node, innerHTML) {
        while (node.childNodes.length) {
            node.removeChild(node.firstChild);
        }
        self.appendNodeContent(node, innerHTML);
    });

Divmod.Runtime.InternetExplorer = Divmod.Runtime.Platform.subclass("Divmod.Runtime.InternetExplorer");

Divmod.Runtime.InternetExplorer.isThisTheOne = function isThisTheOne() {
    return navigator.appName == "Microsoft Internet Explorer";
};

Divmod.Runtime.InternetExplorer.method(
    function __init__(self) {
        Divmod.Runtime.InternetExplorer.upcall(self, '__init__', 'Internet Explorer');
    });

// Divmod.Runtime.InternetExplorer.method(
//     function requestHTTP(self, url) {
//         var req = new XMLHttpRequest();
//         req.open("GET", url, false);
//         req.send(null);
//         if (req.status != 200 && req.status != 304) {
//             throw new Error("Failed to retrieve " + url);
//         }
//         return req.responseText;
//     });

Divmod.Runtime.InternetExplorer.method(
    function parseXHTMLString(self, s) {
        var xmldoc = new ActiveXObject("Microsoft.XMLDOM");
        xmldoc.async = false;
        xmldoc.loadXML(s);
        return xmldoc;
    });

Divmod.Runtime.InternetExplorer.method(
    function appendNodeContent(self, node, innerHTML) {
        var body = document.getElementsByTagName('body')[0];
        var newScript;
        node.innerHTML += innerHTML;
        self.traverse(
            node,
            function(node) {
                if (node.tagName == 'SCRIPT') {
                    newScript = document.createElement('SCRIPT');
                    newScript.setAttribute('src', node.getAttribute('src'));
                    newScript.text = node.text;
                    node.parentNode.removeChild(node);
                    body.appendChild(newScript);
                }
                return self.DOM_DESCEND;
            });
    });

Divmod.Runtime.Platform.determinePlatform = function determinePlatform() {
    var platforms = [Divmod.Runtime.Firefox, Divmod.Runtime.InternetExplorer];
    for (var cls = 0; cls < platforms.length; ++cls) {
        if (platforms[cls].isThisTheOne()) {
            return platforms[cls];
        }
    }
    throw new Error("Unsupported platform");
};

Divmod.Runtime.theRuntimeType = Divmod.Runtime.Platform.determinePlatform();
Divmod.Runtime.theRuntime = new Divmod.Runtime.theRuntimeType();
