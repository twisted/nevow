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

WSGI
----

WSGI is a python interface for plugging web applications into various
HTTP server architectures. It is described in `PEP
333 <http://www.python.org/peps/pep-0333.html>`__, the Python Web
Services Gateway Interface Python Enhancement Proposal. Nevow includes
the ``nevow.wsgi`` module, which includes a ``createWSGIApplication``
function which takes a Page and returns a standard WSGI application
callable. With the help of the ``run_with_cgi`` example gateway from the
PEP (which I will omit here), our CGI example becomes shorter:

.. code-block:: python

    #!/usr/bin/env python

    from nevow import rend, loaders, wsgi

    class HelloWorld(rend.Page):
        docFactory = loaders.stan("Hello, world!")

    run_with_cgi(wsgi.createWSGIApplication(HelloWorld()))


Of course, you can use any available WSGI gateway to publish your
application object, such as one of the gateways which comes with the
`PEAK <http://peak.telecommunity.com/>`__ toolkit. For example, here is
a simple python module which creates a WSGI application which we will
then deploy with PEAK's SimpleHTTPServer gateway:

.. code-block:: python

    ## helloworld.py

    from nevow import rend, loaders, wsgi

    class HelloWorld(rend.Page):
        docFactory = loaders.stan("Hello, world!")

    application = wsgi.createWSGIApplication(HelloWorld())


Save this file as "helloworld.py" somewhere on your PYTHONPATH and then
run the following command:

::

    peak launch WSGI import:helloworld.application

This will bring up a SimpleHTTPServer running your Nevow code and launch
a web browser to view the output. (TODO: I couldn't get this working
immediately but I will seek assistance with PEAK and update the
instructions once I do.)

Twisted.Web
-----------

A convenient and powerful way to deploy Nevow applications is inside a
process running the twisted.web HTTP server. With Python, Twisted, and
Nevow installed, you have all you need to run a Web Application, with no
other dependencies or external HTTP servers such as Apache required.
Running your Nevow applications under twisted.web also gives you access
to some of the more advanced "Live" features of Nevow, such as
``nevow.livepage`` and ``nevow.canvas``. Currently, these modules
require more control over the HTTP socket than CGI or WSGI can provide.
(This may change in the future.)

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

Zomne
-----

*Warning* Zomne is experimental. It may blow up your computer and
require your first born son as a sacrifice. Zomne also only works in
UNIX-like environments where unix domain sockets are available, and may
not work on windows.

Zomne, or "Zombie Nevow", is a CGI written in C which can start up a
long- running Application Server process if one is not already running.
It then uses a simple custom protocol to transmit information about the
HTTP request from the CGI process to the application server process.

Zomne combines the ease of deployment of the CGI environment with the
speed and flexibility of the twisted.web long-running application server
process model.

To use Zomne, you must first compile the CGI. cd into the directory
created when unpacking the Nevow tarball, and compile the CGI:

::

    % gcc zomne.c

Move it into your cgi-bin:

::

    % mv a.out /Library/WebServer/CGI-Executables/nevow.cgi

Create a file which tells the cgi where to look for the application:

::

    % cat > /Library/WebServer/CGI-Executables/.nevow.cgi.dir
    /Users/dp/zomne-test
    ^D

The CGI name can be anything, as long as there is a file with a
prepended "." and a postfixed ".dir" in the same directory which
contains the full path of a zomne application directory. Next, create
the application directory:

::

    mkdir /Users/dp/zomne-test

Finally, create the zomne.tac file which the zomne.cgi will execute to
start the long-running application server process:

.. code-block:: python

    from nevow import rend, loaders, zomnesrv

    class HelloWorld(rend.Page):
        docFactory = loaders.stan("Hello, world!")

    from twisted.application import service, internet
    application = service.Application('nevow-zomne-test')
    internet.UNIXServer('zomne.socket', zomnesrv.ZomneFactory(HelloWorld())).setServiceParent(application)


Now, visiting the nevow.cgi URL through the web should render the Hello
World page, after a pause while the server is starting up. Subsequent
requests should be very fast, because the application server is already
running, and the CGI merely has to forward the request to it.

Another useful capability of the zomne CGI process is the ability to
control environment variables the CGI will use. Create a directory named
"zomne\_environ" in the application directory, and fill it with text
files whose name will be the environment key and whose contents will be
the environment value:

::

    % cd zomne-test
    % mkdir zomne-environ
    % cd zomne-environ
    % cat > PYTHONPATH
    /Users/dp/Projects/Nevow:/Users/dp/Projects/helloworld
    ^D

Conclusion
----------

Nevow may be deployed in a number of environments, from the most
restrictive to the most permissive. Writing a CGI can be an easy way to
try out the Nevow templating mechanism, but can be slow. A long-running
application server process can be a good way to get good performance as
well as additional features such as in-memory server-side sessions,
advanced automatic form handling with formless, and live page updating
features such as nevow.livepage and nevow.canvas.

Which deployment option you choose will depend on the amount of control
you have over your deployment environment, and what advanced features
your application will require.
