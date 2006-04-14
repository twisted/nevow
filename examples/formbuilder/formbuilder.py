## formbuilder

from zope.interface import implements

from nevow import rend
from nevow import loaders
from nevow import tags as T
from nevow import util

from formless import annotate
from formless import webform
from formless import configurable

from twisted.python import reflect


class BuilderCore(configurable.Configurable):
    def __init__(self):
        configurable.Configurable.__init__(self, None)
        self.formElements = []

    def getBindingNames(self, ctx):
        return ['form']

    def bind_form(self, ctx):
        return annotate.MethodBinding(
            'action',
            annotate.Method(arguments=self.formElements))

    def action(self, **kw):
        print "ACTION!", kw

    def addElement(self, name, type):
        self.formElements.append(
            annotate.Argument(name, type()))


allTypes = [annotate.String, annotate.Text, annotate.Integer, annotate.Real, annotate.Password]
typeChoice = annotate.Choice(choices=allTypes, valueToKey=reflect.qual, keyToValue=reflect.namedAny, stringify=lambda x: x.__name__)


class IFormBuilder(annotate.TypedInterface):
    def addElement(name=annotate.String(required=True), type=typeChoice):
        """Add Element
        
        Add an element to this form.
        """
        pass
    addElement = annotate.autocallable(addElement)

    def clearForm():
        """Clear Form
        
        Clear this form.
        """
    clearForm = annotate.autocallable(clearForm)
        

class FormBuilder(rend.Page):
    implements(IFormBuilder)
    addSlash = True

    def __init__(self):
        rend.Page.__init__(self)
        self.clearForm()

    def configurable_formBuilder(self, ctx):
        return configurable.TypedInterfaceConfigurable(self)

    def configurable_dynamicForm(self, ctx):
        return self.builderCore

    def addElement(self, name, type):
        self.builderCore.addElement(name, type)

    def clearForm(self):
        self.builderCore = BuilderCore()

    docFactory = loaders.stan(T.html[
    T.head[
        T.title["Form builder!"]],
        T.style(type="text/css")[
            open(util.resource_filename('formless', 'freeform-default.css')).read()],
    T.body[
        T.h1["Welcome to form builder"],
        webform.renderForms('formBuilder'),
        T.h2["Here is your form:"],
        webform.renderForms('dynamicForm')]])


## Startup glue
from nevow import appserver
from twisted.application import service
from twisted.application import internet

application = service.Application('formbuilder')
internet.TCPServer(8080, appserver.NevowSite(FormBuilder())).setServiceParent(application)

