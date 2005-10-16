function nevow_baseURL() {

    // Use "cached" value if it exists
    if (typeof(_nevow_baseURL) != "undefined") {
        return _nevow_baseURL;
    }

    var baseURL = this.location.toString();
    var queryParamIndex = baseURL.indexOf('?');

    if (queryParamIndex != -1) {
        baseURL = baseURL.substring(0, queryParamIndex);
    }

    if (baseURL.charAt(baseURL.length - 1) != '/') {
        baseURL += '/';
    }

    baseURL += 'transport';

    // "Cache" and return
    _nevow_baseURL = baseURL;
    return _nevow_baseURL;
}

var nevow_debugging = true;
function nevow_debug(msg) {
    if (nevow_debugging) {
        MochiKit.Logging.logDebug(msg);
    }
}

function nevow_constructActionURL(action, arguments) {
    var argumentQueryArgument = MochiKit.Base.serializeJSON(arguments);
    return (nevow_baseURL()
            + '?action='
            + encodeURIComponent(action)
            + '&args='
            + encodeURIComponent(argumentQueryArgument));
}

var nevow_failureCount = 0;
var nevow_remoteCallCount = 0;
var nevow_remoteCalls = {};
var nevow_outstandingTransports = 0;
var nevow_responseDispatchTable = new Object();

nevow_responseDispatchTable['text/xml'] = function(d, content) {
    d.callback(TEH_XML_PARSER(content));
}

nevow_responseDispatchTable['text/json'] = function(d, content) {
    d.callback(content);
}

function nevow_XMLHttpRequestFinished(passthrough) {
    nevow_outstandingTransports--;
    return passthrough;
}

function nevow_XMLHttpRequestReady(req) {
    nevow_debug('A request is completed: ' + req.responseText);

    /* The response's content is a JSON-encoded 4-array of [Response-Id,
     * Request-Id, Content-Type, Content].  If this is a response to a
     * previous request, responseId will not be null.  If this is a
     * server-initiated request, requestId will not be null.
     */

    if (req.responseText == '') {
        /* Server timed out the transport, just re-request */
        nevow_debug('Empty server message, reconnecting');
        if (nevow_outstandingTransports == 0) {
            nevow_debug('No outstanding transports, sending no-op');
            nevow_sendNoOp();
        }
        return;
    }

    nevow_debug('evaluating json in responseText');
    var responseParts = MochiKit.Base.evalJSON(req.responseText);
    nevow_debug('evaluated it');

    nevow_failureCount = 0;

    var responseId = responseParts[0];
    var requestId = responseParts[1];

    if (requestId != null) {
        nevow_debug('Got a response to a request');

        var contentType = responseParts[2];
        var contentBody = responseParts[3];

        var d = nevow_remoteCalls[requestId];
        var handler = nevow_responseDispatchTable[contentType];
        delete nevow_remoteCalls[requestId];

        if (handler != null) {
            handler(d, contentBody);
        } else {
            nevow_debug("Unknown content-type: " + contentType);
            d.errback(new Error("Unhandled content type: " + contentType));
        }

    } else if (responseId != null) {
        nevow_debug('Server initiated request');

        var contentBody = responseParts[2];

        var objectId = contentBody[0];
        var methodName = contentBody[1];
        var methodArgs = contentBody[2];

        /*
        var resultD = nevow_localObjectTable[objectId].dispatch(methodName, methodArgs);
        resultD.addCallbacks(nevow_respondToRequest
        */

        nevow_debug('Invoking ' + new String(methodName) + ' with arguments ' + new String(methodArgs));
        var result = eval(methodName).apply(null, methodArgs);
        nevow_debug('Invoked it');

        var isDeferred = false;

        if (result == undefined) {
            nevow_debug('it was undefined');
            result = null;
        } else {
            /* if it quacks like a duck ...
               this sucks!!!  */
            isDeferred = (typeof(result.addCallback) != 'undefined' &&
                          typeof(result.addErrback) != 'undefined');
        }
        nevow_debug('Is it a deferred? ' + new String(isDeferred));

        if (isDeferred) {
            nevow_debug('It is a deferred, adding a callback');
            result.addCallback(function(result) {
                nevow_respondToRemote(responseId, result);
            });
        } else {
            nevow_debug('Responding synchronously to remote request with ID ' + new String(responseId));
            nevow_respondToRemote(responseId, result);
        }

    }

    /* Client code has had a chance to run now, in response to
     * receiving the result.  If it issued a new request, we've got an
     * output channel already.  If it didn't, though, we might not
     * have one.  In that case, issue a no-op to the server so it can
     * send us things if it needs to. */
    if (nevow_outstandingTransports == 0) {
        nevow_sendNoOp();
    }
}

function nevow_XMLHttpRequestFail(err) {
    nevow_debug('A request failed!');

    nevow_failureCount++;

    if (nevow_failureCount >= 3) {
        nevow_debug('There are too many failures!');
        var calls = nevow_remoteCalls;
        nevow_remoteCalls = {};
        for (var k in calls) {
            calls[k].errback(new Error("Connection lost"));
        }
        return;
    } else {
        nevow_debug('There are not too many failures.');
    }

    if (nevow_outstandingTransports == 0) {
        nevow_sendNoOp();
    }
}

function nevow_prepareRemoteAction(actionType, args) {

    var url = nevow_constructActionURL(actionType, args);
    var req = MochiKit.Async.getXMLHttpRequest();

    try {
        req.open('GET', url, true);
        yes = 1;
    } catch (err) {
        return resultD = MochiKit.Async.fail(err);
    }

    nevow_outstandingTransports++;

    nevow_debug("Setting livepage id " + new String(nevow_livepageId));
    req.setRequestHeader('Livepage-Id', nevow_livepageId);
    return resultD = MochiKit.Async.succeed(req);
}

function nevow_respondToRemote(requestID, args) {
    var reqD = nevow_prepareRemoteAction('respond', [args]);
    reqD.addCallback(function(req) {
        req.setRequestHeader('Response-Id', requestID);
        var reqD2 = MochiKit.Async.sendXMLHttpRequest(req);
        reqD2.addBoth(nevow_XMLHttpRequestFinished);
        reqD2.addCallback(nevow_XMLHttpRequestReady);
        reqD2.addErrback(nevow_XMLHttpRequestFail);
    });
}

function nevow_sendNoOp() {
    nevow_debug('Sending no-op');
    var reqD = nevow_prepareRemoteAction('noop', []);
    nevow_debug('Prepared remote action');
    reqD.addCallback(function(req) {
        nevow_debug('Got request');
        var reqD2 = MochiKit.Async.sendXMLHttpRequest(req);
        reqD2.addBoth(nevow_XMLHttpRequestFinished);
        nevow_debug('Sent request');
        reqD2.addCallback(function(ign) {
            nevow_debug('reqD2 succeeded');
            return nevow_XMLHttpRequestReady(req);
        });
        reqD2.addErrback(function(err) {
            nevow_debug('reqD2 failed');
            return nevow_XMLHttpRequestFail(err);
        });
        nevow_debug('Added callback and errback');
    });
}

function nevow_callRemote(methodName, args) {
    var resultDeferred = new MochiKit.Async.Deferred();
    var reqD = nevow_prepareRemoteAction('call', MochiKit.Base.extend([methodName], args));
    var requestId = 'c2s' + nevow_remoteCallCount;

    nevow_remoteCallCount++;
    nevow_remoteCalls[requestId] = resultDeferred;

    reqD.addCallback(function(req) {
        req.setRequestHeader('Request-Id', requestId);

        var reqD2 = MochiKit.Async.sendXMLHttpRequest(req);
        reqD2.addBoth(nevow_XMLHttpRequestFinished);
        reqD2.addCallback(nevow_XMLHttpRequestReady);
        return reqD2
    });

    reqD.addErrback(nevow_XMLHttpRequestFail);

    return resultDeferred;
}

var server = {
    /* Backwards compatibility API - you really want callRemote */
    handle: function(handlerName /*, ... */ ) {
        var args = [handlerName];
        for (var idx = 1; idx < arguments.length; idx++) {
            args.push(arguments[idx]);
        }
        nevow_callRemote('handle', args).addCallback(eval);
    },

    /* Invoke a method on the server.  Return a Deferred that fires
     * when the method completes. */
    callRemote: function(methodName /*, ... */) {
        var args = [];
        for (var idx = 1; idx < arguments.length; idx++) {
            args.push(arguments[idx]);
        }
        return nevow_callRemote(methodName, args);
    }
};
