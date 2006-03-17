#################################################################################
# Example of using patterns to change the appearance of a webform.

#from twisted.application import internet, service
#from twisted.web import static

from zope.interface import implements

from nevow import rend
from nevow import url
from nevow import loaders
from nevow import tags as T

from formless import annotate
from formless import webform


#################################################################################
# This beasty defines how I want the form to look. It's a table (eek!).
# webform looks for patterns to use when rendering parts of the form and fills
# slots with key information.
#
# Key patterns are:
#   freeform-form   -- the form itself, mostly just the structure
#   argument        -- the pattern to use for arguments when nothing better
#                      is found
#   argument!!fo    -- the pattern to use for the 'fo' argument
#
# Inside the patterns the following slots are filled:
#   freeform-form:
#     form-action       -- action attribute, where the form will be posted
#     form-id           -- id of the form
#     form-name         -- name of the form
#     form-label        -- form label, extracted from the docstring
#     form-description  -- description, also extracted from the docstring
#     form-error        -- "global" error
#     form-arguments    -- insertion point for the arguments' HTML
#   argument:
#     label             -- label
#     input             -- the form element (input, textarea, etc)
#     error             -- error message (if any)
#     description       -- description of argument
#
# Note that you do not have to provide slots for all of the above. For
# instance, you may not want to display the descriptions.
#
# Chances are that this block of text would be in a disk template or
# perhaps defined using stan in a taglib module.


FORM_LAYOUT = loaders.xmlstr(
    """<?xml version="1.0"?>
    <form xmlns:n="http://nevow.com/ns/nevow/0.1" n:pattern="freeform-form">
    
      <!-- Replace/fill the form attributes -->
      <n:attr name="action"><n:slot name="form-action"/></n:attr>
      <n:attr name="id"><n:slot name="form-id"/></n:attr>
      <n:attr name="name"><n:slot name="form-name"/></n:attr>
      
      <!-- General form information -->
      <p><strong><n:slot name="form-label"/></strong></p>
      <p><em><n:slot name="form-description"/></em></p>
      <p><strong><em><n:slot name="form-error"/></em></strong></p>
      
      <!-- Start of the form layout table -->
      <table style="background: #eee; border: 1px solid #bbb; padding: 1em;" >
        <!-- Mark location arguments will be added -->
        <n:slot name="form-arguments"/>
        <!-- General argument layout pattern -->
        <n:invisible n:pattern="argument" n:render="remove">
          <tr>
            <th><n:slot name="label"/>:</th>
            <td><n:slot name="input"/><span class="freeform-error"><n:slot name="error"/></span></td>
          </tr>
          <tr>
            <th></th>
            <td><n:slot name="description"/></td>
          </tr>
        </n:invisible>
        <!-- Argument layout, just for fum -->
        <n:invisible n:pattern="argument!!fo" n:render="remove">
          <tr>
            <th><n:slot name="label"/>:</th>
            <td>
              <textarea cols="40" rows="5"><n:attr name="id"><n:slot name="id"/></n:attr><n:attr name="name"><n:slot name="name"/></n:attr><n:slot name="value"/></textarea>
              <span class="freeform-error"><n:slot name="error"/></span></td>
          </tr>
          <tr>
            <th></th>
            <td><n:slot name="description"/></td>
          </tr>
        </n:invisible>
        <!-- Button row -->
        <tr>
          <td colspan="2">
            <n:slot name="form-button"/>
          </td>
        </tr>
      </table>
    </form>
    """).load()


#################################################################################
# ISomething and Page are just something to test the form rendering on.

class ISomething(annotate.TypedInterface):
    
    def doSomething(
        ctx = annotate.Context(),
        fee = annotate.String(required=True, description="Wee!"),
        fi = annotate.Integer(description="Tra-la-la"),
        fo = annotate.Text(),
        fum = annotate.String(),
        ):
        """Do Something Really Exciting

        Normally you would put a useful description of the interface here but,
        since the inteface is useless anyway, I cannot think of anything
        useful to say about it. Although ... did I mention it is useless?"""
    doSomething = annotate.autocallable(doSomething)
    

class Root(rend.Page):
    """Render a custom and normal form for an ISomething.
    """
    implements(ISomething)
    addSlash = True
    
    child_webform_css = webform.defaultCSS
    
    def render_normalForm(self, ctx, data):
        return webform.renderForms()
    
    def render_customForm(self, ctx, data):
        return webform.renderForms()[FORM_LAYOUT]
    
    def doSomething(self, ctx, **kwargs):
        print '***** doSomething called with:', kwargs
    
    docFactory = loaders.stan(
        T.html[
            T.head[
                T.title['Example :: Custom Form Layout'],
                T.link(rel='stylesheet', type='text/css', href=url.here.child("webform_css")),
                ],
            T.body[
                T.h1['Custom'],
                render_customForm,
                T.h1['Default'],
                render_normalForm,
                ]
            ]
        )


#application = service.Application('hellostan')
#webServer = internet.TCPServer(8080, appserver.NevowSite(Root()))
#webServer.setServiceParent(application)
