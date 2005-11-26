# Copyright (c) 2004 Divmod.
# See LICENSE for details.

from twisted.trial import unittest

from nevow import json

TEST_OBJECTS = [
    0,
    None,
    True,
    False,
    u'string',
    u'string with "embedded" quotes',
    u"string with 'embedded' single-quotes",
    u'string with \\"escaped embedded\\" quotes',
    u"string with \\'escaped embedded\\' single-quotes",
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
    {'foo': u'bar'},
    {'foo': None},
    {'bar': True},
    {'baz': [1, 2, 3]},
    {'quux': {'bar': u'foo'}}]


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
