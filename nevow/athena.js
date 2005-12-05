
if (typeof(Divmod) == 'undefined') {
    Divmod = {};
}

Divmod.log = function(msg) {
    var logElement = document.getElementById('nevow-log');
    if (logElement != null) {
        var msgElement = document.createElement('div');
        msgElement.appendChild(document.createTextNode(msg));
        logElement.appendChild(msgElement);
    }
}

Divmod.namedAny = function(name) {
    return eval(name);
}

Divmod._PROTOTYPE_ONLY = {};

Divmod.Class = function(asPrototype) {
    if (asPrototype !== Divmod._PROTOTYPE_ONLY) {
        this.__init__.apply(this, arguments);
    }
};

Divmod.__classDebugCounter__ = 0;

Divmod.Class.subclass = function() {
    var superClass = this;
    var subClass = function() {
        return Divmod.Class.apply(this, arguments)
    };
    subClass.prototype = new superClass(Divmod._PROTOTYPE_ONLY);
    subClass.subclass = Divmod.Class.subclass;

    /* Copy class methods and attributes, so that you can do polymorphism on
     * class methods (needed for Nevow.Athena.Widget.get below).
     */

    for (var varname in superClass) {
        if ((varname != 'prototype') &&
            (varname != 'constructor') &&
            (superClass[varname] != undefined)) {
            subClass[varname] = superClass[varname];
        }
    }

    subClass.upcall = function(otherThis, methodName) {
        var funcArgs = [];
        for (var i = 2; i < arguments.length; ++i) {
            funcArgs.push(arguments[i]);
        }
        var superResult = superClass.prototype[methodName].apply(otherThis, funcArgs);
        return superResult;
    };

    /**
       Not quite sure what to do with this...
    **/
    Divmod.__classDebugCounter__ += 1;
    subClass.__classDebugCounter__ = Divmod.__classDebugCounter__;
    subClass.toString = function() {
        return '<Class #' + subClass.__classDebugCounter__ + '>';
    };
    subClass.prototype.toString = function() {
        return '<"Instance" of #' + subClass.__classDebugCounter__ + '>';
    };
    return subClass;
};

Divmod.Class.prototype.__init__ = function() {
    throw new Error("If you ever hit this code path something has gone horribly wrong");
};

if (typeof(Nevow) == 'undefined') {
    Nevow = {};
}

if (typeof(Nevow.Athena) == 'undefined') {
    Nevow.Athena = {};
}

Nevow.Athena.NAME = 'Nevow.Athena';
Nevow.Athena.__repr__ = function() {
    return '[' + this.NAME + ']';
};

Nevow.Athena.toString = function() {
    return this.__repr__();
};

Nevow.Athena.XMLNS_URI = 'http://divmod.org/ns/athena/0.7';

Nevow.Athena.baseURL = function() {

    // Use "cached" value if it exists
    if (typeof(Nevow.Athena._baseURL) != "undefined") {
        return Nevow.Athena._baseURL;
    }

    var baseURL = window.location.toString();
    var queryParamIndex = baseURL.indexOf('?');

    if (queryParamIndex != -1) {
        baseURL = baseURL.substring(0, queryParamIndex);
    }

    if (baseURL.charAt(baseURL.length - 1) != '/') {
        baseURL += '/';
    }

    baseURL += 'transport';

    // "Cache" and return
    Nevow.Athena._baseURL = baseURL;
    return Nevow.Athena._baseURL;
};

Nevow.Athena.debugging = false;
Nevow.Athena.debug = function(msg) {
    if (Nevow.Athena.debugging) {
        Divmod.log(msg);
    }
};

Nevow.Athena.constructActionURL = function(action) {
    return (Nevow.Athena.baseURL()
            + '?action='
            + encodeURIComponent(action));
};

Nevow.Athena.failureCount = 0;
Nevow.Athena.remoteCallCount = 0;
Nevow.Athena.remoteCalls = {};
Nevow.Athena.outstandingTransports = 0;
Nevow.Athena.responseDispatchTable = new Object();

Nevow.Athena.responseDispatchTable['text/xml'] = function(d, content) {
    d.callback(TEH_XML_PARSER(content));
};

Nevow.Athena.responseDispatchTable['text/json'] = function(d, content) {
    if (content[0]) {
        d.callback(content[1]);
    } else {
        d.errback(new Error(content[1]));
    }
};

Nevow.Athena.XMLHttpRequestFinished = function(passthrough) {
    Nevow.Athena.outstandingTransports--;
    return passthrough;
};

Nevow.Athena.XMLHttpRequestReady = function(req) {
    Nevow.Athena.debug('A request is completed: ' + req.responseText);

    /* The response's content is a JSON-encoded 4-array of
     * [Response-Id, Request-Id, Content-Type, [success, result]].  If
     * this is a response to a previous request, responseId will not
     * be null.  If this is a server-initiated request, requestId will
     * not be null.
     */

    if (req.responseText == '') {
        /* Server timed out the transport, just re-request */
        Nevow.Athena.debug('Empty server message, reconnecting');
        if (Nevow.Athena.outstandingTransports == 0) {
            Nevow.Athena.debug('No outstanding transports, sending no-op');
            Nevow.Athena.sendNoOp();
        }
        return;
    }

    Nevow.Athena.debug('evaluating json in responseText');
    var responseParts = MochiKit.Base.evalJSON(req.responseText);
    Nevow.Athena.debug('evaluated it');

    Nevow.Athena.failureCount = 0;

    var responseId = responseParts[0];
    var requestId = responseParts[1];

    if (requestId != null) {
        Nevow.Athena.debug('Got a response to a request');

        var contentType = responseParts[2];
        var contentBody = responseParts[3];

        var d = Nevow.Athena.remoteCalls[requestId];
        var handler = Nevow.Athena.responseDispatchTable[contentType];
        delete Nevow.Athena.remoteCalls[requestId];

        if (handler != null) {
            handler(d, contentBody);
        } else {
            Nevow.Athena.debug("Unknown content-type: " + contentType);
            d.errback(new Error("Unhandled content type: " + contentType));
        }

    } else if (responseId != null) {
        Nevow.Athena.debug('Server initiated request');

        var contentBody = responseParts[2];

        var objectId = contentBody[0];
        var methodName = contentBody[1];
        var methodArgs = contentBody[2];

        /*
        var resultD = Nevow.Athena.localObjectTable[objectId].dispatch(methodName, methodArgs);
        resultD.addCallbacks(Nevow.Athena.respondToRequest
        */

        Nevow.Athena.debug('Invoking ' + new String(methodName) + ' with arguments ' + new String(methodArgs));
        var methodObj = Divmod.namedAny(methodName);
        var result;
        var success;
        try {
            result = methodObj.apply(null, methodArgs);
            success = true;
        } catch (error) {
            result = error;
            success = false;
        } 
        Nevow.Athena.debug('Invoked it');

        var isDeferred = false;

        if (result == undefined) {
            Nevow.Athena.debug('it was undefined');
            result = null;
        } else {
            /* if it quacks like a duck ...
               this sucks!!!  */
            isDeferred = (result.addCallback && result.addErrback);
        }
        Nevow.Athena.debug('Is it a deferred? ' + new String(isDeferred));

        if (isDeferred) {
            Nevow.Athena.debug('It is a deferred, adding a callback');
            result.addCallbacks(function(result) {
                    Nevow.Athena.respondToRemote(responseId, [true, result]);
                }, function(err) {
                    Nevow.Athena.respondToRemote(responseId, [false, result]);
                });
        } else {
            Nevow.Athena.debug('Responding synchronously to remote request with ID ' + new String(responseId));
            Nevow.Athena.respondToRemote(responseId, [success, result]);
        }

    }

    /* Client code has had a chance to run now, in response to
     * receiving the result.  If it issued a new request, we've got an
     * output channel already.  If it didn't, though, we might not
     * have one.  In that case, issue a no-op to the server so it can
     * send us things if it needs to. */
    if (Nevow.Athena.outstandingTransports == 0) {
        Nevow.Athena.sendNoOp();
    }
};

Nevow.Athena.XMLHttpRequestFail = function(err) {
    Nevow.Athena.debug('A request failed!');

    Nevow.Athena.failureCount++;

    if (Nevow.Athena.failureCount >= 3) {
        Nevow.Athena.debug('There are too many failures!');
        var calls = Nevow.Athena.remoteCalls;
        Nevow.Athena.remoteCalls = {};
        for (var k in calls) {
            calls[k].errback(new Error("Connection lost"));
        }
        return;
    } else {
        Nevow.Athena.debug('There are not too many failures.');
    }

    if (Nevow.Athena.outstandingTransports == 0) {
        Nevow.Athena.sendNoOp();
    }
};

Nevow.Athena.prepareRemoteAction = function(actionType) {
    var url = Nevow.Athena.constructActionURL(actionType);
    var req = MochiKit.Async.getXMLHttpRequest();

    try {
        req.open('POST', url, true);
    } catch (err) {
        return resultD = MochiKit.Async.fail(err);
    }

    Nevow.Athena.outstandingTransports++;

    Nevow.Athena.debug("Setting livepage id " + new String(Nevow.Athena.livepageId));
    req.setRequestHeader('Livepage-Id', Nevow.Athena.livepageId);
    req.setRequestHeader('content-type', 'text/x-json+athena')
    return resultD = MochiKit.Async.succeed(req);
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
        reqD2.addBoth(Nevow.Athena.XMLHttpRequestFinished);
        reqD2.addCallback(Nevow.Athena.XMLHttpRequestReady);
        reqD2.addErrback(Nevow.Athena.XMLHttpRequestFail);
    });
};

Nevow.Athena.sendNoOp = function() {
    Nevow.Athena.debug('Sending no-op');
    var reqD = Nevow.Athena.prepareRemoteAction('noop');
    Nevow.Athena.debug('Prepared remote action');
    reqD.addCallback(function(req) {
        Nevow.Athena.debug('Got request');
        var reqD2 = MochiKit.Async.sendXMLHttpRequest(req, Nevow.Athena.preparePostContent([], {}));
        reqD2.addBoth(Nevow.Athena.XMLHttpRequestFinished);
        Nevow.Athena.debug('Sent request');
        reqD2.addCallback(function(ign) {
            Nevow.Athena.debug('reqD2 succeeded');
            return Nevow.Athena.XMLHttpRequestReady(req);
        });
        reqD2.addErrback(function(err) {
            Nevow.Athena.debug('reqD2 failed');
            return Nevow.Athena.XMLHttpRequestFail(err);
        });
        Nevow.Athena.debug('Added callback and errback');
    });
};

Nevow.Athena._callRemote = function(methodName, args) {
    var resultDeferred = new MochiKit.Async.Deferred();
    var reqD = Nevow.Athena.prepareRemoteAction('call');
    var requestId = 'c2s' + Nevow.Athena.remoteCallCount;

    var actionArguments = Nevow.Athena.preparePostContent(MochiKit.Base.extend([methodName], args), {});

    Nevow.Athena.remoteCallCount++;
    Nevow.Athena.remoteCalls[requestId] = resultDeferred;

    reqD.addCallback(function(req) {
        req.setRequestHeader('Request-Id', requestId);

        var reqD2 = MochiKit.Async.sendXMLHttpRequest(req, actionArguments);
        reqD2.addBoth(Nevow.Athena.XMLHttpRequestFinished);
        reqD2.addCallback(Nevow.Athena.XMLHttpRequestReady);
        return reqD2
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
        var s = namespaceIdentifier + ':' + localName;
        if (node.hasAttribute(r)) {
            return node.getAttribute(r);
        } else if (node.hasAttribute(s)) {
            return node.getAttribute(s);
        }
    }
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
    var athenaClass = Nevow.Athena.getAttribute(n, Nevow.Athena.XMLNS_URI, 'athena', 'class');
    if (athenaClass != null) {
        return Divmod.namedAny(athenaClass);
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

Nevow.Athena.RemoteReference = Divmod.Class.subclass();
Nevow.Athena.RemoteReference.prototype.__init__ = function(objectID) {
    Nevow.Athena.debug("Creating a RemoteReference with objectID " + objectID);
    this.objectID = objectID;
};

Nevow.Athena.RemoteReference.prototype.callRemote = function(methodName /*, ... */) {
    var args = [this.objectID];
    for (var idx = 1; idx < arguments.length; idx++) {
        args.push(arguments[idx]);
    }
    return Nevow.Athena._callRemote(methodName, args);
};

Nevow.Athena.Widget = Nevow.Athena.RemoteReference.subclass();
Nevow.Athena.Widget.prototype.__init__ = function(widgetNode) {
    this.node = widgetNode;
    Nevow.Athena.Widget.upcall(this, "__init__", Nevow.Athena.athenaIDFromNode(widgetNode));
};

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
        Nevow.Athena.debug("Creating new widget from class " + this + " for node " + widgetId);
        Nevow.Athena.Widget._athenaWidgets[widgetId] = new this(widgetNode);
    } else {
        Nevow.Athena.debug("Returning existing widget for node " + widgetId);
    }
    return Nevow.Athena.Widget._athenaWidgets[widgetId];
};

Nevow.Athena.DOMWalk = function(parent, test, memo) {
    if (memo == undefined) {
        memo = [];
    }
    /* alert(parent); */
    if ((parent == undefined) ||
        (parent.childNodes == undefined)) {
        return;
    }
    var child;
    var len = parent.childNodes.length;
    for (var i = 0; i < len; i++) {
        child = parent.childNodes[i];
        if (test(child)) {
            Nevow.Athena.debug("Pushing " + child);
            memo.push(child);
        }
        Nevow.Athena.DOMWalk(child, test, memo);
    }
    return memo;
};

Nevow.Athena.NodesByAttribute = function(root, attrName, attrValue) {
    var result = Nevow.Athena.DOMWalk(root,
                        function(child) {
                            return ((child.getAttribute != undefined) &&
                                    (child.getAttribute(attrName) == attrValue));
                        });
    Nevow.Athena.debug("NodesByAttribute found: " + result);
    return result;
};

Nevow.Athena.NodeByAttribute = function(root, attrName, attrValue) {
    var nodes = Nevow.Athena.NodesByAttribute(root, attrName, attrValue);
    Nevow.Athena.debug("NodeByAttribute found: " + nodes);
    if (nodes.length > 1) {
        throw new Error("Found too many " + attrValue + " " + n);
    } else if (nodes.length < 1) {
        throw new Error("Failed to discover node with class value " +
                        attrValue + " beneath " + root +
                        " (programmer error).");

    } else {
        Nevow.Athena.debug("NodeByAttribute - before nodes[0]");
        var result = nodes[0];
        Nevow.Athena.debug("NodeByAttribute - after nodes[0]");
        return result;
    }

}

Nevow.Athena.Widget.fromAthenaID = function(widgetId) {
    /* scan the whole document for a particular widgetId */
    var nodes = Nevow.Athena.DOMWalk(document.documentElement,
                                 function(nodeToTest) {
                                     return (Nevow.Athena.athenaIDFromNode(nodeToTest) == widgetId);
                                 });
    if (nodes.length != 1) {
        throw new Error(nodes.length + " nodes with athena id " + widgetId);
    };

    Nevow.Athena.debug("Got some nodes: " + nodes);
    n = nodes[0];
    Nevow.Athena.debug("Returning this.get(" + n + ");");
    return this.get(n);
};

Nevow.Athena.refByDOM = function() {
    /* This API is deprecated.  Use Nevow.Athena.Widget.get()
     */
    return Nevow.Athena.Widget.get.apply(Nevow.Athena.Widget, arguments);
};


/*
 * Walk the document.  Find things with a athena:class attribute
 * and instantiate them.
 */
Nevow.Athena.Widget._instantiateAll = function() {
    var tw = document.createTreeWalker(document,
                                       NodeFilter.SHOW_ELEMENT,
                                       function(n) {
                                           var cls = Nevow.Athena.athenaClassFromNode(n);
                                           if (cls) {
                                               var inst = cls.get(n);
                                               if (inst.loaded != undefined) {
                                                   inst.loaded();
                                               }
                                           }
                                           return NodeFilter.FILTER_ACCEPT;
                                       },
                                       false);
    var n;
    while ((n = tw.nextNode()) != null) {};
};

Nevow.Athena.callByAthenaID = function(athenaID, methodName, varargs) {
    var widget = Nevow.Athena.Widget.fromAthenaID(athenaID);
    Nevow.Athena.debug("Got a widget: " + widget);
    Nevow.Athena.debug("Calling " + methodName + " on it with " + varargs);
    return widget[methodName].apply(widget, varargs);
};

Nevow.Athena.server = new Nevow.Athena.RemoteReference(0);
var server = Nevow.Athena.server;

MochiKit.DOM.addLoadEvent(function() {
    Nevow.Athena.sendNoOp();
    Nevow.Athena.Widget._instantiateAll();
});
