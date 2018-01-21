=====================================
Strings vs. Bytes in Nevow on python3
=====================================

Twisted.web decided to have represent several items in their Request
class – which is used quite frequently in nevow and exposed to user code
– as bytes.  Also, at some point nevow has to produce bytes, as that is
what needs to go down the line.

In between, however, I'd like to keep out bytes as much as possible and
let people work with strings as far as possible.  This document attempts
to delineate the string/bytes perimeter.

Given that, unfortunately, that perimeter is long and twisted, the plan
is to accept bytes and strings in several places (in particular, always
for URIs), where bytes, for these purposes, are supposed to be in a
(perhaps at some poin configurable) default encoding, which for now is
utf-8 independent of the enviroment.

Use utils.toBytes or utils.toString to turn function arguments into
strings or bytes as requrired.


Bytes within Twisted we're concerned with
=========================================

The most important items that are byte strings within request, include:

* uri
* keys and values in args (this hurts a lot)
* header keys (but header values are decoded)
* prePath -- this is where segments come from; segments, however, are
  nevow interface and hence strings.
* the arguments to write (in nevow, we accept strings, too)


At least cred.checkers.InMemoryUsernamePasswordDatabaseDontUse
explicitly ASCII-encodes their usernames right now.  Since that's
what's used in the unit tests, I'm following ASCII-encoded usernames
in guard.  This seems insane.  Anyone actually working with guard
should look into this.


Bytes usage within nevow itself
===============================

While flatteners still return strings, what is passed on to
twisted.web requests' write methods must, of course, be bytes.
nevow.appserver.Requests make that translation using utils.toBytes; user
code requiring non-UTF-8 encodings needs to translate to bytes itself at
this point.

Since renderHTTP can (and is, indeed, encouraged to) write strings and
the translation is done within nevow.Request.write (or similar),
Page.renderSynchronously and Page.renderString return strings rather
than bytes.

This is particularly relevant for unit tests: what is in the
FakeRequest's accumulator is bytes.


.. vim:tw=72
