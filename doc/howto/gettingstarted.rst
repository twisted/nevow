Getting Started
===============

Warning: This document has only just been started. It's not going to get
you very far right now.

Nevow is a reasonably large library and can be quite daunting at first.
This document's aim is to guide the first time user in building a Nevow
application.

Our First Application
---------------------

Let's dive straight in, here's the code for our first (very, very
simple) application. Create the following module, ``helloworld.py``:

.. literalinclude:: listings/gettingstarted/helloworld.py
    :language: python
    :linenos:

It looks quite simple but let's walk through it anyway.

First, we import two Nevow modules. ``nevow.loaders`` contains template
loaders of which the two most useful are ``xmlfile`` and ``stan``.
``xmlfile`` can load any well-formed XML (i.e. XHTML) file; ``stan``
loads a stan tree (more on these later). The other module,
``nevow.rend``, contains all Nevow's standard renders, many of which
we'll meet in this document.

We then define the ``HelloWorld`` class that subclasses ``rend.Page``,
Nevow's main resource class. ``HelloWorld`` has two class attributes.
``addSlash`` tells ``rend.Page`` to redirect to a version of the request
URL that ends in a ``/`` if necessary. You generally want to set this to
``True`` for the root resource. ``docFactory`` tells the page instance
where to get the template from. In this case we're providing a loader
that parses an HTML file (not shown) from disk.

Hmm, ok I hear you say but how do I see it. Well, Twisted provides a
good web server which we can use. Twisted also includes a clever little
application for starting Twisted applications. Here's the ``helloworld.tac``
file, a Twisted Application Configuration:

.. literalinclude:: listings/gettingstarted/helloworld.tac
    :language: python
    :linenos:

Give it a go, run the following and connect to http://localhost:8080/ to
see your application:

::

    twistd -ny helloworld.tac

You'll probably notice that you get log output on the console. This is
just one of the good things that twistd does. It can also daemonize the
application, shed privileges if run as root, etc.

TAC files are covered in more detail in the Twisted documentation but
let's quickly explain what all this does anyway.

When ``twistd`` starts up it loads the ``.tac`` file (it's just Python)
and looks for the attribute called ``application``. When ``twistd`` is
all ready to go it starts the ``application``.

The application is not much use unless it actually does something so the
next thing we do is create a ``NevowSite`` instance, ``site``, and pass
it a root resource, a ``HelloWorld`` instance. Finally, we create a TCP
server that makes the site available on port 8080 and bind the server to
the application to ensure the server is started when the application is
started.
