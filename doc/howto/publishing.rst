Object Publishing
=================

In :doc:`traversal`, we learned about the
``nevow.inevow.IResource.renderHTTP`` method, which is the most basic
way to send HTML to a browser when using Nevow. However, it is not very
convenient (or clean) to generate HTML tags by concatenating strings in
Python code. In the :doc:`deployment` documentation, we
saw that it was possible to render a *Hello World* page using a
``nevow.rend.Page`` subclass and providing a ``docFactory``:

.. code-block:: python

    >>> from nevow import rend, loaders
    >>> class HelloWorld(rend.Page):
    ...     docFactory = loaders.stan("Hello, world!")
    ...
    >>> HelloWorld().renderSynchronously()
    'Hello, world!'

This example does nothing interesting, but the concept of a loader is
important in Nevow. The ``rend.Page.renderHTTP`` implementation always
starts rendering HTML by loading a template from the ``docFactory``.

The stan DOM
------------

Nevow uses a DOM-based approach to rendering HTML. A tree of objects is
first constructed in memory by the template loader. This tree is then
processed one node at a time, applying functions which transform from
various Python types to HTML strings.

Nevow uses a nonstandard DOM named "stan". Unlike the W3C DOM, stan is
made up of simple python lists, strings, and instances of the
nevow.stan.Tag class. During the rendering process, "Flattener"
functions convert from rich types to HTML strings. For example, we can
load a template made up of some nested lists and Python types, render
it, and see what happens:

.. code-block:: python

    >>> class PythonTypes(rend.Page):
    ...     docFactory = loaders.stan(["Hello", 1, 1.5, True, ["Goodbye", 3]])
    ...
    >>> PythonTypes().renderSynchronously()
    'Hello11.5TrueGoodbye3'

Tag instances
-------------

So far, we have only rendered simple strings as output. However, the
main purpose of Nevow is HTML generation. In the stan DOM, HTML tags are
represented by instances of the ``nevow.stan.Tag`` class. ``Tag`` is a
very simple class, whose instances have an ``attributes`` dictionary and
a ``children`` list. The ``Tag`` flattener knows how to recursively
flatten attributes and children of the tag. To show you how ``Tag``\ s
really work before you layer Nevow's convenience syntax on top, try this
horrible example:

.. code-block:: python

    >>> from nevow import stan
    >>> h = stan.Tag('html')
    >>> d = stan.Tag('div')
    >>> d.attributes['style'] = 'border: 1px solid black'
    >>> h.children.append(d)
    >>> class Tags(rend.Page):
    ...     docFactory = loaders.stan(h)
    ...
    >>> Tags().renderSynchronously()
    '<html><div style="border: 1px solid black"></div></html>'

So, we see how it is possible to programatically generate HTML by
constructing and nesting stan ``Tag`` instances. However, it is far more
convenient to use the overloaded operators ``Tag`` provides to
manipulate them. ``Tag`` implements a ``__call__`` method which takes
any keyword arguments and values and updates the attributes dictionary;
it also implements a ``__getitem__`` method which takes whatever is
between the square brackets and appends them to the children list. A
simple example should clarify things:

.. code-block:: python

    >>> class Tags2(rend.Page):
    ...     docFactory = loaders.stan(stan.Tag('html')[stan.Tag('div')(style="border: 1px solid black")])
    ...
    >>> Tags2().renderSynchronously()
    '<html><div style="border: 1px solid black"></div></html>'

This isn't very easy to read, but luckily we can simplify the example
even further by using the nevow.tags module, which is full of "Tag
prototypes" for every tag type described by the XHTML 1.0 specification:

.. code-block:: python

    >>> class Tags3(rend.Page):
    ...     docFactory = loaders.stan(tags.html[tags.div(style="border: 1px solid black")])
    ...
    >>> Tags3().renderSynchronously()
    '<html><div style="border: 1px solid black"></div></html>'

Using stan syntax is not the only way to construct template DOM for use
by the Nevow rendering process. Nevow also includes ``loaders.xmlfile``
which implements a simple tag attribute language similar to the Zope
Page Templates (ZPT) Tag Attribute Language (TAL). However, experience
with the stan DOM should give you insight into how the Nevow rendering
process really works. Rendering a template into HTML in Nevow is really
nothing more than iterating a tree of objects and recursively applying
"Flattener" functions to objects in this tree, until all HTML has been
generated.

Functions in the DOM
--------------------

So far, all of our examples have generated static HTML pages, which is
not terribly interesting when discussing dynamic web applications. Nevow
takes a very simple approach to dynamic HTML generation. If you put a
Python function reference in the DOM, Nevow will call it when the page
is rendered. The return value of the function replaces the function
itself in the DOM, and the results are flattened further. This makes it
easy to express looping and branching structures in Nevow, because
normal Python looping and branching constructs are used to do the job:

.. code-block:: python

    >>> def repeat(ctx, data):
    ...     return [tags.div(style="color: %s" % (color, ))
    ...         for color in ['red', 'blue', 'green']]
    ...
    >>> class Repeat(rend.Page):
    ...     docFactory = loaders.stan(tags.html[repeat])
    ...
    >>> Repeat().renderSynchronously()
    '<html><div style="color: red"></div><div style="color: blue"></div><div style="color: green"></div></html>'

However, in the example above, the repeat function isn't even necessary,
because we could have inlined the list comprehension right where we
placed the function reference in the DOM. Things only really become
interesting when we begin writing parameterized render functions which
cause templates to render differently depending on the input to the web
application.

The required signature of functions which we can place in the DOM is
(ctx, data). The "context" object is essentially opaque for now, and we
will learn how to extract useful information out of it later. The "data"
object is anything we want it to be, and can change during the rendering
of the page. By default, the data object is whatever we pass as the
first argument to the Page constructor, *or* the Page instance itself if
nothing is passed. Armed with this knowledge, we can create a Page which
renders differently depending on the data we pass to the Page
constructor:

.. code-block:: python

    class Root(rend.Page):
        docFactory = loaders.stan(tags.html[
            tags.h1["Welcome."],
            tags.a(href="foo")["Foo"],
            tags.a(href="bar")["Bar"],
            tags.a(href="baz")["Baz"]])

        def childFactory(self, ctx, name):
            return Leaf(name)

    def greet(ctx, name):
        return "Hello. You are visiting the ", name, " page."

    class Leaf(rend.Page):
        docFactory = loaders.stan(tags.html[greet])


Armed with this knowledge and the information in the :doc:`traversal`
documentation, we now have enough information to create dynamic websites with
arbitrary URL hierarchies whose pages render dynamically depending on which URL
was used to access them.

Accessing query parameters and form post data
---------------------------------------------

Before we move on to more advanced rendering techniques, let us first
examine how one could further customize the rendering of a Page based on
the URL query parameters and form post information provided to us by a
browser. Recall that URL parameters are expressed in the form:

::

    http://example.com/foo/bar?baz=1&quux=2

And form post data can be generated by providing a form to a browser:

.. code-block:: html

    <form action="" method="POST">
      <input type="text" name="baz" />
      <input type="text" name="quux" />
      <input type="submit" />
    </form>

Accessing this information is such a common procedure that Nevow
provides a convenience method on the context to do it. Let's examine a
simple page whose output can be influenced by the query parameters in
the URL used to access it:

.. code-block:: python

    def showChoice(ctx, data):
        choice = ctx.arg('choice')
        if choice is None:
            return ''
        return "You chose ", choice, "."

    class Custom(rend.Page):
        docFactory = loaders.stan(tags.html[
            tags.a(href="?choice=baz")["Baz"],
            tags.a(href="?choice=quux")["Quux"],
            tags.p[showChoice]])


The procedure is exactly the same for simple form post information:

.. code-block:: python

    def greet(ctx, data):
        name = ctx.arg('name')
        if name is None:
            return ''
        return "Greetings, ", name, "!"

    class Form(rend.Page):
        docFactory = loaders.stan(tags.html[
            tags.form(action="", method="POST")[
                tags.input(name="name"),
                tags.input(type="submit")],
            greet])

Note that ``ctx.arg`` returns only the first argument with the given
name. For complex cases where multiple arguments and lists of argument
values are required, you can access the request argument dictionary
directly using the syntax:

.. code-block:: python

    def arguments(ctx, data):
        args = inevow.IRequest(ctx).args
        return "Request arguments are: ", str(args)


Generators in the DOM
---------------------

One common operation when building dynamic pages is iterating a list of
data and emitting some HTML for each item. Python generators are well
suited for expressing this sort of logic, and code which is written as a
python generator can perform tests (``if``) and loops of various kinds
(``while``, ``for``) and emit a row of html whenever it has enough data
to do so. Nevow can handle generators in the DOM just as gracefully as
it can handle anything else:

.. code-block:: python

    >>> from nevow import rend, loaders, tags
    >>> def generate(ctx, items):
    ...     for item in items:
    ...         yield tags.div[ item ]
    ...
    >>> class List(rend.Page):
    ...     docFactory = loaders.stan(tags.html[ generate ])
    ...
    >>> List(['one', 'two', 'three']).renderSynchronously()
    '<html><div>one</div><div>two</div><div>three</div></html>'

As you can see, generating HTML inside of functions or generators can be
very convenient, and can lead to very rapid application development.
However, it is also what I would call a "template abstraction
violation", and we will learn how we can keep knowledge of HTML out of
our python code when we learn about patterns and slots.

Methods in the DOM
------------------

Up until now, we have been placing our template manipulation logic
inside of simple Python functions and generators. However, it is often
appropriate to use a method instead of a function. Nevow makes it just
as easy to use a method to render HTML:

.. code-block:: python

    class MethodRender(rend.Page):
        def __init__(self, foo):
            self.foo = foo

        def render_foo(self, ctx, data):
            return self.foo

        docFactory = loaders.stan(tags.html[ render_foo ])


Using render methods makes it possible to parameterize your Page class
with more parameters. With render methods, you can also use the Page
instance as a state machine to keep track of the state of the render.
While Nevow is designed to allow you to render the same Page instance
repeatedly, it can also be convenient to know that a Page instance will
only be used one time, and that the Page instance can be used as a
scratch pad to manage information about the render.

Data specials
-------------

Previously we saw how passing a parameter to the default Page
constructor makes it available as the "data" parameter to all of our
render methods. This "data" parameter can change as the page render
proceeds, and is a useful way to ensure that render functions are
isolated and only act upon the data which is available to them. Render
functions which do not pull information from sources other than the
"data" parameter are more easily reusable and can be composed into
larger parts more easily.

Deciding which data gets passed as the data parameter is as simple as
changing the "Data special" for a Tag. See the
:doc:`glossary` under "Tag Specials" for more information
about specials. Assigning to the data special is as simple as assigning
to a tag attribute:

.. code-block:: python

    >>> def hello(ctx, name):
    ...     return "Hello, ", name
    ...
    >>> class DataSpecial(rend.Page):
    ...     docFactory = loaders.stan(tags.html[
    ...     tags.div(data="foo")[ hello ],
    ...     tags.div(data="bar")[ hello ]])
    ...
    >>> DataSpecial().renderSynchronously()
    '<html><div>Hello, foo</div><div>Hello, bar</div></html>'

Data specials may be assigned any python value. Data specials are only
in scope during the rendering of the tag they are assigned to, so if the
"hello" renderer were placed in the DOM inside the html node directly,
"Hello, None" would be output.

Before data is passed to a render function, Nevow first checks to see if
there is an ``IGettable`` adapter for it. If there is, it calls
``IGettable.get()``, and passes the result of this as the data parameter
instead. Nevow includes an ``IGettable`` adapter for python functions,
which means you can set a Tag data special to a function reference and
Nevow will call it to obtain the data when the Tag is rendered. The
signature for data methods is similar to that of render methods, (ctx,
data). For example:

.. code-block:: python

    def getName(ctx, data):
        return ctx.arg('name')

    def greet(ctx, name):
        return "Greetings, ", name

    class GreetName(rend.Page):
        docFactory = loaders.stan(tags.html[
            tags.form(action="")[
                tags.input(name="name"),
                tags.input(type="submit")],
                tags.div(data=getName)[ greet ]])


Data specials exist mainly to allow you to construct and enforce a
Model-View- Controller style separation of the Model code from the View.
Here we see that the greet function is capable of rendering a greeting
view for a name model, and that the implementation of getName may change
without the view code changing.

Render specials
---------------

Previously, we have seen how render functions can be placed directly in
the DOM, and the return value replaces the render function in the DOM.
However, these free functions and methods are devoid of any contextual
information about the template they are living in. The render special is
a way to associate a render function or method with a particular Tag
instance, which the render function can then examine to decide how to
render:

.. code-block:: python

    >>> def alignment(ctx, data):
    ...     align = ctx.tag.attributes.get('align')
    ...     if align == 'right':
    ...         return ctx.tag["Aligned right"]
    ...     elif align == 'center':
    ...         return ctx.tag["Aligned center"]
    ...     else:
    ...         return ctx.tag["Aligned left"]
    ...
    >>> class AlignmentPage(rend.Page):
    ...     docFactory = loaders.stan(tags.html[
    ...     tags.p(render=alignment),
    ...     tags.p(render=alignment, align="center"),
    ...     tags.p(render=alignment, align="right")])
    ...
    >>> AlignmentPage().renderSynchronously()
    '<html><p>Aligned left</p><p align="center">Aligned center</p><p align="right">Aligned right</p></html>'

Note how the alignment renderer has access to the template node as
``ctx.tag``. It can examine and change this node, and the return value
of the render function replaces the original node in the DOM. Note that
here we are returning the template node after changing it. We will see
later how we can instead mutate the context and use slots so that the
knowledge the renderer requires about the structure of the template is
reduced even more.

Pattern specials
----------------

When writing render methods, it is easy to inline the construction of
Tag instances to generate HTML programatically. However, this creates a
template abstraction violation, where part of the HTML which will show
up in the final page output is hidden away inside of render methods
instead of inside the template. Pattern specials are designed to avoid
this problem. A node which has been tagged with a pattern special can
then be located and copied by a render method. The render method does
not need to know anything about the structure or location of the
pattern, only it's name.

We can rewrite our previous generator example so that the generator does
not have to know what type of tag the template designer would like
repeated for each item in the list:

.. code-block:: python

    >>> from nevow import rend, loaders, tags, inevow
    >>> def generate(ctx, items):
    ...     pat = inevow.IQ(ctx).patternGenerator('item')
    ...     for item in items:
    ...         ctx.tag[ pat(data=item) ]
    ...     return ctx.tag
    ...
    >>> def string(ctx, item):
    ...     return ctx.tag[ str(item) ]
    ...
    >>> class List(rend.Page):
    ...     docFactory = loaders.stan(tags.html[
    ...     tags.ul(render=generate)[
    ...         tags.li(pattern="item", render=string)]])
    ...
    >>> List([1, 2, 3]).renderSynchronously()
    '<html><ol><li>1</li><li>2</li><li>3</li></ol></html>'

Note that we have to mutate the tag in place and repeatedly copy the
item pattern, applying the item as the data special to the resulting
Tag. It turns out that this is such a common operation that nevow comes
out of the box with these two render functions:

.. code-block:: python

    >>> class List(rend.Page):
    ...     docFactory = loaders.stan(tags.html[
    ...     tags.ul(render=rend.sequence)[
    ...         tags.li(pattern="item", render=rend.data)]])
    ...
    >>> List([1, 2, 3]).renderSynchronously()
    '<html><ul><li>1</li><li>2</li><li>3</li></ul></html>'

Slot specials
-------------

The problem with render methods is that they are only capable of making
changes to their direct children. Because of the architecture of Nevow,
they should not attempt to change grandchildren or parent nodes. It is
possible to write one render method for every node you wish to change,
but there is a better way. A node with a slot special can be "filled"
with content by any renderer above the slot. Creating a slot special is
such a frequent task that there is a prototype in ``nevow.tags`` which
is usually used.

Let us examine a renderer which fills a template with information about
a person:

.. code-block:: python

    >>> from nevow import loaders, rend, tags
    ...
    >>> person = ('Donovan', 'Preston', 'Male', 'California')
    ...
    >>> def render_person(ctx, person):
    ...     firstName, lastName, sex, location = person
    ...     ctx.fillSlots('firstName', firstName)
    ...     ctx.fillSlots('lastName', lastName)
    ...     ctx.fillSlots('sex', sex)
    ...     ctx.fillSlots('location', location)
    ...     return ctx.tag
    ...
    >>> class PersonPage(rend.Page):
    ...     docFactory = loaders.stan(tags.html(render=render_person)[
    ...     tags.table[
    ...         tags.tr[
    ...             tags.td[tags.slot('firstName')],
    ...             tags.td[tags.slot('lastName')],
    ...             tags.td[tags.slot('sex')],
    ...             tags.td[tags.slot('location')]]]])
    ...
    >>> PersonPage(person).renderSynchronously()
    '<html><table><tr><td>Donovan</td><td>Preston</td><td>Male</td><td>California</td></tr></table></html>'

Using patterns in combination with slots can lead to very powerful
template abstraction. Nevow also includes another standard renderer
called "mapping" which takes any data which responds to the "items()"
message and inserts the items into appropriate slots:

.. code-block:: python

    >>> class DictPage(rend.Page):
    ...     docFactory = loaders.stan(tags.html(render=rend.mapping)[
    ...         tags.span[ tags.slot('foo') ], tags.span[ tags.slot('bar') ]])
    ...
    >>> DictPage(dict(foo=1, bar=2)).renderSynchronously()
    '<html><span>1</span><span>2</span></html>'

Data directives
---------------

So far, we have always placed data functions directly in the Data
special attribute of a Tag. Sometimes, it is preferable to look up a
data method from the Page class as the Page has being rendered. For
example, a base class may define a template and a subclass may provide
the implementation of the data method. We can accomplish this effect by
using a data directive as a Tag's data special:

.. code-block:: python

    class Base(rend.Page):
        docFactory = loaders.stan(tags.html[
            tags.div(data=tags.directive('name'), render=rend.data)])

    class Subclass(Base):
        def data_name(self, ctx, data):
            return "Your name"


The data directive is resolved by searching for the ``IContainer``
implementation in the context. ``rend.Page`` implements
``IContainer.get`` by performing an attribute lookup on the Page with
the prefix 'data\_\*'. You can provide your own ``IContainer``
implementation if you wish, and also you should know that ``IContainer``
implementations for list and dict are included in the
``nevow.accessors`` module.

A common gotcha is that the closest ``IContainer`` is used to resolve
data directives. This means that if a list is being used as the data
during the rendering process, data directives below this will be
resolved against the ``IContainer`` implementation in
``nevow.accessors.ListAccessor``. If you are expecting a data directive
to invoke a Page's data\_\* method but instead get a ``KeyError``, this
is why.

Render directives
-----------------

Render directives are almost exactly the same, except they are resolved
using the closest ``IRendererFactory`` implementation in the context.
Render directives can be used to allow subclasses to override certain
render methods, and also can be used to allow Fragments to locate their
own prefixed render methods.

Flatteners
----------

.. warning:: TODO: This section isn't done yet.

Nevow's flatteners use a type/function registry to determine how to
render objects which Nevow encounters in the DOM during the rendering
process. "Explicit is better than implicit", so in most cases,
explicitly applying render methods to data will be better than
registering a flattener, but in some cases it can be useful:

.. code-block:: python

    class Person(object):
        def __init__(self, firstName, lastName):
            self.firstName = firstName
            self.lastName = lastName

    def flattenPerson(person, ctx):
        return flat.partialflatten(ctx, (person.firstName, " ", person.lastName))

    from nevow import flat
    flat.registerFlattener(flattenPerson, Person)

    def insertData(ctx, data):
        return data

    class PersonPage(rend.Page):
        docFactory = loaders.stan(tags.html[insertData])
