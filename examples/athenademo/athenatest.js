
// import Nevow.Athena

if (typeof AthenaTest == 'undefined') {
    AthenaTest = {};
}

AthenaTest.AutomaticClass = Nevow.Athena.Widget.subclass();
AthenaTest.AutomaticClass.prototype.__init__ = function() {
};

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
