# -*- python -*-

from zope.interface import implements

from nevow import loaders
from nevow import rend
from nevow import tags
from nevow import url

from formless import annotate
from formless import webform

class IMyForm(annotate.TypedInterface):
    foo = annotate.Integer()


class FormPage(rend.Page):
    implements(IMyForm)

    addSlash = True

    child_webform_css = webform.defaultCSS

    # We need this to implement IMyForm
    foo = 5

    docFactory = loaders.stan(
        tags.html[
            tags.head[
                tags.link(rel='stylesheet', type='text/css', href=url.here.child('webform_css')),
                ],
            tags.body[
                "Hello! Here is a form:",

                # We want to render the "default" configurable.
                # This is located in Page.configurable_() and is going to be
                # 'self' (which, as you see above, implements IMyForm).
                webform.renderForms(),
                ],
            ],
        )
