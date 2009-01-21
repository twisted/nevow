// import Nevow.Athena

Nevow.Athena.Widget.subclass(EchoThing, 'EchoWidget').methods(
    function __init__(self, node) {
        EchoThing.EchoWidget.upcall(self, "__init__", node);
        self.echoWidget = self.nodeByAttribute('name', 'echoElement');
        self.scrollArea = self.nodeByAttribute('name', 'scrollArea');
        self.message = self.nodeByAttribute('name', 'message');
    },  

    function doSay(self) {
        self.callRemote("say", self.message.value);
        self.message.value = ""; 
        return false;
    },
 
    function addText(self, text) {
        var newNode = document.createElement('div');
        newNode.appendChild(document.createTextNode(text));
        self.scrollArea.appendChild(newNode);
        document.body.scrollTop = document.body.scrollHeight;
    });
