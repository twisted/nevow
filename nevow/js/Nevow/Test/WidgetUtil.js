// Copyright (c) 2007 Divmod.
// See LICENSE for details.

/**
 * Utilities for testing L{Nevow.Athena.Widget} subclasses.
 */


/**
 * Make a node suitable for passing as the first argument to a
 * L{Nevow.Athena.Widget} constructor.
 *
 * @param athenaID: the athena ID of the widget this node belongs to.
 * defaults to '1'.
 * @type athenaID: C{Number}
 *
 * @return: a node.
 */
Nevow.Test.WidgetUtil.makeWidgetNode = function makeWidgetNode(athenaID/*=1*/) {
    if(athenaID === undefined) {
        athenaID = 1;
    }
    var node = document.createElement('div');
    node.id = 'athena:' + athenaID;
    return node;
}

/**
 * Tell athena that there is a widget with the ID C{athenaID}.
 *
 * @param widget:  a widget (the one to associate with C{athenaID}).
 * @type widget: L{Nevow.Athena.Widget}
 *
 * @param athenaID: the athena ID of this widget.  defaults to '1'.
 * @type athenaID: C{Number}
 *
 * @rtype: C{undefined}
 */
Nevow.Test.WidgetUtil.registerWidget = function registerWidget(widget, athenaID/*=1*/) {
    if(athenaID == undefined) {
        athenaID = 1;
    }
    Nevow.Athena.Widget._athenaWidgets[athenaID] = widget;
}

/**
 * Replace L{Nevow.Athena._rdm} with an object which doesn't attempt to do any
 * network stuff.
 *
 * @return: a thunk which will restore L{Nevow.Athena._rdm} to what it was at
 * the time this function was called.
 * @rtype: C{Function}
 */
Nevow.Test.WidgetUtil.mockTheRDM = function mockTheRDM() {
    // this should probably be a "callWithMockRDM" function
    var originalRDM = Nevow.Athena._rdm;
    Nevow.Athena._rdm = {
        pause: function() {},
        unpause: function() {}
    };
    return function() {
        Nevow.Athena._rdm = originalRDM;
    }
}
