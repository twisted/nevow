// -*- test-case-name: nevow.test.test_javascript -*-

// import Divmod
// import Divmod.Runtime

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


Nevow.Athena._connectionLost = function(reason) {
    if (Nevow.Athena.connectionState == Nevow.Athena.DISCONNECTED) {
        Divmod.debug("transport", "Warning: duplicate close notification.");
        return;
    }
    Divmod.debug('transport', 'Closed');
    Nevow.Athena.connectionState = Nevow.Athena.DISCONNECTED;
    var calls = Nevow.Athena.remoteCalls;
    Nevow.Athena.remoteCalls = {};
    for (var k in calls) {
        Divmod.msg("Errbacking an existing call");
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


Nevow.Athena._notifyOnDisconnectCounter = 0;
/*
 * Set up to have a function called when the LivePage connection has been
 * lost, either due to an explicit close, a timeout, or some other error. 
 * The function will be invoked with one argument, probably a Failure
 * indicating the reason the connection was lost.
 */
Nevow.Athena.notifyOnDisconnect = function(callback) {
    var d;
    d = new Divmod.Defer.Deferred();
    /*
     * Cheat a little bit.  Add a Deferred to the remoteCalls object
     * (DICTIONARY NGNGRNGRNGNRN) so that when the connection is lost, we
     * will get told about it.  This is somewhat abusive and could probably
     * be improved, but it works pretty nicely for now.  We use a different
     * counter and a different prefix so as to avoid the possibility of
     * colliding with an actual remote call.
     */
    Nevow.Athena.remoteCalls['notifyOnDisconnect-' + Nevow.Athena._notifyOnDisconnectCounter] = d;
    d.addBoth(callback);
};


Nevow.Athena.preparePostContent = function(args, kwargs) {
    return MochiKit.Base.serializeJSON([args, kwargs]);
};


Nevow.Athena._updateTransportTracking = function(passthrough, reqId) {
    Divmod.debug(
        'transport',
        ('request ' +
         reqId +
         ' completed - now ' +
         Nevow.Athena._numTransports() +
         ' transports, returning ' +
         typeof passthrough + ' ' +
         Divmod.vars(passthrough)));

    if (!delete Nevow.Athena.outstandingTransports[reqId]) {
        Divmod.debug("Crap failed to delete crap");
    }

    return passthrough;
};


Nevow.Athena.sendMessage = function(actionType, args, kwargs, requestId, responseId) {
    if (Nevow.Athena.connectionState != Nevow.Athena.CONNECTED) {
        return Divmod.Defer.fail(Error("Not Connected"));
    }

    if (!args) {
        args = [];
    }

    if (!kwargs) {
        kwargs = {};
    }

    var headers = [
        ['Livepage-Id', Nevow.Athena.livepageId],
        ['Content-Type', 'text/x-json+athena']];

    if (requestId) {
        headers.push(['Request-Id', requestId]);
    } else if (responseId) {
        headers.push(['Response-Id', responseId]);
    }

    var request = Divmod.Runtime.theRuntime.getPage(
        Nevow.Athena.baseURL(),
        [['action', actionType]],
        'POST',
        headers,
        Nevow.Athena.preparePostContent(args, kwargs));

    Nevow.Athena.outstandingTransports[++Nevow.Athena._transportCounter] = request[0];

    request[1].addBoth(Nevow.Athena._updateTransportTracking, Nevow.Athena._transportCounter);
    request[1].addCallback(Nevow.Athena._cbMessage);
    request[1].addErrback(Nevow.Athena._ebMessage);

    Divmod.debug(
        'transport',
        ('Issuing a request ' +
         Nevow.Athena._transportCounter +
         ' transport of type ' +
         actionType +
         '(now ' +
         Nevow.Athena._numTransports() +
         ' outstanding)'));

    return request[1];
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
                    Nevow.Athena.respondToRemote(requestId, [false, err]);
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


Nevow.Athena._cbMessage = function(result) {
    /* The response is a JSON-encoded 2-array of [action, arguments]
     * where action is one of "noop", "call", "respond", or "close".
     * The arguments are action-specific and passed on to the handler
     * for the action.
     */

    if (result.status != 200) {
        throw Error("Non-success response code: " + result.status);
    }

    Divmod.debug('request', 'Ready: ' + result.response);

    var actionParts = eval('(' + result.response + ')');

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
        Nevow.Athena.sendMessage('noop');
    }
};


Nevow.Athena._ebMessage = function(err) {
    Divmod.err(err, 'request failed');

    Nevow.Athena.failureCount++;

    if (Nevow.Athena.failureCount >= 3) {
        Nevow.Athena._connectionLost('There are too many failures!');
        return;
    }

    if (Nevow.Athena._numTransports() == 0) {
        Nevow.Athena.sendMessage('noop');
    }
};


Nevow.Athena.respondToRemote = function(requestId, response) {
    return Nevow.Athena.sendMessage('respond', [response], {}, null, requestId);
};


Nevow.Athena.sendClose = function() {
    Divmod.debug('transport', 'Sending close for AthenaID ' + Nevow.Athena.livepageId);
    Nevow.Athena.sendMessage('close');
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
    var resultDeferred = new Divmod.Defer.Deferred();
    var requestId = 'c2s' + Nevow.Athena.remoteCallCount;

    Nevow.Athena.remoteCallCount++;
    Nevow.Athena.remoteCalls[requestId] = resultDeferred;

    Nevow.Athena.sendMessage(
        'call',
        MochiKit.Base.extend([methodName], args),
        kwargs,
        requestId,
        null);

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
        Nevow.Athena.sendMessage('noop');
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
        };

        for (var i = 0; i < events.length; ++i) {
            var event = events[i];
            var evtName = event.getAttribute('event');
            var evtHandler = event.getAttribute('handler');
            event.parentNode[evtName] = makeHandler(evtHandler);
            Divmod.msg("Hooked " + evtName + " up to " + evtHandler + " on " + self);
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

        self.events = [];
        self.eventLimit = 1000;

        self._logWindow = null;
        self._logNode = null;

        Divmod.logger.addObserver(function(event) { self.observe(event); });

        self.setDebuggingDisplayStyle();
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
            self._addEvent(self.events[i]);
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


Nevow.Athena.Widget._defaultDisconnectionNotifier = function() {
    var url = Divmod.baseURL() + '__athena_private__/connection-status-down.png';

    var img = document.createElement('img');
    img.src = url;

    var div = document.createElement('div');
    div.appendChild(img);
    div.appendChild(document.createElement('br'));
    div.appendChild(document.createTextNode('Connection to server lost! '));
    div.appendChild(document.createElement('br'));

    var a = document.createElement('a');
    a.appendChild(document.createTextNode('Click to attempt to reconnect.'));
    a.href = '#';
    a.onclick = function() {
        document.location = document.location;
        return false;
        };
    div.appendChild(a);

    div.style.textAlign = 'center';
    div.style.position = 'absolute';
    div.style.top = '1em';
    div.style.left = '1em';
    div.style.backgroundColor = '#fff';
    div.style.border = 'thick solid red';
    div.style.padding = '2em';
    div.style.margin = '2em';

    Nevow.Athena.notifyOnDisconnect(function() {
            Divmod.msg("Appending connection status image to document.");
            document.body.appendChild(div);

            var setInvisible = function() {
                img.style.visibility = 'hidden';
                setTimeout(setVisible, 1000);
            };
            var setVisible = function() {
                img.style.visibility = 'visible';
                setTimeout(setInvisible, 1000);
            };
            setVisible();
        });
};

Nevow.Athena.Widget._initialize = function() {

    Divmod.debug("widget", "Instantiating live widgets");
    Nevow.Athena.Widget._pageLoaded = true;
    Nevow.Athena.Widget._instantiateWidgets();
    Divmod.debug("widget", "Finished instantiating live widgets");

    Divmod.debug("transport", "Setting up page disconnect notifier");
    /*
     * XXX TODO: Certain pages may want to disable the default disconnection
     * notifier, if they are going to provide something nicer that indicates
     * connection status.
     */
    Nevow.Athena.Widget._defaultDisconnectionNotifier();
    Divmod.debug("transport", "Finished setting up page disconnect notifier");
};

MochiKit.DOM.addLoadEvent(Nevow.Athena._initialize);
MochiKit.DOM.addLoadEvent(Nevow.Athena.Widget._initialize);

