Toy Echo Application
====================

What is an "Echo Application?"
------------------------------

Our first foray into building an Athena application will be an easy
venture: we want to type something in an input box and have it echoed
back to us on the same page, without having to reload anything. Why?
Well, our eventual goal is to have a working chat server, with all sorts
of technical bells and whistles (persistent storage, authentication,
etc.), but that's a bit heady for right now. Many of the same principles
which we will eventually employ in our chat application exist for a
simple case of sending textual messages between a web browser and a
server. This is the essence of our "Echo" application.

Mental Preparation
------------------

In the :doc:`../intro` and the :doc:`../concepts` pages, we had a
refresher on AJAX and COMET and we learned a little bit about what that
looks like for Athena.  But as we sit down to actually write an Athena
application, what do we need to wrap our heads around?

Given the introductory knowledge we have, we know that we will need to
write some JavaScript, some Python, and if our past experience in
developing web applications is any guide, some form of template. This
indeed is the case, but here's something big: we're not working with
pages and page templates; we're working with "elements", or parts of the
DOM tree. We will not be creating page resources; we will be creating
just the parts of a "traditional" page that will be dynamic and
interactive.

Architecture
------------

Now that we've pumped ourselves up and before we start clacking away at
the keyboard, we need to get pointed in the right direction. We need a
plan. Here's what we know:

1. We will have a server that:

   -  serves dynamic elements in a resource accessible via a URL;
   -  communicates with a client.

2. We will have a client that:

   -  communicates with the server;
   -  updates its DOM tree.

The user experience of this application will be the following:

1. they will type text in an input on a form; and
2. the typed text will be rendered to a different part of the page upon
   hitting a submit button.

We will not simply write user input to a ``div`` with JavaScript DOM
manipulation, but will instead pass data like we expect will be
necessary when we write our chat application. After all, it's probably
best to build towards our goal. In order to accomplish this, the
application will do something like the following:

1. JavaScript client code will extract user input and send it to our
   server;
2. Python code will receive messages from the client;
3. Python code will send messages to the client; and
4. a template file (or ``stan`` code) will be used for presentation.

Let the Coding Begin
--------------------

In a future installment, we will outline the development process from
the perspective of test-driven development, in order to not only show
how to write unit tests for Athena (Python and JavaScript), but to
encourage good programming practices while working with Athena. For now,
though, we will just dive right in.

Presentation
~~~~~~~~~~~~

Let's start with the easy bit: what our app will look like. Here is the
template for our echo application:

.. literalinclude:: listings/echothing/template.html
    :language: html
    :linenos:

Things to note:

-  This is not a complete HTML document, but is an XHTML template for an
   "element".
-  The name space declarations in the top ``div`` tag are necessary for
   the operation of Athena.
-  When we hit the "Send" button, our JavaScript class will call the
   ``doSay()`` method.

Writing the Client
~~~~~~~~~~~~~~~~~~

Next up is the JavaScript. We need to send our data to the server. In a
full chat application, it would be necessary to send the data to the
server so that we could propagate the message to all connected clients.
In this case, with the simple echo, we're not going to do anything with
the data that gets sent to the server, except send it back, of course.

Our JavaScript will need to do several things:

1. import required modules;
2. inherit ``callRemote`` functionality from the base ``Widget`` class;
3. setup convenience attributes;
4. implement the ``doSay()`` method we put in our template above; and
5. implement a method for updating the DOM with data it receives from
   the server:

.. literalinclude:: listings/echothing/js/EchoThing.js
    :language: javascript
    :linenos:

Points to note:

-  Those import statements aren't just pretty: they are necessary! In
   Athena, you need to treat those like you treat the import statements
   in Python.
-  The attributes set in the ``__init__()`` method are for convenience
   when we reference them in other methods.
-  Note the ``callRemote()`` method in ``doSay()``, As mentioned in the
   `Concepts <../concepts.html>`__ section, this is how JavaScript is
   communicating with our Python server.
-  Another thing about ``doSay``: this is the submit handler. As such,
   it needs to return false so that the browser is prevented from doing
   a normal form submission.
-  ``addText()`` is the method that will be updating the browser DOM
   once the server sends the data back.

There's not much to say about the next one. This is what sets up the
relationship between our module name and the actual file itself (so that
the JavaScript can be loaded):

.. literalinclude:: listings/nevow/plugins/echothing_package.py
    :language: python
    :linenos:

Writing the Server
~~~~~~~~~~~~~~~~~~

Despite what one might think, writing the server may be the easiest
part! If you've created Nevow applications before, then this will look
very familiar. The only method we need is one that will send data back
to the client. Besides importing the necessary modules and creating a
class with some boilerplate, that's about it.

Let's take a look at the code:

.. literalinclude:: listings/echothing/echobox.py
    :language: python
    :linenos:

As promised, simple as can be. We do make use of a Twisted utility that
simplifies typing the path to our template. Some very important points:

-  The ``jsClass`` assignment is what connects this code to your
   JavaScript code.
-  As discussed in the `Concepts <../concepts.html>`__ section, the
   ``expose`` decorator is required if our JavaScript is going to be
   able to call the ``say()`` method.

Putting it All Together
~~~~~~~~~~~~~~~~~~~~~~~

Now that we've got all the code in front of us, we can trace out exactly
what happens:

1. the user loads the resource in their browser, and the template is
   rendered;
2. after typing a message in the input box, the user hits submit;
3. upon hitting submit, the client code ``doSay()`` method is called;
4. ``doSay()`` makes a remote call to the Python server method
   ``say()``;
5. the Python server receives the data when ``say()`` is called, and
   then it passes that data to the client code's ``addText()`` method;
6. with control back in the client code and data fresh from the server,
   JavaScript can now update the page's DOM with the new data, and this
   is what the ``addText()`` method does;
7. when ``addText()`` finishes, the cycle has completed and the browser
   now displays the latest data input by the user.

The Fruits of Our Labor
~~~~~~~~~~~~~~~~~~~~~~~

Now we get to run it! This is a little different than what you may be
used to, if you have written Twisted applications in the past. We are
using the plugin architecture of Twisted and Nevow such that ``twistd``
will publish our element in an HTTP service. To do this, we will use
``twistd``'s ``athena-widget`` command:

::

    cd Nevow/doc/howto/chattutorial/part00/listings
    twistd -n athena-widget --element=echothing.echobox.EchoElement

If you executed this against the tutorial code on your local machine,
you can now visit `localhost:8080 <http://localhost:8080>`__ and start
echoing to your heart's content.

Summary
-------

As you can see, our echo application is a toy app that doesn't do
anything very useful. However, it has provided us with a basis for
learning how to write working Athena code that lets a browser and server
communicate with each other, both sending and receiving data. As such,
we now have a solid foundation upon which we can build a functional,
useful *and* instructional chat application.
