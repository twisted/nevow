
/**
 * Athena Widgets
 *
 * This module defines a base class useful for adding behaviors to
 * discrete portions of a page.  These widgets can be independent of
 * other content on the same page, allowing separately developed
 * widgets to be combined, or multiple instances of a single widget to
 * appear repeatedly on the same page.
 */

Nevow.Athena.Widget = Nevow.Athena.RemoteReference.subclass();

Nevow.Athena.Widget.prototype.__init__ = function(widgetNode) {
    this.node = widgetNode;
    this.childWidgets = [];
    this.widgetParent = null;
    Nevow.Athena.Widget.upcall(this, "__init__", Nevow.Athena.athenaIDFromNode(widgetNode));
};

Nevow.Athena.Widget.method(
    function addChildWidget(self, newChild) {
        self.childWidgets.push(newChild);
        newChild.setWidgetParent(self);
    });

Nevow.Athena.Widget.method(
    function setWidgetParent(self, widgetParent) {
        self.widgetParent = widgetParent;
    });

Nevow.Athena.Widget.prototype.visitNodes = function(visitor) {
    Nevow.Athena._walkDOM(this.node, function(node) {
        var result = visitor(node);
        if (result || result == undefined) {
            return true;
        } else {
            return false;
        }
    });
};

Nevow.Athena.Widget.prototype.nodeByAttribute = function(attrName, attrValue) {
    return Nevow.Athena.NodeByAttribute(this.node, attrName, attrValue);
};

Nevow.Athena.Widget.prototype.nodesByAttribute = function(attrName, attrValue) {
    return Nevow.Athena.NodesByAttribute(this.node, attrName, attrValue);
};

Nevow.Athena.Widget._athenaWidgets = {};

/**
 * Given any node within a Widget (the client-side representation of a
 * LiveFragment), return the instance of the Widget subclass that corresponds
 * with that node, creating that Widget subclass if necessary.
 */
Nevow.Athena.Widget.get = function(node) {
    var widgetNode = Nevow.Athena.nodeByDOM(node);
    var widgetId = Nevow.Athena.athenaIDFromNode(widgetNode);
    if (Nevow.Athena.Widget._athenaWidgets[widgetId] == null) {
        Nevow.Athena.Widget._athenaWidgets[widgetId] = new this(widgetNode);
    }
    return Nevow.Athena.Widget._athenaWidgets[widgetId];
};

/**
 * Search the whole document for a particular widget id.
 */
Nevow.Athena.Widget.fromAthenaID = function(widgetId) {
    var visitor = function(node) {
        return (Nevow.Athena.athenaIDFromNode(node) == widgetId);
    }
    var nodes = Nevow.Athena._walkDOM(document, visitor);

    if (nodes.length != 1) {
        throw new Error(nodes.length + " nodes with athena id " + widgetId);
    };

    return Nevow.Athena.Widget.get(nodes[0]);
};

/*
 * Walk the document.  Find things with a athena:class attribute
 * and instantiate them.
 */
Nevow.Athena.Widget._instantiateWidgets = function() {
    var visitor = function(n) {
        try {
            var cls = Nevow.Athena.athenaClassFromNode(n);
            if (cls) {
                Divmod.debug("widget", "Found Widget class " + cls + ", instantiating.");
                var inst = cls.get(n);
                Divmod.debug("widget", "Widget class " + cls + " instantiated.");
                try {
                    var widgetParent = Nevow.Athena.Widget.get(n.parentNode);
                    widgetParent.addChildWidget(inst);
                } catch (noParent) {
                    // Right now we're going to do nothing here.
                    Divmod.debug("widget", "No parent found for widget " + inst);
                }
                if (inst.loaded != undefined) {
                    inst.loaded();
                    Divmod.debug("widget", "Widget class " + cls + " loaded.");
                }
            }
        } catch (e) {
            Divmod.debug('widget', '==================================================');
            Divmod.debug('widget', 'Error instantiating widget on tag ' + n.tagName);
            for (var i in n.attributes) {
                Divmod.debug('widget', i + ': ' + n.attributes[i].value);
            }
            Divmod.debug('widget', '==================================================');
        }

    }
    Nevow.Athena._walkDOM(document, visitor);
}

Nevow.Athena.callByAthenaID = function(athenaID, methodName, varargs) {
    var widget = Nevow.Athena.Widget.fromAthenaID(athenaID);
    Divmod.debug('widget', 'Invoking ' + methodName + ' on ' + widget + '(' + widget[methodName] + ')');
    return widget[methodName].apply(widget, varargs);
};


Nevow.Athena.IntrospectionWidget = Nevow.Athena.Widget.subclass('Nevow.Athena.IntrospectionWidget');

Nevow.Athena.IntrospectionWidget.method(
    function __init__(self, node) {
        Nevow.Athena.IntrospectionWidget.upcall(self, '__init__', node);

        self.infoNodes = {
            'toggleDebugging': self.nodeByAttribute('class', 'toggle-debug'),
        };

        self.infoNodes['toggleDebugging'].onclick = function() { return self.toggleDebugging(); };

        self.setDebuggingDisplayStyle();

        self.events = [];
        self.eventLimit = 1000;

        self._logWindow = null;
        self._logNode = null;

        Divmod.logger.addObserver(function(event) { self.observe(event); });
    });

Nevow.Athena.IntrospectionWidget.method(
    function observe(self, event) {
        self.events.push(event);
        if (self.events.length > self.eventLimit) {
            self.events.shift();
        }
        if (self._logNode != null) {
            try { self._addEvent(self._logNode, event); }
            catch (e) { alert(e); }
        }
    });

Nevow.Athena.IntrospectionWidget.method(
    function _addEvent(self, node, event) {
        var div = document.createElement('div');
        if (event['isError']) {
            div.setAttribute('class', 'log-message-error');
        } else if (event['channel']) {
            div.setAttribute('class', 'log-message-' + event['channel']);
        }
        div.appendChild(document.createTextNode(event['message']));
        node.appendChild(div);
        div.scrollIntoView(false);
    });

Nevow.Athena.consoleDoc = (
    '<html>' +
    '  <head>' +
    '    <title>Log Console</title>' +
    '    <style type="text/css">' +
    '    body {' +
    '      background-color: #fff;' +
    '      color: #333;' +
    '      font-size: 8pt;' +
    '      margin: 0;' +
    '      padding: 0;' +
    '    }' +
    '    #clear {' +
    '      position: absolute;' +
    '      right: 1em;' +
    '      color: #900;' +
    '    }' +
    '    #console {' +
    '      position: absolute;' +
    '      top: 3em;' +
    '      bottom: 0;' +
    '      left: 0;' +
    '      right: 0;' +
    '      overflow: scroll;' +
    '      font-family: monospace;' +
    '      padding: 0 0.5em;' +
    '    }' +
    '    .log-message-error {' +
    '      margin: 0 0 0 0;' +
    '      padding: 0;' +
    '      border-bottom: 1px dashed #ccf;' +
    '      color: red;' +
    '    }' +
    '    .timestamp {' +
    '      display: block;' +
    '      font-weight: bold;' +
    '      color: #999;' +
    '    }' +
    '    </style>' +
    '  </head>' +
    '  <body>' +
    '    <div id="console" />' +
    '  </body>' +
    '</html>');

Nevow.Athena.IntrospectionWidget.method(
    function _openLogWindow(self) {
        self._logWindow = window.open('', 'Nevow Athena Log Window', 'dependent=yes,height=640,width=480,resizable=yes');
        self._logWindow.document.write(Nevow.Athena.consoleDoc);
        self._logWindow.document.close();
        self._logNode = self._logWindow.document.getElementById('console');
    });

Nevow.Athena.IntrospectionWidget.method(
    function _closeLogWindow(self) {
        if (self._logWindow) {
            self._logWindow.close();
            self._logWindow = null;
            self._logNode = null;
        }
    });

Nevow.Athena.IntrospectionWidget.method(
    function toggleDebugging(self) {
        Divmod.debugging ^= 1;
        self.setDebuggingDisplayStyle();
    });

Nevow.Athena.IntrospectionWidget.method(
    function setDebuggingDisplayStyle(self) {
        if (Divmod.debugging) {
            self.infoNodes['toggleDebugging'].setAttribute('class', 'nevow-athena-debugging-enabled');
            self._openLogWindow();
        } else {
            self.infoNodes['toggleDebugging'].setAttribute('class', 'nevow-athena-debugging-disabled');
            self._closeLogWindow();
        }
    });


/**
 * Instantiate Athena Widgets, make initial server connection, and set
 * up listener for "onunload" event to do finalization.
 */
Nevow.Athena.Widget._initialize = function() {
    Divmod.debug("widget", "Instantiating live widgets");
    Nevow.Athena.Widget._instantiateWidgets();
    Divmod.debug("widget", "Finished instantiating live widgets");
}

MochiKit.DOM.addLoadEvent(Nevow.Athena.Widget._initialize);
