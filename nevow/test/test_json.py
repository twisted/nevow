# Copyright (c) 2004 Divmod.
# See LICENSE for details.

from twisted.trial import unittest

from nevow import json, rend, page, loaders, tags, athena

TEST_OBJECTS = [
    0,
    None,
    True,
    False,
    [],
    [0],
    [0, 1, 2],
    [None, 1, 2],
    [None, u'one', 2],
    [True, False, u'string', 10],
    [[1, 2], [3, 4]],
    [[1.5, 2.5], [3.5, 4.5]],
    [0, [1, 2], [u'hello'], [u'world'], [True, None, False]],
    {},
    {u'foo': u'bar'},
    {u'foo': None},
    {u'bar': True},
    {u'baz': [1, 2, 3]},
    {u'quux': {u'bar': u'foo'}},
    ]

TEST_STRINGLIKE_OBJECTS = [
    u'',
    u'string',
    u'string with "embedded" quotes',
    u"string with 'embedded' single-quotes",
    u'string with \\"escaped embedded\\" quotes',
    u"string with \\'escaped embedded\\' single-quotes",
    u"string with backslashes\\\\",
    u"string with trailing accented vowels: \xe1\xe9\xed\xf3\xfa\xfd\xff",
    u"string with trailing control characters: \f\b\n\t\r",
    u'string with high codepoint characters: \u0111\u2222\u3333\u4444\uffff',
    u'string with very high codepoint characters: \U00011111\U00022222\U00033333\U00044444\U000fffff',
    ]


class DummyLivePage(object):
    """
    Stand-in for L{athena.LivePage} which implements only enough of its
    behavior so that a L{LiveFragment} or L{LiveElement} can be set as its
    child and flattened.
    """
    localCounter = 0

    def __init__(self):
        self.page = self
        self.liveFragmentChildren = []


    def addLocalObject(self, obj):
        """
        Return an Athena ID for the given object.  Returns a new value on every
        call.
        """
        self.localCounter += 1
        return self.localCounter


    def _shouldInclude(self, module):
        """
        Stub module-system method.  Always declares that the given module
        should not be included.
        """
        return False



class JavascriptObjectNotationTestCase(unittest.TestCase):

    def testSerialize(self):
        for struct in TEST_OBJECTS:
            json.serialize(struct)

    def testRoundtrip(self):
        for struct in TEST_OBJECTS:
            bytes = json.serialize(struct)
            unstruct = json.parse(bytes)
            self.assertEquals(
                unstruct, struct,
                "Failed to roundtrip %r: %r (through %r)" % (
                    struct, unstruct, bytes))

    def testStringlikeRountrip(self):
        for struct in TEST_STRINGLIKE_OBJECTS:
            bytes = json.serialize(struct)
            unstruct = json.parse(bytes)
            failMsg = "Failed to roundtrip %r: %r (through %r)" % (
                    struct, unstruct, bytes)
            self.assertEquals(unstruct, struct, failMsg)
            self.assert_(isinstance(unstruct, unicode), failMsg)

    def testScientificNotation(self):
        self.assertEquals(json.parse('1e10'), 10**10)
        self.assertEquals(json.parse('1e0'), 1)


    def testHexEscapedCodepoints(self):
        self.assertEquals(
            json.parse('"\\xe1\\xe9\\xed\\xf3\\xfa\\xfd"'),
            u"\xe1\xe9\xed\xf3\xfa\xfd")

    def testEscapedControls(self):
        self.assertEquals(
            json.parse('"\\f\\b\\n\\t\\r"'),
            u"\f\b\n\t\r")


    def _rendererTest(self, cls):
        self.assertEquals(
            json.serialize(
                cls(
                    docFactory=loaders.stan(tags.p['Hello, world.']))),
            '"<div xmlns=\\"http://www.w3.org/1999/xhtml\\"><p>Hello, world.</p></div>"')


    def test_fragmentSerialization(self):
        """
        Test that instances of L{nevow.rend.Fragment} serialize as an xhtml
        string.
        """
        return self._rendererTest(rend.Fragment)


    def test_elementSerialization(self):
        """
        Test that instances of L{nevow.page.Element} serialize as an xhtml
        string.
        """
        return self._rendererTest(page.Element)


    def _doubleSerialization(self, cls):
        fragment = cls(docFactory=loaders.stan(tags.div['Hello']))
        self.assertEqual(
            json.serialize(fragment),
            json.serialize(fragment))


    def test_doubleFragmentSerialization(self):
        """
        Test that repeatedly calling L{json.serialize} with an instance of
        L{rend.Fragment} results in the same result each time.
        """
        return self._doubleSerialization(rend.Fragment)


    def test_doubleElementSerialization(self):
        """
        Like L{test_doubleElementSerialization} but for L{page.Element}
        instances.
        """
        return self._doubleSerialization(page.Element)


    def _doubleLiveSerialization(self, cls, renderer):
        livePage = DummyLivePage()
        liveFragment = cls(
            docFactory=loaders.stan(
                tags.div(render=tags.directive(renderer))['Hello']))
        liveFragment.setFragmentParent(livePage)
        self.assertEqual(
            json.serialize(liveFragment),
            json.serialize(liveFragment))


    def test_doubleLiveFragmentSerialization(self):
        """
        Like L{test_doubleFragmentSerialization} but for L{athena.LiveFragment}
        instances.
        """
        return self._doubleLiveSerialization(athena.LiveFragment, 'liveFragment')


    def test_doubleLiveElementSerialization(self):
        """
        Like L{test_doubleFragmentSerialization} but for L{athena.LiveElement}
        instances.
        """
        return self._doubleLiveSerialization(athena.LiveElement, 'liveElement')
