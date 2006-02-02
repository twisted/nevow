// -*- test-case-name: nevow.test.test_javascript -*-

// import Divmod
// import Nevow

Nevow.Athena = {};

Nevow.Athena.NAME = 'Nevow.Athena';
Nevow.Athena.__repr__ = function() {
    return '[' + this.NAME + ']';
};

Nevow.Athena.toString = function() {
    return this.__repr__();
};

Nevow.Athena.XMLNS_URI = 'http://divmod.org/ns/athena/0.7';

Nevow.Athena.baseURL = function() {
    return Divmod.baseURL() + 'transport';
};

Nevow.Athena.constructActionURL = function(action) {
    return (Nevow.Athena.baseURL()
            + '?action='
            + encodeURIComponent(action));
};

Nevow.Athena.CONNECTED = 'connected';
Nevow.Athena.DISCONNECTED = 'disconnected';

Nevow.Athena.connectionState = Nevow.Athena.CONNECTED;
Nevow.Athena.failureCount = 0;
Nevow.Athena.remoteCallCount = 0;
Nevow.Athena.remoteCalls = {};
Nevow.Athena._transportCounter = 0;
Nevow.Athena.outstandingTransports = {};

Nevow.Athena._numTransports = function() {
    /* XXX UGGG */
    var num = 0;
    var e = null;
    for (e in Nevow.Athena.outstandingTransports) {
        num += 1;
    }
    return num;
};

/**
 * Notice the unusual ordering of arguments here.  Please ask Bob
 * Ippolito about it.
 */
Nevow.Athena.XMLHttpRequestFinished = function(reqId, passthrough) {
    Divmod.debug('transport', 'request ' + reqId + ' completed');
    if (!delete Nevow.Athena.outstandingTransports[reqId]) {
        Divmod.debug("Crap failed to delete crap");
    }
    Divmod.debug('transport', 'outstanding transport removed');
    Divmod.debug('transport', 'there are ' + Nevow.Athena._numTransports() + ' transports');

    Divmod.debug('transport', 'Passthrough returning ' + passthrough);
    return passthrough;
};

Nevow.Athena._actionHandlers = {
    noop: function() {
        /* Noop! */
    },

    call: function(functionName, requestId, funcArgs) {
        var funcObj = Divmod.namedAny(functionName);
        var result = undefined;
        var success = true;
        try {
            result = funcObj.apply(null, funcArgs);
        } catch (error) {
            result = error;
            success = false;
        }

        var isDeferred = false;

        if (result == undefined) {
            result = null;
        } else {
            /* if it quacks like a duck ...  this sucks!!!  */
            isDeferred = (result.addCallback && result.addErrback);
        }

        if (isDeferred) {
            result.addCallbacks(function(result) {
                    Nevow.Athena.respondToRemote(requestId, [true, result]);
                }, function(err) {
                    Nevow.Athena.respondToRemote(requestId, [false, result]);
                });
        } else {
            Nevow.Athena.respondToRemote(requestId, [success, result]);
        }
    },

    respond: function(responseId, success, result) {
        var d = Nevow.Athena.remoteCalls[responseId];
        delete Nevow.Athena.remoteCalls[responseId];

        if (success) {
            Divmod.debug('object', 'Callback');
            d.callback(result);
        } else {
            Divmod.debug('object', 'Errback');
            d.errback(new Error(result[0] + ': ' + result[1]));
        }
    },

    close: function() {
        Nevow.Athena._connectionLost('Connection closed by remote host');
    }
};


Nevow.Athena.XMLHttpRequestReady = function(req) {
    /* The response is a JSON-encoded 2-array of [action, arguments]
     * where action is one of "noop", "call", "respond", or "close".
     * The arguments are action-specific and passed on to the handler
     * for the action.
     */

    Divmod.debug('request', 'Ready "' + req.responseText.replace('\\', '\\\\').replace('"', '\\"') + '"');

    var actionParts = MochiKit.Base.evalJSON(req.responseText);

    Nevow.Athena.failureCount = 0;

    var actionName = actionParts[0];
    var actionArgs = actionParts[1];
    var action = Nevow.Athena._actionHandlers[actionName];

    Divmod.debug('transport', 'Received ' + actionName);

    action.apply(null, actionArgs);

    /* Client code has had a chance to run now, in response to
     * receiving the result.  If it issued a new request, we've got an
     * output channel already.  If it didn't, though, we might not
     * have one.  In that case, issue a no-op to the server so it can
     * send us things if it needs to. */
    if (Nevow.Athena._numTransports() == 0) {
        Nevow.Athena.sendNoOp();
    }
};

Nevow.Athena._connectionLost = function(reason) {
    Divmod.debug('transport', 'Closed');
    Nevow.Athena.connectionState = Nevow.Athena.DISCONNECTED;
    var calls = Nevow.Athena.remoteCalls;
    Nevow.Athena.remoteCalls = {};
    for (var k in calls) {
        calls[k].errback(new Error("Connection lost"));
    }
    /* IE doesn't close outstanding requests when a user navigates
     * away from the page that spawned them.  Also, we may have lost
     * the connection without navigating away from the page.  So,
     * clean up any outstanding requests right here.
     */
    var cancelledTransports = Nevow.Athena.outstandingTransports;
    Nevow.Athena.outstandingTransports = {};
    for (var reqId in cancelledTransports) {
        cancelledTransports[reqId].abort();
    }
};

Nevow.Athena.XMLHttpRequestFail = function(err) {
    Divmod.debug('request', 'Failed ' + err.message);

    Nevow.Athena.failureCount++;

    if (Nevow.Athena.failureCount >= 3) {
        Nevow.Athena._connectionLost('There are too many failures!');
        return;
    }

    if (Nevow.Athena._numTransports() == 0) {
        Nevow.Athena.sendNoOp();
    }
};

Nevow.Athena.prepareRemoteAction = function(actionType) {
    var url = Nevow.Athena.constructActionURL(actionType);
    var req = MochiKit.Async.getXMLHttpRequest();

    if (Nevow.Athena.connectionState != Nevow.Athena.CONNECTED) {
        return MochiKit.Async.fail(new Error("Not connected"));
    }

    try {
        req.open('POST', url, true);
    } catch (err) {
        return MochiKit.Async.fail(err);
    }

    /* The values in this object aren't actually used by anything.
     */
    Nevow.Athena.outstandingTransports[++Nevow.Athena._transportCounter] = req;
    Divmod.debug('transport', 'Added a request ' + Nevow.Athena._transportCounter + ' transport of type ' + actionType);
    Divmod.debug('transport', 'There are ' + Nevow.Athena._numTransports() + ' transports');

    Divmod.debug('transport', 'Issuing ' + actionType);

    req.setRequestHeader('Livepage-Id', Nevow.Athena.livepageId);
    req.setRequestHeader('content-type', 'text/x-json+athena')
    return MochiKit.Async.succeed(req);
};

Nevow.Athena.preparePostContent = function(args, kwargs) {
    return MochiKit.Base.serializeJSON([args, kwargs]);
};

Nevow.Athena.respondToRemote = function(requestID, response) {
    var reqD = Nevow.Athena.prepareRemoteAction('respond');
    var argumentQueryArgument = Nevow.Athena.preparePostContent([response], {});

    reqD.addCallback(function(req) {
        req.setRequestHeader('Response-Id', requestID);
        var reqD2 = MochiKit.Async.sendXMLHttpRequest(req, argumentQueryArgument);
        reqD2.addBoth(Nevow.Athena.XMLHttpRequestFinished, Nevow.Athena._transportCounter);
        reqD2.addCallback(Nevow.Athena.XMLHttpRequestReady);
        reqD2.addErrback(Nevow.Athena.XMLHttpRequestFail);
    });
};

Nevow.Athena._noArgAction = function(actionName) {
    var reqD = Nevow.Athena.prepareRemoteAction(actionName);
    reqD.addCallback(function(req) {
        var reqD2 = MochiKit.Async.sendXMLHttpRequest(req, Nevow.Athena.preparePostContent([], {}));
        reqD2.addBoth(Nevow.Athena.XMLHttpRequestFinished, Nevow.Athena._transportCounter);
        reqD2.addCallback(function(ign) {
            return Nevow.Athena.XMLHttpRequestReady(req);
        });
        reqD2.addErrback(function(err) {
            return Nevow.Athena.XMLHttpRequestFail(err);
        });
    });
};

Nevow.Athena.sendNoOp = function() {
    Divmod.debug('transport', 'Sending no-op for AthenaID ' + Nevow.Athena.livepageId);
    Nevow.Athena._noArgAction('noop');
};

Nevow.Athena.sendClose = function() {
    Divmod.debug('transport', 'Sending close for AthenaID ' + Nevow.Athena.livepageId);
    Nevow.Athena._noArgAction('close');
};

Nevow.Athena._walkDOM = function(parent, test, memo) {
    if (memo == undefined) {
        memo = [];
    }
    /* alert(parent); */
    if ((parent == undefined) ||
        (parent.childNodes == undefined)) {
        return null;
    }
    var child;
    var len = parent.childNodes.length;
    for (var i = 0; i < len; i++) {
        child = parent.childNodes[i];
        if (test(child)) {
            memo.push(child);
        }
        Nevow.Athena._walkDOM(child, test, memo);
    }
    return memo;
};

Nevow.Athena._callRemote = function(methodName, args, kwargs) {
    var resultDeferred = new MochiKit.Async.Deferred();
    var reqD = Nevow.Athena.prepareRemoteAction('call');
    var requestId = 'c2s' + Nevow.Athena.remoteCallCount;

    var actionArguments = Nevow.Athena.preparePostContent(MochiKit.Base.extend([methodName], args), kwargs);

    Nevow.Athena.remoteCallCount++;
    Nevow.Athena.remoteCalls[requestId] = resultDeferred;

    reqD.addCallback(function(req) {
        req.setRequestHeader('Request-Id', requestId);

        var reqD2 = MochiKit.Async.sendXMLHttpRequest(req, actionArguments);
        reqD2.addBoth(Nevow.Athena.XMLHttpRequestFinished, Nevow.Athena._transportCounter);
        reqD2.addCallback(Nevow.Athena.XMLHttpRequestReady);
        return reqD2;
    });

    reqD.addErrback(Nevow.Athena.XMLHttpRequestFail);

    return resultDeferred;
};

Nevow.Athena.getAttribute = function(node, namespaceURI, namespaceIdentifier, localName) {
    if (node.hasAttributeNS) {
        if (node.hasAttributeNS(namespaceURI, localName)) {
            return node.getAttributeNS(namespaceURI, localName);
        } else if (node.hasAttributeNS(namespaceIdentifier, localName)) {
            return node.getAttributeNS(namespaceIdentifier, localName);
        }
    }
    if (node.hasAttribute) {
        var r = namespaceURI + ':' + localName;
        if (node.hasAttribute(r)) {
            return node.getAttribute(r);
        }
    }
    if (node.getAttribute) {
        var s = namespaceIdentifier + ':' + localName;
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
};

Nevow.Athena.athenaIDFromNode = function(n) {
    var athenaID = Nevow.Athena.getAttribute(n, Nevow.Athena.XMLNS_URI, 'athena', 'id');
    if (athenaID != null) {
        return parseInt(athenaID);
    } else {
        return null;
    }
};

Nevow.Athena.athenaClassFromNode = function(n) {
    var athenaClass = Nevow.Athena.getAttribute(
        n, Nevow.Athena.XMLNS_URI, 'athena', 'class');
    if (athenaClass != null) {
        var cls = Divmod.namedAny(athenaClass);
        if (cls == undefined) {
            throw new Error('NameError: ' + athenaClass);
        } else {
            return cls;
        }
    } else {
        return null;
    }
};

Nevow.Athena.nodeByDOM = function(node) {
    /*
     * Return DOM node which represents the LiveFragment, given the node itself
     * or any child or descendent of that node.
     */
    for (var n = node; n != null; n = n.parentNode) {
        var nID = Nevow.Athena.athenaIDFromNode(n);
        if (nID != null) {
            return n;
        }
    }
    throw new Error("nodeByDOM passed node with no containing Athena Ref ID");
};

Nevow.Athena.RemoteReference = Divmod.Class.subclass('Nevow.Athena.RemoteReference');
Nevow.Athena.RemoteReference.methods(
    function __init__(self, objectID) {
        self.objectID = objectID;
    },

    function callRemote(self, methodName /*, ... */) {
        if (self.objectID == undefined) {
            throw new Error("Cannot callRemote without an objectID");
        }
        var args = [self.objectID];
        for (var idx = 2; idx < arguments.length; idx++) {
            args.push(arguments[idx]);
        }
        return Nevow.Athena._callRemote(methodName, args, {});
    },

    function callRemoteKw(self, methodName, kwargs) {
        return Nevow.Athena._callRemote(methodName, [self.objectID], kwargs);
    });

/**
 * Given a Node, find all of its children (to any depth) with the
 * given attribute set to the given value.  Note: you probably don't
 * want to call this directly; instead, see
 * C{Nevow.Athena.Widget.nodesByAttribute}.
 */
Nevow.Athena.NodesByAttribute = function(root, attrName, attrValue) {
    var visitor = function(node) {
        return (attrValue == MochiKit.DOM.getNodeAttribute(node, attrName));
    }
    return Nevow.Athena._walkDOM(root, visitor);
};

/**
 * Given a Node, find the single child node (to any depth) with the
 * given attribute set to the given value.  If there are more than one
 * Nodes which satisfy this constraint or if there are none at all,
 * throw an error.  Note: you probably don't want to call this
 * directly; instead, see C{Nevow.Athena.Widget.nodeByAttribute}.
 */
Nevow.Athena.NodeByAttribute = function(root, attrName, attrValue) {
    var nodes = Nevow.Athena.NodesByAttribute(root, attrName, attrValue);
    if (nodes.length > 1) {
        throw new Error("Found too many " + attrName + " = " + attrValue);
    } else if (nodes.length < 1) {
        throw new Error("Failed to discover node with class value " +
                        attrValue + " beneath " + root +
                        " (programmer error).");

    } else {
        var result = nodes[0];
        return result;
    }
};

Nevow.Athena.server = new Nevow.Athena.RemoteReference(0);
var server = Nevow.Athena.server;

/**
 * Inform the server that we no longer wish to exchange data, then
 * abort all outstanding requests (Hey, is there a race here?
 * Probably.) and set the local state to reflect that we are no longer
 * connected.
 */
Nevow.Athena._finalize = function() {
    Nevow.Athena.sendClose();
    Nevow.Athena._connectionLost('page unloaded');
};

/**
 *
 */
Nevow.Athena._initialize = function() {
    MochiKit.DOM.addToCallStack(window, 'onunload', Nevow.Athena._finalize, true);

    /**
     * Delay initialization for just a moment so that Safari stops whirling
     * its loading icon.
     */
    setTimeout(function() {
        Divmod.debug("transport", "starting up");
        Nevow.Athena.sendNoOp();
        Divmod.debug("transport", "started up");
    }, 1);
};


/**
 * Athena Widgets
 *
 * This module defines a base class useful for adding behaviors to
 * discrete portions of a page.  These widgets can be independent of
 * other content on the same page, allowing separately developed
 * widgets to be combined, or multiple instances of a single widget to
 * appear repeatedly on the same page.
 */

Nevow.Athena.Widget = Nevow.Athena.RemoteReference.subclass('Nevow.Athena.Widget');
Nevow.Athena.Widget.methods(
    function __init__(self, widgetNode) {
        self.node = widgetNode;
        self.childWidgets = [];
        self.widgetParent = null;
        self.createEventBindings();
        Nevow.Athena.Widget.upcall(self, "__init__", Nevow.Athena.athenaIDFromNode(widgetNode));
    },

    function createEventBindings(self) {
        if (self.node.getElementsByTagNameNS) {
            var events = self.node.getElementsByTagNameNS(Nevow.Athena.XMLNS_URI, 'handler');
            if (events.length == 0) {
                // Maybe namespaces aren't being handled properly, let's check
                var events = self.node.getElementsByTagName('athena:handler');
            }
        } else {
            // We haven't even heard of namespaces, so do without
            var events = self.node.getElementsByTagName('athena:handler');
        }

        function makeHandler(evtHandler) {
            return function (e) {
                try {
                    return self[evtHandler](this, e);
                } catch (e) {
                    Divmod.err(e);
                    return false;
                }
           };
        }

        for (var i = 0; i < events.length; ++i) {
            var event = events[i];
            var evtName = event.getAttribute('event');
            var evtHandler = event.getAttribute('handler');
            event.parentNode[evtName] = makeHandler(evtHandler);
        }
    },

    function addChildWidget(self, newChild) {
        self.childWidgets.push(newChild);
        newChild.setWidgetParent(self);
    },

    function setWidgetParent(self, widgetParent) {
        self.widgetParent = widgetParent;
    },

    function visitNodes(self, visitor) {
        Nevow.Athena._walkDOM(self.node, function(node) {
            var result = visitor(node);
            if (result || result == undefined) {
                return true;
            } else {
                return false;
            }
        });
    },

    function nodeByAttribute(self, attrName, attrValue) {
        return Nevow.Athena.NodeByAttribute(self.node, attrName, attrValue);
    },


    function nodesByAttribute(self, attrName, attrValue) {
        return Nevow.Athena.NodesByAttribute(self.node, attrName, attrValue);
    });

Nevow.Athena.Widget._athenaWidgets = {};

/**
 * Given any node within a Widget (the client-side representation of a
 * LiveFragment), return the instance of the Widget subclass that corresponds
 * with that node, creating that Widget subclass if necessary.
 */
Nevow.Athena.Widget.get = function(node) {
    var widgetNode = Nevow.Athena.nodeByDOM(node);
    var widgetId = Nevow.Athena.athenaIDFromNode(widgetNode);
    if (Nevow.Athena.Widget._athenaWidgets[widgetId] == null) {
        var widgetClass = Nevow.Athena.athenaClassFromNode(widgetNode);
        Nevow.Athena.Widget._athenaWidgets[widgetId] = new widgetClass(widgetNode);
    }
    return Nevow.Athena.Widget._athenaWidgets[widgetId];
};

/**
 * Search the whole document for a particular widget id.
 */
Nevow.Athena.Widget.fromAthenaID = function(widgetId) {
    var visitor = function(node) {
        return (Nevow.Athena.athenaIDFromNode(node) == widgetId);
    }
    var nodes = Nevow.Athena._walkDOM(document, visitor);

    if (nodes.length != 1) {
        throw new Error(nodes.length + " nodes with athena id " + widgetId);
    };

    return Nevow.Athena.Widget.get(nodes[0]);
};


Nevow.Athena.callByAthenaID = function(athenaID, methodName, varargs) {
    var widget = Nevow.Athena.Widget.fromAthenaID(athenaID);
    var method = widget[methodName];
    Divmod.debug('widget', 'Invoking ' + methodName + ' on ' + widget + '(' + widget[methodName] + ')');
    if (method == undefined) {
        throw new Error(widget + ' has no method ' + methodName);
    }
    return method.apply(widget, varargs);
};

Nevow.Athena.consoleDoc = (
    '<html>' +
    '  <head>' +
    '    <title>Log Console</title>' +
    '    <style type="text/css">' +
    '    body {' +
    '      background-color: #fff;' +
    '      color: #333;' +
    '      font-size: 8pt;' +
    '      margin: 0;' +
    '      padding: 0;' +
    '    }' +
    '    #console {' +
    '      font-family: monospace;' +
    '    }' +
    '    .log-message-error {' +
    '      margin: 0 0 0 0;' +
    '      padding: 0;' +
    '      border-bottom: 1px dashed #ccf;' +
    '      color: red;' +
    '    }' +
    '    .timestamp {' +
    '      display: block;' +
    '      font-weight: bold;' +
    '      color: #999;' +
    '    }' +
    '    </style>' +
    '  </head>' +
    '  <body>' +
    '    <div id="console">' +
    '    </div>' +
    '    <hr />' +
    '    <a id="clear" href="">Clear</button>' +
    '  </body>' +
    '</html>');

Nevow.Athena.IntrospectionWidget = Nevow.Athena.Widget.subclass('Nevow.Athena.IntrospectionWidget');
Nevow.Athena.IntrospectionWidget.methods(
    function __init__(self, node) {
        Nevow.Athena.IntrospectionWidget.upcall(self, '__init__', node);

        self.infoNodes = {
            'toggleDebugging': self.nodeByAttribute('class', 'toggle-debug')
        };

        self.infoNodes['toggleDebugging'].onclick = function() { self.toggleDebugging(); return false; };

        self.setDebuggingDisplayStyle();

        self.events = [];
        self.eventLimit = 1000;

        self._logWindow = null;
        self._logNode = null;

        Divmod.logger.addObserver(function(event) { self.observe(event); });
    },

    function observe(self, event) {
        self.events.push(event);
        if (self.events.length > self.eventLimit) {
            self.events.shift();
        }
        if (self._logNode != null) {
            self._addEvent(event);
        }
    },

    function _addEvent(self, event) {
        var node = self._logNode;
        var document = self._logWindow.document;

        var div = document.createElement('div');
        if (event['isError']) {
            div.setAttribute('class', 'log-message-error');
        } else if (event['channel']) {
            div.setAttribute('class', 'log-message-' + event['channel']);
        }
        div.appendChild(document.createTextNode(event['message']));
        node.appendChild(div);
        div.scrollIntoView(false);
    },

    function _clearEvents(self) {
        while (self._logNode.firstChild) {
            self._logNode.removeChild(self._logNode.firstChild);
        }
    },

    function _openLogWindow(self) {
        self._logWindow = window.open('', 'Nevow_Athena_Log_Window', 'width=640,height=480,scrollbars');
        self._logWindow.document.write(Nevow.Athena.consoleDoc);
        self._logWindow.document.close();
        self._logNode = self._logWindow.document.getElementById('console');
        self._logWindow.document.title = 'Mantissa Debug Log Viewer';
        for (var i = 0; i < self.events.length; i++) {
            self.observe(self.events[i]);
        }

        self._clearNode = self._logWindow.document.getElementById('clear');
        self._clearNode.onclick = function(event) { self._clearEvents(); return false; };
    },

    function _closeLogWindow(self) {
        if (self._logWindow) {
            self._logWindow.close();
            self._logWindow = null;
            self._logNode = null;
        }
    },

    function toggleDebugging(self) {
        Divmod.debugging ^= 1;
        self.setDebuggingDisplayStyle();
    },

    function setDebuggingDisplayStyle(self) {
        if (Divmod.debugging) {
            self.infoNodes['toggleDebugging'].setAttribute('class', 'nevow-athena-debugging-enabled');
            self._openLogWindow();
        } else {
            self.infoNodes['toggleDebugging'].setAttribute('class', 'nevow-athena-debugging-disabled');
            self._closeLogWindow();
        }
    });


/**
 * Instantiate Athena Widgets.
 */
Nevow.Athena.Widget._instantiateOneWidget = function(cls, node) {
    Divmod.debug("widget", "Found Widget class " + cls + ", instantiating.");
    var inst = cls.get(node);
    Divmod.debug("widget", "Widget class " + cls + " instantiated.");
    try {
        var widgetParent = Nevow.Athena.Widget.get(node.parentNode);
        widgetParent.addChildWidget(inst);
    } catch (noParent) {
        // Right now we're going to do nothing here.
        Divmod.debug("widget", "No parent found for widget " + inst);
    }
    if (inst.loaded != undefined) {
        inst.loaded();
        Divmod.debug("widget", "Widget class " + cls + " loaded.");
    }
};

Nevow.Athena.Widget._pageLoaded = false;
Nevow.Athena.Widget._waitingWidgets = {};
Nevow.Athena.Widget._widgetNodeAdded = function(nodeId) {
    Nevow.Athena.Widget._waitingWidgets[nodeId] = null;
    if (Nevow.Athena.Widget._pageLoaded) {
        if (Nevow.Athena.Widget._instantiationTimer == null) {
            Nevow.Athena.Widget._instantiationTimer = setTimeout(Nevow.Athena.Widget._instantiateWidgets, 1);
        }
    }
};

Nevow.Athena.Widget._instantiateWidgets = function() {
    var widgetIds = Nevow.Athena.Widget._waitingWidgets;
    Nevow.Athena.Widget._waitingWidgets = {};

    Nevow.Athena.Widget._instantiationTimer = null;

    Nevow.Athena._walkDOM(
        document.documentElement,
        function(node) {
            var cls = Nevow.Athena.athenaClassFromNode(node);
            if (cls) {
                var widgetId = Nevow.Athena.athenaIDFromNode(node);
                if (widgetId != null && widgetId in widgetIds) {
                    Nevow.Athena.Widget._instantiateOneWidget(cls, node);
                }
            }
            return false;
        });
};

Nevow.Athena.Widget._initialize = function() {
    Divmod.debug("widget", "Instantiating live widgets");
    Nevow.Athena.Widget._pageLoaded = true;
    Nevow.Athena.Widget._instantiateWidgets();
    Divmod.debug("widget", "Finished instantiating live widgets");
}

MochiKit.DOM.addLoadEvent(Nevow.Athena._initialize);
MochiKit.DOM.addLoadEvent(Nevow.Athena.Widget._initialize);

