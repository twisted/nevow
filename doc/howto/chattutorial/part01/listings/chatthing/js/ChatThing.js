// import Nevow.Athena

Nevow.Athena.Widget.subclass(ChatThing, 'ChatterWidget').methods(
    function __init__(self, node) {
        ChatThing.ChatterWidget.upcall(self, "__init__", node);
        self.chooseBox = self.nodeByAttribute('name', 'chooseBox');
        self.scrollArea = self.nodeByAttribute('name', 'scrollArea');
	self.sendLine = self.nodeByAttribute('name', 'sendLine');
        self.usernameField = self.nodeByAttribute('name', 'username');
        self.userMessage = self.nodeByAttribute('name', 'userMessage');
        self.loggedInAs = self.nodeByAttribute('name', 'loggedInAs');
    },

    function doSetUsername(self) {
        var username = self.usernameField.value;
        self.callRemote("setUsername", username).addCallback(
            function (result) {
                self.chooseBox.style.display = "none";
                self.sendLine.style.display = "block";
                self.loggedInAs.appendChild(document.createTextNode(username));
                self.loggedInAs.style.display = "block";
            });
        return false;
    },

    function doSay(self) {
        self.callRemote("say", self.userMessage.value);
        self.nodeByAttribute('name', 'userMessage').value = "";
        return false;
    },

    function displayMessage(self, message) {
        var newNode = document.createElement('div');
        newNode.appendChild(document.createTextNode(message));
        self.scrollArea.appendChild(newNode);
        document.body.scrollTop = document.body.scrollHeight;
    },

    function displayUserMessage(self, avatarName, text) {
        var msg = avatarName+': '+text;
        self.displayMessage(msg);
    });
