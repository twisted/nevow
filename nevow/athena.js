if (typeof(Nevow) == 'undefined') {
    Nevow = {};
}

if (typeof(Nevow.Athena) == 'undefined') {
    Nevow.Athena = {};
}

Nevow.Athena.NAME = 'Nevow.Athena';
Nevow.Athena.__repr__ = function () {
    return '[' + this.NAME + ']';
};

Nevow.Athena.toString = function () {
    return this.__repr__();
};

Nevow.Athena.clone = function (obj) {
    var me = arguments.callee;
    if (arguments.length == 1) {
        me.prototype = obj;
        return new me();
    }
};

Nevow.Athena.baseURL = function () {

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

Nevow.Athena.debugging = true;
Nevow.Athena.debug = function (msg) {
    if (Nevow.Athena.debugging) {
        MochiKit.Logging.logDebug(msg);
    }
};

Nevow.Athena.constructActionURL = function (action, args) {
    var argumentQueryArgument = MochiKit.Base.serializeJSON(args);

    return (Nevow.Athena.baseURL()
            + '?action='
            + encodeURIComponent(action)
            + '&args='
            + encodeURIComponent(argumentQueryArgument));
};

Nevow.Athena.failureCount = 0;
Nevow.Athena.remoteCallCount = 0;
Nevow.Athena.remoteCalls = {};
Nevow.Athena.outstandingTransports = 0;
Nevow.Athena.responseDispatchTable = new Object();

Nevow.Athena.responseDispatchTable['text/xml'] = function (d, content) {
    d.callback(TEH_XML_PARSER(content));
};

Nevow.Athena.responseDispatchTable['text/json'] = function (d, content) {
    d.callback(content);
};

Nevow.Athena.XMLHttpRequestFinished = function (passthrough) {
    Nevow.Athena.outstandingTransports--;
    return passthrough;
};

Nevow.Athena.XMLHttpRequestReady = function (req) {
    Nevow.Athena.debug('A request is completed: ' + req.responseText);

    /* The response's content is a JSON-encoded 4-array of [Response-Id,
     * Request-Id, Content-Type, Content].  If this is a response to a
     * previous request, responseId will not be null.  If this is a
     * server-initiated request, requestId will not be null.
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
        var result = eval(methodName).apply(null, methodArgs);
        Nevow.Athena.debug('Invoked it');

        var isDeferred = false;

        if (result == undefined) {
            Nevow.Athena.debug('it was undefined');
            result = null;
        } else {
            /* if it quacks like a duck ...
               this sucks!!!  */
            isDeferred = (typeof(result.addCallback) != 'undefined' &&
                          typeof(result.addErrback) != 'undefined');
        }
        Nevow.Athena.debug('Is it a deferred? ' + new String(isDeferred));

        if (isDeferred) {
            Nevow.Athena.debug('It is a deferred, adding a callback');
            result.addCallback(function(result) {
                Nevow.Athena.respondToRemote(responseId, result);
            });
        } else {
            Nevow.Athena.debug('Responding synchronously to remote request with ID ' + new String(responseId));
            Nevow.Athena.respondToRemote(responseId, result);
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

Nevow.Athena.XMLHttpRequestFail = function (err) {
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

Nevow.Athena.prepareRemoteAction = function (actionType, args) {
    var url = Nevow.Athena.constructActionURL(actionType, args);
    var req = MochiKit.Async.getXMLHttpRequest();

    try {
        req.open('GET', url, true);
        yes = 1;
    } catch (err) {
        return resultD = MochiKit.Async.fail(err);
    }

    Nevow.Athena.outstandingTransports++;

    Nevow.Athena.debug("Setting livepage id " + new String(Nevow.Athena.livepageId));
    req.setRequestHeader('Livepage-Id', Nevow.Athena.livepageId);
    return resultD = MochiKit.Async.succeed(req);
};

Nevow.Athena.respondToRemote = function (requestID, args) {
    var reqD = Nevow.Athena.prepareRemoteAction('respond', [args]);
    reqD.addCallback(function(req) {
        req.setRequestHeader('Response-Id', requestID);
        var reqD2 = MochiKit.Async.sendXMLHttpRequest(req);
        reqD2.addBoth(Nevow.Athena.XMLHttpRequestFinished);
        reqD2.addCallback(Nevow.Athena.XMLHttpRequestReady);
        reqD2.addErrback(Nevow.Athena.XMLHttpRequestFail);
    });
};

Nevow.Athena.sendNoOp = function () {
    Nevow.Athena.debug('Sending no-op');
    var reqD = Nevow.Athena.prepareRemoteAction('noop', []);
    Nevow.Athena.debug('Prepared remote action');
    reqD.addCallback(function(req) {
        Nevow.Athena.debug('Got request');
        var reqD2 = MochiKit.Async.sendXMLHttpRequest(req);
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

Nevow.Athena._callRemote = function (methodName, args) {
    var resultDeferred = new MochiKit.Async.Deferred();
    var reqD = Nevow.Athena.prepareRemoteAction('call', MochiKit.Base.extend([methodName], args));
    var requestId = 'c2s' + Nevow.Athena.remoteCallCount;

    Nevow.Athena.remoteCallCount++;
    Nevow.Athena.remoteCalls[requestId] = resultDeferred;

    reqD.addCallback(function(req) {
        req.setRequestHeader('Request-Id', requestId);

        var reqD2 = MochiKit.Async.sendXMLHttpRequest(req);
        reqD2.addBoth(Nevow.Athena.XMLHttpRequestFinished);
        reqD2.addCallback(Nevow.Athena.XMLHttpRequestReady);
        return reqD2
    });

    reqD.addErrback(Nevow.Athena.XMLHttpRequestFail);

    return resultDeferred;
};

Nevow.Athena.RemoteReference = function(objectID) {
    this.objectID = objectID;
};

Nevow.Athena.RemoteReference.prototype = {
    callRemote: function(methodName /*, ... */) {
        var args = [this.objectID];
        for (var idx = 1; idx < arguments.length; idx++) {
            args.push(arguments[idx]);
        }
        return Nevow.Athena._callRemote(methodName, args);
    }
};

Nevow.Athena.refByDOM = function(node) {
    var pfx = "athena_";
    for (var n = node; n != null; n = n.parentNode) {
	if (n.hasAttribute('id')) {
	    var nID = n.getAttribute('id');
	    if (nID.slice(0, pfx.length) == pfx) {
		var refID = nID.slice(pfx.length, nID.length);
		return new Nevow.Athena.RemoteReference(parseInt(refID));
	    }
	}
    }
    throw new Error("refByDOM passed node with no containing Athena Ref ID");
}

Nevow.Athena.server = new Nevow.Athena.RemoteReference(0);
var server = Nevow.Athena.server;
