# Copyright (c) 2004 Divmod.
# See LICENSE for details.

from nevow.flat import ten
from nevow import tags

from nevow.testutil import TestCase


class TestSerialization(TestCase):
    def test_someTypes(self):
        self.assertEqual(ten.flatten(1), '1')
        self.assertEqual(ten.flatten([1,2,3]), '123')

    def test_nestedTags(self):
        self.assertEqual(
            ten.flatten(
                tags.html(hi='there')[
                    tags.body[ 42 ]]),
            '<html hi="there"><body>42</body></html>')

    def test_dynamic(self):
        self.assertEqual(
            ten.flatten(
                tags.html[
                    tags.body(render=lambda c, d: 'body!')]),
            '<html>body!</html>')

    def test_reallyDynamic(self):
        self.assertEqual(
            ten.flatten(
                tags.html[
                    lambda c, d: tags.body[
                        lambda c, d: 'stuff']]),
            '<html><body>stuff</body></html>')

    def test_serializeString(self):
        self.assertEqual(ten.flatten('one'), 'one')
        self.assertEqual(type(ten.flatten('<>')), tags.raw)
        self.assertEqual(ten.flatten('<abc&&>123'), '&lt;abc&amp;&amp;&gt;123')
        self.assertEqual(ten.flatten(tags.xml('<>&')), '<>&')
        self.assertEqual(ten.flatten(tags.xml('\xc2\xa3')), '\xc3\x82\xc2\xa3')
        
    def test_flattenTwice(self):
        """Test that flattening a string twice does not encode it twice.
        """
        self.assertEqual(ten.flatten(ten.flatten('&')), '&amp;')


class TestPrecompile(TestCase):
    def test_simple(self):
        self.assertEqual(ten.precompile(1), ['1'])

    def test_complex(self):
        self.assertEqual(ten.precompile(
            tags.html[
                tags.head[
                    tags.title["Hi"]],
                tags.body[
                    tags.div(style="color:red")["Bye"]]]),
            ['<html><head><title>Hi</title></head><body><div style="color:red">Bye</div></body></html>'])

    def test_dynamic(self):
        render = lambda c, d: 'one'
        result = ten.precompile(
            tags.html[
                render])
        prelude, dynamic, postlude = result
        self.assertEqual(prelude, '<html>')
        self.assertEqual(dynamic.tag.render, render)
        self.assertEqual(postlude, '</html>')
        self.assertEqual(ten.flatten(result), '<html>one</html>')

    def test_tagWithRender(self):
        render = lambda c, d: 'body'
        result = ten.precompile(
            tags.html[
                tags.body(render=render)])
        prelude, dynamic, postlude = result
        self.assertEqual(prelude, '<html>')
        self.assertEqual(dynamic.tag.render, render)
        self.assertEqual(postlude, '</html>')
        self.assertEqual(ten.flatten(result), '<html>body</html>')


import unicodedata
u = unicodedata.lookup('QUARTER NOTE')


class TestUnicode(TestCase):
    
    def test_it(self):
        self.assertEqual(ten.flatten(u), u.encode('utf8'))

    def test_unescaped(self):
        self.assertEqual(ten.flatten(tags.xml('<<<%s>>>' % u)), ('<<<%s>>>' % u).encode('utf8'))
    
class Registration(TestCase):
    def testBadRegister(self):
        try:
            ten.registerFlattener('adouijwd.dwijd hi mom', '1234567890')
        except:
            # Yay
            pass
        else:
            self.fail("Registering invalid flattener names raised no exception")
