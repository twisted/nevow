============
Introduction
============

Summary
-------

Nevow is a next-generation web application templating system, based on
the ideas developed in the Twisted Woven package. Its main focus is on
separating the HTML template from both the business logic and the
display logic, while allowing the programmer to write pure Python code
as much as possible. It separates your code into 'data' and 'render'
functions, a simplified implementation of traditional MVC. It has
various parts which can be used individually or as a whole, integrated
web solution:

-  XHTML templates: contain no programming logic, only nodes tagged with
   nevow attributes
-  data/render methods: simplified MVC
-  stan: An s-expression-like syntax for expressing xml in pure python
-  formless: For describing the types of objects which may be passed to
   methods of your classes, validating and coercing string input from
   either web or command-line sources, and calling your methods
   automatically once validation passes
-  formless.webform: For rendering web forms based on formless type
   descriptions, accepting form posts and passing them to formless
   validators, and rendering error forms in the event validation fails

Disk based templates
--------------------

Nevow includes the ability to load templates off disk. These templates
may have processing directives which cause the execution of python
methods at render time. The attribute technique was inspired by the
attributes used by ZPT. However, no actual code may be embedded in the
HTML template:

.. code-block:: html

    <html xmlns:nevow="http://nevow.com/ns/nevow/0.1">
      <head>
        <title>Greetings!</title>
      </head>
      <body>
        <h1 style="font-size: large">Now I will greet you:</h1>
        <span nevow:render="greet" />
      </body>
    </html>

This template can then be loaded and rendered like so:

.. code-block:: python

    class Greeter(rend.Page):
        docFactory = loaders.xmlfile("Greeting.html")

        def render_greet(self, context, data):
            return random.choice(["Hello", "Greetings", "Hi"]), " ", data

    Greeter("My name is").renderString()


data/render methods
-------------------

To allow clean isolation between code which fetches data from a data
source and code which renders the data into HTML, nevow allows you to
write both 'data' methods and 'render' methods. These concepts are
inspired by MVC, but simpler, since the framework can handle most of the
controller aspect. An example:

.. code-block:: html

    <html xmlns:nevow="http://nevow.com/ns/nevow/0.1">
      <body>
        <span nevow:data="name" nevow:render="colorful" />
        <span nevow:data="fun" nevow:render="colorful" />
      </body>
    </html>

This template can be loaded and rendered using a class such as this:

.. code-block:: python

    class Colorful(rend.Page):
        docFactory = loaders.xmlfile("Colorful.html")

        def render_colorful(self, context, data):
            color = random.choice(['red', 'green', 'blue'])
            return context.tag(style="color: %s" % color)

        def data_name(self, context, data):
            return "Your name here"

        def data_fun(self, context, data):
            return "Are we having fun yet?"


Stan
----

One of the most powerful things about nevow is stan, an
s-expression-like syntax for producing XML fragments in pure Python
syntax. Stan is not required for using nevow, but it is both a simple
and powerful way to both lay out one's XHTML templates and express one's
display logic. A brief example will illustrate its utility:

.. code-block:: python

    import random
    from nevow import rend, tags

    class Greeter(rend.Page):
        def greet(self, context, data):
            return random.choice(["Hello", "Greetings", "Hi"]), " ", data

        docFactory = loaders.stan(
            tags.html[
            tags.head[ tags.title[ "Greetings!" ]],
            tags.body[
                tags.h1(style="font-size: large")[ "Now I will greet you:" ],
                greet
            ]
        ])


When the Greeter class is constructed, it is passed a Python object
which will be used as that page's data:

.. code-block:: python

    Greeter("Your name here").renderString()


Formless
--------

Python is dynamically typed, which means it has no built-in controls for
enforcing the types of objects which are passed to one's methods. This
is great for programmers, but not necessarily great if you are going to
be passing user-entered input to those methods. Formless is a simple way
to describe the types of objects that can be passed to one's methods, as
well as coerce from string input to those types. Other code can then
accept user input from a command line or from a web form, validate the
input against the types described using formless, and call the method
once validation has passed. A simple example:

.. code-block:: python

    from zope.interface import implements
    from formless.annotate import TypedInterface, Integer, String

    class ISimpleMethod(TypedInterface):
        def simple(self,
                   name=String(description="Your name."),
                   age=Integer(description="Your age.")):
            """
            Simple

            Please enter your name and age.
            """

    class Implementation(object):
        implements(ISimpleMethod)

        def simple(self, name, age):
            print "Hello, %s, who is %s" % (name, age)


Webform
-------

Webform is a nevow module which will automatically render web forms and
accept form posts based on types described using the classes in
formless. Used in conjunction with the twisted.web HTTP server, the
process is almost automatic:

.. code-block:: python


    from nevow import rend, tags
    from formless import webform

    class WebForm(rend.Page):
        document = rend.stan(
        tags.html[
        tags.body[
            h1["Here is the form:"],
            webform.renderForms('original')
        ]
    ])

    resource = WebForm(Implementation())


Exposing this resource instance to the web using twisted.web and
visiting it will cause a form with two input boxes to be rendered.
Posting the form will cause form validation to occur. Upon error, the
user will be returned to the original page, with the form annotated with
error messages. Upon success, the "simple" method of the Implementation
instance will be called and passed a string and an integer.

LivePage
--------

LivePage was a Woven technology which allowed programmers to receive
server- side notification of client-side JavaScript events, and to send
JavaScript to the client in response to a server-side event. New for
Nevow 0.3, LivePage has been updated to support Mozilla, Firefox, IE6
Win, and Safari. Using LivePage is very easy:

.. code-block:: python

    from nevow.liveevil import handler

    def greeter(client, nodeName):
        client.alert("Greetings. You clicked the %s node." % nodeName)

    # Any string arguments after the event handler function will be evaluated
    # as JavaScript in the context of the web browser and results passed to the
    # Python event handler
    handler = handler(greeter, 'node.name')

    class Live(rend.Page):
        docFactory = loaders.stan(
            tags.html[
            tags.body[
                ol[
                    li(onclick=handler, name="one")["One"]
                    li(onclick=handler, name="two")["Two"]
                    li(onclick=handler, name="three")["Three"]
                ]
            ]
        ])


More Information
----------------

The `Nevow website <https://divmod.org/trac/wiki/DivmodNevow>`__ has more
information. Starting with 0.3, it contains a simple WSGI implementation
and can also be used to render CGIs. However, the recommended mode of
operation is using the `Twisted
web <http://twistedmatrix.com/trac/wiki/TwistedWeb>`__ server. Nevow is
an active project, and many new bugfixes and features are committed to
the Nevow Git repository. Information about Nevow commits is available
by subscribing to the `Divmod
commits <http://divmod.net/users/mailman.twistd/listinfo/divmod-commits>`__
mailing list. The Nevow Git repository can be checked out using:

::

    git clone git://github.com/twisted/nevow

Discussion of Nevow occurs on the `twisted.web mailing
list <http://twistedmatrix.com/cgi-bin/mailman/listinfo/twisted-web>`__.
The Nevow developers are also often available for real-time help on the
`#twisted.web channel <irc://irc.freenode.net/#twisted.web>`__ on
irc.freenode.net.
