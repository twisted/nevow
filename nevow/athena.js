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


Nevow.Athena.ReliableMessageDelivery = Divmod.Class.subclass('Nevow.Athena.ReliableMessageDelivery');
Nevow.Athena.ReliableMessageDelivery.methods(
    function __init__(self,
                      outputFactory,
                      /* optional */
                      connectionLost /* = null */,
                      transportlessTimeout /* = 30 */,
                      idleTimeout /* = 300 */,
                      scheduler /* = setTimeout */) {

        self.messages = [];
        self.outputs = [];

        self.ack = -1;
        self.seq = -1;

        self._paused = 0;

        self.failureCount = 0;

        self.outputFactory = outputFactory;
        self.requests = [];

        if (transportlessTimeout == undefined) {
            transportlessTimeout = 30;
        }
        if (idleTimeout == undefined) {
            idleTimeout = 300;
        }
        if (connectionLost == undefined) {
            connectionLost = null;
        }
        if (scheduler == undefined) {
            scheduler = setTimeout;
        }
        self.transportlessTimeout = transportlessTimeout * 1000;
        self.idleTimeout = idleTimeout * 1000;
        self.connectionLost = connectionLost;
        self.scheduler = scheduler;
    },

    function start(self) {
        self.running = true;
        if (self.requests.length == 0) {
            self.flushMessages();
        }
    },

    function stop(self) {
        self.running = false;
        for (var i = 0; i < self.requests.length; ++i) {
            self.requests[i].abort();
        }
        self.requests = null;
    },

    function acknowledgeMessage(self, ack) {
        while (self.messages.length && self.messages[0][0] <= ack) {
            self.messages.shift();
        }
    },

    function messageReceived(self, message) {
        self.pause();
        if (message.length) {
           if (self.ack + 1 >= message[0][0]) {
               var ack = self.ack;
               self.ack = Divmod.max(self.ack, message[message.length - 1][0]);
               for (var i = 0; i < message.length; ++i) {
                   var msg = message[i];
                   var seq = msg[0];
                   var payload = msg[1];
                   if (seq > ack) {
                       try {
                           Nevow.Athena._actionHandlers[payload[0]].apply(null, payload[1]);
                       } catch (e) {
                           Divmod.err(e, 'Action handler ' + payload[0] + ' for ' + seq + ' failed.');
                       }
                   }
               }
           } else {
               Divmod.debug("transport", "Sequence gap!  " + Nevow.Athena.livepageId + " went from " + self.ack + " to " + message[0][0]);
           }
        }
        self.unpause();
    },

    function pause(self) {
        self._paused += 1;
        var s = "";
        for (var i = 0; i < self._paused; ++i) {
            s += " *";
        }
        Divmod.debug("transport", s + "Pausing.");
    },

    function unpause(self) {
        var s = "";
        for (var i = 0; i < self._paused; ++i) {
            s += " *";
        }
        Divmod.debug("transport", s + "Unpausing.");
        self._paused -= 1;
        if (self._paused == 0) {
            Divmod.debug("transport", s + "And flushing");
            self.flushMessages();
        }
    },

    function addMessage(self, msg) {
        ++self.seq;
        self.messages.push([self.seq, msg]);
        self.flushMessages();
    },

    function flushMessages(self) {
        if (!self.running || self._paused) {
            return;
        }

        var outgoingMessages = self.messages;

        if (outgoingMessages.length == 0) {
            if (self.requests.length != 0) {
                return;
            }
        }

        if (self.requests.length > 1) {
            self.failureCount -= 1;
            self.requests[0].abort();
        }

        var theRequest = self.outputFactory().send(self.ack, outgoingMessages);

        self.requests.push(theRequest);
        theRequest.deferred.addCallback(function(result) {
            self.failureCount = 0;
            self.acknowledgeMessage(result[0]);
            self.messageReceived(result[1]);
        });
        theRequest.deferred.addErrback(function(err) {
            self.failureCount += 1;
        });
        theRequest.deferred.addCallback(function(ign) {
            for (var i = 0; i < self.requests.length; ++i) {
                if (self.requests[i] === theRequest) {
                    self.requests.splice(i, 1);
                    break;
                }
            }
            if (self.failureCount < 3) {
                if (!theRequest.aborted) {
                    self.flushMessages();
                }
            } else if (self.connectionLost != null) {
                var connLost = self.connectionLost;
                self.stop();
                connLost();
            }
        });
    });

Nevow.Athena.AbortableHTTPRequest = Divmod.Class.subclass("Nevow.Athena.AbortableHTTPRequest");
Nevow.Athena.AbortableHTTPRequest.methods(
    function __init__(self,
                      request,
                      deferred) {
        self.request = request;
        self.deferred = deferred;
        self.aborted = false;
    },

    function abort(self) {
        self.aborted = true;
        self.request.abort();
    });

Nevow.Athena.HTTPRequestOutput = Divmod.Class.subclass('Nevow.Athena.HTTPRequestOutput');
Nevow.Athena.HTTPRequestOutput.methods(
    function __init__(self,
                      /* optional */
                      baseURL /* = Nevow.Athena.baseURL() */,
                      queryArgs /* = [] */,
                      headers /* = [] */) {
        if (baseURL == undefined) {
            baseURL = Nevow.Athena.baseURL();
        }
        self.baseURL = baseURL;
        self.queryArgs = queryArgs;
        self.headers = headers;
    },

    function send(self, ack, message) {
        var serialized = MochiKit.Base.serializeJSON([ack, message]);
        var response = Divmod.Runtime.theRuntime.getPage(
            self.baseURL,
            self.queryArgs,
            'POST',
            self.headers,
            serialized);
        var requestWrapper = new Nevow.Athena.AbortableHTTPRequest(
            response[0], response[1]);
        requestWrapper.deferred.addCallback(function(result) {
            if (result.status == 200) {
                return Divmod.Runtime.theRuntime.eval(result.response);
            }
            throw new Error("Request failed: " + result.status);
        });
        return requestWrapper;
    });


Nevow.Athena.remoteCallCount = 0;
Nevow.Athena.remoteCalls = {};

Nevow.Athena.CONNECTED = 'connected';
Nevow.Athena.DISCONNECTED = 'disconnected';
Nevow.Athena.connectionState = Nevow.Athena.CONNECTED;

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


Nevow.Athena._actionHandlers = {
    noop: function() {
        /* Noop! */
    },

    call: function(functionName, requestId, funcArgs) {
        var path = [null];
        var funcObj = Divmod.namedAny(functionName, path);
        var self = path.pop();
        var result = undefined;
        var success = true;
        try {
            result = funcObj.apply(self, funcArgs);
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
                    Nevow.Athena._rdm.addMessage(['respond', [requestId, true, result]]);
                }, function(err) {
                    Nevow.Athena._rdm.addMessage(['respond', [requestId, false, err.error]]);
                });
        } else {
            Nevow.Athena._rdm.addMessage(['respond', [requestId, success, result]]);
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
        Nevow.Athena._rdm.stop();
        Nevow.Athena._connectionLost('Connection closed by remote host');
    }
};

Nevow.Athena._rf = (function() {
    var rf;
    return function() {
        if (rf == undefined) {
            rf = new Nevow.Athena.HTTPRequestOutput(
                Nevow.Athena.baseURL(),
                [],
                [['Livepage-Id', Nevow.Athena.livepageId],
                 ['Content-Type', 'text/x-json+athena']]);
        }
        return rf;
    };
})();

Nevow.Athena._walkDOM = function(parent, test, memo, onlyOne) {
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
        if(onlyOne && memo.length) {
            return memo[0];
        }
        Nevow.Athena._walkDOM(child, test, memo, onlyOne);
    }
    if(onlyOne) {
        return null;
    }
    return memo;
};

Nevow.Athena._rdm = new Nevow.Athena.ReliableMessageDelivery(Nevow.Athena._rf, Nevow.Athena._connectionLost);

Nevow.Athena.getAttribute = function() {
    /* Deprecated alias */
    return Divmod.Runtime.theRuntime.getAttribute.apply(Divmod.Runtime.theRuntime, arguments);
};

Nevow.Athena.athenaIDFromNode = function(n) {
    var athenaID = Divmod.Runtime.theRuntime.getAttribute(n, Nevow.Athena.XMLNS_URI, 'athena', 'id');
    if (athenaID != null) {
        return parseInt(athenaID);
    } else {
        return null;
    }
};

Nevow.Athena.athenaClassFromNode = function(n) {
    var athenaClass = Divmod.Runtime.theRuntime.getAttribute(
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

    function _call(self, methodName, args, kwargs) {
        if (self.objectID == undefined) {
            throw new Error("Cannot callRemote without an objectID");
        }

        if (Nevow.Athena.connectionState == Nevow.Athena.DISCONNECTED) {
            return Divmod.Defer.fail(new Error("Connection lost"));
        }

        var resultDeferred = new Divmod.Defer.Deferred();
        var requestId = 'c2s' + Nevow.Athena.remoteCallCount;

        Nevow.Athena.remoteCallCount++;
        Nevow.Athena.remoteCalls[requestId] = resultDeferred;

        Nevow.Athena._rdm.addMessage(['call', [requestId, methodName, self.objectID, args, kwargs]]);

        return resultDeferred;
    },

    function callRemote(self, methodName /*, ... */) {
        var args = [];
        for (var idx = 2; idx < arguments.length; idx++) {
            args.push(arguments[idx]);
        }
        return self._call(methodName, args, {});
    },

    function callRemoteKw(self, methodName, kwargs) {
        return self._call(methodName, [], kwargs);
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

Nevow.Athena.FirstNodeByAttribute = function(root, attrName, attrValue) {
    /* duplicate this here rather than adding an "onlyOne" arg to
       NodesByAttribute so adding an extra arg accidentally doesn't
       change it's behaviour if called directly
    */
    var visitor = function(node) {
        return (attrValue == MochiKit.DOM.getNodeAttribute(node, attrName));
    }
    var node = Nevow.Athena._walkDOM(root, visitor, undefined, true);
    if(!node) {
        throw new Error("Failed to discover node with " + attrName +
                        " value " + attrValue + " beneath " + root +
                        " (programmer error).");
    }
    return node;
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
    Nevow.Athena._rdm.addMessage(['close', []]);
};

Nevow.Athena._pageUnloaded = false;
Nevow.Athena._unloaded = function() {
    Nevow.Athena._pageUnloaded = true;
    Nevow.Athena._finalize();
};

Nevow.Athena._checkEscape = function(event) {
    if (event.keyCode == 27) {
        Nevow.Athena._finalize();
        return false;
    }
};

/**
 *
 */
Nevow.Athena._initialize = function() {
    MochiKit.DOM.addToCallStack(window, 'onunload', Nevow.Athena._unloaded, true);

    MochiKit.DOM.addToCallStack(window, 'onkeypress', Nevow.Athena._checkEscape, false);
    MochiKit.DOM.addToCallStack(window, 'onkeyup', Nevow.Athena._checkEscape, false);

    /**
     * Delay initialization for just a moment so that Safari stops whirling
     * its loading icon.
     */
    setTimeout(function() {
        Divmod.debug("transport", "starting up");
        Nevow.Athena._rdm.start();
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
                events = self.node.getElementsByTagName('athena:handler');
            }
        } else {
            // We haven't even heard of namespaces, so do without
            events = self.node.getElementsByTagName('athena:handler');
        }

        function makeHandler(evtHandler) {
            return function (e) {
                Divmod.debug("widget", "Handling an event.");
                var success = false;
                var result = false;
                Nevow.Athena._rdm.pause();
                try {
                    result = self[evtHandler](this, e);
                } catch (e) {
                    success = false;
                    Divmod.err(e);
                }
                Nevow.Athena._rdm.unpause();
                Divmod.debug("widget", "Finished handling event.");
                return result;
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


    function firstNodeByAttribute(self, attrName, attrValue) {
        return Nevow.Athena.FirstNodeByAttribute(self.node, attrName, attrValue);
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
        var initNode = document.getElementById('athena-init-args-' + widgetId);
        var initText = initNode.value;
        var initArgs = Divmod.Runtime.theRuntime.eval(initText);
        initArgs.unshift(widgetNode);
        Nevow.Athena.Widget._athenaWidgets[widgetId] = widgetClass.apply(null, initArgs);
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
    '    .log-message-transport {' +
    '      margin: 0 0 0 0;' +
    '      padding: 0;' +
    '      border-bottom: 1px dashed #ccf;' +
    '      color: magenta;' +
    '    }' +
    '    .log-message-request {' +
    '      margin: 0 0 0 0;' +
    '      padding: 0;' +
    '      border-bottom: 1px dashed #ccf;' +
    '      color: blue;' +
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
        if (!Nevow.Athena._pageUnloaded) {
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
        }
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

