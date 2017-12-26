# Copyright (c) 2004 Divmod.
# See LICENSE for details.


from nevow import stan
from nevow.testutil import TestCase

class TestProto(TestCase):
    def test_proto(self):
        tagName = "hello"
        proto = stan.Proto(tagName)
        self.assertEqual(tagName, str(proto))

    def test_callCreatesTag(self):
        proto = stan.Proto("hello")
        tag = proto(world="1")
        self.assertEqual(proto, tag.tagName)
        self.assertEqual(tag.attributes['world'], '1')

    def test_getItemCreatesTag(self):
        proto = stan.Proto("hello")
        tag = proto[proto]
        self.assertEqual(proto, tag.tagName)
        self.assertEqual(tag.children, [proto])


proto = stan.Proto("hello")


class TestTag(TestCase):
    def test_clone(self):
        tag = proto(hello="world")["How are you"]
        tag.fillSlots('foo', 'bar')
        tag.filename = "foo/bar"
        tag.lineNumber = 6
        tag.columnNumber = 12
        clone = tag.clone()
        self.assertEqual(clone.attributes['hello'], 'world')
        self.assertNotIdentical(clone.attributes, tag.attributes)
        self.assertEqual(clone.children, ["How are you"])
        self.assertNotIdentical(clone.children, tag.children)
        self.assertEqual(tag.slotData, clone.slotData)
        self.assertNotIdentical(tag.slotData, clone.slotData)
        self.assertEqual(clone.filename, "foo/bar")
        self.assertEqual(clone.lineNumber, 6)
        self.assertEqual(clone.columnNumber, 12)

    ## TODO: need better clone test here to test clone(deep=True),
    ## and behavior of cloning nested lists.

    def test_clear(self):
        tag = proto["these are", "children", "cool"]
        tag.clear()
        self.assertEqual(tag.children, [])

    def test_specials(self):
        tag = proto(data=1, render=str, remember="stuff", key="myKey", **{'pattern': "item"})
        self.assertEqual(tag.data, 1)
        self.assertEqual(getattr(tag, 'render'), str)
        self.assertEqual(tag.remember, "stuff")
        self.assertEqual(tag.key, "myKey")
        self.assertEqual(tag.pattern, "item")


    def test_visit(self):
        """
        Test that L{nevow.stan.visit} invokes the visitor it is given with all
        the nodes in the DOM it is given in pre-order.
        """
        visited = []
        def visitor(t):
            visited.append(t)
        root = stan.Proto('root')()
        firstChild = stan.Proto('firstChild')()
        secondChild = stan.Proto('secondChild')()
        firstGrandchild = stan.Proto('firstGrandchild')()
        secondGrandchild = stan.Proto('secondGrandchild')()
        thirdGrandchild = 'thirdGrandchild'
        root[firstChild, secondChild]
        secondChild[firstGrandchild, secondGrandchild, thirdGrandchild]
        stan.visit(root, visitor)
        self.assertEqual(
            visited,
            [root, firstChild, secondChild,
             firstGrandchild, secondGrandchild, thirdGrandchild])



class TestComment(TestCase):

    def test_notCallable(self):
        comment = stan.CommentProto()
        self.assertRaises(NotImplementedError, comment, id='oops')

class TestUnderscore(TestCase):
    def test_prefix(self):
        proto = stan.Proto('div')
        tag = proto()
        tag(_class='a')
        self.assertEqual(tag.attributes, {'class': 'a'})

    def test_suffix(self):
        proto = stan.Proto('div')
        tag = proto()
        tag(class_='a')
        self.assertEqual(tag.attributes, {'class': 'a'})
