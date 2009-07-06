try:
    import zope.interface
except ImportError:
    print """ Please install ZopeInterface product from
    http://www.zope.org/Products/ZopeInterface/
to run Nevow """
    import sys
    sys.exit(1)


from twisted.python import components
import warnings
warnings.filterwarnings(
    'ignore',
    category=components.ComponentsDeprecationWarning)

from twisted.application import service, strports
from twisted.python import util

from nevow import inevow, rend, loaders, url, tags, appserver, static, guard, athena

import sys

try:
    from advanced_manualform import advanced_manualform
    from customform import customform
    from disktemplates import disktemplates
    from disktemplates import disktemplates_stan
    from simple import simple
    from simple import simplehtml
    from tree import tree
    from formpost import formpost2
    from formpost import formpost
    from children import children
    from children import childrenhtml
    from table import tablehtml
    from irenderer import irenderer
    from irenderer import simple_irenderer
    from formbuilder import formbuilder
    from db import db
    from hello import hellohtml
    from hello import hellostan
    from canvas import canvas
    from manualform import manualform
    from guarded import guarded
    from guarded import guarded2
    from xul import xul_nevow
    from liveanimal import liveanimal
    from most_basic import most_basic
    from http_auth import http_auth
    from logout_guard import logout_guard
    from logout_guard import logout_guard2
    from objcontainer import objcontainer
    from nestedsequence import nestedsequence
    from fragments import fragments
    from macros import macros
    from i18n import i18n, xmli18n
    from cal import cal
    from tabbed import tabbed
    from progress import progress
    from tests import testformless, testexamples
    from nevow import livetest

    from athenademo import calculator
    from athenademo import typeahead
    from athenademo import widgets
    from athenademo import benchmark
except ImportError, e:
    if str(e).find('No module named') != -1:
        msg = """
Original error message:
%s
=======================================
Please check the following things:
* You are not root
* You are running examples.tac from examples directory or examples
    directory is in the PYTHONPATH

A possible fix could be to run examples.tac with the following
command:
    PYTHONPATH=/path/to/examples/ twistd -noy examples.tac
=======================================
""" % str(e)
        raise Exception(msg)
    raise e
except AttributeError, e:
    if str(e).find("'module' object has no attribute") != -1:
        msg = """
Original error message:
%s
============================
Please check that nevow and formless are correctly installed
============================
""" % str(e)
        raise Exception(msg)
    raise e

class Sources(rend.Page):
    def __init__(self, path, _):
        rend.Page.__init__(self, path)

    def render_htmlizer(self, ctx, path):
        from twisted.python import htmlizer
        from StringIO import StringIO
        output = StringIO()
        try:
            htmlizer.filter(open(path), output, writer=htmlizer.SmallerHTMLWriter)
        except AttributeError:
            output = StringIO("""Starting after Nevow 0.4.1 Twisted
2.0 is a required dependency. Please install it""")
        return tags.xml(output.getvalue())

    docFactory = loaders.stan(
    tags.html[
        tags.head[
            tags.title["Python source file: ", str],
            tags.link(type='text/css', rel='stylesheet', href='/cssfile')],
        tags.body[
            render_htmlizer]])

import os
class Examples(rend.Page):
    addSlash = True ## This is a directory-like resource
    docFactory = loaders.xmlfile(os.path.abspath('.')+'/index.html')
    child_sources = static.File('.', defaultType='text/plain')
    child_sources.processors['.py'] = Sources
    child_sources.contentTypes = {}
    child_cssfile = static.File('index.css')
    children = dict(
        customform=customform.Root(),
        disktemplates=disktemplates.Mine(),
        disktemplates_stan=disktemplates_stan.Mine(),
        simple=simple.Simple(),
        simplehtml=simplehtml.Simple(),
        tree=tree.Tree('base', 'base'),
        formpost2=formpost2.FormPage(formpost2.Implementation()),
        formpost=formpost.FormPage(),
        children=children.RootPage(),
        childrenhtml=childrenhtml.RootPage(),
        tablehtml=tablehtml.Table(),
        irenderer=irenderer.Page(),
        simple_irenderer=simple_irenderer.Page(),
        formbuilder=formbuilder.FormBuilder(),
        db=db.DBBrowser(),
        hellohtml=hellohtml.Page(),
        hellostan=hellostan.Page(),
        canvas=canvas.createResource(),
        manualform=manualform.Page(),
        guarded=guarded.createResource(),
        guarded2=guarded2.createResource(),
        xul_nevow=xul_nevow.createResource(),
        advanced_manualform=advanced_manualform.Page(),
        liveanimal=liveanimal.createResource(),
        http_auth=http_auth.AuthorizationRequired(),
        most_basic=most_basic.root,
        logout_guard=logout_guard.createResource(),
        logout_guard2=logout_guard2.createResource(),
        objcontainer=objcontainer.createResource(),
        nestedsequence=nestedsequence.Root(),
        i18n=i18n.createResource(),
        xmli18n=xmli18n.createResource(),
        calendar=cal.Calendar(),
        tabbed=tabbed.TabbedPage(),
        progress=progress.createResource(),
        tests=testexamples.createResource(),
        livetests=testexamples.createLiveSuite(),
        testtests=livetest.createResource(),
        testformless=testformless.NameWizard(),
        formless_redirector=testformless.Redirector(),
        formless_tests=testformless.formless_tests,
        fragments=fragments.Root(),
        macros=macros.Root(),
        typeahead=typeahead.DataEntry(),
        )

    def child_calculator(self, ctx):
        return calculator.CalculatorParentPage(calc=calculator.Calculator())

    def child_widgets(self, ctx):
        return widgets.WidgetPage(None, None)

    def child_benchmark(self, ctx):
        return benchmark.Benchmark(400, 20)


application = service.Application("examples")
strports.service("8080", appserver.NevowSite(Examples())).setServiceParent(application)
