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


Nevow.Test.TestWidget.SetupTests = Divmod.UnitTest.TestCase.subclass(
    'Nevow.Test.TestWidget.SetupTests');

/**
 * Test things about the global state that Athena needs to set up in order to
 * function properly.
 */
Nevow.Test.TestWidget.SetupTests.methods(

    /**
     * Safely replace a global for the duration of the test, such that it will
     * be restored in tearDown.  NB: this only works for top-level globals
     * right now, i.e. it doesn't support dots in the name yet.
     */
    function mockGlobalForTest(self, name, newValue) {
        self._mocks.push([name, Divmod.namedAny(name)]);
        Divmod._global[name] = newValue;
    },

    /**
     * Replace the 'window' object so the tests can inspect it easily.
     */
    function setUp(self) {
        self._mocks = [];
    },

    /**
     * The 'Escape' key's default behavior in Firefox is to kill the outgoing
     * connection immediately.  If the user does this 3 times, it will cancel
     * 3 output channels, which will cause the Athena connection to die.
     *
     * When we receive such an event on the top-level window, cancel it so
     * that the connections will not be affected, but do not otherwise alter
     * the event, so that users can handle keys as they see fit.
     */
    function test_escapeCancelsDefault(self) {
        var fakeEvt = self._fakeEvent(Nevow.Athena.KEYCODE_ESCAPE);
        var result = Nevow.Athena._checkEscape(fakeEvt);
        self.assertIdentical(fakeEvt.cancelBubble, false);
        self.assertIdentical(result, true);
        self.assert(fakeEvt.prevented, "Did not prevent default behavior.");
    },

    /**
     * Create a fake event object.
     */
    function _fakeEvent(self, keyCode) {
        var evt = {
          prevented: false,
          keyCode: keyCode,
          cancelBubble: false,
          stopPropagation: function () {
                self.fail("Should not stop propagation.")
            },
          preventDefault: function () {
                evt.prevented = true;
            }
        };
        return evt;
    },

    /**
     * The 'escape' key handler should not modify the event in any way, it
     * should simply return true.
     */
    function test_nonEscapeKeyDoesNothing(self) {
        var NOT_ESCAPE = 1234;
        var fakeEvt = self._fakeEvent(NOT_ESCAPE);
        var result = Nevow.Athena._checkEscape(fakeEvt);
        self.assertIdentical(fakeEvt.cancelBubble, false);
        self.assertIdentical(result, true);
        self.assert(!fakeEvt.prevented, "Prevented default behavior.");
    },

    /**
     * Verify that the window's top-level key-press handler is installed.  See
     * test_escapeCancelsDefault for an explanation of why we need to do this.
     */
    function test_registeredKeyPress(self) {
        self.mockGlobalForTest('window', {});
        Nevow.Athena._initialize();
        self.assertIdentical(window.onkeypress.callStack[0],
                             Nevow.Athena._checkEscape);
    },

    /**
     * Put back the original 'window' object.
     */
    function tearDown(self) {
        for (var i = 0; i < self._mocks.length; i++) {
            var mockInfo = self._mocks[i];
            Divmod._global[mockInfo[0]] = mockInfo[1];
        }
    });
