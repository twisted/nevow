Nevow 0.14.3 (2017-07-26)
=========================

Bugfixes
--------

- Athena will now time requests out client-side rather than waiting forever (up
  to the browser timeout, at least) for a server response that may never come.
  (#98)


Misc
----

- #96


Nevow 0.14.2 (2016-08-29)
=========================

Re-release of 0.14.2 due to a release engineering mistake.

No changes other than the version number.


Nevow 0.14.1 (2016-08-29)
=========================

Features
--------

- Nevow will now correctly map the MIME type of SVG files even if the
  platform registry does not have such a mapping. (#88)
- Athena no longer logs widget instantiation on initial page load.
  (#92)

Bugfixes
--------

- Nevow's test suite is now compatible with Twisted 16.3. (#82)
- Athena will no longer cause spurious errors resulting from page
  disconnection. (#84)
- Athena will now ignore responses to already-responded remote calls
  during page shutdown. (#86)

Improved Documentation
----------------------

- Nevow's NEWS file is now generated from news fragments by towncrier.
  (#81)


0.14.0 (2016-05-08):
  - Fixed compatibility with Twisted 16.1.
  - nevow.page rendering speed was increased by about 7% on CPython (2.7.11)
    and 58% on PyPy (5.0.1).

0.13.0 (2016-02-16):
  - nevow.appserver.Request.headers and received_headers are now deprecated to
    follow suit with Twisted; older versions of Nevow will not be compatible
    with Twisted 16.0.0 due to these being removed in Twisted.
  - nevow.testutil.FakeRequest had similar changes made to assist with
    compatibility in test code, and there should be no Nevow code left that
    touches the deprecated APIs, but any application code using the old APIs
    should be migrated.
  - Some very ancient, deprecated things were removed: nevow.canvas,
    nevow.livepage, nevow.livetest, nevow.taglibrary (except for the Athena
    version of nevow.taglibrary.tabbedPane), nevow.wsgi, and zomne.

0.12.0 (2015-12-16):
  - Responses are no longer finished if the connection went away, avoiding an
    error message that this used to cause.
  - Detach all children on detach (previously only every other child was
    detached due to a bug).
  - The documentation is now in Sphinx format instead of Lore format.
  - Nevow templates now have attributes serialized in a stable order (the
    ordering is lexicographic).
  - The Athena runtime now works on Internet Explorer versions higher than 7.
  - Athena can now handle messages containing `undefined` (this deserializes to
    `None`, same as `null`; previously an error would occur).
  - Athena no longer logs about receiving duplicate messages (there is nothing
    the user / developer can do about these, so the log message didn't serve
    any purpose other than flooding your logs).
  - connectionMade on Athena widgets is now always invoked before any remote
    calls are handled (previously some remote calls might be handled before
    connectionMade was invoked).

0.11.1 (2014-06-21):
  - The athena-widget twistd plugin is now distributed in the wheel package.

0.11.0 (2014-06-20):
  - nevow.json now always emits escaped forms of U+2028 and U+2029.
  - formless now works with recent versions of zope.interface without
    triggering warnings.
  - Several problems in the test suite which resulted in failing tests when
    using recent versions of Twisted are now fixed.
  - The JavaScript API Divmod.UnitTest.TestCase.assertThrows now accepts
    variable arguments to be passed on to the API under test.
  - Nevow now unconditionally depends on setuptools for packaging.
  - Nevow now uses python-versioneer for version management.
  - Nevow now requires Twisted 13.0 or newer.
  - The dangerous testing helper module nevow.test.segfault has been removed.
  - Nevow is now hosted on Github: https://github.com/twisted/nevow
  - Nevow now uses travis-ci for continuous integration:
    https://travis-ci.org/twisted/nevow

0.10.0 (2009-11-25):
  - Added a system for CSS dependency declarations similar to the one in
    Athena for JavaScript.
  - Fix Athena's transport cleanup on page unload in Internet Explorer.
  - Fix nit's results coloring in Internet Explorer.
  - Added an API for declaring JavaScript classes which involves less
    repetition than the existing Divmod.Class.subclass API.
  - Added human-readable formatting for the new flattener's error reporting;
    rendering error stacks will now display lines from Python code as well
    as stan and XML templates.
  - Override the setuptools sdist command with the original distutils sdist
    command to avoid setuptools' version number transformation.
  - Added support for default values for slots in XML templates.
  - Fixed a problem with setup.py which led to css files not being
    installed.
  - Removed the old Chatola example and replaced it with a link to the new
    chat example.
  - Sped up some of the JavaScript dependency calculations.

0.9.33 (2008-12-09):
  - Add error handling to the integration between the old flattener
    and the new flattener so that if the new flattener fails with an
    exception or a Failure the error is propagated properly to the old
    flattener which invoked it.
  - Changed nit so that it doesn't use private `twistd` APIs and
    instead just sets up a server and runs the reactor.  This makes
    nit work with all versions of Twisted supported by Nevow.
  - Changed Nevow's setup.py to use setuptools if setuptools is
    available.  This has the user-facing consequence of installing
    Nevow as an egg if setuptools is available at installation time
    and of making Nevow installable using the `easy_install´ tool.
  - TabbedPane naively set DOM attributes, making it unusable in
    Internet Explorer 6 and 7.  Introduced a reliable method for
    setting DOM node attributes, with name mangling, to address the
    issue.

0.9.32 (2008-08-12):
  - A resource wrapper for on-the-fly gzip compression has been added.
  - A twistd plugin, 'athena-widget', is now available for serving
    single Athena widgets.
  - Basic Athena support for Safari added.
  - Added file name, line number, and column number information to
    slots and tags parsed from XML files in order to make debugging
    template/renderer interactions simpler.
  - A context-free flattener has been added. Fragment and its
    subclasses are now deprecated in favor of Element.
  - Javascript classes derived from the tabbedpane class can now
    override how tab selection is handled.

0.9.31 (2008-02-06):
  - Fixed Guard's request parameter save/restore feature to not
    clobber request state after login succeeds when a session has
    already been negotiated.
  - Added a hook to nevow.guard.SessionWrapper which allows the
    domain parameter of the session cookie to be specified.

0.9.30 (2008-01-16):
  - Change DeferredSerializer so that it passes failures from the
    Deferred being serialized on to the Deferred returned by the
    flattening function.  Without this behavior, the Deferred
    returned by the flattening function is never fired when a
    Deferred which fails is serialized.

0.9.29 (2008-01-02):
  - Prevent NevowSite.handleSegment from raising IndexError in certain
    situations.
  - Deprecated wsgi and zomne modules.

0.9.28 (2007-12-10):
  - Added two APIs to Athena, one for creating the string used as the id
    attribute of the top node of a widget and one for creating the string
    used as the id attribute of a node which had an id attribute in the
    widget's template document.

0.9.27 (2007-11-27):
  - Unicode URLs now supported.

0.9.26 (2007-11-02):
  - url.URL.path now correctly escapes segments in the string it
    evaluates to.
  - inevow.IAthenaTransportable added, along with support for
    serialization of custom types for server-to-client Athena
    messages.
  - Global client-side behaviour is now customizable via a client
    PageWidget class.

0.9.25 (2007-10-16):
  - The Athena message queue implementation has been improved, fixing problems
    masked by bugs in Firebug/YSlow.

0.9.24 (2007-09-05):
  - ESC key no longer disconnects Athena connections.
  - Fixed a bug where URLs with quote characters will cause the Athena
     connection to be lost.
  - Fixed 'twistd athena-widget' to create a fresh widget instance for each
    hit.

0.9.23 (2007-08-01):
  - Fixed install script to include all JavaScript files.

0.9.22 (2007-07-06):
  - Mock DOM implementation for easier browser testing added.
  - JavaScript source files are now read using universal newlines mode.
  - athena.AutoJSPackage now excludes dotfiles.
  - url.URL now properly subclassable.
  - User-agent parsing added to Athena, to detect known-unsupported browsers.

0.9.21 (2007-06-06):
  - Debug logging messages from the reliable message delivery queue
    disabled.

0.9.20 (2007-05-24):
  - Athena now no longer holds more than one idle transport open to
    the browser.

0.9.19 (2007-04-27):
  - Changed the styling of the progressbar to work on IE6.
  - Athena.Widget.detach added, to allow widgets to cleanly be removed
    from a page.
  - Athena.Widget.callLater added, a wrapper around setTimeout and
    clearTimeout.
  - 'athena-widget' twistd command added, for starting a server which
    serves a single LiveFragment or LiveElement.

0.9.18 (2007-02-23):
  - Athena 'connection lost' notification now styleable via the
    'nevow-connection-lost' CSS class.
  - The 'runjstests' script has been removed, now that JS tests can be
    run with trial.

0.9.17 (2006-12-08):
  - More efficient JSON string parsing.
  - Give FakeRequests a default status code of OK.  Accept all of
    FakeRequest.__init__'s arguments in the __init__ of
    AccumulatingFakeRequest.

0.9.16 (2006-11-17):
  - Updated nit to work with Twisted trunk.
  - Athena module import caching has been fixed.

0.9.15 (2006-11-08):
  - Changed _LiveMixin rendering to be idempotent to support the case
    where a transport hiccup causes a LiveFragment or LiveElement to
    be sent to the browser multiple times.
  - Improvements to the tests.

0.9.14 (2006-10-31):
  - Support code for running non-browser javascript tests has been added.
  - Added a workaround for nodeById on widgets not yet added to the document in
    IE.
  - Athena will now invoke the nodeInserted method (if it exists) on a widget
    that it instantiates statically.
  - ID rewriting, similar to existing rewriting support for 'id' attributes,
    has been added in 'for' and 'headers' attributes of 'label' and 'td'/'th'
    elements, respectively.

0.9.13 (2006-10-21):
  - Adjust non-selected panes in tabbedpane to be further out of the viewport.
  - Convert to using the Javascript module plugin system for Nevow-provided
    modules.

0.9.12 (2006-10-17):
  - Added id rewriting for LiveElement and LiveFragment, such that id
    attributes in a widget template are rewritten so that they are unique to
    the widget instance. A client-side API, Nevow.Athena.Widget.nodeById(),
    is provided to allow location of these nodes.

0.9.11 (2006-10-10):
  - Fixed dynamic widget instantiation in IE.
  - Added support for correctly quoting the values of slots which are used as
    attributes.

0.9.10 (2006-10-05):
  - Minor update to nevow.testutil.

0.9.9 (2006-09-26):
  - Several nit changes, including the addition of the "check" method to
    Failure, and the addition of an "assertFailure" method.
  - The ability to pass Python exceptions to Javascript has been added to
    Athena.
  - Dynamic module import has been added for the cases where it is necessary
    to dynamically add a widget to an existing page.

0.9.8 (2009-09-20):
  - A bug in nit that caused it to fail if there were too many tests in a
    test case, and swallow failures in some cases, has been fixed.
  - Widgets can no longer be added to a page after render time using
    Divmod.Runtime.Platform.{set,append}NodeContent.  Instead, they must be
    added using Nevow.Athena.Widget.addChildWidgetFromWidgetInfo.

0.9.7 (2009-09-12):
  - Automatic Athena event handler registration is fixed for all supported browsers
    and is no longer document-sensitive (ie, it works inside tables now).
  - Nit has gained a new assertion method, assertIn.

0.9.6 (2008-08-30):
  - Fixed a bug in the IE implementation of the runtime.js node fetching
    functions.

0.9.5 (2006-08-22):
  - Instance attributes can now be exposed to Athena with nevow.utils.Expose
    and Expose.exposedMethodNames() no longer returns unexposed names.

0.9.4 (2006-08-14):
  - Added test method discovery to nit test cases, so multiple test methods
    may be put in a single test case.
  - use XPath for certain DOM traversals when available. This yields
    significant speedups on Opera.
  - Made Divmod.Runtime.Platform.getAttribute deal with IE attribute
    name-mangling properly.
  - Javascript logging is now done in Firebug 0.4 style rather than 0.3.
  - Some cases where Deferred-returning render methods raised
    exceptions or buried failures were fixed.
  - Removed MochiKit. The pieces Nevow depends on have been moved to
    Divmod.Base in nevow/base.js.
  - Various doc fixes.

0.9.3 (2006-07-17):
  - Page rendering now supports preprocessors.

0.9.2 (2006-07-08):
  - Fixes to the typeahead demo.
  - Elements are now automatically serialized by json, just like Fragments.

0.9.1 (2006-07-05):
  - Made nevow.athena.expose the mandatory means of publishing a method to
    the browser.  The allowedMethods dictionary will no longer be respected.
  - Added nevow.page.Element and nevow.athena.LiveElement: these are
    preferred over nevow.rend.Fragment and nevow.athena.LiveFragment for all
    new development.

0.9.0 (2006-06-12):
  - Fixed a bug where nested fragment sending rarely worked.
  - Sending large strings in Athena arguments and results is now faster due to
    less unnecessary unicode character quoting.
  - Module objects are now automatically created for all Athena imports.
  - Better error reporting for fragments which are rendered without a parent.
  - Disconnect notifiers in Athena pages will no longer clobber each other.
  - Many optimizations to javascript initialization.
  - Javascript packages are now defined with less boilerplate: a filesystem
    convention similar to Python's for module naming, plus one declaration in a
    Nevow plugin which indicates the directory, rather than a declaration for
    each module.
  - Updated README to refer to Athena rather than LivePage
