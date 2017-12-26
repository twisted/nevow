from nevow import tags, flat, context
from nevow.testutil import TestCase

class TestTags(TestCase):
    def test_directiveComparison(self):
        """
        Test that only directives with the same name compare equal.
        """
        foo = tags.directive('foo')
        foo2 = tags.directive('foo')
        bar = tags.directive('bar')
        self.assertEqual(foo, foo)
        self.assertEqual(foo, foo2)
        self.assertNotEqual(foo, bar)


    def test_directiveHashing(self):
        """
        Test that only directives with the same name hash to the same thing.
        """
        foo = tags.directive('foo')
        foo2 = tags.directive('foo')
        bar = tags.directive('bar')
        self.assertEqual(hash(foo), hash(foo2))

        # XXX What if 'foo' and 'bar' accidentally hash equal in some version
        # of Python?
        self.assertNotEqual(hash(foo), hash(bar))
