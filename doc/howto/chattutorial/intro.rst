Introduction
============

Who is this tutorial for?
-------------------------

This tutorial is for people who want to build interactive client-server
functionality where a web-browser is the client. It will show you how to
build a live, interactive chat application that requires nothing more
than a web browser that supports JavaScript.

The interesting thing about a chat application, which shows why Nevow
Athena is special, is that it involves two-way communication. In other
words, it involves not only the recently-popular AJAX (the web browser
sending commands to the server without loading a new page) but also the
trickier and, in our opinion, somewhat cooler technique known as COMET
(the web server sending commands to the *browser*).

Who is this tutorial *not* for?
-------------------------------

Nevow Athena is *not* for people who want a normal web application
framework. If you want one of those, you should use non-
Athena-\ `Nevow <http://divmod.org/trac/wiki/DivmodNevow>`__,
`Django <http://www.djangoproject.com/>`__,
`TurboGears <http://turbogears.org/>`__, or maybe even `Ruby On
Rails <http://rubyonrails.org/>`__. Athena doesn't work in terms of
pages, links, or HTTP requests and responses; it is a client-server
framework that works in terms of widgets, JavaScript objects, and
symmetric asynchronous message queues.

However, as alluded to above, Athena is part of a larger framework,
Nevow, which can be used to build more general-purpose and traditional
web applications.

AJAX
----

AJAX isn't a technology in and of itself, bur rather an amalgam of
technologies used together in order to accomplish the goal of making web
applications more responsive than traditional delivery and interactive
mechanisms, such as HTML forms submitted to a server.

In particular, AJAX consists of the following:

-  Asynchronous communications from a user's browser to a server
-  JavaScript
-  Exchanged data (usually XML or JSON)

COMET
-----

Historically, the focus of AJAX technologies was user-event driven.
However, with the need to update the user's browser with events
generated at the server, a solution more sophisticated than AJAX was
needed; this has been dubbed COMET. Athena is implemented using both
AJAX and COMET techniques, and therefore allows two-way browser <->
server communications.

Athena Basics
-------------

We've provided brief background information on AJAX/COMET, but what is
the purpose of Athena? What makes Athena different than other solutions?
Here are a few key points that should help with these questions:

-  Athena exists to make writing COMET web applications easy.
-  Athena is written in Python and JavaScript
-  It is written to be used with Nevow, a
   `Twisted <http://twistedmatrix.com/>`__-based web framework.
-  Similar to Twisted's `Perspective
   Broker <http://twistedmatrix.com/projects/core/documentation/howto/pb-intro.html>`__,
   Athena employs remote calls.

Athena was written by Twisted and Divmod developers (in addition to
contributing members of the community) in order to bring the outdated
and Nevow-incompatible Woven LivePage technology to Nevow. In addition,
it was an opportunity to improve upon the original design and
incorporate new features to address the growing needs of developers.

Target Applications
-------------------

Good candidates for Athena web applications would include those where
the application needs to respond to user input and/or updates from
servers, such as the following:

-  conference software (e.g. whiteboard, shared text, chat, etc.)
-  mail clients
-  interactive, multi-player games
-  social networking tools
-  office applications (e.g., spreadsheets, word processors, etc.)

Target Developers
-----------------

Anyone who wants to create interactive, web-based applications is a
potential Nevow/Athena user. It's best to have some background in
writing web applications, and in addition, to know how to use Nevow.
However, we hope that this tutorial will be just as useful for beginners
as experienced developers.
