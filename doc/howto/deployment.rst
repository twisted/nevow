Deployment
==========

Nevow includes two major phases for deciding what HTML to render.
:doc:`traversal` is the procedure by which a URL
is mapped to a Python object which will perform the HTML generation.
:ref:`glossary-page_rendering` is the process by which data objects
are combined with an HTML template to produce the final output.

Before any of this can take place, however, we must have an environment
in which our Python code can run in response to an HTTP request, and
HTML can be returned to the browser for rendering. This is called the
:ref:`glossary-deployment_environment`.

There are various deployment options for Nevow page code:

-  CGI: Simple deployment in almost any HTTP server
-  WSGI: A more complete and flexible way for deploying on many HTTP
   servers
-  Twisted.Web: A standalone application server process which includes a
   built-in HTTP server
-  Zomne: A small CGI which hands off HTTP requests to a long-running
   application server process, similar to FastCGI or SCGI

CGI
---

You can deploy Nevow on any webserver which uses the Common Gateway
Interface. Using this method, your code is responsible for properly
formatting and outputting the HTTP response headers, and Nevow is used
only to generate the HTML body of your page. Here is the simplest
possible CGI:

.. code-block:: python

    #!/usr/bin/env python

    print "Content-type: text/plain\r\n\r\n",

    from nevow import rend, loaders

    class HelloWorld(rend.Page):
        docFactory = loaders.stan("Hello, world!")

    print HelloWorld().renderSynchronously()


With this simple CGI you can use the Nevow template loaders and standard
nevow template interpolation techniques in your CGIs. However, you do
not get any :doc:`traversal` features, and you
have to generate HTTP headers yourself. WSGI is a slightly higher-level
deployment option which does not suffer these problems.

Twisted.Web
-----------

A convenient and powerful way to deploy Nevow applications is inside a process
running the twisted.web HTTP server. With Python, Twisted, and Nevow installed,
you have all you need to run a Web Application, with no other dependencies or
external HTTP servers such as Apache required.  Running your Nevow applications
under twisted.web also gives you access to some of the more advanced "Live"
features of Nevow, such as ``nevow.athena``.  Currently, these modules require
more control over the HTTP socket than CGI can provide.  (This may change in
the future.)

Deploying a Nevow application under twisted.web requires a little more
boilerplate, but can be considerably easier to set up than other
deployment options because there are no external dependencies. Note that
normally you should declare your Page classes in modules external to the
twisted configuration file, but everything is included in one file here
for brevity. Here is the minimal configuration file required to use
Nevow with twisted.web:

.. code-block:: python

    from nevow import rend, loaders, appserver

    class HelloWorld(rend.Page):
        docFactory = loaders.stan("Hello, world!")

    from twisted.application import service, internet
    application = service.Application("hello-world")
    internet.TCPServer(8080, appserver.NevowSite(HelloWorld())).setServiceParent(application)


Save this file as "helloworld.tac" and start the server using the
command:

::

    twistd -noy helloworld.tac

Then visit your twisted.web server by viewing the url
"http://localhost:8080/" in your browser. See the twistd man page for
more information about what twistd is capable of, including daemonizing
the HTTP server.

Conclusion
----------

Nevow may be deployed in a number of environments, from the most
restrictive to the most permissive. Writing a CGI can be an easy way to
try out the Nevow templating mechanism, but can be slow. A long-running
application server process can be a good way to get good performance as
well as additional features such as in-memory server-side sessions,
advanced automatic form handling with formless, and live page updating
features such as nevow.athena.

Which deployment option you choose will depend on the amount of control
you have over your deployment environment, and what advanced features
your application will require.
