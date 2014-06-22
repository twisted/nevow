Nevow Athena from Scratch, or The Evolution of a Chat Application
=================================================================

The Chat Tutorial Series
------------------------

Athena is the JavaScript engine behind Nevow, providing a great deal of
resources and power to the developer of asynchronous web applications.
To demonstrate this, we are using a web chat application as our primary
example in this tutorial. The tutorial is split into several parts: a
few introductory pages and then independent (but related) tutorials of
increasing complexity.

.. toctree::
    :maxdepth: 2

    intro
    concepts
    env
    part00/index
    part01/index


History
-------

Nevow's predecessor was Woven (and prior to that, WebMVC). Woven had
something called ``LivePage`` that was doing DOM manipulation as far
back as 2002. In early 2003, Woven event handlers supported sending
JavaScript back to the user's browser, allowing pages to be updated in
response to user-generated events. The earliest publicly visible
revisions of Nevow made use of XHR (XMLHttpRequest) in early 2004. These
facts are notable because Nevow was using AJAX a year before the term
was coined in 2005 and had working code in 2002 and 2003 that predated
Netscape publishing articles on what they called Inner Browsing where
all navigation takes place withing a single page.

Again taking the lead, Athena offers features which developers cannot
find elsewhere. In this series, we attempt to expose these excellent
qualities to the world of application developers.
