
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

    function test_widgetInitializationArguments(self) {
        return self.callRemote('test', self.args);
    });

Nevow.Athena.Tests.ClientToServerArgumentSerialization = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.ClientToServerArgumentSerialization');
Nevow.Athena.Tests.ClientToServerArgumentSerialization.methods(
    function test_clientToServerArgumentSerialization(self) {
        var L = [1, 1.5, 'Hello world'];
        var O = {'hello world': 'object value'};
        return self.callRemote('test', 1, 1.5, 'Hello world', L, O);
    });

Nevow.Athena.Tests.ClientToServerResultSerialization = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.ClientToServerResultSerialization');
Nevow.Athena.Tests.ClientToServerResultSerialization.methods(
    function test_clientToServerResultSerialization(self) {
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
    function test_exceptionFromServer(self) {
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
    function test_jsonRoundTrip(self) {
        return self.callRemote('test');
    },

    function identity(self, value) {
        return value;
    });

Nevow.Athena.Tests.AsyncExceptionFromServer = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.AsyncExceptionFromServer');
Nevow.Athena.Tests.AsyncExceptionFromServer.methods(
    function test_asyncExceptionFromServer(self) {
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
    function test_exceptionFromClient(self) {
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
    function test_asyncExceptionFromClient(self) {
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
    function test_serverToClientArgumentSerialization(self) {
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
    function test_serverToClientResultSerialization(self) {
        return self.callRemote('test');
    },

    function reverse(self) {
        return [1, 1.5, 'hello', {'world': 'value'}];
    });

Nevow.Athena.Tests.WidgetInATable = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.WidgetInATable');
Nevow.Athena.Tests.WidgetInATable.methods(
    function test_widgetInATable(self) {
        // Nothing to do
    });

Nevow.Athena.Tests.WidgetIsATable = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.WidgetIsATable');
Nevow.Athena.Tests.WidgetIsATable.methods(
    function test_widgetIsATable(self) {
        // Nothing to do
    });

Nevow.Athena.Tests.ChildParentRelationshipTest = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.ChildParentRelationshipTest');
Nevow.Athena.Tests.ChildParentRelationshipTest.methods(
    function checkParent(self, proposedParent) {
        self.assertEquals(self.widgetParent, proposedParent);
    },

    function test_childParentRelationship(self) {
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
                childWidget.test_childParentRelationship().addCallback(cb).addErrback(function(err) { d.errback(err); });
            }
            return d;
        });
        return result;
    });

Nevow.Athena.Tests.AutomaticClass = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.AutomaticClass');
Nevow.Athena.Tests.AutomaticClass.methods(
    function test_automaticClass(self) {
        // Nothing to do here
    });


Nevow.Athena.Tests.ImportBeforeLiteralJavaScript = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.ImportBeforeLiteralJavaScript');
Nevow.Athena.Tests.ImportBeforeLiteralJavaScript.methods(
    function test_importBeforeLiteralJavaScript(self) {
        self.assertEquals(importBeforeLiteralJavaScriptResult, false);
    });

Nevow.Athena.Tests.AthenaHandler = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.AthenaHandler');
Nevow.Athena.Tests.AthenaHandler.methods(
    /**
     * Call the given object if it is a function.  eval() it if it is a string.
     */
    function _execute(self, thisObject, stringOrFunction) {
        if (typeof stringOrFunction === 'string') {
            return (
                function() {
                    return eval(stringOrFunction);
                }).call(thisObject);
        } else if (typeof stringOrFunction === 'function') {
            return stringOrFunction.call(thisObject);
        } else {
            self.fail(
                "_execute() given something that is neither a " +
                "string nor a function: " + stringOrFunction);
        }
    },

    function test_athenaHandler(self) {
        self.handled = false;
        var button = self.node.getElementsByTagName('button')[0];
        var onclick = button.onclick;
        self.assertEquals(self._execute(button, onclick), false);
        self.assertEquals(self.handled, true);
    },

    function handler(self, evt) {
        self.handled = true;
        return false;
    });

Nevow.Athena.Tests.FirstNodeByAttribute = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.FirstNodeByAttribute');
Nevow.Athena.Tests.FirstNodeByAttribute.methods(
    function test_firstNodeByAttribute(self) {
        var html = '<div xmlns="http://www.w3.org/1999/xhtml" class="foo" />';
        Divmod.Runtime.theRuntime.appendNodeContent(self.node, html);
        var node = self.firstNodeByAttribute("class", "foo");
        self.assertEquals(node.className, "foo");
        self.assertEquals(node.tagName.toLowerCase(), "div");
    });


Nevow.Athena.Tests.DynamicWidgetClass = Nevow.Athena.Widget.subclass('Nevow.Athena.Tests.DynamicWidgetClass');
Nevow.Athena.Tests.DynamicWidgetClass.methods(
    function someMethod(self) {
        /*
         * Do something that hits our Fragment on the server to make sure we
         * can.
         */
        return self.callRemote('someMethod');
    });


/**
 * Test that retrieving several LiveFragments from the server using a
 * method call returns something which can be passed to
 * L{Divmod.Runtime.Platform.setNodeContent} to add new widgets to the
 * page.
 */
Nevow.Athena.Tests.DynamicWidgetInstantiation = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.DynamicWidgetInstantiation');
Nevow.Athena.Tests.DynamicWidgetInstantiation.methods(
    /**
     * Test the API for adding a widget based on an ID, class name, and
     * __init__ arguments to an existing page.
     */
    function test_addChildWidgetFromComponents(self) {
        var widgetID;
        var widgetClass;

        /*
         * Get a widget from the server
         */
        var result = self.callRemote('getDynamicWidgetInfo');
        result.addCallback(
            function(widgetInfo) {
                widgetID = widgetInfo.id;
                widgetClass = widgetInfo.klass;

                /*
                 * Server isn't going to give us any markup because markup is
                 * fugly.  So, construct the widget's root node ourselves.  It
                 * still needs to have all the special attributes for anything
                 * to work right.
                 */
                return self._addChildWidgetFromComponents(
                    [], widgetID, widgetClass, [], [],
                    '<span xmlns="http://www.w3.org/1999/xhtml" id="athena:' +
                    widgetID + '" class="' + widgetClass + '" />');
            });
        result.addCallback(
            function(childWidget) {
                self.assertEqual(Nevow.Athena.Widget.get(childWidget.node), childWidget);
                self.assertEqual(childWidget.widgetParent, self);
                self.assertEqual(self.childWidgets[self.childWidgets.length - 1], childWidget);
                return childWidget.someMethod();
            });
        result.addCallback(
            function(methodResult) {
                self.assertEqual(methodResult, 'foo');
            });
        return result;
    },

    /**
     * Test the API for adding a widget based on a messy pile of data.
     */
    function test_addChildWidgetFromWidgetInfo(self) {
        var result = self.callRemote('getDynamicWidget');
        result.addCallback(
            function(widget) {
                return self.addChildWidgetFromWidgetInfo(widget);
            });
        result.addCallback(
            function(widget) {
                self.assertEqual(Nevow.Athena.Widget.get(widget.node), widget);
                self.assertEqual(widget.node.parentNode.parentNode, null);
                self.assertEqual(widget.widgetParent, self);
                self.assertEqual(self.childWidgets[self.childWidgets.length - 1], widget);

                return widget.someMethod();
            });
        result.addCallback(
            function(methodResult) {
                self.assertEqual(methodResult, 'foo');
            });
        return result;
    }
    );

/**
 * Test that calling Widget.get() on a node which is not part of any Widget
 * throws an error.
 */
Nevow.Athena.Tests.GettingWidgetlessNodeRaisesException = Nevow.Athena.Test.TestCase.subclass('Nevow.Athena.Tests.GettingWidgetlessNodeRaisesException');
Nevow.Athena.Tests.GettingWidgetlessNodeRaisesException.methods(
    function test_gettingWidgetlessNodeRaisesException(self) {
        var result;
        var threw;
        try {
            result = Nevow.Athena.Widget.get(document.head);
            threw = false;
        } catch (err) {
            threw = true;
        }
        if (!threw) {
            self.fail("No error thrown by Widget.get() - returned " + result + " instead.");
        }
    });

Nevow.Athena.Tests.RemoteMethodErrorShowsDialog = Nevow.Athena.Test.TestCase.subclass('RemoteMethodErrorShowsDialog');
Nevow.Athena.Tests.RemoteMethodErrorShowsDialog.methods(
    function test_remoteMethodErrorShowsDialog(self) {
        var getDialogs = function() {
            return Nevow.Athena.NodesByAttribute(
                        document.body,
                        "class",
                        "athena-error-dialog-" + Nevow.Athena.athenaIDFromNode(self.node));
        }

        return self.callRemote("raiseValueError").addErrback(
            function(err) {
                /* we added the errback before the setTimeout()
                   in callRemote() fired, so it won't get the error */

                self.assertEquals(getDialogs().length, 0);

                var D = self.callRemote("raiseValueError");

                /* we make another deferred to return from this method
                   because the test machinery will add callbacks to D,
                   which will get run before athena adds the errback,
                   resulting in a test failure */

                var waitD = Divmod.Defer.Deferred();

                /* setTimeout() the callback-adding, because we want
                   the callback to run after athena has added the
                   error dialog errback to the callRemote() deferred */

                setTimeout(function() {
                    D.addCallback(
                        function() {
                            var dialogs = getDialogs();

                            if(dialogs.length == 1) {
                                document.body.removeChild(dialogs[0]);
                                waitD.callback(null);
                            } else {
                                waitD.errback(
                                    new Error("expected 1 dialog, got " + dialogs.length));
                            }
                        });
                    }, 0);
                return waitD;
            });
    });
