XML Templates
=============

Stan syntax is cool, but eventually you are going to want to integrate
your Python code with a template designed by an HTML monkey. Nevow
accomplishes this by providing an xmlfile loader which uses the built-in
Python SAX libraries to generate a tree of stan behind the scenes. The
general rule is anything that is possible in stan should be possible in
a pure XML template; of course, the XML syntax is generally going to be
much more verbose.

loaders.xmlfile
---------------

Wherever you have seen a loaders.stan being created in any of the
example code, a ``loaders.xmlfile`` can be substituted instead. At the
most basic, ``xmlfile`` merely requires the name of an xml template:

.. code-block:: python

    class HelloXML(rend.Page):
        docFactory = loaders.xmlfile('hello.xml')


Placing the following xml in the ``hello.xml`` file will cause
``HelloXML`` to display a static page when it is rendered:

.. code-block:: html

    <html>Hello, world!</html>

The following additional keyword arguments may be given to ``xmlfile``
to configure it:

-  ``templateDirectory``: The path to the directory which contains the
   template file. Defaults to ''.
-  ``ignoreDocType``: If True, discard any DOCTYPE declaration when
   building the DOM from this template. When false, preserve the
   DOCTYPE, causing it to show up in the final output. Useful for when
   you are inserting an XML fragment into a larger page and do not wish
   to generate invalid XML as output. Defaults to False.
-  ``ignoreComment``: If True, discard XML comments, causing them to
   disappear from the output. If False, preserve comments and render
   them in the final output unchanged. Defaults to False.
-  ``pattern``: If present, the given pattern name will be looked up and
   used as the root of the template. If not present, the entire document
   will be used as the template. Useful for embedding fragments of an
   XML document in a larger page. Defaults to None.

Nevow's xmlns declaration
-------------------------

In order for Nevow to notice and process any XML directives in the
template file, you must declare the Nevow xmlns at the top of your XML
document. Nevow's xmlns is:

::

    http://nevow.com/ns/nevow/0.1

The syntax for declaring that your xml document uses this namespace is:

.. code-block:: html

    <html xmlns:nevow="http://nevow.com/ns/nevow/0.1"></html>

You may replace the text "nevow" in the above example with any name you
choose. For example, many people use "n" because it is shorter to type.
If you do so, be sure to replace all occurrences of the nevow namespace
in the examples with the namespace name you choose.

Nevow's Tag Attribute Language
------------------------------

The markup you will add to your XHTML file in order to invoke Nevow code
consists mostly of namespaced tag attributes. This approach was
influenced heavily by the Zope Page Templates (ZPT) Tag Attribute
Language (TAL). However, I felt that TAL did not go far enough in
removing control flow and branching possibilities from the XML template.
Nevow's main philosophy is that it should be as easy as possible to move
from the XML document into Python code, and that the Python code should
have ultimate control over manipulating the structure of the XML
template.

The key is that it is easy to expose Python methods that you write to
your XML template, and it is easy for the XML templates to mark nodes
which it wishes the Python method to manipulate. In this way, if either
the Python implementation changes or the location or content of the
marked nodes change in the XML template, the other side will be isolated
from these changes.

Nevow's XML templating has two attributes which invoke Python code:

-  ``nevow:render`` -- Invokes a Python method and replaces the template
   node with the result
-  ``nevow:data`` -- Invokes a Python method and sets the data special
   for the node to the result

It has one attribute which marks nodes as manipulatable by Python code:

-  ``nevow:pattern`` -- Gives a node a name so that Python code may
   clone and mutate copies of this node

It also has two namespaced tags:

-  ``nevow:slot`` -- Works in the same way as the slot attribute
-  ``nevow:attr`` -- Indicates that an attribute of the parent tag
   should be manipulated by Python code in some way

nevow:render
------------

When the ``nevow:render`` attribute is encountered, the xmlfile loader
sets the render special to a directive constructed with the attribute
value. When the template is rendered, this means that the appropriate
render\_\* method will be looked up on the ``IRendererFactory``
(generally the Page instance):

.. code-block:: html

    <html><div nevow:render="foo" /></html>

With the ``render_foo`` method:

.. code-block:: python

    def render_foo(self, ctx, data):
        return "Hello"


Will result in the document:

.. code-block:: html

    <html>Hello</html>

Note that the return value of the render method replaces the template
node in the DOM, so if you want the template node to remain, you should
use ``ctx.tag``.

Built-in renderers
------------------

Nevow comes with various built in renderers on the Page class.

-  ``data``: Renders the current data as-is inside the current node.
-  ``string``: Renders the current data as a string inside the current
   node.
-  ``sequence``: Iterates the current data, copying the "item" pattern
   for each item. Sets the the data special of the new node to the item,
   and inserts the result in the current node. See the
   nevow.rend.sequence docstring for information about other used
   patterns, including "header", "divider", "footer" and "empty".
-  ``mapping``: Calls .items() on the current data, and calls
   ctx.fillSlots(key, value) for every key, value pair in the result.
   Returns the template tag.
-  ``xml``: Inserts the current data into the template after wrapping it
   in an xml instance. Not very useful in practice.

nevow:data
----------

When the ``nevow:data`` attribute is encountered, the xmlfile loader
sets the data special of the current node to a directive constructed
with the attribute value. When the template is rendered, this means that
the appropriate data\_\ * method will be looked up on the current
``IContainer`` (generally the Page instance). The data\_* method will be
called, and the result will be set as the data special of the current
Tag:

.. code-block:: html

    <html><div nevow:data="name" nevow:render="data" /></html>

With the ``data_name`` method:

.. code-block:: python

    def data_name(self, ctx, data):
        return "Hello!"


Will result in the document:

.. code-block:: html

    <html><div>Hello!</div></html>

Note that with a data attribute on a node but no renderer, the result of
the data method will be set as the data special for that tag, and child
render methods will be passed this data.

nevow:pattern
-------------

When the ``nevow:pattern`` attribute is encountered, the xmlfile loader
sets the pattern special of the current node to the attribute value as a
string. Renderers which are above this node may then make copies of it
using the ``nevow.inevow.IQ`` of the current context. With the template:

.. code-block:: html

    <html nevow:render="stuff"><div nevow:pattern="somePattern" nevow:render="data" /></html>

And the renderer:

.. code-block:: python

    def render_stuff(self, ctx, data):
        pat = inevow.IQ(ctx).patternGenerator('somePattern')
        return [pat(data=1), pat(data=2)]


Will result in the document:

.. code-block:: html

    <html><div>1</div><div>2</div></html>

nevow:slot
----------

When the ``nevow:slot`` tag is encountered, the xmlfile loader
constructs a ``nevow.stan.slot`` instance, passing the name attribute
value as the slot name. The children of the slot node are added as
children of the new slot instance. This is useful if you wish to put
patterns inside the slot. With the template:

.. code-block:: html

    <html nevow:render="stuff"><nevow:slot name="slotName" /></html>

And the render method:

.. code-block:: python

    def render_stuff(self, ctx, data):
        ctx.fillSlots('slotName', "Hello.")
        return ctx.tag


This document will be produced:

.. code-block:: html

    <html>Hello.</html>

nevow:attr
----------

When the ``nevow:attr`` tag is encountered, the contents of the
nevow:attr node will be assigned to the attribute of the parent tag with
the name of the value of the name attribute. Perhaps an example will be
a little clearer:

.. code-block:: html

    <html><a><nevow:attr name="href">HELLO!</nevow:attr>Goodbye</a></html>

This document will be produced:

.. code-block:: html

    <html><a href="HELLO!">Goodbye</a></html>

While this syntax is somewhat awkward, every other type of nevow tag and
attribute may be used inside the ``nevow:attr`` node. This makes setting
attributes of tags uniform with every other method of manipulating the
XML template.

nevow:invisible
---------------

Sometimes you need to group some elements, because you need to use a
renderer for a group of children.

However, it may not be desirable to give these elements a parent/child
relationship in your XML structure. For these cases, use
``nevow:invisible``.

As suggested by the name, a ``nevow:invisible`` tag is removed in the
rendered XML. Here is an example:

.. code-block:: html

    <html><nevow:invisible nevow:data="name" nevow:render="data" /></html>

With the ``data_name`` method:

.. code-block:: python

    def data_name(self, ctx, data):
        return "Hello!"


Will result in the document:

.. code-block:: html

    <html>Hello!</html>


xmlstr, htmlfile, and htmlstr
-----------------------------

xmlstr is a loader which is identical to xmlfile except it takes a
string of XML directly.

htmlfile and htmlstr should generally be avoided. They are similar to
xmlfile and xmlstr, except they use twisted.web.microdom in
beExtremelyLenient mode to attempt to parse badly-formed HTML
(non-XHTML) templates. See the nevow.loaders docstrings for more
information.

Conclusions
-----------

Nevow's xmlfile tag attribute language allows you to integrate
externally- designed XHTML templates into the Nevow rendering process.
