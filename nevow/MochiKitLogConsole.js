var consoleDoc = ''+
'<html>'+
'  <head>'+
'    <title>Log Console</title>'+
'    <script type="text/javascript" src="mochikit.js"></script>'+
'    <script type="text/javascript" src="MochiKitLogConsole.js"></script>'+
'    <style type="text/css">'+
'    body {'+
'      background-color: #fff;'+
'      color: #333;'+
'      font-size: 8pt;'+
'      margin: 0;'+
'      padding: 0;'+
'    }'+
'    #clear {'+
'      position: absolute;'+
'      right: 1em;'+
'      color: #900;'+
'    }'+
'    #console {'+
'      position: absolute;'+
'      top: 3em;'+
'      bottom: 0;'+
'      left: 0;'+
'      right: 0;'+
'      overflow: scroll;'+
'      font-family: monospace;'+
'      padding: 0 0.5em;'+
'    }'+
'    .message {'+
'      margin: 0 0 0 0;'+
'      padding: 0;'+
'      border-bottom: 1px dashed #ccf;'+
'    }'+
'     .timestamp {'+
'       display: block;'+
'       font-weight: bold;'+
'       color: #999;'+
'     }'+
'     .level {'+
'       font-weight: bold;'+
'       color: #666;'+
'     }'+
'    </style>'+
'  </head>'+
'  <body onload="LogConsole.init()">'+
'    <div id="controls" />'+
'      <label><input type="checkbox" id="timestamp" onclick="LogConsole.init()"/>Show timestamps</label>'+
'      <a href="#" id="clear" onclick="LogConsole.clear(); return false;">Clear</a>'+
'    </div>'+
'    <div id="console" />'+
'  </body>'+
'</html>'

if(typeof(LogConsole) == "undefined") {
    LogConsole = {}
}

LogConsole.show = function() {
    var consoleWindow = window.open('', 'MochiKitLogConsole', 'dependent=yes,height=600,width=400,resizable=yes');
    consoleWindow.document.write(consoleDoc);
    consoleWindow.document.close();
}

LogConsole.init = function() {
    // Clear all messages
    MochiKit.DOM.replaceChildNodes(MochiKit.DOM.getElement("console"), null);
    // Work out how much room the scroll bar along the bottom takes up o we
    // can tell if the user was scrolled to the end of the list.
    var console = MochiKit.DOM.getElement('console');
    LogConsole.scrollBarHeight = console.offsetHeight-console.scrollHeight;
    // Load the current message list into the console.
    var logger = LogConsole.getLogger();
    msgs = logger.getMessages();
    forEach(msgs, LogConsole.appendMessage);
    // Listen for new messages
    //logger.removeListener('logConsole');
    logger.addListener('logConsole', null, LogConsole.appendMessage);
}

LogConsole.scrollBarHeight = null;

LogConsole.getLogger = function() {
    return window.opener.logger;
}

LogConsole.appendMessage = function(message) {

    var console = MochiKit.DOM.getElement('console');
    var showTimestamp = MochiKit.DOM.getElement('timestamp').checked;

    var tsTag = SPAN({'class':'timestamp'}, [message.timestamp]);
    var levelTag = SPAN({'class':'level'}, [message.level]);
    var infoTag = message.info;

    if(showTimestamp) {
        var tags = [tsTag, ' ', levelTag, ' ', infoTag];
    } else {
        var tags = [levelTag, ' ', infoTag];
    }

    var wasAtEnd = console.scrollTop+console.offsetHeight-console.scrollHeight == LogConsole.scrollBarHeight;
    appendChildNodes(console, P({'class':'message'}, tags));

    if(wasAtEnd) {
        console.scrollTop = console.scrollHeight;
    }
}

LogConsole.clear = function() {
    LogConsole.getLogger().clear();
    LogConsole.init();
}

