Concepts of Athena: AJAX, COMET, and Python
===========================================

Servers and Clients
-------------------

COMET applications can seem an almost impenetrable mess when one is
first learning about them, much like when writing event-based desktop
applications. However, there are some basic concepts that we can
emphasize now to circumvent or alleviate most of the confusion.

In principle, the problem is very simple:

-  We want out users to interact with a web page with out having to
   refresh the page, and we want new data and/or views to be rendered in
   response to our users' actions;
-  We want the ability to push updates to user pages from the server to
   the browser, when the server has new data or views that are ready.

As usual, the implementation of the solution is much more complicated
than the statement of the problem, but hopefully the way that we have
designed Athena will hide those implementation details while providing
powerful tools to build the applications you envision. So, let's take a
look at what you need to know about servers and clients when building
Athena web applications.

It is crucial that one understands that when we write Athena
applications, we are doing a few different things:

-  Writing server code in Python that performs server actions
-  Writing server code in Python that makes remote calls to the browser
-  Writing browser code in JavaScript that performs browser actions
-  Writing browser code in JavaScript that makes remote calls to the
   server

Since server-on-server and client-on-client are rather common place and
generally well understood, we will ignore those for now. As the other
two are the focus of AJAX/COMET and thus also the primary domain of
Athena, that is what we will discuss below.

Browser-to-server calls are made by Athena via the now-famous
XMLHttpRequest. Server-to-browser calls are opened by the browser ahead
of time, and when the server is ready, the data is sent to the browser
via that connection.

JavaScript: Making Calls to the Server
--------------------------------------

When creating the JavaScript portion of our applications, we subclass an
Athena JavaScript widget, which has a method named ``callRemote()``. By
utilizing this method, we can send messages from our JavaScript client
to the server (as long as the method we call exists in the server code).

For example, in the chat application we will be building in this series
of tutorials, we will have a JavaScript class called ``ChatterBox`` with
a ``say()`` method, like the following:

.. code-block:: javascript

    function say(self, msg) {
        self.callRemote("say", msg);
        // Now show the text to the user somehow...
    }

This will make a remote call to the Python server code, executing the
``say()`` method and passing the ``msg`` variable as a parameter.

In Athena, the relationship between the browser code and the server code
is established by declaring the JavaScript module in the Python server
code, in the following manner:

.. code-block:: python

    class ChatterBox(LiveElement):
        jsClass = u'ChatThing.ChatterBox'

Additionally, in order for the JS to be able to make a call to remote
Python code, the Python method has to be exposed. This is a security
feature, implemented to ensure the JavaScript code can only call Python
methods that have been specifically marked as safe. Appropriately
enough, this is done in your Python class with the ``expose`` decorator:

.. code-block:: python

    def say(self, text):
        for chatter in chatRoom:
            chatter.youHeardSomething(text)
    say = expose(say)

Python: Making Calls to the Browser
-----------------------------------

Now what about the COMET side of the equation? If we want our server to
update data in the browser, we need to be able to call JavaScript code
from our Python server. We use a similar Python method as the JavaScript
one (when making calls from the browser to the server), acquired when
our Python class inherited from ``nevow.athena.LiveElement``:

.. code-block:: python

    def hear(self, sayer, text):
        self.callRemote("hear", sayer, text)

In order for this call to work, we need to have the ``hear()`` method
defined in our ``ChatterBox`` JavaScript class, and that will look like
this:

.. code-block:: javascript

    function hear(self, avatarName, text) {
        // Here, you'd show the user some text.
    }

Unlike on our Python classes, no special annotations need to be made on
the JavaScript side: all JavaScript methods on browser-side Widget
objects are allowed to be called by the server. If you've sent code to
the browser, you've already forfeited the ability to control when it's
called. There wouldn't be a point to limiting the server's rights to run
its code when the user can freely run it herself.

Summary
-------

With the samples above, you should have a growing sense of how Python
and JavaScript interact as servers and clients in the world of Athena.
In particular, you should be getting a sense of how JavaScript and
Python will be interacting in your Athena applications.

This has just been a taste of Athena with a few peeks into the code we
will be writing. We will cover these topics in greater detail in the
following pages, within the context of creating a functional Athena
application, complete with step-by-step instructions and rationale.
