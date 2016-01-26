Object Traversal
================

**Object traversal** is the process Nevow uses to determine what object
to use to render HTML for a particular URL. When an HTTP request comes
in to the web server, the object publisher splits the URL into segments,
and repeatedly calls methods which consume path segments and return
objects which represent that path, until all segments have been
consumed. At the core, the Nevow traversal API is very simple. However,
it provides some higher level functionality layered on top of this to
satisfy common use cases.

Object Traversal Basics
-----------------------

The **root resource** is the top-level object in the URL space; it
conceptually represents the URI ``/``. The Nevow **object traversal**
and **object publishing** machinery uses only two methods to locate an
object suitable for publishing and to generate the HTML from it; these
methods are described in the interface ``nevow.inevow.IResource``:

.. code-block:: python

    class IResource(Interface):
        def locateChild(self, ctx, segments):
            """Locate another object which can be adapted to IResource
            Return a tuple of resource, path segments
            """

        def renderHTTP(self, ctx):
            """Render a request
            """


``renderHTTP`` can be as simple as a method which simply returns a
string of HTML. Let's examine what happens when object traversal occurs
over a very simple root resource:

.. code-block:: python

    from zope.interface import implements

    class SimpleRoot(object):
        implements(inevow.IResource)

        def locateChild(self, ctx, segments):
            return self, ()

        def renderHTTP(self, ctx):
            return "Hello, world!"


This resource, when passed as the root resource to ``appserver.NevowSite``,
will immediately return itself, consuming all path segments. This means that
for every URI a user visits on a web server which is serving this root
resource, the text ``"Hello, world!"`` will be rendered. Let's examine the
value of ``segments`` for various values of URI:

-  ``/`` - ``('',)``
-  ``/foo/bar`` - ``('foo', 'bar')``
-  ``/foo/bar/baz.html`` - ``('foo', 'bar', 'baz.html')``
-  ``/foo/bar/directory/`` - ``('foo', 'bar', 'directory', '')``

So we see that Nevow does nothing more than split the URI on the string
``/`` and pass these path segments to our application for consumption.
Armed with these two methods alone, we already have enough information
to write applications which service any form of URL imaginable in any
way we wish. However, there are some common URL handling patterns which
Nevow provides higher level support for.

``locateChild`` In Depth
------------------------

One common URL handling pattern involves parents which only know about
their direct children. For example, a ``Directory`` object may only know
about the contents of a single directory, but if it contains other
directories, it does not know about the contents of them. Let's examine
a simple ``Directory`` object which can provide directory listings and
serves up objects for child directories and files:

.. code-block:: python

    from zope.interface import implements

    class Directory(object):
        implements(inevow.IResource)

        def __init__(self, directory):
            self.directory = directory

        def renderHTTP(self, ctx):
            html = ['<ul>']
            for child in os.listdir(self.directory):
                fullpath = os.path.join(self.directory, child)
                if os.path.isdir(fullpath):
                    child += '/'
                html.extend(['<li><a href="', child, '">', child, '</a></li>'])
            html.append('</ul>')
            return ''.join(html)

        def locateChild(self, ctx, segments):
            name = segments[0]
            fullpath = os.path.join(self.directory, name)
            if not os.path.exists(fullpath):
                return None, () # 404

            if os.path.isdir(fullpath):
                return Directory(fullpath), segments[1:]
            if os.path.isfile(fullpath):
                return static.File(fullpath), segments[1:]


Because this implementation of ``locateChild`` only consumed one segment
and returned the rest of them (``segments[1:]``), the object traversal
process will continue by calling ``locateChild`` on the returned
resource and passing the partially-consumed segments. In this way, a
directory structure of any depth can be traversed, and directory
listings or file contents can be rendered for any existing directories
and files.

So, let us examine what happens when the URI ``"/foo/bar/baz.html"`` is
traversed, where ``"foo"`` and ``"bar"`` are directories, and
``"baz.html"`` is a file.

1. ``Directory('/').locateChild(ctx, ('foo', 'bar', 'baz.html'))``
   returns ``Directory('/foo'), ('bar', 'baz.html')``
2. ``Directory('/foo').locateChild(ctx, ('bar', 'baz.html'))`` returns
   ``Directory('/foo/bar'), ('baz.html, )``
3. ``Directory('/foo/bar').locateChild(ctx, ('baz.html'))`` returns
   ``File('/foo/bar/baz.html'), ()``
4. No more segments to be consumed;
   ``File('/foo/bar/baz.html').renderHTTP(ctx)`` is called, and the
   result is sent to the browser.

``childFactory`` Method
-----------------------

Consuming one URI segment at a time by checking to see if a requested
resource exists and returning a new object is a very common pattern.
Nevow's default implementation of ``IResource``, ``nevow.rend.Page``,
contains an implementation of ``locateChild`` which provides more
convenient hooks for implementing object traversal. One of these hooks
is ``childFactory``. Let us imagine for the sake of example that we
wished to render a tree of dictionaries. Our data structure might look
something like this:

.. code-block:: python

    tree = dict(
        one=dict(
            foo=None,
            bar=None),
        two=dict(
            baz=dict(
            quux=None)))


Given this data structure, the valid URIs would be:

- ``/``
- ``/one``
- ``/one/foo``
- ``/one/bar``
- ``/two``
- ``/two/baz``
- ``/two/baz/quux``

Let us construct a ``rend.Page`` subclass which uses the default
``locateChild`` implementation and overrides the ``childFactory`` hook
instead:

.. code-block:: python

    class DictTree(rend.Page):
        def __init__(self, dataDict):
            self.dataDict = dataDict

        def renderHTTP(self, ctx):
            if self.dataDict is None:
                return "Leaf"
            html = ['<ul>']
            for key in self.dataDict.keys():
                html.extend(['<li><a href="', key, '">', key, '</a></li>'])
            html.append('</ul>')
            return ''.join(html)

        def childFactory(self, ctx, name):
            if name not in self.dataDict:
                return rend.NotFound # 404
            return DictTree(self.dataDict[name])


As you can see, the ``childFactory`` implementation is considerably
shorter than the equivalent ``locateChild`` implementation would have
been.

``child_*`` methods and attributes
----------------------------------

Often we may wish to have some hardcoded URLs which are not dynamically
generated based on some data structure. For example, we might have an
application which uses an external CSS stylesheet, an external
JavaScript file, and a folder full of images. The
``rend.Page.locateChild`` implementation provides a convenient way for
us to express these relationships by using child-prefixed methods:

::

    class Linker(rend.Page):
        def renderHTTP(self, ctx):
            return """<html>
    <head>
        <link href="css" rel="stylesheet" />
        <script type="text/javascript" src="scripts" />
      <body>
        <img src="images/logo.png" />
      </body>
    </html>"""

        def child_css(self, ctx):
            return static.File('styles.css')

        def child_scripts(self, ctx):
            return static.File('scripts.js')

        def child_images(self, ctx):
            return static.File('images/')


One thing you may have noticed is that all of the examples so far have
returned new object instances whenever they were implementing a
traversal API. However, there is no reason these instances cannot be
shared. One could for example return a global resource instance, an
instance which was previously inserted in a dict, or lazily create and
cache dynamic resource instances on the fly. The
``rend.Page.locateChild`` implementation also provides a convenient way
to express that one global resource instance should always be used for a
particular URL, the child-prefixed attribute:

::

    class FasterLinker(Linker):
        child_css = static.File('styles.css')
        child_scripts = static.File('scripts.js')
        child_images = static.File('images/')


Dots in child names
-------------------

When a URL contains dots, which is quite common in normal URLs, it is
simple enough to handle these URL segments in ``locateChild`` or
``childFactory`` -- one of the passed segments will simply be a string
containing a dot. However, it is not immediately obvious how one would
express a URL segment with a dot in it when using child-prefixed
methods. The solution is really quite simple:

::

    class DotChildren(rend.Page):
        def renderHTTP(self, ctx):
            return """
            <html>
              <head>
                <script type="text/javascript" src="scripts.js" />
              </head>
            </html>"""

    setattr(DotChildren, 'child_scripts.js', static.File('scripts.js'))


The same technique could be used to install a child method with a dot in
the name.

children dictionary
-------------------

The final hook supported by the default implementation of
``locateChild`` is the ``rend.Page.children`` dictionary:

::

    class Main(rend.Page):
        children = {
            'people': People(),
            'jobs': Jobs(),
            'events': Events()}

        def renderHTTP(self, ctx):
            return """
            <html>
              <head>
                <title>Our Site</title>
              </head>
              <body>
                <p>bla bla bla</p>
              </body>
            </html>"""


Hooks are checked in the following order:

1. ``self.children``
2. ``self.child_*``
3. ``self.childFactory``

The default trailing slash handler
----------------------------------

When a URI which is being handled ends in a slash, such as when the
``/`` URI is being rendered or when a directory-like URI is being
rendered, the string ``''`` appears in the path segments which will be
traversed. Again, handling this case is trivial inside either
``locateChild`` or ``childFactory``, but it may not be immediately
obvious what child-prefixed method or attribute will be looked up. The
method or attribute name which will be used is simply ``child`` with a
single trailing underscore.

The ``rend.Page`` class provides an implementation of this method which
can work in two different ways. If the attribute ``addSlash`` is
``True``, the default trailing slash handler will return ``self``. In
the case when ``addSlash`` is ``True``, the default
``rend.Page.renderHTTP`` implementation will simply perform a redirect
which adds the missing slash to the URL.

The default trailing slash handler also returns self if ``addSlash`` is
``False``, but emits a warning as it does so. This warning may become an
exception at some point in the future.

``ICurrentSegments`` and ``IRemainingSegments``
-----------------------------------------------

During the object traversal process, it may be useful to discover which
segments have already been handled and which segments are remaining to
be handled. This information may be obtained from the ``context`` object
which is passed to all the traversal APIs. The interfaces
``nevow.inevow.ICurrentSegments`` and
``nevow.inevow.IRemainingSegments`` are used to retrieve this
information. To retrieve a tuple of segments which have previously been
consumed during object traversal, use this syntax:

::

    segs = ICurrentSegments(ctx)


The same is true of ``IRemainingSegments``. ``IRemainingSegments`` is
the same value which is passed as ``segments`` to ``locateChild``, but
may also be useful in the implementations of ``childFactory`` or a
child-prefixed method, where this information would not otherwise be
available.

Conclusion
----------

Nevow makes it easy to handle complex URL hierarchies. The most basic
object traversal interface, ``nevow.inevow.IResource.locateChild``,
provides powerful and flexible control over the entire object traversal
process. Nevow's canonical ``IResource`` implementation, ``rend.Page``,
also includes the convenience hooks ``childFactory`` along with
child-prefixed method and attribute semantics to simplify common use
cases.
