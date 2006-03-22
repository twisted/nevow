# -*- python -*-

from zope.interface import implements

from nevow import loaders
from nevow import rend
from nevow import tags
from nevow import inevow
from nevow import url

from formless import annotate
from formless import webform

from twisted.internet import defer


#oldChoicesWay = annotate.Choice(choicesAttribute='theChoices') # Doing this gives you a DeprecationWarning now

# If you still want to use an attribute or method of some other object, you should use a function as shown below,
# but look up IResource(ctx) or IConfigurable(ctx), whichever is more appropriate.
newChoicesWay = annotate.Choice(lambda c, d: range(30))
deferChoicesWay = annotate.Choice(lambda c, d: defer.succeed(['abcd', 'efgh', 'ijkl']))
radioChoices = annotate.Radio(["Old", "Tyme", "Radio"])

## An example of using custom valueToKey and keyToValue functions to serialize/deserialize items
values = {0: dict(name="Zero", stuff=1234), 1: dict(name="One", stuff=1234), 2: dict(name="Two", stuff=2345435)}
customValueToKey = annotate.Choice(
    [0, 1, 2], # Perhaps these are primary keys in a database
    stringify=lambda x: values[x]['name'], # Do a database lookup to render a nice label in the ui
    valueToKey=str,                                  # Convert the primary key to a value suitable for sending across the web
    keyToValue=lambda x: values[int(x)]) # Do a database lookup to get the actual value to pass to the binding


class IMyForm(annotate.TypedInterface):
    foo = annotate.Integer()

    def bar(baz=annotate.Integer(), 
        slam=newChoicesWay, ham=deferChoicesWay, radio=radioChoices, custom=customValueToKey):
        pass
    bar = annotate.autocallable(bar)


class Implementation(object):
    implements(IMyForm)

    foo = 5

    def bar(self, baz, slam, ham, radio, custom):
        return "You called bar! %s %s %s %s %r" % (baz, slam, ham, radio, custom)

    theChoices = [1, 2, 3]


class FormPage(rend.Page):

    addSlash = True

    child_webform_css = webform.defaultCSS

    def render_hand(self, ctx, data):
        hand = inevow.IHand(ctx, None)
        if hand is not None:
            return ctx.tag[hand]
        return ''

    docFactory = loaders.stan(
        tags.html[
            tags.head[
                tags.link(rel='stylesheet', type='text/css', href=url.here.child('webform_css')),
                ],
            tags.body[
                tags.h3(render=render_hand, style="color: red; font-size: xx-large"),
                "Hello! Here is a form:",

                # We want to render forms defined by the Implementation instance.
                # When we pass the Implementation instance to FormPage below,
                # rend.Page sets it as the .original attribute. To tell webform to render
                # forms described by this object, we use the configurable name "original".
                webform.renderForms('original'),
                ],
            ],
        )

