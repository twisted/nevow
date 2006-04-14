from cStringIO import StringIO
import time
from zope.interface import implements

from twisted.python import htmlizer
from twisted.web import static

from nevow import loaders
from nevow import rend
from nevow import tags
from nevow import url

from formless import annotate
from formless import iformless
from formless import webform

ANONYMOUS = 'anonymous'


##
# Text colourisers (aka syntax highlighting)
##

def _python_colouriser(text):
    out = StringIO()
    try:
        htmlizer.filter(StringIO(text), out)
    except AttributeError:
        out = StringIO("""Starting after Nevow 0.4.1 Twisted
2.0 is a required dependency. Please install it""")
    return out.getvalue()

_colourisers = {
    'python': _python_colouriser
    }


##
# Formless
##

class IAddPasting(annotate.TypedInterface):
    def addPasting(
        request=annotate.Request(),
        author=annotate.String(strip=True),
        text=annotate.Text(strip=True, required=True)):
        pass
    addPasting = annotate.autocallable(addPasting)


class IEditPasting(annotate.TypedInterface):
    def editPasting(
        request=annotate.Request(),
        postedBy=annotate.String(immutable=1),
        author=annotate.String(strip=True),
        text=annotate.Text(strip=True, required=True)):
        pass
    editPasting = annotate.autocallable(editPasting)


##
# "Standard" renderers
##

def render_time(theTime):
    def _(context, data):
        return time.strftime('%Y-%m-%d %H:%M:%S %Z', theTime)
    return _

def render_pastingText(text):
    def _(context, data):
        colouriser = _colourisers.get('python')
        if colouriser:
            return tags.xml(colouriser(text))
        return tags.pre[tags.xml(text)]
    return _

def render_pasting(version):
    def _(context, data):
        context.fillSlots('author', version.getAuthor() or ANONYMOUS)
        time = context.fillSlots('time', render_time(version.getTime()))
        text = context.fillSlots('text', render_pastingText(version.getText()))
        return context.tag
    return _


class BasePage(rend.Page):

    docFactory = loaders.htmlfile(templateDir='templates', template='site.html')

    child_css = static.File('static/css')
    child_images = static.File('static/images')

    def data_pastings(self, context, data):
        return self.pastebin.getListOfPastings(20)

    def render_pasting(self, context, data):
        oid, author, time = data
        context.tag.fillSlots('url', url.root.child(str(oid)))
        context.tag.fillSlots('id', oid)
        context.tag.fillSlots('author', author or ANONYMOUS)
        return context.tag

    def render_content(self, context, data):
        tag = context.tag.clear()
        tag[loaders.htmlfile(templateDir='templates', template=self.contentTemplateFile)]
        return tag
    

class RootPage(BasePage):
    implements(IAddPasting)

    addSlash = True

    def __init__(self, pastebin):
        BasePage.__init__(self)
        self.pastebin = pastebin

    def locateChild(self, context, segments):
        try:
            return Pasting(self.pastebin, int(segments[0])), segments[1:]
        except ValueError:
            pass
        return BasePage.locateChild(self, context, segments)

    def render_content(self, context, data):
        tag = context.tag.clear()
        return tag[webform.renderForms()]

    def addPasting(self, request, author, text):
        oid = self.pastebin.addPasting(author, text)
        request.setComponent(iformless.IRedirectAfterPost, '/'+str(oid))
        

class Pasting(BasePage):

    implements(IEditPasting)
    contentTemplateFile = 'pasting.html'

    def __init__(self, pastebin, pastingOid, version=-1):
        BasePage.__init__(self)
        self.pastebin = pastebin
        self.pastingOid = pastingOid
        self.version = version
        self.pasting = self.pastebin.getPasting(self.pastingOid)

    def locateChild(self, context, segments):
        try:
            return Pasting(self.pastebin, self.pastingOid, int(segments[0])), segments[1:]
        except:
            pass
        return BasePage.locateChild(self, context, segments)

    def data_history(self, context, data):
        return self.pasting.getHistory()

    def render_aPasting(self, context, data):
        return render_pasting(self.pasting.getVersion(self.version))

    def render_form(self, context, data):
        if self.version != -1:
            return ''
        version = self.pasting.getVersion(self.version)
        formDefaults = context.locate(iformless.IFormDefaults)
        formDefaults.setDefault('editPasting.text', version.getText())
        formDefaults.setDefault('editPasting.postedBy', version.getAuthor())
        return webform.renderForms()

    def render_version(self, context, data):
        version, author, theTime = data
        if self.version == -1:
            u = url.here.child
        else:
            u = url.here.sibling
        context.tag.fillSlots('url', u(version))
        context.tag.fillSlots('time', render_time(theTime))
        context.tag.fillSlots('author', author or ANONYMOUS)
##         context.fillSlots('link', a(href=[u(version)])[
##             render_time(theTime), ' (',author or ANONYMOUS,')'
##             ])
        return context.tag

    def editPasting(self, request, postedBy, author, text):
        self.pastebin.updatePasting(self.pastingOid, author, text)
        request.setComponent(iformless.IRedirectAfterPost, '/%s'%self.pastingOid)


class Version(BasePage):

    contentTemplateFile = "pasting.html"

    child_ = rend.FourOhFour()

    def __init__(self, pastebin, pasting, version):
        BasePage.__init__(self)
        self.pastebin = pastebin
        self.pasting = pasting
        self.version = version
        
    def data_history(self, context, data):
        return self.pasting.getHistory()

    def render_aPasting(self, context, data):
        return render_pasting(self.pasting.getVersion(self.version))

    def render_version(self, context, data):
        version, author, theTime = data
        context.fillSlots('link', tags.a(href=[url.here.sibling(str(version))])[
            render_time(theTime), ' (',author,')'
            ])
        return context.tag
    
