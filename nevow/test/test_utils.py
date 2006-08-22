
"""

Test module for L{nevow.utils}

"""

from twisted.trial.unittest import TestCase

from nevow.util import UnexposedMethodError, Expose

class ExposeTestCase(TestCase):
    def test_singleExpose(self):
        """
        Test exposing a single method with a single call to an Expose instance.
        """
        expose = Expose()

        class Foo(object):
            def bar(self):
                return 'baz'
            expose(bar)

        self.assertEquals(list(expose.exposedMethodNames(Foo())), ['bar'])
        self.assertEquals(expose.get(Foo(), 'bar')(), 'baz')


    def test_multipleExposeCalls(self):
        """
        Test exposing multiple methods, each with a call to an Expose instance.
        """
        expose = Expose()

        class Foo(object):
            def bar(self):
                return 'baz'
            expose(bar)


            def quux(self):
                return 'fooble'
            expose(quux)


        self.assertEquals(list(expose.exposedMethodNames(Foo())), ['bar', 'quux'])
        self.assertEquals(expose.get(Foo(), 'bar')(), 'baz')
        self.assertEquals(expose.get(Foo(), 'quux')(), 'fooble')


    def test_multipleExposeArguments(self):
        """
        Test exposing multiple methods with a single call to an Expose
        instance.
        """
        expose = Expose()

        class Foo(object):
            def bar(self):
                return 'baz'

            def quux(self):
                return 'fooble'

            expose(bar, quux)

        self.assertEquals(list(expose.exposedMethodNames(Foo())), ['bar', 'quux'])
        self.assertEquals(expose.get(Foo(), 'bar')(), 'baz')
        self.assertEquals(expose.get(Foo(), 'quux')(), 'fooble')


    def test_inheritanceExpose(self):
        """
        Test that overridden methods are not exposed.
        """
        expose = Expose()

        class Foo(object):
            def bar(self):
                return 'baz'
            expose(bar)

        class Quux(Foo):
            def bar(self):
                return 'BAZ'

        self.assertEquals(list(expose.exposedMethodNames(Quux())), [])
        self.assertRaises(UnexposedMethodError, expose.get, Quux(), 'bar')


    def test_inheritanceReexpose(self):
        """
        Test that overridden methods can also be re-exposed.
        """
        expose = Expose()

        class Foo(object):
            def bar(self):
                return 'baz'
            expose(bar)

        class Quux(object):
            def bar(self):
                return 'smokey'
            expose(bar)

        self.assertEquals(list(expose.exposedMethodNames(Quux())), ['bar'])
        self.assertEquals(expose.get(Quux(), 'bar')(), 'smokey')


    def test_inheritanceExposeMore(self):
        """
        Test that expose calls in a subclass adds to the parent's exposed
        methods.
        """
        expose = Expose()

        class Foo(object):
            def bar(self):
                return 'baz'
            expose(bar)

        class Quux(Foo):
            def smokey(self):
                return 'stover'
            def pogo(self):
                return 'kelly'
            def albert(self):
                return 'alligator'
            expose(smokey, pogo)

        self.assertEquals(set(expose.exposedMethodNames(Quux())), set(['pogo', 'smokey', 'bar']))
        self.assertEquals(expose.get(Quux(), 'bar')(), 'baz')
        self.assertEquals(expose.get(Quux(), 'smokey')(), 'stover')
        self.assertEquals(expose.get(Quux(), 'pogo')(), 'kelly')
        self.assertRaises(UnexposedMethodError, expose.get, Quux(), 'albert')
        self.assertEquals(Quux().albert(), 'alligator')


    def test_multipleInheritanceExpose(self):
        """
        Test that anything exposed on the parents of a class which multiply
        inherits from several other class are all exposed on the subclass.
        """
        expose = Expose()

        class A(object):
            def foo(self):
                return 'bar'
            expose(foo)

        class B(object):
            def baz(self):
                return 'quux'
            expose(baz)

        class C(A, B):
            def quux(self):
                pass
            expose(quux)

        self.assertEquals(set(expose.exposedMethodNames(C())), set(['quux', 'foo', 'baz']))
        self.assertEquals(expose.get(C(), 'foo')(), 'bar')
        self.assertEquals(expose.get(C(), 'baz')(), 'quux')


    def test_multipleInheritanceExposeWithoutSubclassCall(self):
        """
        Test that anything exposed on the parents of a class which multiply
        inherits from several other class are all exposed on the subclass.
        """
        expose = Expose()

        class A(object):
            def foo(self):
                return 'bar'
            expose(foo)

        class B(object):
            def baz(self):
                return 'quux'
            expose(baz)

        class C(A, B):
            pass

        self.assertEquals(set(expose.exposedMethodNames(C())), set(['foo', 'baz']))
        self.assertEquals(expose.get(C(), 'foo')(), 'bar')
        self.assertEquals(expose.get(C(), 'baz')(), 'quux')


    def test_unexposedMethodInaccessable(self):
        """
        Test that trying to get a method which has not been exposed raises an
        exception.
        """
        expose = Expose()

        class A(object):
            def foo(self):
                return 'bar'

        self.assertRaises(UnexposedMethodError, expose.get, A(), 'foo')
        self.assertRaises(UnexposedMethodError, expose.get, A(), 'bar')


    def test_getUnexposedWithDefault(self):
        """
        Test that a default can be supplied to Expose.get and it is returned if
        and only if the requested method is not exposed.
        """
        expose = Expose()

        class A(object):
            def foo(self):
                return 'bar'
            expose(foo)

        self.assertEquals(expose.get(A(), 'foo', None)(), 'bar')
        self.assertEquals(expose.get(A(), 'bar', None), None)


    def test_exposeReturnValue(self):
        """
        Test that the first argument is returned by a call to an Expose
        instance.
        """
        expose = Expose()
        def f():
            pass
        def g():
            pass
        self.assertIdentical(expose(f), f)
        self.assertIdentical(expose(f, g), f)


    def test_exposeWithoutArguments(self):
        """
        Test that calling an Expose instance with no arguments raises a
        TypeError.
        """
        expose = Expose()
        self.assertRaises(TypeError, expose)


    def test_exposedInstanceAttribute(self):
        """
        Test that exposing an instance attribute works in basically the same
        way as exposing a class method and that the two do not interfer with
        each other.
        """
        expose = Expose()

        class Foo(object):
            def __init__(self):
                # Add an exposed instance attribute
                self.bar = expose(lambda: 'baz')

            def quux(self):
                return 'quux'
            expose(quux)

        self.assertEquals(
            set(expose.exposedMethodNames(Foo())),
            set(['bar', 'quux']))
        self.assertEquals(expose.get(Foo(), 'bar')(), 'baz')
        self.assertEquals(expose.get(Foo(), 'quux')(), 'quux')
