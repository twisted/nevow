# -*- test-case-name: nevow.test -*-
# Copyright (c) 2004-2006 Divmod.
# See LICENSE for details.

import types
types.NoneType=type(None)

from nevow._version import get_versions
__version__ = get_versions()["version"]
__version_info__ = tuple(int(part) for part in __version__.split("-", 1)[0].split(".")[:3])
del get_versions

from twisted.python.versions import Version
version = Version("nevow", *__version_info__)
del Version

import sys
from twisted.python.components import registerAdapter

from nevow import flat
from nevow.util import _namedAnyWithBuiltinTranslation

# Python2.2 has a stupidity where instance methods have name
# 'builtins.instance method' instead of 'builtins.instancemethod'
# Workaround this error.
def clean(o):
    if o == 'builtins.instancemethod' and sys.version_info < (2,3):
        return 'builtins.instance method'
    return o


def load(S):
    for line in S.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            (a, o, i) = line.split()
            registerAdapter(_namedAnyWithBuiltinTranslation(a),
                            _namedAnyWithBuiltinTranslation(clean(o)),
                            _namedAnyWithBuiltinTranslation(i))


def loadFlatteners(S):
    for line in S.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            f, o = line.split()
            flat.registerFlattener(f, clean(o))


namespace = "http://nevow.com/ns/nevow/0.1"
'''The xml namespace of the nevow elements and attributes.'''


basic_adapters = """
formless.annotate.Group                   formless.annotate.MetaTypedInterface        formless.iformless.ITyped

nevow.accessors.DictionaryContainer    builtins.dict                         nevow.inevow.IContainer
nevow.accessors.ListContainer          builtins.list                         nevow.inevow.IContainer
nevow.accessors.ListContainer          builtins.tuple                        nevow.inevow.IContainer

nevow.accessors.FunctionAccessor       builtins.function                     nevow.inevow.IGettable
nevow.accessors.FunctionAccessor       builtins.method                       nevow.inevow.IGettable
nevow.accessors.FunctionAccessor       builtins.instancemethod               nevow.inevow.IGettable
nevow.accessors.DirectiveAccessor      nevow.stan.directive                     nevow.inevow.IGettable
nevow.accessors.SlotAccessor           nevow.stan.slot                          nevow.inevow.IGettable
nevow.accessors.SlotAccessor           nevow.stan._PrecompiledSlot              nevow.inevow.IGettable

    #

formless.webform.PropertyBindingRenderer  formless.annotate.Property         formless.iformless.IBindingRenderer
formless.webform.MethodBindingRenderer    formless.annotate.MethodBinding    formless.iformless.IBindingRenderer
formless.webform.GroupBindingRenderer     formless.annotate.GroupBinding     formless.iformless.IBindingRenderer

    #

formless.webform.StringRenderer         formless.annotate.String         formless.iformless.ITypedRenderer
formless.webform.StringRenderer         formless.annotate.Integer        formless.iformless.ITypedRenderer
formless.webform.StringRenderer         formless.annotate.Directory      formless.iformless.ITypedRenderer
formless.webform.PasswordRenderer       formless.annotate.Password       formless.iformless.ITypedRenderer
formless.webform.PasswordEntryRenderer  formless.annotate.PasswordEntry  formless.iformless.ITypedRenderer
formless.webform.TextRenderer           formless.annotate.Text           formless.iformless.ITypedRenderer
formless.webform.BooleanRenderer        formless.annotate.Boolean        formless.iformless.ITypedRenderer
formless.webform.ChoiceRenderer         formless.annotate.Choice         formless.iformless.ITypedRenderer
formless.webform.RadioRenderer         formless.annotate.Radio         formless.iformless.ITypedRenderer
formless.webform.ObjectRenderer         formless.annotate.Object         formless.iformless.ITypedRenderer
formless.webform.NullRenderer           formless.annotate.Request        formless.iformless.ITypedRenderer
formless.webform.NullRenderer           formless.annotate.Context        formless.iformless.ITypedRenderer
formless.webform.FileUploadRenderer     formless.annotate.FileUpload     formless.iformless.ITypedRenderer
formless.webform.ButtonRenderer         formless.annotate.Button         formless.iformless.ITypedRenderer

    #

formless.processors.ProcessGroupBinding    formless.annotate.GroupBinding     formless.iformless.IInputProcessor
formless.processors.ProcessMethodBinding   formless.annotate.MethodBinding    formless.iformless.IInputProcessor
formless.processors.ProcessPropertyBinding    formless.annotate.Property         formless.iformless.IInputProcessor
formless.processors.ProcessTyped           formless.iformless.ITyped           formless.iformless.IInputProcessor
formless.processors.ProcessPassword        formless.annotate.Password         formless.iformless.IInputProcessor
formless.processors.ProcessRequest         formless.annotate.Request          formless.iformless.IInputProcessor
formless.processors.ProcessContext         formless.annotate.Context          formless.iformless.IInputProcessor
formless.processors.ProcessUpload          formless.annotate.FileUpload       formless.iformless.IInputProcessor

    #

formless.webform.FormDefaults     nevow.appserver.NevowRequest                formless.iformless.IFormDefaults
formless.webform.FormDefaults     nevow.testutil.FakeRequest                  formless.iformless.IFormDefaults
formless.webform.FormDefaults     nevow.testutil.FakeSession                  formless.iformless.IFormDefaults
formless.webform.FormDefaults     twisted.web.server.Session                  formless.iformless.IFormDefaults
formless.webform.FormDefaults     nevow.guard.GuardSession                    formless.iformless.IFormDefaults

formless.webform.FormErrors       twisted.web.server.Session               formless.iformless.IFormErrors
formless.webform.FormErrors       nevow.guard.GuardSession                 formless.iformless.IFormErrors
formless.webform.FormErrors       nevow.testutil.FakeSession               formless.iformless.IFormErrors

nevow.appserver.OldResourceAdapter                  twisted.web.resource.IResource      nevow.inevow.IResource
nevow.static.staticHTML                 builtins.str                          nevow.inevow.IResource

nevow.appserver.sessionFactory  nevow.context.RequestContext    nevow.inevow.ISession
nevow.rend.handFactory   nevow.context.RequestContext    nevow.inevow.IHand
nevow.rend.statusFactory   nevow.context.RequestContext    nevow.inevow.IStatusMessage
nevow.rend.defaultsFactory   nevow.context.RequestContext    formless.iformless.IFormDefaults
nevow.rend.errorsFactory   nevow.context.RequestContext    formless.iformless.IFormErrors
nevow.rend.originalFactory  nevow.context.RequestContext   nevow.inevow.IRequest
nevow.appserver.defaultExceptionHandlerFactory   nevow.context.SiteContext    nevow.inevow.ICanHandleException

nevow.rend.originalFactory  nevow.context.PageContext   nevow.inevow.IRenderer
nevow.rend.originalFactory  nevow.context.PageContext   nevow.inevow.IRendererFactory

nevow.rend.originalFactory  nevow.context.PageContext   formless.iformless.IConfigurableFactory

# URL IResource adapters
nevow.url.URLRedirectAdapter    nevow.url.URL           nevow.inevow.IResource
nevow.url.URLRedirectAdapter    nevow.url.URLOverlay    nevow.inevow.IResource

## The tests rely on these. Remove them ASAP.
nevow.util.remainingSegmentsFactory  nevow.context.RequestContext   nevow.inevow.IRemainingSegments
nevow.util.currentSegmentsFactory  nevow.context.RequestContext   nevow.inevow.ICurrentSegments

nevow.query.QueryContext    nevow.context.WovenContext    nevow.inevow.IQ
nevow.query.QueryLoader     nevow.inevow.IDocFactory      nevow.inevow.IQ
nevow.query.QueryList       builtins.list              nevow.inevow.IQ
nevow.query.QuerySlot       nevow.stan.slot               nevow.inevow.IQ
nevow.query.QuerySlot       nevow.stan._PrecompiledSlot   nevow.inevow.IQ
nevow.query.QueryNeverFind  nevow.stan.xml                nevow.inevow.IQ
nevow.query.QueryNeverFind  nevow.stan.raw                nevow.inevow.IQ
nevow.query.QueryNeverFind  builtins.bytes                nevow.inevow.IQ
nevow.query.QueryNeverFind  nevow.stan.directive          nevow.inevow.IQ

# I18N
nevow.i18n.languagesFactory     nevow.context.RequestContext    nevow.inevow.ILanguages
"""

load(basic_adapters)


flatteners = """

nevow.flat.flatstan.ProtoSerializer               nevow.stan.Proto
nevow.flat.flatstan.TagSerializer                 nevow.stan.Tag
nevow.flat.flatstan.EntitySerializer              nevow.stan.Entity
nevow.flat.flatstan.CommentSerializer             nevow.stan.Comment
nevow.flat.flatstan.XmlSerializer                 nevow.stan.xml
nevow.flat.flatstan.RawSerializer                 nevow.stan.raw
nevow.flat.flatstan.StringSerializer              builtins.str
nevow.flat.flatstan.StringSerializer              builtins.bytes
nevow.flat.flatstan.NoneWarningSerializer         types.NoneType
nevow.flat.flatstan.StringCastSerializer          builtins.int
nevow.flat.flatstan.StringCastSerializer          builtins.float
nevow.flat.flatstan.BooleanSerializer             builtins.bool
nevow.flat.flatstan.ListSerializer                builtins.list
nevow.flat.flatstan.StringCastSerializer          builtins.dict
nevow.flat.flatstan.ListSerializer                builtins.tuple
nevow.flat.flatstan.ListSerializer                builtins.generator
nevow.flat.flatstan.FunctionSerializer            builtins.function
nevow.flat.flatstan.FunctionSerializer            builtins.type
nevow.flat.flatstan.MethodSerializer              builtins.instancemethod
nevow.flat.flatstan.RendererSerializer            nevow.inevow.IRenderer
nevow.flat.flatstan.DirectiveSerializer           nevow.stan.directive
nevow.flat.flatstan.SlotSerializer                nevow.stan.slot
nevow.flat.flatstan.PrecompiledSlotSerializer     nevow.stan._PrecompiledSlot
nevow.flat.flatstan.ContextSerializer             nevow.context.WovenContext
nevow.flat.twist.DeferredSerializer               twisted.internet.defer.Deferred
nevow.flat.twist.DeferredSerializer               twisted.internet.defer.DeferredList

nevow.flat.flatstan.FailureSerializer             twisted.python.failure.Failure

nevow.url.URLOverlaySerializer            nevow.url.URLOverlay
nevow.url.URLSerializer            nevow.url.URL

    # Itertools uses special types

nevow.flat.flatstan.ListSerializer  itertools.chain
nevow.flat.flatstan.ListSerializer  itertools.count
nevow.flat.flatstan.ListSerializer  itertools.cycle
nevow.flat.flatstan.ListSerializer  itertools.dropwhile
nevow.flat.flatstan.ListSerializer  builtins.filter
nevow.flat.flatstan.ListSerializer  itertools.filterfalse
nevow.flat.flatstan.ListSerializer  builtins.map
nevow.flat.flatstan.ListSerializer  builtins.slice
nevow.flat.flatstan.ListSerializer  builtins.zip
nevow.flat.flatstan.ListSerializer  builtins.range
nevow.flat.flatstan.ListSerializer  itertools.repeat
nevow.flat.flatstan.ListSerializer  itertools.starmap
nevow.flat.flatstan.ListSerializer  itertools.takewhile

nevow.flat.flatstan.DocFactorySerializer nevow.inevow.IDocFactory

# I18N
nevow.i18n.flattenL10n              nevow.i18n.PlaceHolder
"""

flatteners_2_4 = """
nevow.flat.flatstan.StringCastSerializer          decimal.Decimal
"""
if sys.version_info >= (2, 4):
    flatteners += flatteners_2_4

loadFlatteners(flatteners)


__all__ = [
    'accessors', 'appserver', 'blocks', 'canvas', 'context', 'dirlist', 'entities', 'events', 'failure', 'guard', 'inevow',
    'loaders', 'rend', 'scripts', 'stan', 'static', 'tags', 'test', 'testutil', 'url', 'util', 'vhost', 'flat', 'version',
]
