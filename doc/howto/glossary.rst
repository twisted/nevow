Glossary
========

Object Traversal
----------------

The process by which a Python object is located to render HTML for a
given HTTP URL. For example, given the URL http://example.com/foo/bar,
Object Traversal will begin at the "Root Resource" object by asking it
for an object which is capable of rendering the page at ('foo', 'bar').
The "Root Resource" returns an object and a list of unhandled path
segments, and the traversal continues across this new Resource object
until all path segments have been consumed.

.. _glossary-page_rendering:

Page Rendering
--------------

The process by which a Python object, usually a rend.Page subclass,
turns itself into HTML. Page Rendering involves locating some page data,
loading a template document, and applying the template to the data, in
the process generating HTML.

.. _glossary-deployment_environment:

Deployment Environment
----------------------

The environment in which a Nevow application is deployed. Generally
involves an HTTP server which is configured to route certain (or all)
HTTP requests through the Nevow Object Traversal and Page Rendering
process. Deployment environments include CGI, WSGI, and twisted.web.

DOM
---

Document Object Model. A tree of objects which represent the structure
of an XHTML document in memory. Nevow uses a nonstandard DOM named
"stan", which is made up of simple Python lists, dicts, strings, and
nevow.stan.Tag instances.

Flattener
---------

A Python function which knows how to translate from a rich type to a
string containing HTML. For example, the integer flattener calls str()
on the integer. The string flattener escapes characters which are unsafe
in HTML, such as <, >, and &.

Tag
---

A class, defined at nevow.stan.Tag, which holds information about a
single HTML tag in a DOM. Tag instances have three attributes: tagName,
attributes, and children. tagName is a string indicating the tag name.
attributes is a dict indicating the HTML attributes of that node.
children is a list indicating the child nodes of that node.

Tag Specials
------------

A Tag attribute which is "special" to nevow. Tag specials include data,
render, pattern, slot, and macro. Tag Specials will never be output as
HTML attributes of tags, but will be used by the internal Nevow
rendering process to influence how the Tag is rendered.
