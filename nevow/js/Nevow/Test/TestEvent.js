// import Divmod
// import Divmod.UnitTest
// import Nevow.Athena



/**
 * A mock DOM event that behaves according to the W3C guide that most browsers
 * follow.
 *
 * @ivar type: Event type.
 *
 * @ivar target: Element to which the DOM event was originally dispatched.
 *
 * @ivar cancelled: Has the default action been cancelled?
 *
 * @ivar stopped: Has event propagation been stopped?
 */
Divmod.Class.subclass(Nevow.Test.TestEvent, 'W3CEvent').methods(
    function __init__(self, type, target) {
        self.type = type;
        self.target = target;
        self.cancelled = false;
        self.stopped = false;
    },


    /**
     * If an event is cancelable, the preventDefault method is used to signify
     * that the event is to be canceled, meaning any default action normally
     * taken by the implementation as a result of the event will not occur.
     */
    function preventDefault(self) {
        self.cancelled = true;
    },


    /**
     * The stopPropagation method is used prevent further propagation of an
     * event during event flow.
     */
    function stopPropagation(self) {
        self.stopped = true;
    });



/**
 * A mock DOM event that behaves according to IE before IE9.
 *
 * @ivar type: Event type.
 *
 * @ivar srcElement: Element to which the DOM event was originally dispatched.
 *
 * @ivar returnValue: Has the default action been cancelled?
 *
 * @ivar cancelBubble: Has event propagation been stopped?
 */
Divmod.Class.subclass(Nevow.Test.TestEvent, 'IEEvent').methods(
    function __init__(self, type, srcElement) {
        self.type = type;
        self.srcElement = srcElement;
        self.returnValue = true;
        self.cancelBubble = false;
    });



/**
 * Tests for L{Nevow.Athena.Event} when using W3C-style event objects.
 */
Divmod.UnitTest.TestCase.subclass(Nevow.Test.TestEvent, 'TestEventW3C').methods(
    function createDOMEvent(self, type, target) {
        return Nevow.Test.TestEvent.W3CEvent(type, target);
    },


    /**
     * L{Nevow.Athena.Event.fromDOMEvent} creates a specific I{Event} subclass
     * if it supports the DOM event otherwise L{Nevow.Athena.Event} is used.
     */
    function test_fromDOMEvent(self) {
        function assertInstanceOf(inst, type, msg) {
            self.assertIdentical(
                evt instanceof type,
                true,
                'Expected ' + inst.toString() +
                ' to be an instance of ' + type.toString());
        }

        var handlers = [
            Nevow.Athena.KeyEvent,
            Nevow.Athena.MouseEvent];

        for (var i = 0; i < handlers.length; ++i) {
            var handler = handlers[i];
            var knownEventTypes = handler.knownEventTypes;
            for (var j = 0; j < knownEventTypes.length; ++j) {
                var domEvent = self.createDOMEvent(
                    knownEventTypes[j], null);
                var evt = Nevow.Athena.Event.fromDOMEvent(domEvent);
                assertInstanceOf(evt, handler);
            }
        }

        var evt = Nevow.Athena.Event.fromDOMEvent(
            self.createDOMEvent('definitelyunknown', null));
        assertInstanceOf(evt, Nevow.Athena.Event);
    },


    /**
     * L{Nevow.Athena.Event} extracts information from different kinds of DOM
     * events and puts them into a universal API.
     */
    function test_attributes(self) {
        var eventType = 'eventType';
        var target = 42;
        var domEvent = self.createDOMEvent(eventType, target);
        var event = Nevow.Athena.Event.fromDOMEvent(domEvent);
        self.assertIdentical(event.event, domEvent);
        self.assertIdentical(event.type, eventType);
        self.assertIdentical(event.target, target);
    },


    /**
     * L{Nevow.Athena.Event.preventDefault} calls the method or sets the
     * attribute on the underlying DOM event that prevents the event's default
     * return value from being used.
     */
    function test_preventDefault(self) {
        var domEvent = self.createDOMEvent('eventtype', null);
        var event = Nevow.Athena.Event.fromDOMEvent(domEvent);
        self.assertIdentical(domEvent.cancelled, false);
        event.preventDefault();
        self.assertIdentical(domEvent.cancelled, true);
    },


    /**
     * L{Nevow.Athena.Event.stopPropagation} calls the method or sets the
     * attribute on the underlying DOM event that stops the event from
     * propogating futher along in the DOM.
     */
    function test_stopPropagation(self) {
        var domEvent = self.createDOMEvent('eventtype', null);
        var event = Nevow.Athena.Event.fromDOMEvent(domEvent);
        self.assertIdentical(domEvent.stopped, false);
        event.stopPropagation();
        self.assertIdentical(domEvent.stopped, true);
    });



/**
 * Tests for L{Nevow.Athena.Event} when using IE-style event objects.
 */
Nevow.Test.TestEvent.TestEventW3C.subclass(Nevow.Test.TestEvent,
                                           'TestEventIE').methods(
    function createDOMEvent(self, type, target) {
        return Nevow.Test.TestEvent.IEEvent(type, target);
    },


    function test_preventDefault(self) {
        var domEvent = self.createDOMEvent('eventtype', null);
        var event = Nevow.Athena.Event.fromDOMEvent(domEvent);
        self.assertIdentical(domEvent.returnValue, true);
        event.preventDefault();
        self.assertIdentical(domEvent.returnValue, false);
    },


    function test_stopPropagation(self) {
        var domEvent = self.createDOMEvent('eventtype', null);
        var event = Nevow.Athena.Event.fromDOMEvent(domEvent);
        self.assertIdentical(domEvent.cancelBubble, false);
        event.stopPropagation();
        self.assertIdentical(domEvent.cancelBubble, true);
    });



/**
 * Tests for L{Nevow.Athena.KeyEvent} when using W3C-style event objects.
 */
Divmod.UnitTest.TestCase.subclass(Nevow.Test.TestEvent,
                                  'TestKeyEventW3C').methods(
    function setUp(self) {
        self.supportsMeta = true;
        self.eventType = Nevow.Test.TestEvent.W3CEvent;
    },


    function createDOMEvent(self, type, target, args) {
        var evt = self.eventType(type, target);
        for (var key in args) {
            evt[key] = args[key];
        }
        return evt;
    },


    /**
     * Properties relating to modifier keys on the original DOM are accessible
     * on L{Nevow.Athena.KeyEvent}.
     */
    function test_modifiers(self) {
        function createEvent(altKey, ctrlKey, shiftKey, metaKey) {
            return Nevow.Athena.Event.fromDOMEvent(
                self.createDOMEvent('keypress', null, {
                    'altKey': !!altKey,
                    'ctrlKey': !!ctrlKey,
                    'shiftKey': !!shiftKey,
                    'metaKey': !!metaKey}));
        }

        function assertModifiers(evt, altKey, ctrlKey, shiftKey, metaKey) {
            self.assertIdentical(evt.altKey, altKey);
            self.assertIdentical(evt.ctrlKey, ctrlKey);
            self.assertIdentical(evt.shiftKey, shiftKey);
            self.assertIdentical(evt.metaKey, metaKey);
        }

        assertModifiers(
            createEvent(true),
            true, false, false, false);
        assertModifiers(
            createEvent(true, true),
            true, true, false, false);
        assertModifiers(
            createEvent(true, true, true),
            true, true, true, false);

        if (self.supportsMeta) {
            assertModifiers(
                createEvent(true, true, true, true),
                true, true, true, true);
        } else {
            assertModifiers(
                createEvent(true, true, true, true),
                true, true, true, false)
        };
    },


    /**
     * L{Nevow.Athena.KeyEvent.getKeyCode} returns the Unicode key code for the
     * DOM event, preferring I{keyCode} over I{which}.
     */
    function test_getKeyCode(self) {
        function createEvent(keyCode, which) {
            return Nevow.Athena.Event.fromDOMEvent(
                self.createDOMEvent('keypress', null, {
                    'keyCode': keyCode,
                    'which': which}));
        }

        function assertKeyCode(evt, keyCode) {
            self.assertIdentical(evt.getKeyCode(), keyCode);
        }

        assertKeyCode(createEvent(65), 65);
        assertKeyCode(createEvent(65, 97), 65);
        assertKeyCode(createEvent(0, 65), 65);
    },


    /**
     * L{Nevow.Athena.KeyEvent.retKeyCode} sets the Unicode key code for the
     * DOM event.
     */
    function test_setKeyCode(self) {
        var evt = Nevow.Athena.Event.fromDOMEvent(
            self.createDOMEvent('keypress', null, {
                'keyCode': 65}));

        self.assertIdentical(evt.getKeyCode(), 65);
        evt.setKeyCode(97);
        self.assertIdentical(evt.event.keyCode, 97);
        self.assertIdentical(evt.getKeyCode(), 97);
    });



/**
 * Tests for L{Nevow.Athena.KeyEvent} when using IE-style event objects.
 */
Nevow.Test.TestEvent.TestKeyEventW3C.subclass(Nevow.Test.TestEvent,
                                              'TestKeyEventIE').methods(
    function setUp(self) {
        Nevow.Test.TestEvent.TestKeyEventIE.upcall(self, 'setUp');
        self.supportsMeta = false;
        self.eventType = Nevow.Test.TestEvent.IEEvent;
    },


    function createDOMEvent(self, type, target, args) {
        // IE < 9 doesn't support "metaKey".
        delete args['metaKey'];
        return Nevow.Test.TestEvent.TestKeyEventIE.upcall(
            self, 'createDOMEvent', type, target, args);
    });



/**
 * Tests for L{Nevow.Athena.MouseEvent} when using W3C-style event objects.
 */
Divmod.UnitTest.TestCase.subclass(Nevow.Test.TestEvent,
                                  'TestMouseEventW3C').methods(
    function setUp(self) {
        self.eventType = Nevow.Test.TestEvent.W3CEvent;
    },


    function createDOMEvent(self, type, target, args) {
        var evt = self.eventType(type, target);
        for (var key in args) {
            evt[key] = args[key];
        }
        return evt;
    },


    /**
     * Get the platform-specific value for the specified mouse button
     * configuration.
     */
    function getButtonValue(self, left, middle, right) {
        if (left) {
            return 0;
        } else if (middle) {
            return 1;
        } else if (right) {
            return 2;
        }
    },


    /**
     * Assert that L{Nevow.Athena.MouseEvent.getMouseButtons} produces a mapping
     * that matches an expected mouse button configuration.
     */
    function assertMouseButtons(self, evt, left, middle, right) {
        var buttons = evt.getMouseButtons();
        self.assertIdentical(buttons.left, !!left);
        self.assertIdentical(buttons.middle, !!middle);
        self.assertIdentical(buttons.right, !!right);
    },


    /**
     * L{Nevow.Athena.MouseEvent.getMouseButtons} decodes the platform-specific
     * C{event.button} value into a mapping that expresses the mouse button
     * configuration.
     */
    function test_getMouseButtons(self) {
        function createEvent(left, middle, right) {
            return Nevow.Athena.Event.fromDOMEvent(
                self.createDOMEvent('mouseup', null, {
                    'button': self.getButtonValue(left, middle, right)}));
        }

        self.assertMouseButtons(
            createEvent(true, false, false),
            true, false, false);
        self.assertMouseButtons(
            createEvent(false, true, false),
            false, true, false);
        self.assertMouseButtons(
            createEvent(false, false, true),
            false, false, true);
    },


    /**
     * L{Nevow.Athena.MouseEvent.getPagePosition} gets the coordinates of the
     * event relative to the whole document.
     */
    function test_getPagePosition(self) {
        var evt = Nevow.Athena.Event.fromDOMEvent(
            self.createDOMEvent('mouseup', null, {
                'pageX': 51,
                'pageY': 44}));
        var pt = evt.getPagePosition();
        self.assertIdentical(pt.x, 51);
        self.assertIdentical(pt.y, 44);
    },


    /**
     * L{Nevow.Athena.MouseEvent.getClientPosition} gets the coordinates of the
     * event within the browse's client area.
     */
    function test_getClientPosition(self) {
        var evt = Nevow.Athena.Event.fromDOMEvent(
            self.createDOMEvent('mouseup', null, {
                'clientX': 51,
                'clientY': 44}));
        var pt = evt.getClientPosition();
        self.assertIdentical(pt.x, 51);
        self.assertIdentical(pt.y, 44);
    },


    /**
     * L{Nevow.Athena.MouseEvent.getScreenPosition} gets the coordinates of the
     * event within the screen as a whole.
     */
    function test_getScreenPosition(self) {
        var evt = Nevow.Athena.Event.fromDOMEvent(
            self.createDOMEvent('mouseup', null, {
                'screenX': 51,
                'screenY': 44}));
        var pt = evt.getScreenPosition();
        self.assertIdentical(pt.x, 51);
        self.assertIdentical(pt.y, 44);
    });



/**
 * Tests for L{Nevow.Athena.MouseEvent} when using IE-style event objects.
 */
Nevow.Test.TestEvent.TestMouseEventW3C.subclass(
        Nevow.Test.TestEvent,
        'TestMouseEventIE').methods(
    function setUp(self) {
        self.eventType = Nevow.Test.TestEvent.IEEvent;
        self.oldRuntime = Divmod.Runtime.theRuntime;
        Divmod.Runtime.theRuntime = Divmod.Runtime.InternetExplorer();
    },


    function tearDown(self) {
        Divmod.Runtime.theRuntime = self.oldRuntime;
    },


    /**
     * Get the platform-specific value for the specified mouse button
     * configuration.
     */
    function getButtonValue(self, left, middle, right) {
        var button = 0;
        if (left) {
            button |= 1;
        }
        if (middle) {
            button |= 4;
        }
        if (right) {
            button |= 2;
        }
        return button;
    },


    /**
     * Internet Explorer can express configurations where multiple mouse
     * buttons are pushed.
     */
    function test_getMouseButtonsMultiple(self) {
        function createEvent(left, middle, right) {
            return Nevow.Athena.Event.fromDOMEvent(
                self.createDOMEvent('mouseup', null, {
                    'button': self.getButtonValue(left, middle, right)}));
        }

        self.assertMouseButtons(
            createEvent(true, true, false),
            true, true, false);
        self.assertMouseButtons(
            createEvent(false, true, true),
            false, true, true);
        self.assertMouseButtons(
            createEvent(true, true, true),
            true, true, true);
    },


    /**
     * L{Nevow.Athena.MouseEvent.getPagePosition} gets the coordinates of the
     * event relative to the whole document. In Internet Explorer < 9 there are
     * no C{'pageX'} or C{'pageY'} attributes instead a page position is
     * derived from client position and the document and body scroll offsets.
     */
    function test_getPagePosition(self) {
        var evt = Nevow.Athena.Event.fromDOMEvent(
            self.createDOMEvent('mouseup', null, {
                'clientX': 41,
                'clientY': 34}));
        document.documentElement = {
            'scrollLeft': 4,
            'scrollTop': 6};
        document.body.scrollLeft = 6;
        document.body.scrollTop = 4;

        var pt = evt.getPagePosition();
        self.assertIdentical(pt.x, 51);
        self.assertIdentical(pt.y, 44);
    });
