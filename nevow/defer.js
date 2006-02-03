// -*- test-case-name: nevow.test.test_javascript -*-

// import Divmod

Divmod.Defer = {};

Divmod.Defer.AlreadyCalledError = Divmod.Class.subclass("Divmod.Defer.AlreadyCalledError");

Divmod.Defer.Failure = Divmod.Class.subclass("Divmod.Defer.Failure");
Divmod.Defer.Failure.methods(
    function __init__(self, error) {
        self.error = error;
    });

Divmod.Defer.Deferred = Divmod.Class.subclass("Divmod.Defer.Deferred");

Divmod.Defer.Deferred.methods(
    function __init__(self) {
        self._callbacks = [];
        self._called = false;
        self._pauseLevel = 0;
    },
    function addCallbacks(self, callback, errback,
                          callbackArgs, errbackArgs) {
        if (!callbackArgs) {
            callbackArgs = [];
        }
        if (!errbackArgs) {
            errbackArgs = [];
        }
        self._callbacks.push([callback, errback, callbackArgs, errbackArgs]);
        if (self._called) {
            self._runCallbacks();
        }
    },
    function addCallback(self, callback) {
        var callbackArgs = [];
        for (var i = 2; i < arguments.length; ++i) {
            callbackArgs.push(arguments[i]);
        }
        self.addCallbacks(callback, null, callbackArgs, null);
    },
    function addErrback(self, errback) {
        var errbackArgs = [];
        for (var i = 2; i < arguments.length; ++i) {
            errbackArgs.push(arguments[i]);
        }
        self.addCallbacks(null, errback, null, errbackArgs);
    },
    function addBoth(self, callback) {
        var callbackArgs = [];
        for (var i = 2; i < arguments.length; ++i) {
            callbackArgs.push(arguments[i]);
        }
        self.addCallbacks(callback, callback, callbackArgs, callbackArgs);
    },
    function _pause(self) {
        self._pauseLevel++;
    },
    function _unpause(self) {
        self._pauseLevel--;
        if (self._pauseLevel) {
            return;
        }
        if (!self._called) {
            return;
        }
        self._runCallbacks();
    },
    function _isFailure(self, obj) {
        return (obj instanceof Divmod.Defer.Failure);
    },
    function _isDeferred(self, obj) {
        return (obj instanceof Divmod.Defer.Deferred);
    },
    function _continue(self, result) {
        self._result = result;
        self._unpause();
    },
    function _runCallbacks(self) {
        if (!self._pauseLevel) {
            var cb = self._callbacks;
            self._callbacks = [];
            while (cb.length) {
                var item = cb.shift();
                if (self._isFailure(self._result)) {
                    var callback = item[1];
                    var args = item[3];
                } else {
                    var callback = item[0];
                    var args = item[2];
                }

                if (callback == null) {
                    continue;
                }

                args.unshift(self._result);
                try {
                    self._result = callback.apply(null, args);
                    if (self._isDeferred(self._result)) {
                        self._callbacks = cb;
                        self._pause();
                        self._result.addBoth(function (r) {
                                self._continue(r);
                            });
                        break;
                    }
                } catch (e) {
                    self._result = new Divmod.Defer.Failure(e);
                }
            }
        }

        if (self._isFailure(self._result)) {
            // This might be spurious
            Divmod.err(self._result);
        }
    },
    function _startRunCallbacks(self, result) {
        if (self._called) {
            throw new Divmod.Defer.AlreadyCalledError();
        }
        self._called = true;
        self._result = result;
        self._runCallbacks();
    },
    function callback(self, result) {
        self._startRunCallbacks(result);
    },
    function errback(self, err) {
        if (!self._isFailure(err)) {
            err = new Divmod.Defer.Failure(err);
        }
        self._startRunCallbacks(err);
    });

Divmod.Defer.succeed = function(result) {
    var d = new Divmod.Defer.Deferred();
    d.callback(result);
    return d;
};

Divmod.Defer.fail = function(err) {
    var d = new Divmod.Defer.Deferred();
    d.errback(err);
    return d;
};
