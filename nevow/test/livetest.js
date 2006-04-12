
// import Nevow.Athena

Nevow.Athena.Tests.WidgetInitializerArguments = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.WidgetInitializerArguments');
Nevow.Athena.Tests.WidgetInitializerArguments.methods(
    function __init__(self, node) {
        Nevow.Athena.Tests.WidgetInitializerArguments.upcall(self, '__init__', node);
        self.args = [];
        for (var i = 2; i < arguments.length; ++i) {
            self.args.push(arguments[i]);
        }
    },

    function run(self) {
        return self.callRemote('test', self.args);
    });

Nevow.Athena.Tests.ClientToServerArgumentSerialization = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.ClientToServerArgumentSerialization');
Nevow.Athena.Tests.ClientToServerArgumentSerialization.methods(
    function run(self) {
        var L = [1, 1.5, 'Hello world'];
        var O = {'hello world': 'object value'};
        return self.callRemote('test', 1, 1.5, 'Hello world', L, O);
    });

Nevow.Athena.Tests.ClientToServerResultSerialization = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.ClientToServerResultSerialization');
Nevow.Athena.Tests.ClientToServerResultSerialization.methods(
    function run(self) {
        var L = [1, 1.5, 'Hello world'];
        var O = {'hello world': 'object value'};
        var d = self.callRemote('test', 1, 1.5, 'Hello world', L, O);
        d.addCallback(function(result) {
            self.assertEquals(result[0], 1);
            self.assertEquals(result[1], 1.5);
            self.assertEquals(result[2], 'Hello world');
            self.assertEquals(result[3][0], 1);
            self.assertEquals(result[3][1], 1.5);
            self.assertEquals(result[3][2], 'Hello world');
            self.assertEquals(result[4]['hello world'], 'object value');
        });
        return d;
    });

Nevow.Athena.Tests.ExceptionFromServer = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.ExceptionFromServer');
Nevow.Athena.Tests.ExceptionFromServer.methods(
    function run(self) {
        var d;
        var s = 'This exception should appear on the client.';
        d = self.callRemote('testSync', s);
        d.addCallbacks(
            function(result) {
                self.fail('Erroneously received a result: ' + result);
            },
            function(f) {
                var idx = f.error.message.indexOf(s);
                if (idx == -1) {
                    self.fail('Did not find expected message in error message: ' + f.error.message);
                }
            });
        return d;
    });

Nevow.Athena.Tests.JSONRoundtrip = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.JSONRoundtrip');
Nevow.Athena.Tests.JSONRoundtrip.methods(
    function run(self) {
        return self.callRemote('test');
    },

    function identity(self, value) {
        return value;
    });

Nevow.Athena.Tests.AsyncExceptionFromServer = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.AsyncExceptionFromServer');
Nevow.Athena.Tests.AsyncExceptionFromServer.methods(
    function run(self) {
        var d;
        var s = 'This exception should appear on the client.';
        d = self.callRemote('testAsync', s);
        d.addCallbacks(
            function(result) {
                self.fail('Erroneously received a result: ' + result);
            },
            function(f) {
                var idx = f.error.message.indexOf(s);
                if (idx == -1) {
                    self.fail('Did not find expected message in error message: ' + f.error.message);
                }
            });
        return d;
    });

Nevow.Athena.Tests.ExceptionFromClient = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.ExceptionFromClient');
Nevow.Athena.Tests.ExceptionFromClient.methods(
    function run(self) {
        var d;
        d = self.callRemote('loopbackError');
        d.addCallbacks(
            function (result) {
            },
            function (f) {
                self.fail('Received unexpected exception: ' + f.error.message);
            });
        return d;
    },

    function generateError(self) {
        throw new Error('This is a test exception');
    });

Nevow.Athena.Tests.AsyncExceptionFromClient = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.AsyncExceptionFromClient');
Nevow.Athena.Tests.AsyncExceptionFromClient.methods(
    function run(self) {
        var d;
        d = self.callRemote('loopbackError');
        d.addCallbacks(
            function (result) {
                if (!result) {
                    self.fail('Received incorrect Javascript exception or no traceback.');
                }
            },
            function (f) {
                self.fail('Received unexpected exception: ' + f.error.message);
            });
        return d;
    },

    function generateError(self) {
        return Divmod.Defer.fail(Error('This is a deferred test exception'));
    });

Nevow.Athena.Tests.ServerToClientArgumentSerialization = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.ServerToClientArgumentSerialization');
Nevow.Athena.Tests.ServerToClientArgumentSerialization.methods(
    function run(self) {
        return self.callRemote('test');
    },

    function reverse(self, i, f, s, o) {
        self.assertEquals(i, 1);
        self.assertEquals(f, 1.5);
        self.assertEquals(s, 'hello');
        self.assertEquals(o['world'], 'value');
    });

Nevow.Athena.Tests.ServerToClientResultSerialization = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.ServerToClientResultSerialization');
Nevow.Athena.Tests.ServerToClientResultSerialization.methods(
    function run(self) {
        return self.callRemote('test');
    },

    function reverse(self) {
        return [1, 1.5, 'hello', {'world': 'value'}];
    });

Nevow.Athena.Tests.WidgetInATable = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.WidgetInATable');
Nevow.Athena.Tests.WidgetInATable.methods(
    function run(self) {
        // Nothing to do
    });

Nevow.Athena.Tests.WidgetIsATable = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.WidgetIsATable');
Nevow.Athena.Tests.WidgetIsATable.methods(
    function run(self) {
        // Nothing to do
    });

Nevow.Athena.Tests.ChildParentRelationshipTest = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.ChildParentRelationshipTest');
Nevow.Athena.Tests.ChildParentRelationshipTest.methods(
    function checkParent(self, proposedParent) {
        self.assertEquals(self.widgetParent, proposedParent);
    },

    function run(self) {
        var deferredList = function(finalDeferred, counter) {
            if (counter == 0) {
                finalDeferred.callback(null);
            }
            var callback = function(ignored) {
                counter -= 1;
                Divmod.log('test', 'One more down, ' + counter + ' to go.');
                if (counter == 0) {
                    finalDeferred.callback(null);
                }
            };
            return callback;
        };

        var result = self.callRemote('getChildCount');

        result.addCallback(function(count) {
            Divmod.log('test', 'Discovered I have ' + count + ' children');
            var d = new Divmod.Defer.Deferred();
            d.addCallback(function() { self.node.style.border = 'thin solid green'; });
            var cb = deferredList(d, count);
            self.assertEquals(self.childWidgets.length, count);
            for (var i = 0; i < self.childWidgets.length; i++) {
                var childWidget = self.childWidgets[i];
                childWidget.checkParent(self);
                childWidget.run().addCallback(cb).addErrback(function(err) { d.errback(err); });
            }
            return d;
        });
        return result;
    });

Nevow.Athena.Tests.AutomaticClass = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.AutomaticClass');
Nevow.Athena.Tests.AutomaticClass.methods(
    function run(self) {
        // Nothing to do here
    });


Nevow.Athena.Tests.ImportBeforeLiteralJavaScript = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.ImportBeforeLiteralJavaScript');
Nevow.Athena.Tests.ImportBeforeLiteralJavaScript.methods(
    function run(self) {
        self.assertEquals(importBeforeLiteralJavaScriptResult, false);
    });

Nevow.Athena.Tests.AthenaHandler = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.AthenaHandler');
Nevow.Athena.Tests.AthenaHandler.methods(
    function run(self) {
        self.handled = false;
        var onsubmit = self.node.getElementsByTagName('button')[0].onclick;
        self.assertEquals(onsubmit(), false);
        self.assertEquals(self.handled, true);
    },

    function handler(self, evt) {
        self.handled = true;
        return false;
    });

Nevow.Athena.Tests.FirstNodeByAttribute = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.FirstNodeByAttribute');
Nevow.Athena.Tests.FirstNodeByAttribute.methods(
    function run(self) {
        var html = '<div xmlns="http://www.w3.org/1999/xhtml" class="foo" />';
        Divmod.Runtime.theRuntime.appendNodeContent(self.node, html);
        var node = self.firstNodeByAttribute("class", "foo");
        self.assertEquals(node.className, "foo");
        self.assertEquals(node.tagName.toLowerCase(), "div");
    });


/**
 * Test that retrieving several LiveFragments from the server using a
 * method call returns something which can be passed to
 * L{Divmod.Runtime.Platform.setNodeContent} to add new widgets to the
 * page.
 */
Nevow.Athena.Tests.DynamicWidgetInstantiation = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.DynamicWidgetInstantiation');
Nevow.Athena.Tests.DynamicWidgetInstantiation.methods(
    function __init__(self, node, childCount) {
        Nevow.Athena.Tests.DynamicWidgetInstantiation.upcall(self, '__init__', node);
        self.expectedChildCount = childCount;
    },

    function run(self) {
        var d = self.callRemote('getWidgets');
        d.addCallback(function(result) {
            self.waiting = Divmod.Defer.Deferred();
            self.waitingCount = self.expectedChildCount;
            Divmod.Runtime.theRuntime.setNodeContent(self.node, result);
        });
        return d;
    },

    function addChildWidget(self, newChild) {
        Nevow.Athena.Tests.DynamicWidgetInstantiation.upcall(self, 'addChildWidget', newChild);
        self.waitingCount--;
        if (self.waitingCount == 0) {
            self.waiting.callback(null);
        }
    });
