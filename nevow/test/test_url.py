# Copyright (c) 2004-2007 Divmod.
# See LICENSE for details.

"""
Tests for L{nevow.url}.
"""

import urlparse, urllib

from nevow.url import URL, iridecode, iriencode, IRIDecodeError
from nevow import context, url, inevow, util, loaders
from nevow import tags
from nevow.testutil import TestCase, FakeRequest
from nevow.flat import flatten

theurl = "http://www.foo.com:80/a/nice/path/?zot=23&zut"

# RFC1808 relative tests. Not all of these pass yet.
rfc1808_relative_link_base='http://a/b/c/d;p?q#f'
rfc1808_relative_link_tests = [
    # "Normal"
    ('g:h', 'g:h'),
    ('g', 'http://a/b/c/g'),
    ('./g', 'http://a/b/c/g'),
    ('g/', 'http://a/b/c/g/'),
    ('/g', 'http://a/g'),
    ('//g', 'http://g'),
    ('?y', 'http://a/b/c/d;p?y'),
    ('g?y', 'http://a/b/c/g?y'),
    ('g?y/./x', 'http://a/b/c/g?y/./x'),
    ('#s', 'http://a/b/c/d;p?q#s'),
    ('g#s', 'http://a/b/c/g#s'),
    ('g#s/./x', 'http://a/b/c/g#s/./x'),
    ('g?y#s', 'http://a/b/c/g?y#s'),
    #(';x', 'http://a/b/c/d;x'),
    ('g;x', 'http://a/b/c/g;x'),
    ('g;x?y#s', 'http://a/b/c/g;x?y#s'),
    ('.', 'http://a/b/c/'),
    ('./', 'http://a/b/c/'),
    ('..', 'http://a/b/'),
    ('../', 'http://a/b/'),
    ('../g', 'http://a/b/g'),
    #('../..', 'http://a/'),
    #('../../', 'http://a/'),
    ('../../g', 'http://a/g'),

    # "Abnormal"
    ('', 'http://a/b/c/d;p?q#f'),
    #('../../../g', 'http://a/../g'),
    #('../../../../g', 'http://a/../../g'),
    #('/./g', 'http://a/./g'),
    #('/../g', 'http://a/../g'),
    ('g.', 'http://a/b/c/g.'),
    ('.g', 'http://a/b/c/.g'),
    ('g..', 'http://a/b/c/g..'),
    ('..g', 'http://a/b/c/..g'),
    ('./../g', 'http://a/b/g'),
    ('./g/.', 'http://a/b/c/g/'),
    ('g/./h', 'http://a/b/c/g/h'),
    ('g/../h', 'http://a/b/c/h'),
    #('http:g', 'http:g'),          # Not sure whether the spec means
    #('http:', 'http:'),            # these two are valid tests or not.
    ]



_percentenc = lambda s: ''.join('%%%02X' % ord(c) for c in s)

class TestComponentCoding(TestCase):
    """
    Test basic encoding and decoding of URI/IRI components.
    """

    # 0x00 - 0x7F (unreserved subset)
    unreserved_dec = (u'abcdefghijklmnopqrstuvwxyz' +
                      u'ABCDEFGHIJKLMNOPQRSTUVWXYZ' +
                      u'0123456789' + u'-._~')
    unreserved_enc = unreserved_dec.encode('ascii')

    # 0x00 - 0x7F (maybe-reserved subset)
    otherASCII_dec = u''.join(sorted(set(map(unichr, range(0x80)))
                                     - set(unreserved_dec)))
    otherASCII_enc = _percentenc(otherASCII_dec.encode('ascii'))

    # 0x80 - 0xFF, non-ASCII octets
    nonASCII_dec = u''.join(map(unichr, range(0x80, 0x100)))
    nonASCII_enc = _percentenc(nonASCII_dec.encode('utf-8'))

    # non-octet Unicode codepoints
    nonOctet_dec = u'\u0100\u0800\U00010000'
    nonOctet_enc = _percentenc(nonOctet_dec.encode('utf-8'))

    # Random non-string types
    nonStrings = [5, lambda: 5, [], {}, object()]


    def assertMatches(self, x, y):
        """
        Like L{assertEquals}, but also require matching types.
        """
        self.assertEquals(type(x), type(y))
        self.assertEquals(x, y)


    def test_iriencode(self):
        """
        L{iriencode} should encode URI/IRI components (L{unicode} values)
        according to RFC 3986/3987.
        """
        for (dec, enc) in [(self.unreserved_dec, self.unreserved_enc),
                           (self.otherASCII_dec, self.otherASCII_enc),
                           (self.nonASCII_dec, self.nonASCII_enc),
                           (self.nonOctet_dec, self.nonOctet_enc)]:
            self.assertMatches(iriencode(dec), enc)
            self.assertMatches(iriencode(dec, unencoded=''), enc)


    def test_iriencodeUnencoded(self):
        """
        L{iriencode} should not percent-encode octets in C{unencoded}.
        """
        self.assertMatches(iriencode(u'_:_/_', unencoded=':'), '_:_%2F_')
        self.assertMatches(iriencode(u'_:_/_', unencoded='/'), '_%3A_/_')


    def test_iriencodeASCII(self):
        """
        L{iriencode} should accept ASCII-encoded L{str} values.
        """
        for (dec, enc) in [(self.unreserved_dec, self.unreserved_enc),
                           (self.otherASCII_dec, self.otherASCII_enc)]:
            self.assertMatches(iriencode(dec.encode('ascii')), enc)
            self.assertMatches(iriencode(dec.encode('ascii'), unencoded=''),
                               enc)


    def test_iridecode(self):
        """
        L{iridecode} should decode encoded URI/IRI components (L{unicode} or
        ASCII L{str} values) to unencoded L{unicode} according to RFC 3986/3987.
        """
        for (enc, dec) in [(self.unreserved_enc, self.unreserved_dec),
                           (self.otherASCII_enc, self.otherASCII_dec),
                           (self.nonASCII_enc, self.nonASCII_dec),
                           (self.nonOctet_enc, self.nonOctet_dec)]:
            self.assertMatches(iridecode(enc), dec)
            self.assertMatches(iridecode(enc.decode('ascii')), dec)


    def test_iridecodeNonPercent(self):
        """
        L{iridecode} should return non-percent-encoded values as-is.
        """
        for dec in [self.unreserved_dec, self.otherASCII_dec.replace('%', ''),
                    self.nonASCII_dec, self.nonOctet_dec]:
            self.assertMatches(iridecode(dec), dec)


    def test_iridecodeIRIDecodeError(self):
        """
        L{iridecode} should raise L{IRIDecodeError} for percent-encoded
        sequences that do not describe valid UTF-8.
        """
        for s in [u'r%E9sum%E9', u'D%FCrst']:
            self.assertRaises(IRIDecodeError, iridecode, s)
            self.assertRaises(IRIDecodeError, iridecode, s.decode('ascii'))


    def test_nonASCII(self):
        """
        L{iriencode} and L{iridecode} should not try to interpret non-ASCII
        L{str} values.
        """
        for s in [self.nonASCII_dec.encode('latin1'),
                  self.nonASCII_dec.encode('utf-8'),
                  self.nonOctet_dec.encode('utf-8')]:
            self.assertRaises(UnicodeDecodeError, iriencode, s)
            self.assertRaises(UnicodeDecodeError, iridecode, s)


    def test_nonString(self):
        """
        L{iriencode} and L{iridecode} should raise L{TypeError} for non-string
        values.
        """
        for x in self.nonStrings:
            self.assertRaises(TypeError, iridecode, x)
            self.assertRaises(TypeError, iriencode, x)


    def test_doubleEncode(self):
        """
        Encoding and decoding an already-encoded value should not change it.
        """
        for dec in [self.unreserved_dec, self.otherASCII_dec,
                    self.nonASCII_dec, self.nonOctet_dec]:
            enc = iriencode(dec)
            uenc = enc.decode('ascii')
            self.assertMatches(iridecode(iriencode(uenc)), uenc)
            self.assertMatches(iridecode(iriencode(enc)), uenc)


    def test_iriencodePath(self):
        """
        L{iriencodePath} should avoid percent-encoding characters not reserved
        in path segments.
        """
        self.assertMatches(url.iriencodePath(url.gen_delims+url.sub_delims),
                           ":%2F%3F%23%5B%5D@!$&'()*+,;=")


    def test_iriencodeParam(self):
        """
        L{iriencodeParam} should avoid percent-encoding characters not reserved
        in query and fragment components.
        """
        self.assertMatches(url.iriencodeParam(url.gen_delims+url.sub_delims),
                           ":/?%23%5B%5D@!$&'()*+,;=")


    # Examples for querify/unquerify.
    queryPairs = [('=', [('', '')]),
                  ('==', [('', '=')]),
                  ('k', [('k', None)]),
                  ('k=', [('k', '')]),
                  ('k=v', [('k', 'v')]),
                  ('%26', [('%26', None)]),
                  ('%3D', [('%3D', None)]),
                  ('%26=%3D', [('%26', '%3D')]),
                  ('%3D=%26', [('%3D', '%26')]),
                  ('%2B=%2B', [('%2B', '%2B')])]


    def test_querify(self):
        """
        L{url.querify} should compose x-www-form-urlencoded strings.
        """
        for (q, p) in self.queryPairs:
            self.assertEquals(url.querify(p), q)
            for (q2, p2) in self.queryPairs:
                self.assertEquals(url.querify(p+p2), q+'&'+q2)


    def test_unquerify(self):
        """
        L{url.unquerify} should decompose x-www-form-urlencoded strings.
        """
        for (q, p) in self.queryPairs:
            self.assertEquals(url.unquerify(q), p)
            for (q2, p2) in self.queryPairs:
                self.assertEquals(url.unquerify(q+'&'+q2), p+p2)


    def test_querifyEmpty(self):
        """
        L{url.querify} should coalesce empty fields.
        """
        for p in [[], [('', None)], [('', None), ('', None)]]:
            self.assertEquals(url.querify(p), '')


    def test_unquerifyEmpty(self):
        """
        L{url.unquerify} should coalesce empty fields.
        """
        for q in ['', '&', '&&']:
            self.assertEquals(url.unquerify(q), [])


    def test_unquerifyPlus(self):
        """
        L{url.unquerify} should replace C{'+'} with C{' '}.
        """
        self.assertEquals(url.unquerify('foo=bar+baz'), [('foo', 'bar baz')])



class _IncompatibleSignatureURL(URL):
    """
    A test fixture for verifying that subclasses which override C{cloneURL}
    won't be copied by any other means (e.g. constructing C{self.__class___}
    directly).  It accomplishes this by having a constructor signature which
    is incompatible with L{URL}'s.
    """
    def __init__(
        self, magicValue, scheme, netloc, pathsegs, querysegs, fragment):
        URL.__init__(self, scheme, netloc, pathsegs, querysegs, fragment)
        self.magicValue = magicValue


    def cloneURL(self, scheme, netloc, pathsegs, querysegs, fragment):
        """
        Override the base implementation to pass along C{self.magicValue}.
        """
        return self.__class__(
            self.magicValue, scheme, netloc, pathsegs, querysegs, fragment)



class TestURL(TestCase):
    """
    Tests for L{URL}.
    """

    def assertUnicoded(self, u):
        """
        The given L{URL}'s components should be L{unicode}.
        """
        self.assertTrue(isinstance(u.scheme, unicode), repr(u))
        self.assertTrue(isinstance(u.netloc, unicode), repr(u))
        for seg in u.pathList():
            self.assertTrue(isinstance(seg, unicode), repr(u))
        for (k, v) in u.queryList():
            self.assertTrue(isinstance(k, unicode), repr(u))
            self.assertTrue(v is None or isinstance(v, unicode), repr(u))
        self.assertTrue(isinstance(u.fragment, unicode), repr(u))


    def assertURL(self, u, scheme, netloc, pathsegs, querysegs, fragment):
        """
        The given L{URL} should have the given components.
        """
        self.assertEqual(
            (u.scheme, u.netloc, u.pathList(), u.queryList(), u.fragment),
            (scheme, netloc, pathsegs, querysegs, fragment))


    def test_initDefaults(self):
        """
        L{URL} should have appropriate default values.
        """
        for u in [URL(),
                  URL(u'http', u'', None, None, None),
                  URL(u'http', u'', [u''], [], u''),
                  URL('http', '', [''], [], '')]:
            self.assertUnicoded(u)
            self.assertURL(u, u'http', u'', [u''], [], u'')


    def test_initASCII(self):
        """
        L{URL} should percent-decode its parameters, and coerce L{str} to
        L{unicode}.
        """
        for u in [URL(u's', u'h', [u'p'], [(u'k', u'v'), (u'k', None)], u'f'),
                  URL('s', 'h', ['p'], [('k', 'v'), ('k', None)], 'f'),
                  URL(u's', u'%68', [u'%70'], [(u'%6B', u'%76'), (u'%6B', None)], u'%66'),
                  URL('s', '%68', ['%70'], [('%6B', '%76'), ('%6B', None)], '%66')]:
            self.assertUnicoded(u)
            self.assertURL(u, u's', u'h', [u'p'], [(u'k', u'v'), (u'k', None)], u'f')


    def test_initUnicode(self):
        """
        L{URL} should accept non-ASCII L{unicode} parameters, and decode
        non-ASCII L{str} parameters according to RFC 3987.
        """
        for u in [URL(u'http', u'\xe0', [u'\xe9'],
                      [(u'\u03bb', u'\u03c0')], u'\u22a5'),
                  URL('http', '%C3%A0', ['%C3%A9'],
                      [('%CE%BB', '%CF%80')], '%E2%8A%A5')]:
            self.assertUnicoded(u)
            self.assertURL(u, u'http', u'\xe0', [u'\xe9'],
                           [(u'\u03bb', u'\u03c0')], u'\u22a5')


    def test_initNonString(self):
        """
        L{URL} should store non-string parameters (flattenables) as-is.
        """
        for f in [5, lambda: 5, tags.slot('five')]:
            self.assertURL(URL(u'http', u'', [f], [(f, f)], f),
                           u'http', u'', [f], [(f, f)], f)


    def test_repr(self):
        """
        L{URL.__repr__} should return something meaningful.
        """
        self.assertEquals(
            repr(URL(scheme='http', netloc='foo', pathsegs=['bar'],
                     querysegs=[('baz', None), ('k', 'v')], fragment='frob')),
            "URL(scheme=u'http', netloc=u'foo', pathsegs=[u'bar'], "
                "querysegs=[(u'baz', None), (u'k', u'v')], fragment=u'frob')")


    def test_fromString(self):
        urlpath = URL.fromString(theurl)
        self.assertEquals(theurl, str(urlpath))

    def test_roundtrip(self):
        tests = (
            "http://localhost",
            "http://localhost/",
            "http://localhost/foo",
            "http://localhost/foo/",
            "http://localhost/foo!!bar/",
            "http://localhost/foo%20bar/",
            "http://localhost/foo%2Fbar/",
            "http://localhost/foo?n",
            "http://localhost/foo?n=v",
            "http://localhost/foo?n=/a/b",
            "http://example.com/foo!@$bar?b!@z=123",
            "http://localhost/asd?a=asd%20sdf/345",
            "http://(%2525)/(%2525)?(%2525)&(%2525)=(%2525)#(%2525)",
            "http://(%C3%A9)/(%C3%A9)?(%C3%A9)&(%C3%A9)=(%C3%A9)#(%C3%A9)",
            )
        for test in tests:
            result = str(URL.fromString(test))
            self.assertEquals(test, result)

    def test_fromRequest(self):
        request = FakeRequest(uri='/a/nice/path/?zot=23&zut',
                              currentSegments=["a", "nice", "path", ""],
                              headers={'host': 'www.foo.com:80'})
        urlpath = URL.fromRequest(request)
        self.assertEquals(theurl, str(urlpath))

    def test_fromContext(self):

        r = FakeRequest(uri='/a/b/c')
        urlpath = URL.fromContext(context.RequestContext(tag=r))
        self.assertEquals('http://localhost/', str(urlpath))

        r.prepath = ['a']
        urlpath = URL.fromContext(context.RequestContext(tag=r))
        self.assertEquals('http://localhost/a', str(urlpath))

        r = FakeRequest(uri='/a/b/c?foo=bar')
        r.prepath = ['a','b']
        urlpath = URL.fromContext(context.RequestContext(tag=r))
        self.assertEquals('http://localhost/a/b?foo=bar', str(urlpath))

    def test_equality(self):
        urlpath = URL.fromString(theurl)
        self.failUnlessEqual(urlpath, URL.fromString(theurl))
        self.failIfEqual(urlpath, URL.fromString('ftp://www.anotherinvaliddomain.com/foo/bar/baz/?zot=21&zut'))


    def test_fragmentEquality(self):
        """
        An URL created with the empty string for a fragment compares equal
        to an URL created with C{None} for a fragment.
        """
        self.assertEqual(URL(fragment=''), URL(fragment=None))


    def test_parent(self):
        urlpath = URL.fromString(theurl)
        self.assertEquals("http://www.foo.com:80/a/nice/?zot=23&zut",
                          str(urlpath.parent()))


    def test_path(self):
        """
        L{URL.path} should be a C{str} giving the I{path} portion of the URL
        only.  Certain bytes should not be quoted.
        """
        urlpath = URL.fromString("http://example.com/foo/bar?baz=quux#foobar")
        self.assertEqual(urlpath.path, "foo/bar")
        urlpath = URL.fromString("http://example.com/foo%2Fbar?baz=quux#foobar")
        self.assertEqual(urlpath.path, "foo%2Fbar")
        urlpath = URL.fromString("http://example.com/-_.!*'()?baz=quux#foo")
        self.assertEqual(urlpath.path, "-_.!*'()")


    def test_parentdir(self):
        urlpath = URL.fromString(theurl)
        self.assertEquals("http://www.foo.com:80/a/nice/?zot=23&zut",
                          str(urlpath.parentdir()))
        urlpath = URL.fromString('http://www.foo.com/a')
        self.assertEquals("http://www.foo.com/",
                          str(urlpath.parentdir()))
        urlpath = URL.fromString('http://www.foo.com/a/')
        self.assertEquals("http://www.foo.com/",
                          str(urlpath.parentdir()))
        urlpath = URL.fromString('http://www.foo.com/a/b')
        self.assertEquals("http://www.foo.com/",
                          str(urlpath.parentdir()))
        urlpath = URL.fromString('http://www.foo.com/a/b/')
        self.assertEquals("http://www.foo.com/a/",
                          str(urlpath.parentdir()))
        urlpath = URL.fromString('http://www.foo.com/a/b/c')
        self.assertEquals("http://www.foo.com/a/",
                          str(urlpath.parentdir()))
        urlpath = URL.fromString('http://www.foo.com/a/b/c/')
        self.assertEquals("http://www.foo.com/a/b/",
                          str(urlpath.parentdir()))
        urlpath = URL.fromString('http://www.foo.com/a/b/c/d')
        self.assertEquals("http://www.foo.com/a/b/",
                          str(urlpath.parentdir()))
        urlpath = URL.fromString('http://www.foo.com/a/b/c/d/')
        self.assertEquals("http://www.foo.com/a/b/c/",
                          str(urlpath.parentdir()))

    def test_parent_root(self):
        urlpath = URL.fromString('http://www.foo.com/')
        self.assertEquals("http://www.foo.com/",
                          str(urlpath.parentdir()))
        self.assertEquals("http://www.foo.com/",
                          str(urlpath.parentdir().parentdir()))

    def test_child(self):
        urlpath = URL.fromString(theurl)
        self.assertEquals("http://www.foo.com:80/a/nice/path/gong?zot=23&zut",
                          str(urlpath.child('gong')))
        self.assertEquals("http://www.foo.com:80/a/nice/path/gong%2F?zot=23&zut",
                          str(urlpath.child('gong/')))
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/gong%2Fdouble?zot=23&zut",
            str(urlpath.child('gong/double')))
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/gong%2Fdouble%2F?zot=23&zut",
            str(urlpath.child('gong/double/')))

    def test_child_init_tuple(self):
        self.assertEquals(
            "http://www.foo.com/a/b/c",
            str(URL(netloc="www.foo.com",
                        pathsegs=['a', 'b']).child("c")))

    def test_child_init_root(self):
        self.assertEquals(
            "http://www.foo.com/c",
            str(URL(netloc="www.foo.com").child("c")))

    def test_sibling(self):
        urlpath = URL.fromString(theurl)
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/sister?zot=23&zut",
            str(urlpath.sibling('sister')))
        # use an url without trailing '/' to check child removal
        theurl2 = "http://www.foo.com:80/a/nice/path?zot=23&zut"
        urlpath = URL.fromString(theurl2)
        self.assertEquals(
            "http://www.foo.com:80/a/nice/sister?zot=23&zut",
            str(urlpath.sibling('sister')))

    def test_curdir(self):
        urlpath = URL.fromString(theurl)
        self.assertEquals(theurl, str(urlpath))
        # use an url without trailing '/' to check object removal
        theurl2 = "http://www.foo.com:80/a/nice/path?zot=23&zut"
        urlpath = URL.fromString(theurl2)
        self.assertEquals("http://www.foo.com:80/a/nice/?zot=23&zut",
                          str(urlpath.curdir()))

    def test_click(self):
        urlpath = URL.fromString(theurl)
        # a null uri should be valid (return here)
        self.assertEquals("http://www.foo.com:80/a/nice/path/?zot=23&zut",
                          str(urlpath.click("")))
        # a simple relative path remove the query
        self.assertEquals("http://www.foo.com:80/a/nice/path/click",
                          str(urlpath.click("click")))
        # an absolute path replace path and query
        self.assertEquals("http://www.foo.com:80/click",
                          str(urlpath.click("/click")))
        # replace just the query
        self.assertEquals("http://www.foo.com:80/a/nice/path/?burp",
                          str(urlpath.click("?burp")))
        # one full url to another should not generate '//' between netloc and pathsegs
        self.failIfIn("//foobar", str(urlpath.click('http://www.foo.com:80/foobar')))

        # from a url with no query clicking a url with a query,
        # the query should be handled properly
        u = URL.fromString('http://www.foo.com:80/me/noquery')
        self.failUnlessEqual('http://www.foo.com:80/me/17?spam=158',
                             str(u.click('/me/17?spam=158')))

        # Check that everything from the path onward is removed when the click link
        # has no path.
        u = URL.fromString('http://localhost/foo?abc=def')
        self.failUnlessEqual(str(u.click('http://www.python.org')), 'http://www.python.org/')


    def test_cloneUnchanged(self):
        """
        Verify that L{URL.cloneURL} doesn't change any of the arguments it
        is passed.
        """
        urlpath = URL.fromString('https://x:1/y?z=1#A')
        self.assertEqual(
            urlpath.cloneURL(urlpath.scheme,
                             urlpath.netloc,
                             urlpath._qpathlist,
                             urlpath._querylist,
                             urlpath.fragment),
            urlpath)


    def _makeIncompatibleSignatureURL(self, magicValue):
        return _IncompatibleSignatureURL(magicValue, '', '', None, None, '')


    def test_clickCloning(self):
        """
        Verify that L{URL.click} uses L{URL.cloneURL} to construct its
        return value.
        """
        urlpath = self._makeIncompatibleSignatureURL(8789)
        self.assertEqual(urlpath.click('/').magicValue, 8789)


    def test_clickCloningScheme(self):
        """
        Verify that L{URL.click} uses L{URL.cloneURL} to construct its
        return value, when the clicked url has a scheme.
        """
        urlpath = self._makeIncompatibleSignatureURL(8031)
        self.assertEqual(urlpath.click('https://foo').magicValue, 8031)


    def test_addCloning(self):
        """
        Verify that L{URL.add} uses L{URL.cloneURL} to construct its
        return value.
        """
        urlpath = self._makeIncompatibleSignatureURL(8789)
        self.assertEqual(urlpath.add('x').magicValue, 8789)


    def test_replaceCloning(self):
        """
        Verify that L{URL.replace} uses L{URL.cloneURL} to construct
        its return value.
        """
        urlpath = self._makeIncompatibleSignatureURL(8789)
        self.assertEqual(urlpath.replace('x').magicValue, 8789)


    def test_removeCloning(self):
        """
        Verify that L{URL.remove} uses L{URL.cloneURL} to construct
        its return value.
        """
        urlpath = self._makeIncompatibleSignatureURL(8789)
        self.assertEqual(urlpath.remove('x').magicValue, 8789)


    def test_clearCloning(self):
        """
        Verify that L{URL.clear} uses L{URL.cloneURL} to construct its
        return value.
        """
        urlpath = self._makeIncompatibleSignatureURL(8789)
        self.assertEqual(urlpath.clear().magicValue, 8789)


    def test_anchorCloning(self):
        """
        Verify that L{URL.anchor} uses L{URL.cloneURL} to construct
        its return value.
        """
        urlpath = self._makeIncompatibleSignatureURL(8789)
        self.assertEqual(urlpath.anchor().magicValue, 8789)


    def test_secureCloning(self):
        """
        Verify that L{URL.secure} uses L{URL.cloneURL} to construct its
        return value.
        """
        urlpath = self._makeIncompatibleSignatureURL(8789)
        self.assertEqual(urlpath.secure().magicValue, 8789)


    def test_clickCollapse(self):
        tests = [
            ['http://localhost/', '.', 'http://localhost/'],
            ['http://localhost/', '..', 'http://localhost/'],
            ['http://localhost/a/b/c', '.', 'http://localhost/a/b/'],
            ['http://localhost/a/b/c', '..', 'http://localhost/a/'],
            ['http://localhost/a/b/c', './d/e', 'http://localhost/a/b/d/e'],
            ['http://localhost/a/b/c', '../d/e', 'http://localhost/a/d/e'],
            ['http://localhost/a/b/c', '/./d/e', 'http://localhost/d/e'],
            ['http://localhost/a/b/c', '/../d/e', 'http://localhost/d/e'],
            ['http://localhost/a/b/c/', '../../d/e/', 'http://localhost/a/d/e/'],
            ['http://localhost/a/./c', '../d/e', 'http://localhost/d/e'],
            ['http://localhost/a/./c/', '../d/e', 'http://localhost/a/d/e'],
            ['http://localhost/a/b/c/d', './e/../f/../g', 'http://localhost/a/b/c/g'],
            ['http://localhost/a/b/c', 'd//e', 'http://localhost/a/b/d//e'],
            ]
        for start, click, result in tests:
            self.assertEquals(
                str(URL.fromString(start).click(click)),
                result
                )

    def test_add(self):
        urlpath = URL.fromString(theurl)
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/?zot=23&zut&burp",
            str(urlpath.add("burp")))
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/?zot=23&zut&burp=xxx",
            str(urlpath.add("burp", "xxx")))
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/?zot=23&zut&burp=xxx&zing",
            str(urlpath.add("burp", "xxx").add("zing")))
        # note the inversion!
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/?zot=23&zut&zing&burp=xxx",
            str(urlpath.add("zing").add("burp", "xxx")))
        # note the two values for the same name
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/?zot=23&zut&burp=xxx&zot=32",
            str(urlpath.add("burp", "xxx").add("zot", 32)))

    def test_add_noquery(self):
        # fromString is a different code path, test them both
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/?foo=bar",
            str(URL.fromString("http://www.foo.com:80/a/nice/path/")
                .add("foo", "bar")))
        self.assertEquals(
            "http://www.foo.com/?foo=bar",
            str(URL(netloc="www.foo.com").add("foo", "bar")))

    def test_replace(self):
        urlpath = URL.fromString(theurl)
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/?zot=32&zut",
            str(urlpath.replace("zot", 32)))
        # replace name without value with name/value and vice-versa
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/?zot&zut=itworked",
            str(urlpath.replace("zot").replace("zut", "itworked")))
        # Q: what happens when the query has two values and we replace?
        # A: we replace both values with a single one
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/?zot=32&zut",
            str(urlpath.add("zot", "xxx").replace("zot", 32)))

    def test_fragment(self):
        urlpath = URL.fromString(theurl)
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/?zot=23&zut#hiboy",
            str(urlpath.anchor("hiboy")))
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/?zot=23&zut",
            str(urlpath.anchor()))
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/?zot=23&zut",
            str(urlpath.anchor('')))

    def test_clear(self):
        urlpath = URL.fromString(theurl)
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/?zut",
            str(urlpath.clear("zot")))
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/?zot=23",
            str(urlpath.clear("zut")))
        # something stranger, query with two values, both should get cleared
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/?zut",
            str(urlpath.add("zot", 1971).clear("zot")))
        # two ways to clear the whole query
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/",
            str(urlpath.clear("zut").clear("zot")))
        self.assertEquals(
            "http://www.foo.com:80/a/nice/path/",
            str(urlpath.clear()))

    def test_secure(self):
        self.assertEquals(str(URL.fromString('http://localhost/').secure()), 'https://localhost/')
        self.assertEquals(str(URL.fromString('http://localhost/').secure(True)), 'https://localhost/')
        self.assertEquals(str(URL.fromString('https://localhost/').secure()), 'https://localhost/')
        self.assertEquals(str(URL.fromString('https://localhost/').secure(False)), 'http://localhost/')
        self.assertEquals(str(URL.fromString('http://localhost/').secure(False)), 'http://localhost/')
        self.assertEquals(str(URL.fromString('http://localhost/foo').secure()), 'https://localhost/foo')
        self.assertEquals(str(URL.fromString('http://localhost/foo?bar=1').secure()), 'https://localhost/foo?bar=1')
        self.assertEquals(str(URL.fromString('http://localhost/').secure(port=443)), 'https://localhost/')
        self.assertEquals(str(URL.fromString('http://localhost:8080/').secure(port=8443)), 'https://localhost:8443/')
        self.assertEquals(str(URL.fromString('https://localhost:8443/').secure(False, 8080)), 'http://localhost:8080/')


    def test_eq_same(self):
        u = URL.fromString('http://localhost/')
        self.failUnless(u == u, "%r != itself" % u)

    def test_eq_similar(self):
        u1 = URL.fromString('http://localhost/')
        u2 = URL.fromString('http://localhost/')
        self.failUnless(u1 == u2, "%r != %r" % (u1, u2))

    def test_eq_different(self):
        u1 = URL.fromString('http://localhost/a')
        u2 = URL.fromString('http://localhost/b')
        self.failIf(u1 == u2, "%r != %r" % (u1, u2))

    def test_eq_apples_vs_oranges(self):
        u = URL.fromString('http://localhost/')
        self.failIf(u == 42, "URL must not equal a number.")
        self.failIf(u == object(), "URL must not equal an object.")

    def test_ne_same(self):
        u = URL.fromString('http://localhost/')
        self.failIf(u != u, "%r == itself" % u)

    def test_ne_similar(self):
        u1 = URL.fromString('http://localhost/')
        u2 = URL.fromString('http://localhost/')
        self.failIf(u1 != u2, "%r == %r" % (u1, u2))

    def test_ne_different(self):
        u1 = URL.fromString('http://localhost/a')
        u2 = URL.fromString('http://localhost/b')
        self.failUnless(u1 != u2, "%r == %r" % (u1, u2))

    def test_ne_apples_vs_oranges(self):
        u = URL.fromString('http://localhost/')
        self.failUnless(u != 42, "URL must differ from a number.")
        self.failUnless(u != object(), "URL must be differ from an object.")

    def test_parseEqualInParamValue(self):
        u = URL.fromString('http://localhost/?=x=x=x')
        self.failUnless(u.query == ['=x=x=x'])
        self.failUnless(str(u) == 'http://localhost/?=x=x=x')
        u = URL.fromString('http://localhost/?foo=x=x=x&bar=y')
        self.failUnless(u.query == ['foo=x=x=x', 'bar=y'])
        self.failUnless(str(u) == 'http://localhost/?foo=x=x=x&bar=y')

class Serialization(TestCase):

    def testQuoting(self):
        context = None
        scheme = 'http'
        loc = 'localhost'
        path = ('baz', 'buz', '/fuzz/')
        query = [("foo", "bar"), ("baz", "=quux"), ("foobar", "?")]
        fragment = 'futz'
        u = URL(scheme, loc, path, query, fragment)
        s = flatten(URL(scheme, loc, path, query, fragment))

        parsedScheme, parsedLoc, parsedPath, parsedQuery, parsedFragment = urlparse.urlsplit(s)

        self.assertEquals(scheme, parsedScheme)
        self.assertEquals(loc, parsedLoc)
        self.assertEquals('/' + '/'.join(map(lambda p: urllib.quote(p,safe=''),path)), parsedPath)
        self.assertEquals(parsedQuery.split('&amp;'),
                          ['foo=bar', 'baz==quux', 'foobar=?'])
        self.assertEquals(query,
                          url.unquerify(parsedQuery.replace('&amp;', '&')))
        self.assertEquals(fragment, parsedFragment)

    def test_slotQueryParam(self):
        original = 'http://foo/bar?baz=bamf'
        u = URL.fromString(original)
        u = u.add('toot', tags.slot('param'))

        def fillIt(ctx, data):
            ctx.fillSlots('param', 5)
            return ctx.tag

        self.assertEquals(flatten(tags.invisible(render=fillIt)[u]),
                          original + '&amp;toot=5')

    def test_childQueryParam(self):
        original = 'http://foo/bar'
        u = URL.fromString(original)
        u = u.child(tags.slot('param'))

        def fillIt(ctx, data):
            ctx.fillSlots('param', 'baz')
            return ctx.tag

        self.assertEquals(flatten(tags.invisible(render=fillIt)[u]), original + '/baz')

    def test_strangeSegs(self):
        base = 'http://localhost/'
        tests = (
            (r'/foo/', '%2Ffoo%2F'),
            (r'c:\foo\bar bar', 'c:%5Cfoo%5Cbar%20bar'),
            (r'&<>', '&amp;%3C%3E'),
            (u'!"\N{POUND SIGN}$%^&*()_+'.encode('utf-8'), '!%22%C2%A3$%25%5E&amp;*()_+'),
            )
        for test, result in tests:
            u = URL.fromString(base).child(test)
            self.assertEquals(flatten(u), base+result)

    def test_urlContent(self):
        u = URL.fromString('http://localhost/').child(r'<c:\foo\bar&>')
        self.assertEquals(flatten(tags.p[u]), '<p>http://localhost/%3Cc:%5Cfoo%5Cbar&amp;%3E</p>')

    def test_urlAttr(self):
        u = URL.fromString('http://localhost/').child(r'<c:\foo\bar&>')
        self.assertEquals(flatten(tags.img(src=u)), '<img src="http://localhost/%3Cc:%5Cfoo%5Cbar&amp;%3E" />')

    def test_urlSlot(self):
        u = URL.fromString('http://localhost/').child(r'<c:\foo\bar&>')
        tag = tags.img(src=tags.slot('src'))
        tag.fillSlots('src', u)
        self.assertEquals(flatten(tag), '<img src="http://localhost/%3Cc:%5Cfoo%5Cbar&amp;%3E" />')

    def test_urlXmlAttrSlot(self):
        u = URL.fromString('http://localhost/').child(r'<c:\foo\bar&>')
        tag = tags.invisible[loaders.xmlstr('<img xmlns:n="http://nevow.com/ns/nevow/0.1" src="#"><n:attr name="src"><n:slot name="src"/></n:attr></img>')]
        tag.fillSlots('src', u)
        self.assertEquals(flatten(tag), '<img src="http://localhost/%3Cc:%5Cfoo%5Cbar&amp;%3E" />')

    def test_safe(self):
        u = URL.fromString('http://localhost/').child(r"foo-_.!*'()bar")
        self.assertEquals(flatten(tags.p[u]), r"<p>http://localhost/foo-_.!*'()bar</p>")

    def test_urlintagwithmultipleamps(self):
        """
        Test the serialization of an URL with an ampersand in it as an
        attribute value.

        The ampersand must be quoted for the attribute to be valid.
        """
        tag = tags.invisible[tags.a(href=URL.fromString('http://localhost/').add('foo', 'bar').add('baz', 'spam'))]
        self.assertEquals(flatten(tag), '<a href="http://localhost/?foo=bar&amp;baz=spam"></a>')

        tag = tags.invisible[loaders.xmlstr('<a xmlns:n="http://nevow.com/ns/nevow/0.1" href="#"><n:attr name="href"><n:slot name="href"/></n:attr></a>')]
        tag.fillSlots('href', URL.fromString('http://localhost/').add('foo', 'bar').add('baz', 'spam'))
        self.assertEquals(flatten(tag), '<a href="http://localhost/?foo=bar&amp;baz=spam"></a>')


    def test_rfc1808(self):
        """Test the relative link resolving stuff I found in rfc1808 section 5.
        """
        base = URL.fromString(rfc1808_relative_link_base)
        for link, result in rfc1808_relative_link_tests:
            #print link
            self.failUnlessEqual(result, flatten(base.click(link)))
    test_rfc1808.todo = 'Many of these fail miserably at the moment; often with a / where there shouldn\'t be'


    def test_unicode(self):
        """
        L{URLSerializer} should provide basic IRI (RFC 3987) support by
        encoding Unicode to UTF-8 before percent-encoding.
        """
        iri = u'http://localhost/expos\xe9?doppelg\xe4nger=Bryan O\u2019Sullivan#r\xe9sum\xe9'
        uri = 'http://localhost/expos%C3%A9?doppelg%C3%A4nger=Bryan%20O%E2%80%99Sullivan#r%C3%A9sum%C3%A9'
        self.assertEquals(flatten(URL.fromString(iri)), uri)



class RedirectResource(TestCase):
    """Test the url redirect resource adapters.
    """

    def renderResource(self, u):
        request = FakeRequest()
        ctx = context.RequestContext(tag=request)
        return util.maybeDeferred(inevow.IResource(u).renderHTTP, ctx).addCallback(
            lambda r: (r, request.redirected_to))


    def test_urlRedirect(self):
        u = "http://localhost/"
        D = self.renderResource(URL.fromString(u))
        def after((html, redirected_to)):
            self.assertIn(u, html)
            self.assertEquals(u, redirected_to)
        return D.addCallback(after)


    def test_urlRedirectWithParams(self):
        D = self.renderResource(URL.fromString("http://localhost/").child('child').add('foo', 'bar'))
        def after((html, redirected_to)):
            self.assertIn("http://localhost/child?foo=bar", html)
            self.assertEquals("http://localhost/child?foo=bar", redirected_to)
        return D.addCallback(after)


    def test_deferredURLParam(self):
        D = self.renderResource(
            URL.fromString("http://localhost/")
            .child(util.succeed('child')).add('foo',util.succeed('bar'))
            )
        def after((html, redirected_to)):
            self.assertIn("http://localhost/child?foo=bar", html)
            self.assertEquals("http://localhost/child?foo=bar", redirected_to)
        return D.addCallback(after)


    def test_deferredURLOverlayParam(self):
        D = self.renderResource(url.here.child(util.succeed('child')).add('foo',util.succeed('bar')))
        def after((html, redirected_to)):
            self.assertIn("http://localhost/child?foo=bar", html)
            self.assertEquals("http://localhost/child?foo=bar", redirected_to)
        return D.addCallback(after)



__doctests__ = ['nevow.url']
