
// import Nevow.Athena

AthenaTest = {};

AthenaTest.TestCase = Nevow.Athena.Widget.subclass('AthenaTest.TestCase');
AthenaTest.TestCase.methods(
    function fail(self, msg) {
        throw new Error('Test Failure: ' + msg);
    },

    function assertEquals(self, a, b) {
        if (!(a == b)) {
            fail(a + ' != ' + b);
        }
    },

    function test(self) {
        var res;
        var subargs = [];
        for (var i = 1; i < arguments.length; ++i) {
            subargs.push(arguments[i]);
        }
        try {
            res = self._test.apply(self, subargs);
        } catch (e) {
            res = MochiKit.Async.fail(e);
        }

        if (res == undefined || !res.addCallback || !res.addErrback) {
            res = MochiKit.Async.succeed(res);
        }

        res.addCallback(function(result) {
            Divmod.log('test', 'Success!');
        });

        res.addErrback(function(err) {
            Divmod.log('test', 'Failure: ' + err.message);
        });

        return false;
    });

AthenaTest.ClientToServerArgumentSerialization = AthenaTest.TestCase.subclass('AthenaTest.ClientToServerArgumentSerialization');
AthenaTest.ClientToServerArgumentSerialization.methods(
    function _test(self) {
        var L = [1, 1.5, 'Hello world'];
        var O = {'hello world': 'object value'};
        return self.callRemote('test', 1, 1.5, 'Hello world', L, O);
    });

AthenaTest.ClientToServerResultSerialization = AthenaTest.TestCase.subclass('AthenaTest.ClientToServerResultSerialization');
AthenaTest.ClientToServerResultSerialization.methods(
    function _test(self) {
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

AthenaTest.ClientToServerExceptionResult = AthenaTest.TestCase.subclass('AthenaTest.ClientToServerExceptionResult');
AthenaTest.ClientToServerExceptionResult.methods(
    function _test(self, sync) {
        var d;
        var s = 'This exception should appear on the client.';
        if (sync) {
            d = self.callRemote('testSync', s);
        } else {
            d = self.callRemote('testAsync', s);
        }
        d.addCallbacks(
            function(result) {
                self.fail('Erroneously received a result: ' + result);
            },
            function(err) {
                var idx = err.message.indexOf(s);
                if (idx == -1) {
                    self.fail('Did not find expected message in error message: ' + err);
                }
            });
        return d;
    });

AthenaTest.ServerToClientArgumentSerialization = AthenaTest.TestCase.subclass('AthenaTest.ServerToClientArgumentSerialization');
AthenaTest.ServerToClientArgumentSerialization.methods(
    function _test(self) {
        return self.callRemote('test');
    },

    function reverse(self, i, f, s, o) {
        self.assertEquals(i, 1);
        self.assertEquals(f, 1.5);
        self.assertEquals(s, 'hello');
        self.assertEquals(o['world'], 'value');
    });

AthenaTest.ServerToClientResultSerialization = AthenaTest.TestCase.subclass('AthenaTest.ServerToClientResultSerialization');
AthenaTest.ServerToClientResultSerialization.methods(
    function _test(self) {
        return self.callRemote('test');
    },

    function reverse(self) {
        return [1, 1.5, 'hello', {'world': 'value'}];
    });

AthenaTest.WidgetInATable = AthenaTest.TestCase.subclass('AthenaTest.WidgetInATable');
AthenaTest.WidgetInATable.methods(
    function _test(self) {
        // Nothing to do
    });

AthenaTest.WidgetIsATable = AthenaTest.TestCase.subclass('AthenaTest.WidgetIsATable');
AthenaTest.WidgetIsATable.methods(
    function _test(self) {
        // Nothing to do
    });

AthenaTest.ChildParentRelationshipTest = AthenaTest.TestCase.subclass('AthenaTest.ChildParentRelationshipTest');
AthenaTest.ChildParentRelationshipTest.methods(
    function checkParent(self, proposedParent) {
        self.assertEquals(self.widgetParent, proposedParent);
    },

    function _test(self) {
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
            var d = new MochiKit.Async.Deferred();
            d.addCallback(function() { self.node.style.border = 'thin solid green'; });
            var cb = deferredList(d, count);
            self.assertEquals(self.childWidgets.length, count);
            for (var i = 0; i < self.childWidgets.length; i++) {
                var childWidget = self.childWidgets[i];
                childWidget.checkParent(self);
                childWidget._test().addCallback(cb).addErrback(function(err) { d.errback(err); });
            }
            return d;
        });
        return result;
    });

AthenaTest.AutomaticClass = AthenaTest.TestCase.subclass('AthenaTest.AutomaticClass');
AthenaTest.AutomaticClass.methods(
    function _test(self) {
        // Nothing to do here
    });


AthenaTest.ImportBeforeLiteralJavaScript = AthenaTest.TestCase.subclass('AthenaTest.ImportBeforeLiteralJavaScript');
AthenaTest.ImportBeforeLiteralJavaScript.methods(
    function _test(self) {
        self.assertEquals(importBeforeLiteralJavaScriptResult, false);
    });
