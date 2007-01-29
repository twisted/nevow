// -*- test-case-name: nevow.test.test_javascript -*-

// import Divmod
// import Divmod.Base
// import Divmod.Runtime

// import Nevow

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
        var serialized = Divmod.Base.serializeJSON([ack, message]);
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
                return eval('(' + result.response + ')');
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
    var d = Divmod.Defer.Deferred();
    /*
     * Cheat a little bit.  Add a Deferred to the remoteCalls object
     * (DICTIONARY NGNGRNGRNGNRN) so that when the connection is lost, we
     * will get told about it.  This is somewhat abusive and could probably
     * be improved, but it works pretty nicely for now.  We use a different
     * counter and a different prefix so as to avoid the possibility of
     * colliding with an actual remote call.
     */
    Nevow.Athena.remoteCalls['notifyOnDisconnect-' + Nevow.Athena._notifyOnDisconnectCounter] = d;
    Nevow.Athena._notifyOnDisconnectCounter++;
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
            d.errback(Divmod.namedAny(result[0]).apply(null, result[1]));
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

Nevow.Athena.getAttribute = function() {
    /* Deprecated alias */
    return Divmod.Runtime.theRuntime.getAttribute.apply(Divmod.Runtime.theRuntime, arguments);
};

Nevow.Athena.athenaIDFromNode = function(n) {
    var athenaID = n.id;
    if (athenaID != undefined) {
        var junk = athenaID.split(":");
        if (junk[0] === 'athena' ) {
            return parseInt(junk[1]);
        }
    }
    return null;
};

Nevow.Athena.athenaClassFromNode = function(n) {
    var athenaClass = Divmod.Runtime.theRuntime.getAttribute(
        n, 'class', Nevow.Athena.XMLNS_URI, 'athena');
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
        if (typeof objectID != "number") {
            throw new Error("Invalid object identifier: " + objectID);
        }
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

        setTimeout(function() {
            resultDeferred.addErrback(
                function(err) {
                    self.showErrorDialog(methodName, err);
                });
            }, 0);

        return resultDeferred;
    },

    /**
     * Display an error dialog to the user, containing some information
     * about the uncaught error C{err}, which occured while trying to call
     * the remote method C{methodName}.  To avoid this happening, errbacks
     * should be added synchronously to the deferred returned by L{callRemote}
     * (the errback that triggers this dialog is added via setTimeout(..., 0))
     */
    function showErrorDialog(self, methodName, err) {
        var e = document.createElement("div");
        e.style.padding = "12px";
        e.style.border = "solid 1px #666666";
        e.style.position = "absolute";
        e.style.whiteSpace = "nowrap";
        e.style.backgroundColor = "#FFFFFF";
        e.style.zIndex = 99;
        e.className = "athena-error-dialog-" + Nevow.Athena.athenaIDFromNode(self.node);

        var titlebar = document.createElement("div");
        titlebar.style.borderBottom = "solid 1px #333333";

        var title = document.createElement("div");
        title.style.fontSize = "1.4em";
        title.style.color = "red";
        title.appendChild(
            document.createTextNode("Error"));

        titlebar.appendChild(title);

        e.appendChild(titlebar);

        e.appendChild(
            document.createTextNode("Your action could not be completed because an error occured."));

// Useful for debugging sometimes, except it really isn't very pretty.
// toPrettyNode needs unit tests or something, though.
//         try {
//             e.appendChild(err.toPrettyNode());
//         } catch (err) {
//             alert(err);
//         }

        var errorLine = document.createElement("div");
        errorLine.style.fontStyle = "italic";
        errorLine.appendChild(
            document.createTextNode(
                err.toString() + ' caught while calling method "' + methodName + '"'));
        e.appendChild(errorLine);

        var line2 = document.createElement("div");
        line2.appendChild(
            document.createTextNode("Please retry."));
        e.appendChild(line2);

        var close = document.createElement("a");
        close.href = "#";
        close.onclick = function() {
            document.body.removeChild(e);
            return false;
        }
        close.style.display = "block";

        close.appendChild(
            document.createTextNode("Click here to close."));

        e.appendChild(close);

        document.body.appendChild(e);

        var elemDimensions = Divmod.Runtime.theRuntime.getElementSize(e);
        var pageDimensions = Divmod.Runtime.theRuntime.getPageSize();

        e.style.top  = Math.round(pageDimensions.h / 2 - elemDimensions.h / 2) + "px";
        e.style.left = Math.round(pageDimensions.w / 2 - elemDimensions.w / 2) + "px";
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
    return Divmod.Runtime.theRuntime.nodesByAttribute(root, attrName, attrValue);
};

Nevow.Athena.FirstNodeByAttribute = function(root, attrName, attrValue) {
    return Divmod.Runtime.theRuntime.firstNodeByAttribute(root, attrName, attrValue);
};

/**
 * Given a Node, find the single child node (to any depth) with the
 * given attribute set to the given value.  If there are more than one
 * Nodes which satisfy this constraint or if there are none at all,
 * throw an error.  Note: you probably don't want to call this
 * directly; instead, see C{Nevow.Athena.Widget.nodeByAttribute}.
 */
Nevow.Athena.NodeByAttribute = function(root, attrName, attrValue, /* optional */ defaultNode) {
    return Divmod.Runtime.theRuntime.nodeByAttribute(root, attrName, attrValue, defaultNode);
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
    Divmod.Base.addToCallStack(window, 'onunload', Nevow.Athena._unloaded, true);

    Divmod.Base.addToCallStack(window, 'onkeypress', Nevow.Athena._checkEscape, false);
    Divmod.Base.addToCallStack(window, 'onkeyup', Nevow.Athena._checkEscape, false);

    Nevow.Athena._rdm = Nevow.Athena.ReliableMessageDelivery(Nevow.Athena._rf, Nevow.Athena._connectionLost);

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
 * Invoke the loaded method of the given widget and all of its child widgets.
 */
Nevow.Athena._recursivelyLoad = function _recursivelyLoad(widget) {
    if (widget.loaded) {
        widget.loaded();
    }
    for (var i = 0; i < widget.childWidgets.length; ++i) {
        Nevow.Athena._recursivelyLoad(widget.childWidgets[i]);
    }
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


/**
 * Error class thrown when an attempt is made to invoke a method which is
 * either undefined or unexposed.
 */
Nevow.Athena.NoSuchMethod = Divmod.Error.subclass("Nevow.Athena.NoSuchMethod");


Nevow.Athena.Widget = Nevow.Athena.RemoteReference.subclass('Nevow.Athena.Widget');
Nevow.Athena.Widget.methods(
    function __init__(self, widgetNode) {
        self.node = widgetNode;
        self.childWidgets = [];
        self.widgetParent = null;
        Nevow.Athena.Widget.upcall(self, "__init__", Nevow.Athena.athenaIDFromNode(widgetNode));
    },

    function addChildWidget(self, newChild) {
        self.childWidgets.push(newChild);
        newChild.setWidgetParent(self);
    },

    /**
     * Add a widget with the given ID, class, and markup as a child of this
     * widget.  Any required modules which have not already been imported will
     * be imported.
     *
     * @type info: Opaque handle received from the server where a
     * LiveFragment/Element was passed.
     *
     * @return: A Deferred which will fire with the newly created widget
     * instance once it has been added as a child.
     */
    function addChildWidgetFromWidgetInfo(self, info) {
        return self._addChildWidgetFromComponents(
            info.requiredModules,
            info.id,
            info['class'],
            info.children,
            info.initArguments,
            info.markup
            );
    },

    /**
     * Actual implementation of dynamic widget instantiation.
     */
    function _addChildWidgetFromComponents(self,
                                           requiredModules, widgetID,
                                           widgetClassName, children,
                                           initArguments, markup) {

        var moduleIndex;
        var childIndex;

        var importDeferreds;
        var allImportsDone;
        var topNode;
        var topWidgetClass;
        var childWidgetClass;
        var topWidget;
        var childWidget;
        var childInitArgs;
        var childNode;
        var childID;
        var parentWidget;

        var moduleURL;
        var moduleName;
        var moduleParts;
        var moduleObj;

        if (widgetID in Nevow.Athena.Widget._athenaWidgets) {
            throw new Error("You blew it.");
        }

        importDeferreds = [];
        for (moduleIndex = 0; moduleIndex < requiredModules.length; ++moduleIndex) {
            moduleName = requiredModules[moduleIndex][0];
            moduleURL = requiredModules[moduleIndex][1];

            moduleParts = moduleName.split('.');
            moduleObj = Divmod._global;

            for (var i = 0; i < moduleParts.length; ++i) {
                if (moduleObj[moduleParts[i]] === undefined) {
                    moduleObj[moduleParts[i]] = {};
                }
                moduleObj = moduleObj[moduleParts[i]];
            }

            importDeferreds.push(
                Divmod.Runtime.theRuntime.loadScript(
                    moduleURL));
        }
        allImportsDone = Divmod.Defer.DeferredList(importDeferreds);
        allImportsDone.addCallback(
            function(ignored) {
                topNode = Divmod.Runtime.theRuntime.firstNodeByAttribute(
                    Divmod.Runtime.theRuntime.importNode(
                        Divmod.Runtime.theRuntime.parseXHTMLString(markup).documentElement,
                        true),
                    'id', 'athena:' + widgetID);

                topWidgetClass = Divmod.namedAny(widgetClassName);
                if (topWidgetClass === undefined) {
                    throw new Error("Bad class: " + widgetClassName);
                }

                initArguments.unshift(topNode);
                topWidget = topWidgetClass.apply(null, initArguments);
                Nevow.Athena.Widget._athenaWidgets[widgetID] = topWidget;

                for (childIndex = 0; childIndex < children.length; ++childIndex) {
                    childWidgetClass = Divmod.namedAny(children[childIndex]['class']);
                    childInitArgs = children[childIndex]['initArguments'];
                    childID = children[childIndex]['id'];

                    if (childID in Nevow.Athena.Widget._athenaWidgets) {
                        throw new Error("You blew it: " + childID);
                    }

                    childNode = Divmod.Runtime.theRuntime.firstNodeByAttribute(topNode, 'id', 'athena:' + childID);

                    if (childWidgetClass === undefined) {
                        throw new Error("Broken: " + children[childIndex]['class']);
                    }

                    childInitArgs.unshift(childNode);
                    childWidget = childWidgetClass.apply(null, childInitArgs);

                    Nevow.Athena.Widget._athenaWidgets[childID] = childWidget;

                    parentWidget = Nevow.Athena.Widget.get(childNode.parentNode);
                    parentWidget.addChildWidget(childWidget);
                }
                self.addChildWidget(topWidget);

                Nevow.Athena._recursivelyLoad(topWidget);

                return topWidget;
            });

        return allImportsDone;
    },

    function setWidgetParent(self, widgetParent) {
        self.widgetParent = widgetParent;
    },

    function nodeByAttribute(self, attrName, attrValue, /* optional */ defaultNode) {
        return Divmod.Runtime.theRuntime.nodeByAttribute(self.node, attrName, attrValue, defaultNode);
    },

    function firstNodeByAttribute(self, attrName, attrValue) {
        return Divmod.Runtime.theRuntime.firstNodeByAttribute(self.node, attrName, attrValue);
    },

    function nodeById(self, id) {
        var translatedId = 'athenaid:' + self.objectID + '-' + id;
        return Divmod.Runtime.theRuntime.getElementByIdWithNode(self.node, translatedId);
    },

    function nodesByAttribute(self, attrName, attrValue) {
        return Divmod.Runtime.theRuntime.nodesByAttribute(self.node, attrName, attrValue);
    },

    /**
     * Remove all the child widgets from this widget.
     */
    function removeAllChildWidgets(self) {
        for (var i=0; i<self.childWidgets.length; i++) {
            self.childWidgets[i].setWidgetParent(null);
        }
        self.childWidgets = [];
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
        var initArgs = eval(initText);
        initArgs.unshift(widgetNode);
        Nevow.Athena.Widget._athenaWidgets[widgetId] = widgetClass.apply(null, initArgs);
    }
    return Nevow.Athena.Widget._athenaWidgets[widgetId];
};

Nevow.Athena.Widget.dispatchEvent = function dispatchEvent(widget, eventName, handlerName, callable) {
    var result = false;
    Nevow.Athena._rdm.pause();
    try {
        try {
            result = callable.call(widget);
        } catch (err) {
            Divmod.err(
                err,
                "Dispatching " + eventName +
                " to " + handlerName +
                " on " + widget +
                " failed.");
        }
    } catch (err) {
        Nevow.Athena._rdm.unpause();
        throw err;
    }
    Nevow.Athena._rdm.unpause();
    return result;
};

/**
 * Given a node and a method name in an event handling context, dispatch the
 * event to the named method on the widget which owns the given node.  This
 * also sets up error handling and does return value translation as
 * appropriate for an event handler.  It also pauses the outgoing message
 * queue to allow multiple messages from the event handler to be batched up
 * into a single request.
 */
Nevow.Athena.Widget.handleEvent = function handleEvent(node, eventName, handlerName) {
    var widget = Nevow.Athena.Widget.get(node);
    var method = widget[handlerName];
    var result = false;
    if (method === undefined) {
        Divmod.msg("Undefined event handler: " + handlerName);
    } else {
        result = Nevow.Athena.Widget.dispatchEvent(
            widget, eventName, handlerName,
            function() {
                return method.call(widget, node);
            });
    }
    return result;
};

/**
 * Retrieve the Widget with the given widget id.
 */
Nevow.Athena.Widget.fromAthenaID = function(widgetId) {
    var widget = Nevow.Athena.Widget._athenaWidgets[widgetId];
    if (widget != undefined) {
        return widget;
    }

    return Nevow.Athena.Widget.get(
        document.getElementById('athena:' + widgetId));
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
    if (inst.nodeInserted != undefined) {
        inst.nodeInserted();
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

    for (var widgetId in widgetIds) {
        var node = document.getElementById('athena:' + widgetId);
        if (node == null) {
            Divmod.debug("widget", "Widget scheduled for addition was missing.  Id = " + widgetId);
        } else {
            var cls = Nevow.Athena.athenaClassFromNode(node);
            Nevow.Athena.Widget._instantiateOneWidget(cls, node);
        }
    }
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

    div.className = 'nevow-connection-lost';
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

Divmod.Base.addLoadEvent(Nevow.Athena._initialize);
Divmod.Base.addLoadEvent(Nevow.Athena.Widget._initialize);

