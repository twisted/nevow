# -*- test-case-name: nevow.test.test_url -*-
# Copyright (c) 2004-2007 Divmod.
# See LICENSE for details.

"""
URL parsing, construction and rendering.
"""

import weakref
import urlparse
import urllib

from zope.interface import implements

from twisted.web.util import redirectTo

from nevow import inevow, flat
from nevow.stan import raw
from nevow.flat import serialize
from nevow.context import WovenContext

# RFC 3986 section 2.2, Reserved Characters
gen_delims = ':/?#[]@'
sub_delims = "!$&'()*+,;="

class IRIDecodeError(ValueError):
    """
    Failed to decode string as an IRI component.

    If the original URI contains non-ASCII percent-encoded octets not from
    UTF-8, those octets should be separately decoded to L{unicode} first.
    """



def iriencode(s, unencoded=''):
    """
    Encode the given URI/IRI component to RFC 3987 percent-encoded form.

    Characters in the unreserved set (see RFC 3986 section 2, Characters) appear
    in the result without percent-encoding.  Particular components (for example,
    path segments) may define additional characters that do not need
    percent-encoding:  these can be specified with the C{unencoded} parameter.

    @param s: string to encode
    @type s: L{unicode} (or ASCII L{str})

    @param unencoded: additional characters to exempt from percent-encoding
    @type unencoded: L{str}

    @rtype: ASCII L{str}

    @raise UnicodeDecodeError: C{s} is a non-ASCII L{str}
    @raise TypeError: C{s} is not a string
    """
    if isinstance(s, str):
        s = s.decode('ascii')
    if isinstance(s, unicode):
        return urllib.quote(s.encode('utf-8'), safe='-._~'+unencoded)
    else:
        raise TypeError(s)



def iriencodePath(s):
    """
    L{iriencode} convenience wrapper for path segments.

    This avoids percent-encoding characters in L{sub_delims} and C{':@'}.

    @see: RFC 3986 section 3.3, Path
    """
    return iriencode(s, unencoded=sub_delims + ':@')


_queryfield_safe = ((sub_delims + ':@/?')
                    .replace('&', '')
                    .replace('=', '')
                    .replace('+', ''))

def iriencodeQuery(s):
    """
    L{iriencode} convenience wrapper for x-www-form-urlencoded query fields.
    
    This is like L{iriencodeFragment}, but without C{'&=+'}.
    """
    return iriencode(s, unencoded=_queryfield_safe)



def iriencodeFragment(s):
    """
    L{iriencode} convenience wrapper for fragment components.

    This is like L{iriencodePath}, but with the addition of C{'/?'}.

    @see: RFC 3986 section 3.5, Fragment
    """
    return iriencode(s, unencoded=sub_delims + ':@/?')



def iridecode(s):
    """
    Decode the given URI/IRI component from RFC 3987 percent-encoded form.

    @param s: string to decode
    @type s: ASCII L{str} or L{unicode}

    @rtype: L{unicode}

    @raise IRIDecodeError: C{s} contained invalid percent-encoded octets
    @raise UnicodeDecodeError: C{s} is a non-ASCII L{str}
    @raise TypeError: C{s} is not a string
    """
    # Note:  urllib.unquote interprets percent-encoded octets in unicode strings
    # as Unicode codepoints (effectively decoding them as Latin1), so we cannot
    # pass it unicode strings directly.
    # It doesn't change non-percent-encoded octets in strings, though, so we can
    # encode unicode strings to UTF-8 first:  decoding the result from UTF-8
    # then restores the original Unicode characters in addition to the ones that
    # were percent-encoded.
    if isinstance(s, str):
        s = s.decode('ascii')
    if isinstance(s, unicode):
        try:
            return urllib.unquote(s.encode('utf-8')).decode('utf-8')
        except UnicodeDecodeError:
            raise IRIDecodeError(s)
    else:
        raise TypeError(s)



def _querify(fields):
    """
    Join key/value fields into an x-www-form-urlencoded string.

    No character encoding occurs.

    @param fields: list of key (L{str}) / value (L{str} or C{None}) pairs

    @return: x-www-form-urlencoded L{str}
    """
    for (k, v) in fields:
        if v is not None:
            yield '='.join((k, v))
        elif k:
            yield k
querify = lambda fields: '&'.join(_querify(fields))



def _unquerify(query):
    """
    Split an x-www-form-urlencoded string into key/value fields.

    C{'+'} is replaced with C{' '}, but no other character decoding occurs.

    @param query: x-www-form-urlencoded L{str}

    @return: list of key (L{str}) / value (L{str} or C{None}) pairs
    """
    query = query.replace('+', ' ')
    for x in query.split('&'):
        if '=' in x:
            yield tuple(x.split('=', 1))
        elif x:
            yield (x, None)
unquerify = lambda query: list(_unquerify(query))



def _maybe(f, x):
    if x is not None:
        return f(x)

def parseIRI(s):
    """
    Parse a URI/IRI into its components.

    The URI is split into five major components:  I{scheme}, I{netloc}, I{path},
    I{query}, and I{fragment}.

    The I{path} and I{query} components are further parsed:

        I{path} is split into a list of segments, such that a path containing
        I{N} C{'/'} separators will always have I{N+1} segments.  A leading
        segment of C{u''} indicates an absolute path reference;  otherwise, the
        path is relative (this implies that I{netloc} is absent).

        I{query} is split into a list of key and (optional) value fields.
        (see L{unquerify})

    All returned components are fully percent-decoded to L{unicode} strings.

    @return: C{(scheme, netloc, pathsegs, querysegs, fragment)}, per above
    """
    (scheme, netloc, path, query, fragment) = urlparse.urlsplit(s)
    pathsegs = map(iridecode, path.split('/'))
    querysegs = [(iridecode(k), _maybe(iridecode, v))
                 for (k, v) in unquerify(query)]
    return (iridecode(scheme),
            iridecode(netloc),
            pathsegs,
            querysegs,
            iridecode(fragment))



def unparseIRI((scheme, netloc, pathsegs, querysegs, fragment)):
    """
    Format a URI/IRI from its components.

    See L{parseIRI};  this is the inverse.
    """
    path = '/'.join(map(iriencodePath, pathsegs))
    query = querify((iriencodeQuery(k), _maybe(iriencodeQuery, v))
                    for (k, v) in querysegs)
    return urlparse.urlunsplit(
        (iriencode(scheme),
         iriencodePath(netloc),
         path,
         query,
         iriencodeFragment(fragment)))



class URL(object):
    """Represents a URL and provides a convenient API for modifying its parts.

    A URL is split into a number of distinct parts: scheme, netloc (domain
    name), path segments, query parameters and fragment identifier.

    Methods are provided to modify many of the parts of the URL, especially
    the path and query parameters. Values can be passed to methods as-is;
    encoding and escaping is handled automatically.

    There are a number of ways to create a URL:
        * Standard Python creation, i.e. __init__.
        * fromString, a class method that parses a string.
        * fromContext, a class method that creates a URL to represent the
          current URL in the path traversal process.

    URL instances can be used in a stan tree or to fill template slots. They can
    also be used as a redirect mechanism - simply return an instance from an
    IResource method. See URLRedirectAdapter for details.

    URL subclasses with different constructor signatures should override
    L{cloneURL} to ensure that the numerous instance methods which return
    copies do so correctly.  Additionally, the L{fromString}, L{fromContext}
    and L{fromRequest} class methods need overriding.

    @type scheme: C{unicode}
    @ivar scheme: the URI scheme

    @type netloc: C{unicode}
    @ivar netloc: the host (and possibly port)

    @type pathsegs: list of C{unicode}
    @ivar pathsegs: the path

    @type querysegs: list of pairs of C{unicode} (or C{None}, for values)
    @ivar querysegs: the query parameters, as name-value pairs

    @type fragment: C{unicode}
    @ivar fragment: the fragment identifier
    """

    def __init__(self, scheme=u'http', netloc=u'', pathsegs=None,
                 querysegs=None, fragment=None):
        def _unicodify(s):
            if isinstance(s, str):
                s = s.decode('ascii')
            return s
        self.scheme = _unicodify(scheme)
        self.netloc = _unicodify(netloc)
        if pathsegs is None:
            pathsegs = [u'']
        self._qpathlist = map(_unicodify, pathsegs)
        if querysegs is None:
            querysegs = []
        self._querylist = [(_unicodify(k), _unicodify(v))
                           for (k, v) in querysegs]
        if fragment is None:
            fragment = u''
        self.fragment = _unicodify(fragment)


    def path(self):
        """
        The percent-encoded path portion of the URL.

        @rtype: str
        """
        return '/'.join(map(iriencodePath, self._qpathlist))
    path = property(path)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        for attr in ['scheme', 'netloc', '_qpathlist', '_querylist', 'fragment']:
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    def __ne__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return not self.__eq__(other)

    query = property(
        lambda self: [y is None and x or '='.join((x,y))
            for (x,y) in self._querylist]
        )

    def _pathMod(self, newpathsegs, newqueryparts):
        return self.cloneURL(self.scheme,
                             self.netloc,
                             newpathsegs,
                             newqueryparts,
                             self.fragment)


    def cloneURL(self, scheme, netloc, pathsegs, querysegs, fragment):
        """
        Make a new instance of C{self.__class__}, passing along the given
        arguments to its constructor.
        """
        return self.__class__(scheme, netloc, pathsegs, querysegs, fragment)


    ## class methods used to build URL objects ##

    def fromString(cls, s):
        """
        Parse the given string into a URL object.

        Relative path references are not supported.

        @param s: a valid URI or IRI
        @type s: L{unicode} or L{str}
        """
        (scheme, netloc, pathsegs, querysegs, fragment) = parseIRI(s)
        # We don't store the leading u'' segment.
        if not pathsegs.pop(0) == u'':
            raise NotImplementedError(
                'relative path references not supported: %r' % (s,))
        return cls(scheme, netloc, pathsegs, querysegs, fragment)
    fromString = classmethod(fromString)

    def fromRequest(klass, request):
        """
        Create a new L{URL} instance which is the same as the URL represented
        by C{request} except that it includes only the path segments which have
        already been processed.
        """
        uri = request.prePathURL()
        if '?' in request.uri:
            uri += '?' + request.uri.split('?')[-1]
        return klass.fromString(uri)
    fromRequest = classmethod(fromRequest)

    def fromContext(klass, context):
        '''Create a URL object that represents the current URL in the traversal
        process.'''
        request = inevow.IRequest(context)
        uri = request.prePathURL()
        if '?' in request.uri:
            uri += '?' + request.uri.split('?')[-1]
        return klass.fromString(uri)
    fromContext = classmethod(fromContext)

    ## path manipulations ##

    def pathList(self, unquote=False, copy=True):
        result = self._qpathlist
        if unquote:
            result = map(urllib.unquote, result)
        if copy:
            result = result[:]
        return result

    def sibling(self, path):
        """Construct a url where the given path segment is a sibling of this url
        """
        l = self.pathList()
        l[-1] = path
        return self._pathMod(l, self.queryList(0))

    def child(self, path):
        """Construct a url where the given path segment is a child of this url
        """
        l = self.pathList()
        if l[-1] == '':
            l[-1] = path
        else:
            l.append(path)
        return self._pathMod(l, self.queryList(0))

    def isRoot(self, pathlist):
        return (pathlist == [''] or not pathlist)

    def parent(self):
        import warnings
        warnings.warn(
            "[v0.4] URL.parent has been deprecated and replaced with parentdir (which does what parent used to do) and up (which does what you probably thought parent would do ;-))",
            DeprecationWarning,
            stacklevel=2)
        return self.parentdir()

    def curdir(self):
        """Construct a url which is a logical equivalent to '.'
        of the current url. For example:

        >>> print URL.fromString('http://foo.com/bar').curdir()
        http://foo.com/
        >>> print URL.fromString('http://foo.com/bar/').curdir()
        http://foo.com/bar/
        """
        l = self.pathList()
        if l[-1] != '':
            l[-1] = ''
        return self._pathMod(l, self.queryList(0))

    def up(self):
        """Pop a URL segment from this url.
        """
        l = self.pathList()
        if len(l):
            l.pop()
        return self._pathMod(l, self.queryList(0))

    def parentdir(self):
        """Construct a url which is the parent of this url's directory;
        This is logically equivalent to '..' of the current url.
        For example:

        >>> print URL.fromString('http://foo.com/bar/file').parentdir()
        http://foo.com/
        >>> print URL.fromString('http://foo.com/bar/dir/').parentdir()
        http://foo.com/bar/
        """
        l = self.pathList()
        if not self.isRoot(l) and l[-1] == '':
            del l[-2]
        else:
            # we are a file, such as http://example.com/foo/bar our
            # parent directory is http://example.com/
            l.pop()
            if self.isRoot(l): l.append('')
            else: l[-1] = ''
        return self._pathMod(l, self.queryList(0))

    def click(self, href):
        """Build a path by merging 'href' and this path.

        Return a path which is the URL where a browser would presumably
        take you if you clicked on a link with an 'href' as given.
        """
        scheme, netloc, path, query, fragment = urlparse.urlsplit(href)

        if (scheme, netloc, path, query, fragment) == ('', '', '', '', ''):
            return self

        query = unquerify(query)

        if scheme:
            if path and path[0] == '/':
                path = path[1:]
            return self.cloneURL(
                scheme, netloc, map(raw, path.split('/')), query, fragment)
        else:
            scheme = self.scheme

        if not netloc:
            netloc = self.netloc
            if not path:
                path = self.path
                if not query:
                    query = self._querylist
                    if not fragment:
                        fragment = self.fragment
            else:
                if path[0] == '/':
                    path = path[1:]
                else:
                    l = self.pathList()
                    l[-1] = path
                    path = '/'.join(l)

        path = normURLPath(path)
        return self.cloneURL(
            scheme, netloc, map(raw, path.split('/')), query, fragment)

    ## query manipulation ##

    def queryList(self, copy=True):
        """Return current query as a list of tuples."""
        if copy:
            return self._querylist[:]
        return self._querylist

    # FIXME: here we call str() on query arg values: is this right?

    def add(self, name, value=None):
        """Add a query argument with the given value
        None indicates that the argument has no value
        """
        q = self.queryList()
        q.append((name, value))
        return self._pathMod(self.pathList(copy=False), q)

    def replace(self, name, value=None):
        """
        Remove all existing occurrences of the query argument 'name', *if it
        exists*, then add the argument with the given value.

        C{None} indicates that the argument has no value.
        """
        ql = self.queryList(False)
        ## Preserve the original position of the query key in the list
        i = 0
        for (k, v) in ql:
            if k == name:
                break
            i += 1
        q = filter(lambda x: x[0] != name, ql)
        q.insert(i, (name, value))
        return self._pathMod(self.pathList(copy=False), q)

    def remove(self, name):
        """Remove all query arguments with the given name
        """
        return self._pathMod(
            self.pathList(copy=False),
            filter(
                lambda x: x[0] != name, self.queryList(False)))

    def clear(self, name=None):
        """Remove all existing query arguments
        """
        if name is None:
            q = []
        else:
            q = filter(lambda x: x[0] != name, self.queryList(False))
        return self._pathMod(self.pathList(copy=False), q)

    ## scheme manipulation ##

    def secure(self, secure=True, port=None):
        """Modify the scheme to https/http and return the new URL.

        @param secure: choose between https and http, default to True (https)
        @param port: port, override the scheme's normal port
        """

        # Choose the scheme and default port.
        if secure:
            scheme, defaultPort = 'https', 443
        else:
            scheme, defaultPort = 'http', 80

        # Rebuild the netloc with port if not default.
        netloc = self.netloc.split(':',1)[0]
        if port is not None and port != defaultPort:
            netloc = '%s:%d' % (netloc, port)

        return self.cloneURL(
            scheme, netloc, self._qpathlist, self._querylist, self.fragment)

    ## fragment/anchor manipulation

    def anchor(self, anchor=None):
        """
        Modify the fragment/anchor and return a new URL. An anchor of
        C{None} (the default) or C{''} (the empty string) will remove the
        current anchor.
        """
        return self.cloneURL(
            self.scheme, self.netloc, self._qpathlist, self._querylist, anchor)

    ## object protocol override ##

    def __str__(self):
        # Note:  we store our path with an implied leading u'' segment, so add
        # it back in before passing to unparseIRI.
        return unparseIRI((self.scheme, self.netloc, [u'']+self._qpathlist,
                           self._querylist, self.fragment))

    def __repr__(self):
        return (
            '%s(scheme=%r, netloc=%r, pathsegs=%r, querysegs=%r, fragment=%r)'
            % (type(self).__name__,
               self.scheme,
               self.netloc,
               self._qpathlist,
               self._querylist,
               self.fragment))


def normURLPath(path):
    """
    Normalise the URL path by resolving segments of '.' and '..'.
    """
    segs = []

    pathSegs = path.split('/')

    for seg in pathSegs:
        if seg == '.':
            pass
        elif seg == '..':
            if segs:
                segs.pop()
        else:
            segs.append(seg)

    if pathSegs[-1:] in (['.'],['..']):
        segs.append('')

    return '/'.join(segs)


class URLOverlay(object):
    def __init__(self, urlaccessor, doc=None, dolater=None, keep=None):
        """A Proto like object for abstractly specifying urls in stan trees.

        @param urlaccessor: a function which takes context and returns a URL

        @param doc: a a string documenting this URLOverlay instance's usage

        @param dolater: a list of tuples of (command, args, kw) where
        command is a string, args is a tuple and kw is a dict; when the
        URL is returned from urlaccessor during rendering, these
        methods will be applied to the URL in order
        """
        if doc is not None:
            self.__doc__ = doc
        self.urlaccessor = urlaccessor
        if dolater is None:
            dolater= []
        self.dolater = dolater
        if keep is None:
            keep = []
        self._keep = keep

    def addCommand(self, cmd, args, kw):
        dl = self.dolater[:]
        dl.append((cmd, args, kw))
        return self.__class__(self.urlaccessor, dolater=dl, keep=self._keep[:])

    def keep(self, *args):
        """A list of arguments to carry over from the previous url.
        """
        K = self._keep[:]
        K.extend(args)
        return self.__class__(self.urlaccessor, dolater=self.dolater[:], keep=K)


def createForwarder(cmd):
    return lambda self, *args, **kw: self.addCommand(cmd, args, kw)


for cmd in [
    'sibling', 'child', 'parent', 'here', 'curdir', 'click', 'add',
    'replace', 'clear', 'remove', 'secure', 'anchor', 'up', 'parentdir'
    ]:
    setattr(URLOverlay, cmd, createForwarder(cmd))


def hereaccessor(context):
    return URL.fromContext(context).clear()
here = URLOverlay(
    hereaccessor,
    "A lazy url construction object representing the current page's URL. "
    "The URL which will be used will be determined at render time by "
    "looking at the request. Any query parameters will be "
    "cleared automatically.")


def gethereaccessor(context):
    return URL.fromContext(context)
gethere = URLOverlay(gethereaccessor,
    "A lazy url construction object like 'here' except query parameters "
    "are preserved. Useful for constructing a URL to this same object "
    "when query parameters need to be preserved but modified slightly.")



def viewhereaccessor(context):
    U = hereaccessor(context)
    i = 1
    while True:
        try:
            params = context.locate(inevow.IViewParameters, depth=i)
        except KeyError:
            break
        for (cmd, args, kw) in iter(params):
            U = getattr(U, cmd)(*args, **kw)
        i += 1
    return U
viewhere = URLOverlay(viewhereaccessor,
    "A lazy url construction object like 'here' IViewParameters objects "
    "are looked up in the context during rendering. Commands provided by "
    "any found IViewParameters objects are applied to the URL object before "
    "rendering it.")


def rootaccessor(context):
    req = context.locate(inevow.IRequest)
    root = req.getRootURL()
    if root is None:
        return URL.fromContext(context).click('/')
    return URL.fromString(root)
root = URLOverlay(rootaccessor,
    "A lazy URL construction object representing the root of the "
    "application. Normally, this will just be the logical '/', but if "
    "request.rememberRootURL() has previously been used in "
    "the request traversal process, the url of the resource "
    "where rememberRootURL was called will be used instead.")


def URLSerializer(original, context):
    """
    Serialize the given L{URL}.

    Unicode path, query and fragment components are handled according to the
    IRI standard (RFC 3987).
    """
    urlContext = WovenContext(parent=context, precompile=context.precompile,
                              inURL=True)
    pathContext = WovenContext(parent=urlContext, precompile=context.precompile,
                               inURLPath=True)
    if original.scheme:
        yield serialize(original.scheme, urlContext)
        yield '://'
        yield serialize(original.netloc, pathContext)
    for pathsegment in original._qpathlist:
        yield '/'
        yield serialize(pathsegment, pathContext)
    query = original._querylist
    if query:
        queryContext = WovenContext(parent=urlContext,
                                    precompile=context.precompile,
                                    inURLQuery=True)
        yield '?'
        first = True
        for key, value in query:
            if not first:
                # xhtml can't handle unescaped '&'
                yield '&amp;'
            else:
                first = False
            yield serialize(key, queryContext)
            if value is not None:
                yield '='
                yield serialize(value, queryContext)
    if original.fragment:
        fragmentContext = WovenContext(parent=urlContext,
                                       precompile=context.precompile,
                                       inURLFragment=True)
        yield "#"
        yield serialize(original.fragment, fragmentContext)


def URLOverlaySerializer(original, context):
    if context.precompile:
        yield original
    else:
        url = original.urlaccessor(context)
        for (cmd, args, kw) in original.dolater:
            url = getattr(url, cmd)(*args, **kw)
        req = context.locate(inevow.IRequest)
        for key in original._keep:
            for value in req.args.get(key, []):
                url = url.add(key, value)
        yield serialize(url, context)


## This is totally unfinished and doesn't work yet.
#class IURLGenerator(compy.Interface):
#    pass


class URLGenerator:
    #implements(IURLGenerator)

    def __init__(self):
        self._objmap = weakref.WeakKeyDictionary()

    def objectMountedAt(self, obj, at):
        self._objmap[obj] = at

    def url(self, obj):
        try:
            return self._objmap.get(obj, None)
        except TypeError:
            return None

    __call__ = url

    def __getstate__(self):
        d = self.__dict__.copy()
        del d['_objmap']
        return d

    def __setstate__(self, state):
        self.__dict__ = state
        self._objmap = weakref.WeakKeyDictionary()


class URLRedirectAdapter:
    """Adapter for URL and URLOverlay instances that results in an HTTP
    redirect.

    Whenever a URL or URLOverlay instance is returned from locateChild or
    renderHTTP an HTTP response is generated that causes a redirect to
    the adapted URL. Any remaining segments of the current request are
    consumed.

    Note that URLOverlay instances are lazy so their use might not be entirely
    obvious when returned from locateChild, i.e. url.here means the request's
    URL and not the URL of the resource that is self.

        def renderHTTP(self, ctx):
            # Redirect to my immediate parent
            return url.here.up()

        def locateChild(self, ctx, segments):
            # Redirect to the URL of this resource
            return url.URL.fromContext(ctx)
    """
    implements(inevow.IResource)

    def __init__(self, original):
        self.original = original

    def locateChild(self, ctx, segments):
        return self, ()

    def renderHTTP(self, ctx):
        # The URL may contain deferreds so we need to flatten it using
        # flattenFactory that will collect the bits into the bits list and
        # call flattened to finish.
        bits = []
        def flattened(spam):
            # Join the bits to make a complete URL.
            u = ''.join(bits)
            # It might also be relative so resolve it against the current URL
            # and flatten it again.
            u = flat.flatten(URL.fromContext(ctx).click(u), ctx)
            return redirectTo(u, inevow.IRequest(ctx))
        return flat.flattenFactory(self.original, ctx, bits.append, flattened)
