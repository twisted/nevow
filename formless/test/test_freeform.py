# Copyright (c) 2004 Divmod.
# See LICENSE for details.

from zope.interface import implements

from nevow import tags
from nevow import inevow
from nevow import context
from nevow import compy
from nevow import util

import formless
from formless import webform
from formless import iformless
from formless import configurable

from nevow.test import test_flatstan

class Base(test_flatstan.Base):
    implements(iformless.IConfigurableFactory)

    synchronousLocateConfigurable = False

    def locateConfigurable(self, *args, **kw):
        r = iformless.IConfigurable(self.conf)
        if not self.synchronousLocateConfigurable:
            r = util.succeed(r)
        return r

    def setupContext(self, *args, **kw):
        ctx = test_flatstan.Base.setupContext(self, *args, **kw)
        return context.PageContext(tag=tags.html(), parent=ctx)

    def render(self, tag, setupContext=lambda c:c):
        return test_flatstan.Base.render(
            self, tag, setupContext=setupContext)

    def renderForms(self, configurable, ctx=None, *args, **kwargs):
        self.conf = configurable
        if ctx is None:
            ctx = self.setupContext(False)
        ctx.remember(self, iformless.IConfigurableFactory)
        return self.render(
            webform.renderForms(*args, **kwargs),
            setupContext=lambda c: ctx)

    def postForm(self, ctx, obj, bindingName, args):
        self.conf = obj
        ctx.remember(self, iformless.IConfigurableFactory)
        try:
            posted = util.maybeDeferred(self.locateConfigurable,obj).addCallback(lambda x: x.postForm(
                ctx, bindingName, args
            ))
            if isinstance(posted, util.Deferred):
                posted = util.deferredResult(posted, 1)
        except formless.ValidateError, e:
            errors = ctx.locate(iformless.IFormErrors)
            ## Set the overall error for this form
            errors.setError(bindingName, e.formErrorMessage)
            errors.updateErrors(bindingName, e.errors)
            ctx.locate(iformless.IFormDefaults).getAllDefaults(bindingName).update(e.partialForm)
            return e


class Complete(Base):
    def test_configureProperty(self):
        class IStupid(formless.TypedInterface):
            foo = formless.String()

        class StupidThing(configurable.Configurable):
            implements(IStupid)

            def __init__(self):
                configurable.Configurable.__init__(self, None)
                self.foo = 'foo'

        dumb = StupidThing()

        val = self.renderForms(dumb)
        self.assertSubstring('freeform_post!!foo', val)
        self.assertSubstring('foo', val)
        self.assertSubstring('type="text"', val)
        self.assertSubstring('<input type="submit"', val)


    def test_configureMethod(self):
        class IDumb(formless.TypedInterface):
            def foo(self, bar=formless.String()):
                return formless.String()
            foo = formless.autocallable(foo)

        class DumbThing(configurable.Configurable):
            implements(IDumb)

            def foo(self, bar):
                return "baz"

        stupid = DumbThing(1)

        val = self.renderForms(stupid)
        self.assertSubstring('freeform_post!!foo', val)
        self.assertSubstring('foo', val)
        self.assertSubstring('bar', val)


class BuildingBlocksTest(Base):
    def test_1_renderTyped(self):
        binding = formless.Property('hello', formless.String(
            label="Hello",
            description="Hello, world."))

        ## Look up a renderer specific to the type of our binding, typedValue;
        renderer = iformless.ITypedRenderer(
            binding.typedValue, None, persist=False)
        
        ## But render the binding itself with this renderer
        ## The binding has the ".name" attribute we need
        val = self.render(tags.invisible(data=binding, render=renderer))

        self.assertSubstring('hello', val)
        self.assertSubstring('Hello', val)
        self.assertSubstring('Hello, world.', val)
        self.failIfSubstring('</form>', val)
        self.failIfSubstring('<input type="submit"', val)
        
        #print val
    test_1_renderTyped.todo = "Render binding"

    def test_2_renderPropertyBinding(self):
        binding = formless.Property('goodbye', formless.String(
            label="Goodbye",
            description="Goodbye cruel world"))

        # Look up an IBindingRenderer, which will render the form and the typed
        renderer = iformless.IBindingRenderer(binding)
        val = self.render(tags.invisible(data=binding, render=renderer))
        
        self.assertSubstring('<form ', val)
        self.assertSubstring('<input type="submit"', val)
        self.assertSubstring('name="goodbye"', val)
        self.assertSubstring('Goodbye', val)
        self.assertSubstring('Goodbye cruel world', val)
        
        #print val

    def test_3_renderMethodBinding(self):
        binding = formless.MethodBinding('doit', formless.Method(
            returnValue=None,
            arguments=[formless.Argument('foo', formless.String(label="Foo"))],
            label="Do It",
            description="Do it to 'em all"))

        renderer = iformless.IBindingRenderer(binding)
        val = self.render(tags.invisible(data=binding, render=renderer))

        self.assertSubstring('<form ', val)
        self.assertSubstring('Do It', val)
        self.assertSubstring("Do it to 'em all", val)
        self.assertSubstring("Foo", val)
        self.assertSubstring('name="foo"', val)
        #print val


class TestDefaults(Base):
    def test_1_renderWithDefaultValues(self):
        binding = formless.MethodBinding('haveFun', formless.Method(
            returnValue=None,
            arguments=[formless.Argument('funValue', formless.Integer(label="Fun Value", default=0))]
        ))

        def setupCtx(ctx):
            ctx.locate(iformless.IFormDefaults).setDefault('funValue', 15)
            return ctx

        renderer = iformless.IBindingRenderer(binding)
        val = self.render(tags.invisible(data=binding, render=renderer), setupContext=setupCtx)
        self.failIfSubstring('0', val)
        self.assertSubstring('15', val)

    def test_2_renderWithObjectPropertyValues(self):
        class IDefaultProperty(formless.TypedInterface):
            default = formless.Integer(default=2)

        class Foo(configurable.Configurable):
            implements(IDefaultProperty)
            default = 54

        val = self.renderForms(Foo(None))
        self.failIfSubstring('2', val)
        self.assertSubstring('54', val)

    def test_3_renderWithAdapteeAttributeValues(self):
        class IDefaultProperty(formless.TypedInterface):
            default = formless.Integer(default=2)

        class Adaptee(object):
            default = 69

        class Bar(configurable.Configurable):
            implements(IDefaultProperty)

        val = self.renderForms(Bar(Adaptee()))
        self.failIfSubstring('2', val)
        self.assertSubstring('69', val)

    def test_4_testBindingDefaults(self):
        class IBindingDefaults(formless.TypedInterface):
            def aMethod(self, foo=formless.String(default="The foo")):
                pass
            aMethod = formless.autocallable(aMethod)

            aProperty = formless.String(default="The property")

        class Implements(configurable.Configurable):
            implements(IBindingDefaults)

        val = self.renderForms(Implements(None))

        self.assertSubstring("The foo", val)
        self.assertSubstring("The property", val)

    def test_5_testDynamicDefaults(self):
        class IDynamicDefaults(formless.TypedInterface):
            def aMethod(self, foo=formless.String(default="NOTFOO")):
                pass
            def bMethod(self, foo=formless.String(default="NOTBAR")):
                pass
            aMethod = formless.autocallable(aMethod)
            bMethod = formless.autocallable(bMethod)

        class Implements(configurable.Configurable):
            implements(IDynamicDefaults)

        val = self.renderForms(Implements(None), bindingDefaults={
                'aMethod': {'foo': 'YESFOO'},
                'bMethod': {'foo': 'YESBAR'}})

        self.assertSubstring("YESFOO", val)
        self.assertSubstring("YESBAR", val)
        self.assertNotSubstring("NOTFOO", val)
        self.assertNotSubstring("NOTBAR", val)



class TestNonConfigurableSubclass(Base):
    def test_1_testSimple(self):
        class ISimpleTypedInterface(formless.TypedInterface):
            anInt = formless.Integer()
            def aMethod(self, aString = formless.String()):
                return None
            aMethod = formless.autocallable(aMethod)

        class ANonConfigurable(object): # Not subclassing Configurable
            implements(ISimpleTypedInterface) # But implements a TypedInterface

        val = self.renderForms(ANonConfigurable())
        self.assertSubstring('anInt', val)
        self.assertSubstring('aMethod', val)



class TestPostAForm(Base):
    def test_1_failAndSucceed(self):
        class IAPasswordMethod(formless.TypedInterface):
            def password(self, pword = formless.Password(), integer=formless.Integer()):
                pass
            password = formless.autocallable(password)

        class APasswordImplementation(object):
            implements(IAPasswordMethod)
            matched = False
            def password(self, pword, integer):
                self.matched = True
                return "password matched"

        theObj = APasswordImplementation()
        ctx = self.setupContext()

        result = self.postForm(ctx, theObj, "password", {"pword": ["these passwords"], "pword____2": ["don't match"], 'integer': ['Not integer']})

        self.assertEquals(theObj.matched, False)

        val = self.renderForms(theObj, ctx)

        self.assertSubstring("Passwords do not match. Please reenter.", val)
        self.assertSubstring('value="Not integer"', val)

    def test_2_propertyFailed(self):
        class IAProperty(formless.TypedInterface):
            prop = formless.Integer()

        class Impl(object):
            implements(IAProperty)
            prop = 5

        theObj = Impl()
        ctx = self.setupContext()
        result = self.postForm(ctx, theObj, 'prop', {'prop': ['bad']})
        val = self.renderForms(theObj, ctx)

        self.assertSubstring('value="bad"', val)


class TestRenderPropertyGroup(Base):
    def test_1_propertyGroup(self):
        class Outer(formless.TypedInterface):
            class Inner(formless.TypedInterface):
                one = formless.Integer()
                two = formless.Integer()

                def buckleMyShoe(self):
                    pass
                buckleMyShoe = formless.autocallable(buckleMyShoe)

                def buriedAlive(self):
                    pass
                buriedAlive = formless.autocallable(buriedAlive)

        class Implementation(object):
            implements(Outer)
            one = 1
            two = 2
            buckled = False
            buried = False
            def buckleMyShoe(self):
                self.buckled = True
            def buriedAlive(self):
                self.buried = True

        impl = Implementation()
        ctx = self.setupContext()
        val = self.renderForms(impl)

        self.postForm(ctx, impl, "Inner", {'one': ['Not an integer'], 'two': ['22']})

        self.assertEquals(impl.one, 1)
        self.assertEquals(impl.two, 2)
        self.assertEquals(impl.buckled, False)
        self.assertEquals(impl.buried, False)

        val = self.renderForms(impl, ctx)
        self.assertSubstring("is not an integer", val)
        # TODO: Get default values for property groups displaying properly.
        #self.assertSubstring('value="Not an integer"', val)

        self.postForm(ctx, impl, "Inner", {'one': ['11'], 'two': ['22']})

        self.assertEquals(impl.one, 11)
        self.assertEquals(impl.two, 22)
        self.assertEquals(impl.buckled, True)
        self.assertEquals(impl.buried, True)


class TestRenderMethod(Base):

    def testDefault(self):

        class IFoo(formless.TypedInterface):
            def foo(self, abc=formless.String()):
                pass
            foo = formless.autocallable(foo)

        class Impl:
            implements(IFoo)

        val = self.renderForms(Impl(), bindingNames=['foo'])
        self.assertSubstring('value="Foo"', val)
        self.assertSubstring('name="abc"', val)

    def testActionLabel(self):

        class IFoo(formless.TypedInterface):
            def foo(self, abc=formless.String()):
                pass
            foo = formless.autocallable(foo, action='FooFooFoo')

        class Impl:
            implements(IFoo)

        val = self.renderForms(Impl(), bindingNames=['foo'])
        self.assertSubstring('value="FooFooFoo"', val)
        self.assertSubstring('name="abc"', val)

    def testOneSigMultiCallables(self):

        class IFoo(formless.TypedInterface):
            def sig(self, abc=formless.String()):
                pass
            foo = formless.autocallable(sig)
            bar = formless.autocallable(sig, action='FooFooFOo')

        class Impl:
            implements(IFoo)

        val = self.renderForms(Impl(), bindingNames=['foo'])
        self.assertSubstring('value="Foo"', val)
        val = self.renderForms(Impl(), bindingNames=['bar'])
        self.assertSubstring('value="FooFooFoo"', val)

    testOneSigMultiCallables.todo = 'autocallable should not set attributes directly on the callable'


class TestCustomTyped(Base):
    def test_typedCoerceWithBinding(self):
        class MyTyped(formless.Typed):
            passed = False
            wasBoundTo = None
            def coerce(self, val, boundTo):
                self.passed = True
                self.wasBoundTo = boundTo
                return "passed"

        typedinst = MyTyped()

        class IMyInterface(formless.TypedInterface):
            def theFunc(self, test=typedinst):
                pass
            theFunc = formless.autocallable(theFunc)

        class Implementation(object):
            implements(IMyInterface)
            called = False
            def theFunc(self, test):
                self.called = True

        inst = Implementation()
        ctx = self.setupContext()
        self.postForm(ctx, inst, 'theFunc', {'test': ['a test value']})
        
        self.assertEquals(typedinst.passed, True)
        self.assertEquals(typedinst.wasBoundTo, inst)

        self.assertEquals(inst.called, True)


class TestUneditableProperties(Base):
    def test_uneditable(self):
        class Uneditable(formless.TypedInterface):
            aProp = formless.String(description="the description", immutable=True)

        class Impl(object):
            implements(Uneditable)
            
            aProp = property(lambda self: "HELLO")

        inst = Impl()

        val = self.renderForms(inst)
        self.assertSubstring('HELLO', val)
        self.failIfSubstring('type="text"', val)


class TestAfterValidation(Base):
    """Test post-validation rendering"""

    def test_property(self):
        """Test that, when validation fails, the value just entered is redisplayed"""

        class IThing(formless.TypedInterface):
            foo = formless.Integer()

        class Thing:
            implements(IThing)
            foo = 1

        inst = Thing()
        ctx = self.setupContext()
        self.postForm(ctx, inst, 'foo', {'foo': ['abc']})

        val = self.renderForms(inst, ctx)
        self.assertSubstring('value="abc"', val)


class TestHandAndStatus(Base):
    """Test that the method result is available as the hand, and that
    a reasonable status message string is available"""
    def test_hand(self):
        """Test that the hand and status message are available before redirecting the post
        """
        returnResult = object()
        class IMethod(formless.TypedInterface):
            def foo(self): pass
            foo = formless.autocallable(foo)

        class Method(object):
            implements(IMethod)
            def foo(self):
                return returnResult

        inst = Method()
        ctx = self.setupContext()
        self.postForm(ctx, inst, 'foo', {})
        self.assertEquals(ctx.locate(inevow.IHand), returnResult)
        self.assertEquals(ctx.locate(inevow.IStatusMessage), "'foo' success.")

    def test_handFactory(self):
        """Test that the hand and status message are available after redirecting the post
        """
        returnResult = object()
        status = 'horray'
        def setupRequest(r):
            r.args['_nevow_carryover_'] = ['abc']
            from nevow import rend
            rend._CARRYOVER['abc'] = compy.Componentized({inevow.IHand: returnResult, inevow.IStatusMessage: status})
            return r
        ctx = self.setupContext(setupRequest=setupRequest)

        self.assertEquals(ctx.locate(inevow.IHand), returnResult)
        self.assertEquals(ctx.locate(inevow.IStatusMessage), status)


class TestCharsetDetectionSupport(Base):

    def test_property(self):

        class ITest(formless.TypedInterface):
            foo = formless.String()

        class Impl:
            implements(ITest)

        impl = Impl()
        ctx = self.setupContext()
        val = self.renderForms(impl, ctx)
        self.assertIn('<input type="hidden" name="_charset_" />', val)
        self.assertIn('accept-charset="utf-8"', val)


    def test_group(self):

        class ITest(formless.TypedInterface):
            class Group(formless.TypedInterface):
                foo = formless.String()

        class Impl:
            implements(ITest)

        impl = Impl()
        ctx = self.setupContext()
        val = self.renderForms(impl, ctx)
        self.assertIn('<input type="hidden" name="_charset_" />', val)
        self.assertIn('accept-charset="utf-8"', val)

    def test_method(self):

        class ITest(formless.TypedInterface):
            def foo(self, foo = formless.String()):
                pass
            foo = formless.autocallable(foo)

        class Impl:
            implements(ITest)

        impl = Impl()
        ctx = self.setupContext()
        val = self.renderForms(impl, ctx)
        self.assertIn('<input type="hidden" name="_charset_" />', val)
        self.assertIn('accept-charset="utf-8"', val)
        
        
class TestUnicode(Base):
    
    def test_property(self):
        
        class IThing(formless.TypedInterface):
            aString = formless.String(unicode=True)
            
        class Impl(object):
            implements(IThing)
            aString = None
            
        inst = Impl()
        ctx = self.setupContext()
        self.postForm(ctx, inst, 'aString', {'aString':['\xc2\xa3']})
        self.assertEquals(inst.aString, u'\xa3')

class TestChoice(Base):
    """Test various behaviors of submitting values to a Choice Typed.
    """

    def test_reject_missing(self):
        # Ensure that if a Choice is not specified, the form is not submitted.

        self.called = []

        class IFormyThing(formless.TypedInterface):
            def choiceyFunc(self, arg = formless.Choice(["one", "two"], required=True)):
                pass
            choiceyFunc = formless.autocallable(choiceyFunc)

        class Impl(object):
            __implements__ = (IFormyThing,)

            def choiceyFunc(innerSelf, arg):
                self.called.append(arg)

        inst = Impl()
        ctx = self.setupContext()
        self.postForm(ctx, inst, 'choiceyFunc', {})
        self.assertEquals(self.called, [])


class mg(Base):

    def test_leakyForms(self):

        class ITest(formless.TypedInterface):
            """Test that a property value on one form does not 'leak' into
            a property of the same name on another form.
            """
            foo = formless.String()

            def meth(self, foo = formless.String()):
                pass
            meth = formless.autocallable(meth)

        class Impl:
            implements(ITest)
            foo = 'fooFOOfoo'

        impl = Impl()
        ctx = self.setupContext()
        val = self.renderForms(
            impl,
            ctx)
        self.assertEquals(val.count('fooFOOfoo'), 1)

# What the *hell* is this?!?

#DeferredTestCases = type(Base)(
#    'DeferredTestCases',
#    tuple([v for v in locals().values()
#     if isinstance(v, type(Base)) and issubclass(v, Base)]),
#    {'synchronousLocateConfigurable': True})

