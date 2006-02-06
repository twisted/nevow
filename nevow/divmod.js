
var Divmod = {};


Divmod.baseURL = function() {
    // Use "cached" value if it exists
    if (Divmod._baseURL != undefined) {
        return Divmod._baseURL;
    }
    var baseURL = Divmod._location;
    if (baseURL == undefined) {
        window.location.toString();
        var queryParamIndex = baseURL.indexOf('?');

        if (queryParamIndex != -1) {
            baseURL = baseURL.substring(0, queryParamIndex);
        }
    }

    if (baseURL.charAt(baseURL.length - 1) != '/') {
        baseURL += '/';
    }

    baseURL += Nevow.Athena.livepageId + '/';

    // "Cache" and return
    Divmod._baseURL = baseURL;
    return Divmod._baseURL;
};


Divmod.importURL = function(moduleName) {
    return Divmod.baseURL() + 'jsmodule/' + moduleName;
};


Divmod._global = this;


Divmod.namedAny = function(name) {
    var namedParts = name.split('.');
    var obj = Divmod._global;
    for (var p in namedParts) {
        obj = obj[namedParts[p]];
        if (obj == undefined) {
            Divmod.debug('widget', 'Failed in namedAny for ' + name + 'at ' + namedParts[p]);
            break;
        }
    }
    return obj;
};


Divmod.vars = function(obj) {
    var L = [];
    for (var i in obj) {
        L.push([i, obj[i]]);
    }
    return L;
};


Divmod.dir = function(obj) {
    var L = [];
    for (var i in obj) {
        L.push(i);
    }
    return L;
};


Divmod._PROTOTYPE_ONLY = {};


Divmod.Class = function(asPrototype) {
    if (asPrototype !== Divmod._PROTOTYPE_ONLY) {
        this.__init__.apply(this, arguments);
    }
};


Divmod.__classDebugCounter__ = 0;


Divmod.Class.subclass = function(/* optional */ className) {
    var superClass = this;
    var subClass = function() {
        return Divmod.Class.apply(this, arguments)
    };
    subClass.prototype = new superClass(Divmod._PROTOTYPE_ONLY);
    subClass.subclass = Divmod.Class.subclass;

    /* Copy class methods and attributes, so that you can do
     * polymorphism on class methods (useful for things like
     * Nevow.Athena.Widget.get in widgets.js).
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

    subClass.method = function(methodName, methodFunction) {
        if (methodFunction != undefined) {
            Divmod.debug('deprecation', 'method() just takes a function now (called with name = ' + methodName +').');
        } else {
            methodFunction = methodName;
            methodName = methodFunction.name;
        }

        if (methodName == undefined) {
            /* Sorry (IE).
             */
            var methodSource = methodFunction.toString();
            methodName = methodSource.slice(methodSource.indexOf(' ') + 1, methodSource.indexOf('('));
        }

        subClass.prototype[methodName] = function() {
            var args = [this];
            for (var i = 0; i < arguments.length; ++i) {
                args.push(arguments[i]);
            }
            return methodFunction.apply(this, args);
        };
    };

    subClass.methods = function() {
        for (var i = 0; i < arguments.length; ++i) {
            subClass.method(arguments[i]);
        }
    };

    /**
       Not quite sure what to do with this...
    **/
    Divmod.__classDebugCounter__ += 1;
    subClass.__classDebugCounter__ = Divmod.__classDebugCounter__;
    subClass.toString = function() {
        if (className == undefined) {
            return '<Class #' + subClass.__classDebugCounter__ + '>';
        } else {
            return '<Class ' + className + '>';
        }
    };
    subClass.prototype.toString = function() {
        if (className == undefined) {
            return '<"Instance" of #' + subClass.__classDebugCounter__ + '>';
        } else {
            return '<"Instance" of ' + className + '>';
        }
    };
    return subClass;
};


Divmod.Class.prototype.__init__ = function() {
    /* throw new Error("If you ever hit this code path something has gone horribly wrong");
     */
};


Divmod.Module = Divmod.Class.subclass('Divmod.Module');
Divmod.Module.method(
    function __init__(self, name) {
        self.name = name;
    });


Divmod.Logger = Divmod.Class.subclass('Divmod.Logger');
Divmod.Logger.methods(
    function __init__(self) {
        self.observers = [];
    },

    function addObserver(self, observer) {
        self.observers.push(observer);
        return function() {
            self._removeObserver(observer);
        };
    },

    function _removeObserver(self, observer) {
        for (var i = 0; i < self.observers.length; ++i) {
            if (observer === self.observers[i]) {
                self.observers.splice(i, 1);
                return;
            }
        }
    },

    function _emit(self, event) {
        var errors = [];
        var obs = self.observers.slice();
        for (var i = 0; i < obs.length; ++i) {
            try {
                obs[i](event);
            } catch (e) {
                self._removeObserver(obs[i]);
                errors.push([e, "Log observer caused error, removing."]);
            }
        }
        return errors;
    },

    function emit(self, event) {
        var errors = self._emit(event);
        while (errors.length) {
            var moreErrors = [];
            for (var i = 0; i < errors.length; ++i) {
                var e = self._emit({'isError': true, 'error': errors[i][0], 'message': errors[i][1]});
                for (var j = 0; j < e.length; ++j) {
                    moreErrors.push(e[j]);
                }
            }
            errors = moreErrors;
        }
    },

    function err(self, error, /* optional */ message) {
        var event = {'isError': true, 'error': error};
        if (message != undefined) {
            event['message'] = message;
        } else {
            event['message'] = error.message;
        }
        self.emit(event);
    },

    function msg(self, message) {
        var event = {'isError': false, 'message': message};
        self.emit(event);
    });


Divmod.logger = new Divmod.Logger();
Divmod.msg = function() { return Divmod.logger.msg.apply(Divmod.logger, arguments); };
Divmod.err = function() { return Divmod.logger.err.apply(Divmod.logger, arguments); };
Divmod.debug = function(kind, msg) {
    Divmod.logger.emit({'isError': false, 'message': msg, 'debug': true, 'channel': kind});
};
Divmod.log = Divmod.debug;
