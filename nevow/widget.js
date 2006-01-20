
/**
 * Athena Widgets
 *
 * This module defines a base class useful for adding behaviors to
 * discrete portions of a page.  These widgets can be independent of
 * other content on the same page, allowing separately developed
 * widgets to be combined, or multiple instances of a single widget to
 * appear repeatedly on the same page.
 */

Nevow.Athena.Widget = Nevow.Athena.RemoteReference.subclass('Nevow.Athena.Widget');
Nevow.Athena.Widget.methods(
    function __init__(self, widgetNode) {
        self.node = widgetNode;
        self.childWidgets = [];
        self.widgetParent = null;
        Nevow.Athena.Widget.upcall(self, "__init__", Nevow.Athena.athenaIDFromNode(widgetNode));
    },

    function addChildWidget(self, newChild) {
        self.childWidgets.push(newChild);
        newChild.setWidgetParent(self);
    },

    function setWidgetParent(self, widgetParent) {
        self.widgetParent = widgetParent;
    },

    function visitNodes(self, visitor) {
        Nevow.Athena._walkDOM(self.node, function(node) {
            var result = visitor(node);
            if (result || result == undefined) {
                return true;
            } else {
                return false;
            }
        });
    },

    function nodeByAttribute(self, attrName, attrValue) {
        return Nevow.Athena.NodeByAttribute(self.node, attrName, attrValue);
    },


    function nodesByAttribute(self, attrName, attrValue) {
        return Nevow.Athena.NodesByAttribute(self.node, attrName, attrValue);
    });

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
        var widgetClass = Nevow.Athena.athenaClassFromNode(widgetNode);
        Nevow.Athena.Widget._athenaWidgets[widgetId] = new widgetClass(widgetNode);
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


Nevow.Athena.callByAthenaID = function(athenaID, methodName, varargs) {
    var widget = Nevow.Athena.Widget.fromAthenaID(athenaID);
    var method = widget[methodName];
    Divmod.debug('widget', 'Invoking ' + methodName + ' on ' + widget + '(' + widget[methodName] + ')');
    if (method == undefined) {
        throw new Error(widget + ' has no method ' + methodName);
    }
    return method.apply(widget, varargs);
};

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

Nevow.Athena.IntrospectionWidget = Nevow.Athena.Widget.subclass('Nevow.Athena.IntrospectionWidget');
Nevow.Athena.IntrospectionWidget.methods(
    function __init__(self, node) {
        Nevow.Athena.IntrospectionWidget.upcall(self, '__init__', node);

        self.infoNodes = {
            'toggleDebugging': self.nodeByAttribute('class', 'toggle-debug')
        };

        self.infoNodes['toggleDebugging'].onclick = function() { return self.toggleDebugging(); };

        self.setDebuggingDisplayStyle();

        self.events = [];
        self.eventLimit = 1000;

        self._logWindow = null;
        self._logNode = null;

        Divmod.logger.addObserver(function(event) { self.observe(event); });
    },

    function observe(self, event) {
        var channel = event['channel'];
        if (channel != 'transport' && channel != 'request' && channel != 'object') {
            self.callRemote('log', event);
        }
        self.events.push(event);
        if (self.events.length > self.eventLimit) {
            self.events.shift();
        }
        if (self._logNode != null) {
            self._addEvent(self._logNode, event);
        }
    },

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
    },

    function _openLogWindow(self) {
        self._logWindow = window.open('', 'Nevow_Athena_Log_Window', 'width=640,height=480');
        self._logWindow.document.write(Nevow.Athena.consoleDoc);
        self._logWindow.document.close();
        self._logNode = self._logWindow.document.getElementById('console');
    },

    function _closeLogWindow(self) {
        if (self._logWindow) {
            self._logWindow.close();
            self._logWindow = null;
            self._logNode = null;
        }
    },

    function toggleDebugging(self) {
        Divmod.debugging ^= 1;
        self.setDebuggingDisplayStyle();
    },

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
 * Instantiate Athena Widgets.
 */
Nevow.Athena.Widget._instantiateOneWidget = function(cls, node) {
    Divmod.debug("widget", "Found Widget class " + cls + ", instantiating.");
    var inst = cls.get(node);
    Divmod.debug("widget", "Widget class " + cls + " instantiated.");
    try {
        var widgetParent = Nevow.Athena.Widget.get(node.parentNode);
        widgetParent.addChildWidget(inst);
    } catch (noParent) {
        // Right now we're going to do nothing here.
        Divmod.debug("widget", "No parent found for widget " + inst);
    }
    if (inst.loaded != undefined) {
        inst.loaded();
        Divmod.debug("widget", "Widget class " + cls + " loaded.");
    }
};

Nevow.Athena.Widget._pageLoaded = false;
Nevow.Athena.Widget._waitingWidgets = {};
Nevow.Athena.Widget._widgetNodeAdded = function(nodeId) {
    Nevow.Athena.Widget._waitingWidgets[nodeId] = null;
    if (Nevow.Athena.Widget._pageLoaded) {
        if (Nevow.Athena.Widget._instantiationTimer == null) {
            Nevow.Athena.Widget._instantiationTimer = setTimeout(Nevow.Athena.Widget._instantiateWidgets, 1);
        }
    }
};

Nevow.Athena.Widget._instantiateWidgets = function() {
    var widgetIds = Nevow.Athena.Widget._waitingWidgets;
    Nevow.Athena.Widget._waitingWidgets = {};

    Nevow.Athena.Widget._instantiationTimer = null;

    Nevow.Athena._walkDOM(
        document.documentElement,
        function(node) {
            var cls = Nevow.Athena.athenaClassFromNode(node);
            if (cls) {
                var widgetId = Nevow.Athena.athenaIDFromNode(node);
                if (widgetId != null && widgetId in widgetIds) {
                    Nevow.Athena.Widget._instantiateOneWidget(cls, node);
                }
            }
            return false;
        });
};

Nevow.Athena.Widget._initialize = function() {
    Divmod.debug("widget", "Instantiating live widgets");
    Nevow.Athena.Widget._pageLoaded = true;
    Nevow.Athena.Widget._instantiateWidgets();
    Divmod.debug("widget", "Finished instantiating live widgets");
}

MochiKit.DOM.addLoadEvent(Nevow.Athena.Widget._initialize);
