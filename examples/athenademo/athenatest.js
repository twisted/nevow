
// import Nevow.Athena

AthenaTest = {};

AthenaTest.AutomaticClass = Nevow.Athena.Widget.subclass();

AthenaTest.AutomaticClass.prototype.clicked = function() {
    /* Yep, it was clicked.
     */
    return 'Win'; /* Can't return undefined, the test() function
                   * doesn't like that.
                   */
};

AthenaTest.WidgetIsATable = Nevow.Athena.Widget.subclass();
AthenaTest.WidgetIsATable.prototype.test = function() {
};

AthenaTest.WidgetInATable = Nevow.Athena.Widget.subclass();
AthenaTest.WidgetInATable.prototype.test = function() {
};

AthenaTest.ChildParent = Nevow.Athena.Widget.subclass();
AthenaTest.ChildParent.method(
    'checkParent',
    function(self, proposedParent) {
        assertEquals(self.widgetParent, proposedParent);
    });

AthenaTest.ChildParent.method(
    'test',
    function(self) {

        var deferredList = function(finalDeferred, counter) {
            if (counter == 0) {
                finalDeferred.callback(null);
            }
            var callback = function(ignored) {
                counter -= 1;
                if (counter == 0) {
                    finalDeferred.callback(null);
                }
            };
            return callback;
        };

        return self.callRemote('getChildCount').addCallback(function(count) {
            var d = new MochiKit.Async.Deferred();
            d.addCallback(function() { self.node.style.border = 'thin solid green'; });
            var cb = deferredList(d, count);
            assertEquals(self.childWidgets.length, count);
            for (var i = 0; i < self.childWidgets.length; i++) {
                var childWidget = self.childWidgets[i];
                childWidget.checkParent(self);
                childWidget.test().addCallback(cb).addErrback(function(err) { d.errback(err); });
            }
            return d;
        });
    });
