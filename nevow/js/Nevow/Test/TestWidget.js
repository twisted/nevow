// -*- test-case-name: nevow.test.test_javascript.JSUnitTests.test_widget -*-

// import Divmod.UnitTest
// import Nevow.Athena

Nevow.Test.TestWidget.DummyWidget = Nevow.Athena.Widget.subclass(
    'Nevow.Test.TestWidget.DummyWidget');
Nevow.Test.TestWidget.DummyWidget.methods(
    function onclick(self, event) {
        self.clicked = 'implicitly';
    },

    function explicitClick(self, event) {
        self.clicked = 'explicitly';
    });

Nevow.Test.TestWidget.WidgetTests = Divmod.UnitTest.TestCase.subclass(
    'Nevow.Test.TestWidget.WidgetTests');
Nevow.Test.TestWidget.WidgetTests.methods(
    /**
     * Create a widget for use in each test.
     */
    function setUp(self) {
        self.node = document.createElement("div");
        self.node.id = "athena:1";
        self.otherNode = document.createElement("span");
        self.node.appendChild(self.otherNode);
        self.widget = Nevow.Test.TestWidget.DummyWidget(self.node);
        Nevow.Athena.Widget._athenaWidgets[1] = self.widget;
        self._origRDM = Nevow.Athena._rdm;
        Nevow.Athena._rdm = self;
    },

    // fake RDM implementation

    function pause(self) {
    },
    function unpause(self) {
    },

    function tearDown(self) {
        Nevow.Athena._rdm = self._origRDM;
    },

    /**
     * Verify that connectDOMEvent will connect the appropriate DOM event to
     * the browser, and the default handler method name and node will be the
     * name of the event and the widget's node.
     */
    function test_connectDOMEventDefaults(self) {
        self.widget.connectDOMEvent("onclick");
        self.node.onclick();
        self.assertIdentical(self.widget.clicked, "implicitly");
    },

    /**
     * Verify that connectDOMEvent will connect the appropriate DOM event to
     * the browser, and the explicitly selected handler will be invoked.
     */
    function test_connectDOMEventCustomMethod(self) {
        self.widget.connectDOMEvent("onclick", "explicitClick");
        self.node.onclick();
        self.assertIdentical(self.widget.clicked, "explicitly");
    },

    /**
     * Verify that connectDOMEvent will connect the appropriate DOM event to
     * the browser, and the explicitly selected node will be used.
     */
    function test_connectDOMEventCustomNode(self) {
        self.widget.connectDOMEvent("onclick", "explicitClick", self.otherNode);
        self.otherNode.onclick();
        self.assertIdentical(self.widget.clicked, "explicitly");
    });
