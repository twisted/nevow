
// import Nevow.Athena

typeahead.TypeAhead = Nevow.Athena.Widget.subclass('typeahead.TypeAhead');
typeahead.TypeAhead.methods(
    function __init__(self, node) {
        typeahead.TypeAhead.upcall(self, '__init__', node);

        /*
         * Save some useful nodes to be used later.
         */
        self.inputNode = self.firstNodeByAttribute('class', 'typehere');
        self.descriptionNode = self.firstNodeByAttribute('class', 'description');
    },

    function replaceDescription(self, result) {
        var animal = result[0];
        var descr = result[1];

        Divmod.Runtime.theRuntime.setNodeContent(
            self.descriptionNode,
            '<span xmlns="http://www.w3.org/1999/xhtml">' + descr + '</span>');

        // fill in the text field and select the portion that was guessed
        if (animal != null) {
            var typedLength = self.inputNode.value.length;
            self.inputNode.value = animal;

            if (self.inputNode.setSelectionRange) {
                self.inputNode.setSelectionRange(typedLength, animal.length);
            } else if (self.inputNode.createTextRange) {
                var range = self.inputNode.createTextRange();
                range.moveStart("character", typedLength);
                range.moveEnd("character", animal.length - typedLength);
                range.select();
            }
            self.inputNode.focus();
        }
    },

    function loadDescription(self, node, event) {
        // filter helpful keys like backspace
        if (event.keyCode < 32) {
            return;
        }
        if (event.keyCode >= 33 && event.keyCode <= 46) {
            return;
        }
        if (event.keyCode >= 112 && event.keyCode <= 123) {
            return;
        }

	var result = self.callRemote('loadDescription', self.inputNode.value);
	result.addCallback(function(description) { return self.replaceDescription(description); });
    });
