
var Divmod = {};
Divmod.debugging = false;

Divmod.baseURL = function() {
    // Use "cached" value if it exists
    if (Divmod._baseURL != undefined) {
        return Divmod._baseURL;
    }
    var baseURL = Divmod._location;
    if (baseURL == undefined) {
        baseURL = window.location.toString();
    }

    var queryParamIndex = baseURL.indexOf('?');

    if (queryParamIndex != -1) {
        baseURL = baseURL.substring(0, queryParamIndex);
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
    for (var i = 0; i < namedParts.length; ++i) {
        obj = obj[namedParts[i]];
        if (obj == undefined) {
            Divmod.debug('widget', 'Failed in namedAny for ' + name + 'at ' + namedParts[i]);
            break;
        }
    }
    return obj;
};


Divmod.max = function(a, b) {
    if (a >= b) {
        return a;
    } else {
        return b;
    }
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


Divmod.__classDebugCounter__ = 0;

Divmod._CONSTRUCTOR = {};

Divmod.Class = function() {};

Divmod.Class.subclass = function(/* optional */ className) {


    if (className == undefined) {
        Divmod.__classDebugCounter__ += 1;
        className = '#' + Divmod.__classDebugCounter__;
    }

    /*
     * subclass() must always be called on Divmod.Class or an object returned
     * from subclass() - so in this execution context, C{this} is the "class"
     * object.
     */
    var superClass = this;

    /*
     * Create a function which basically serves the purpose of type.__call__ in Python:
     */
    var subClass = function(asConstructor) {
        var self;
        if (this instanceof subClass) {
            /*
             * If the instance is being created using C{new Class(args)},
             * C{this} will already be an object with the appropriate
             * prototype, so we can skip creating one ourself.
             */
            self = this;
        } else {
            /*
             * If the instance is being created using just C{Class(args)} (or,
             * similarly, C{Class.apply(null, args)} or C{Class.call(null,
             * args)}), then C{this} is actually some random object - maybe the
             * global execution context object, maybe the window, maybe a
             * pseudo-namespace object (ie, C{Divmod}), maybe null.  Whichever,
             * invoke C{new subClass(Divmod._CONSTRUCTOR)} to create an object
             * with the right prototype without invoking C{__init__}.
             */
            self = new subClass(Divmod._CONSTRUCTOR);
        }
        self.__class__ = subClass;
        /*
         * Once we have an instance, if C{asConstructor} is not the magic internal
         * object C{Divmod._CONSTRUCTOR}, pass all our arguments on to the
         * instance's C{__init__}.
         */
        if (asConstructor !== Divmod._CONSTRUCTOR) {
            self.__init__.apply(self, arguments);
        }

        /*
         * We've accomplished... Something.  Either we made a blank, boring
         * instance of a particular class, or we actually initialized an
         * instance of something (possibly something that we had to create).
         * Whatever it is, give it back to our caller to enjoy.
         */
        return self;
    };

    /*
     * This is how you spell inheritance in JavaScript.
     */
    subClass.prototype = new superClass(Divmod._CONSTRUCTOR);

    /*
     * Make the subclass subclassable in the same way.
     */
    subClass.subclass = Divmod.Class.subclass;

    /*
     * Make a minimal amount of information about this class available.
     */
    subClass.__name__ = className;

    /*
     * Copy class methods and attributes, so that you can do
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

    subClass.toString = function() {
        return '<Class ' + className + '>';
    };
    subClass.prototype.toString = function() {
        if (this.__repr__) {
            return this.__repr__();
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

Divmod.Error = Divmod.Class.subclass("Divmod.Error");
Divmod.Error.methods(
    function __init__(self, message, stack /* = null */) {
        if (stack == undefined) {
            stack = null;
        }

        self.message = message;
        self.stack = stack;

        self.args = [];
        for (var i = 3; i < arguments.length; ++i) {
            self.args.push(arguments[i]);
        }
    },

    function __repr__(self) {
        return '<' + self.__class__.__name__ + ': ' + self.args.toString() + '>';
    });


Divmod.StandardError = Divmod.Error.subclass("Divmod.StandardError");
Divmod.StandardError.methods(
    function __init__(self, err) {
        Divmod.StandardError.upcall(self, '__init__', err.message, err.stack);
    })

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
