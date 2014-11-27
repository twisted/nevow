Simple Chat and Two-Way Communications
======================================

Architecture
------------

We'll assume that you've read all the preceding sections of this
tutorial and have just finished the "Echo" application example. As such,
we don't need to do any more "mental preparation" and can skip straight
to a description of the architecture.

Fundamentally, this is no different than our echo application: there is
a little more chatter that takes place between the client and server;
there's another object involved (a ``ChatRoom``); and we'll have to run
the server a little differently.

Here are the new features we want to support:

-  login form;
-  in-memory user storage;
-  the ability to send global alerts to all users; and
-  the ability for all users to "hear" when another user speaks in the
   chat room;

A general rule we can establish about our architecture is that if
something has to happen for everyone, that code needs to appear on the
server side, since it's the server that is keeping track of all users.
If something is going to happen irrespective of other users or if
browser DOM manipulation is required, then we know the client will be
the recipient of the code.

As such, in the features above, the login form will be client code. The
user storage, global alerts, and "hearing" will be implemented in server
code for the data; updating the DOM with that data will be implemented
in client code.

The user experience of this application will be the following:

1. they will be presented with a login box (no password, only username);
2. upon logging in, a message will be sent to all logged in users that
   this person has joined, they will see a message at the bottom of the
   chat that states their login name, and the login form will be
   replaced with a chat area and a text input field;
3. they will type text in the input field; and
4. the typed text will appear in the browser of every person who is
   logged in.

Building upon our previous example, our application will do the
following:

1. JavaScript client code will extract user input and send it to our
   server;
2. Python code will receive messages from the client;
3. Python code will process these messages;
4. Python code will send messages to the all clients; and
5. a template file (or ``stan`` code) will be used for presentation.

More Coding
-----------

Presentation
~~~~~~~~~~~~

The template is very similar as it was in the previous example, with the
differences being a new login box, a "logged in as" area, and some name
changes:

.. literalinclude:: listings/chatthing/template.html
    :language: html
    :linenos:

We've now got two JavaScript methods that need to be defined:
``doSetUsername()`` and ``doSay()``. We can also infer from this
template that elements will be hidden and shown after login (note the
presence of ``style="display:none"`` in two places). With these
observations in hand, let's proceed to the JavaScript code.

Writing the Client
~~~~~~~~~~~~~~~~~~

Referring back to our thoughts in the "Architecture" section above, we
can establish that the JavaScript code needs the following:

-  have the same basic boilerplate as in the "echo" example (imports,
   inheritance, attribute-setting in the constructor);
-  implement the ``doSetUsername()`` and ``doSay()`` methods;
-  create a method that will send a message to all users; and
-  create a method that will let everyone know when someone says
   something. Let's see how this is done:

.. literalinclude:: listings/chatthing/js/ChatThing.js
    :language: javascript
    :linenos:

There is a little abstraction here:

-  we need a general message-sending method (``displayMessage()``) for
   any message that gets sent to all users;
-  for user chat messages, we need something that will prepend the
   username so that everyone knows who said what
   (``displayUserMessage()``), and once this method does its thing, it
   passes the adjusted message on to ``displayMessage()``.

Other than that, this is very straight-forward code; it's pretty much
the same as the "Echo" tutorial. The ``display*()`` methods are only
responsible for updating the UI, just as we would expect.

We also need the same glue that we demonstrated in the "Echo" example:

.. literalinclude:: listings/nevow/plugins/chatthing_package.py
    :language: python
    :linenos:

Writing the Server
~~~~~~~~~~~~~~~~~~

The server code is a bit more complicated. We anticipated this above in
the "Architecture" section where we noted that the Python code needs to
receive, process and send messages.

.. literalinclude:: listings/chatthing/chatterbox.py
    :language: python
    :linenos:

There is something in our "Chat" code that is not at all present in the
"Echo" application: the ``ChatRoom`` object. We need this object for the
following functionality:

-  a means of instantiating new ``ChatterElement`` clients;
-  a "singleton" instance for keeping track of all ``ChatterElement``
   clients;
-  a means sending messages to all clients;

Let's look at the second two reasons first. In our "Chat" application, a
new ``ChatterElement`` is created whenever a user connects, so we will
have potentially many of these instances. In order for our chat server
to function as designed, it will need a way to communicate with each of
these. If we create an object that can keep the ``ChatterElement``\ es
in a list, then it will be able to iterate that list and call methods
that, in turn, make remote calls to the JavaScript.

Because we need the chat room to be a singleton object, it can only be
instantiated once. But we need many instantiations of ``ChatterElement``
-- one for each connection, in fact. So what do we do? Well, in this
case, we make one of the methods of ``ChatRoom`` a factory for
instantiating a ``ChatterElement``. Before we return the instance,
though, we append it to the list of instances that the ``ChatRoom`` is
keeping track of.

Putting it All Together
~~~~~~~~~~~~~~~~~~~~~~~

Now that we've got all the code in front of us, we can trace out exactly
what happens:

1. the user loads the resource in their browser, and the template is
   rendered;
2. after typing a message in the input box, the user hits submit;
3. JavaScript client code calls to the server with the text the user
   submitted;
4. the server gets the message and shares it with all the connected
   ``ChatterElement``\ s;
5. each ``ChatterElement`` hears this message and passes it back to the
   JavaScript client;
6. the client prepends the username to the message and then updates the
   display with the complete message.

Keep in mind that ``ChatterElement`` entails several duties: it
establishes a relationship with a room object, it "registers" a user
(there's a one-to-one mapping between users and ``ChatterElement``), it
sends messages to the browser, and it receives messages from the chat
room. Being a ``LiveElement`` subclass, ``ChatterElement`` is also
responsible for the view (via the document factory).

Running with ``twistd``
~~~~~~~~~~~~~~~~~~~~~~~

One last bit of code that may seem odd is the ``chat`` variable we
define right after the ``ChatRoom`` class. What is this? This is how we
make all this cleverness work as a twisted plugin.

If you recall, in our "Echo" application, we ran the code with the
following command:

::

    twistd -n athena-widget --element=echothing.echobox.EchoElement

The value we pass as the ``--element`` argument is the dotted name of
the ``LiveElement`` object of which our "web page" is primarily
comprised: the ``EchoElement`` object. In our "Chat" application, we
have more moving parts: not only do we have the ``ChatterElement``
object, but we have the ``ChatRoom`` object which is responsible for
keeping track of many ``ChatterElement``\ es. By defining the ``chat``
variable, we are accomplishing the following all at once:

-  providing a variable that can be accessed as a dotted name and thus
   used when starting the server (``chatthing.chatterbox.chat``);
-  creating a singleton of ``ChatRoom`` (via the "magic" of Python
   module-level instantiations);
-  making use of a factory, that when called, will both return a new
   ``ChatterElement`` instance *and* add itself to the ``ChatRoom``.

Running this version of our code is a little bit different than the
"Echo" version. This is because of the ``ChatRoom`` code we discussed
above. As such, we pass a factory as our element, like so:

::

    cd Nevow/doc/howto/chattutorial/part01/listings
    twistd -n athena-widget --element=chatthing.chatterbox.chat

If you executed this against the tutorial code on your local machine,
you can now visit http://localhost:8080/ and start chatting to your
heart's content.

Summary
-------

Unlike our echo application, the chat application has some real
functionality and does some useful stuff: supporting user chats via
browser/server two-way communications. It should be evident now how the
echo application provided a basic conceptual and (partially) functional
foundation upon which our chat work could be based.
