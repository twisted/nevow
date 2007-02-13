# Copyright (c) 2004 Divmod.
# See LICENSE for details.

import sys, signal
from popen2 import popen2

from zope.interface import implements

try:
    import subunit
except ImportError:
    subunit = None

from twisted.python import procutils
from twisted.python.util import sibpath
from twisted.trial.unittest import TestCase as TrialTestCase
from twisted.python.components import Componentized
from twisted.internet import defer
from twisted.web import http
from twisted.protocols.basic import LineReceiver

from formless import iformless

import nevow
from nevow import inevow, context, athena, loaders, tags, appserver


class FakeChannel:
    def __init__(self, site):
        self.site = site


class FakeSite:
    pass


class FakeSession(Componentized):
    implements(inevow.ISession)
    def __init__(self, avatar):
        Componentized.__init__(self)
        self.avatar = avatar
        self.uid = 12345
    def getLoggedInRoot(self):
        return self.avatar


fs = FakeSession(None)


class FakeRequest(Componentized):
    implements(inevow.IRequest)
    args = {}
    failure = None
    context = None
    redirected_to = None
    content = ""
    method = 'GET'
    code = http.OK

    def __init__(self, headers=None, args=None, avatar=None,
                 uri='/', currentSegments=None, cookies=None,
                 user="", password="", isSecure=False):
        """Create a FakeRequest instance.

        headers:
            dict of headers
        args:
            dict of args
        avatar:
            avatar to pass to the FakeSession instance
        uri:
            request URI
        currentSegments:
            list of segments that have "already been located"
        cookies:
            dict of cookies
        user:
            username (like in http auth)
        password:
            password (like in http auth)
        isSecure:
            whether this request represents an HTTPS url
        """
        Componentized.__init__(self)
        self.uri = uri
        self.prepath = []
        postpath = uri.split('?')[0]
        assert postpath.startswith('/')
        self.postpath = postpath[1:].split('/')
        if currentSegments is not None:
            for seg in currentSegments:
                assert seg == self.postpath[0]
                self.prepath.append(self.postpath.pop(0))
        else:
            self.prepath.append('')
        self.headers = headers or {}
        self.args = args or {}
        self.sess = FakeSession(avatar)
        self.site = FakeSite()
        self.received_headers = {}
        if cookies is not None:
            self.cookies = cookies
        else:
            self.cookies = {}
        self.user = user
        self.password = password
        self.secure = isSecure

    def URLPath(self):
        from nevow import url
        return url.URL.fromString('')

    def getSession(self):
        return self.sess

    v = ''
    def write(self, x):
        self.v += x

    finished=False
    def finish(self):
        self.finished = True

    def getHeader(self, key):
        return self.headers.get(key)

    def setHeader(self, key, val):
        self.headers[key] = val

    def redirect(self, url):
        self.redirected_to = url

    def getRootURL(self):
        return None

    def processingFailed(self, f):
        self.failure = f

    def setResponseCode(self, code):
        self.code = code

    def prePathURL(self):
        return 'http://localhost/%s'%'/'.join(self.prepath)

    def getClientIP(self):
        return '127.0.0.1'

    def addCookie(self, k, v, expires=None, domain=None, path=None, max_age=None, comment=None, secure=None):
        """
        Set a cookie for use in subsequent requests.
        """
        self.cookies[k] = v

    def getCookie(self, k):
        """
        Fetch a cookie previously set.
        """
        return self.cookies.get(k)

    def getUser(self):
        """
        Returns the HTTP auth username.
        """
        return self.user

    def getPassword(self):
        """
        Returns the HTTP auth password.
        """
        return self.password

    def rememberRootURL(self, url=None):
        """
        For compatibility with appserver.NevowRequest.
        """
        pass

    def isSecure(self):
        """
        Returns whether this is an HTTPS request or not.
        """
        return self.secure


class TestCase(TrialTestCase):
    hasBools = (sys.version_info >= (2,3))
    _assertions = 0

    # This should be migrated to Twisted.
    def failUnlessSubstring(self, containee, container, msg=None):
        self._assertions += 1
        if container.find(containee) == -1:
            self.fail(msg or "%r not in %r" % (containee, container))
    def failIfSubstring(self, containee, container, msg=None):
        self._assertions += 1
        if container.find(containee) != -1:
            self.fail(msg or "%r in %r" % (containee, container))

    assertSubstring = failUnlessSubstring
    assertNotSubstring = failIfSubstring

    def assertNotIdentical(self, first, second, msg=None):
        self._assertions += 1
        if first is second:
            self.fail(msg or '%r is %r' % (first, second))

    def failIfIn(self, containee, container, msg=None):
        self._assertions += 1
        if containee in container:
            self.fail(msg or "%r in %r" % (containee, container))

    def assertApproximates(self, first, second, tolerance, msg=None):
        self._assertions += 1
        if abs(first - second) > tolerance:
            self.fail(msg or "%s ~== %s" % (first, second))


if not hasattr(TrialTestCase, 'mktemp'):
    def mktemp(self):
        import tempfile
        return tempfile.mktemp()
    TestCase.mktemp = mktemp


class AccumulatingFakeRequest(FakeRequest):
    """
    I am a fake IRequest that stores data written out in an instance variable.
    I also have a stub implementation of IFormDefaults.

    @ivar accumulator: The accumulated data from write().
    """
    implements(iformless.IFormDefaults)
    method = 'GET'
    def __init__(self, *a, **kw):
        FakeRequest.__init__(self, *a, **kw)
        self.d = defer.Deferred()
        self.accumulator = ''

    def write(self, data):
        FakeRequest.write(self, data)
        self.accumulator+=data

    def getDefault(self, key, context):
        return ''

    def remember(self, object, interface):
        pass


class FragmentWrapper(athena.LivePage):
    """
    I wrap myself around an Athena fragment, providing a minimal amount of html
    scaffolding in addition to an L{athena.LivePage}.
    """
    docFactory = loaders.stan(
                    tags.html[
                        tags.body[
                            tags.directive('fragment')]])

    def __init__(self, f):
        super(FragmentWrapper, self).__init__()
        self.f = f

    def render_fragment(self, ctx, data):
        self.f.setFragmentParent(self)
        return self.f


def renderLivePage(res, topLevelContext=context.WebContext,
                   reqFactory=AccumulatingFakeRequest):
    """
    Render the given LivePage resource, performing LivePage-specific cleanup.
    Return a Deferred which fires when it has rendered.
    """
    D = renderPage(res, topLevelContext, reqFactory)
    return D.addCallback(lambda x: (res._messageDeliverer.close(), x)[1])


def renderPage(res, topLevelContext=context.WebContext,
               reqFactory=AccumulatingFakeRequest):
    """
    Render the given resource.  Return a Deferred which fires when it has
    rendered.
    """
    req = reqFactory()
    ctx = topLevelContext(tag=res)
    ctx.remember(req, inevow.IRequest)

    render = appserver.NevowRequest(None, True).gotPageContext

    result = render(ctx)
    result.addCallback(lambda x: req.accumulator)
    return result



class NotSupported(Exception):
    """
    Raised by L{JavaScriptTestCase} if the installation lacks a certain
    required feature.
    """


_DUMMY_MODULE_NAME = 'ConsoleJSTest'

def getDependencies(fname, ignore=('MochiKit.DOM',),
                    bootstrap=athena.LivePage.BOOTSTRAP_MODULES,
                    packages=None):
    """
    Get the javascript modules that the code in the file with name C{fname}
    depends on, recursively

    @param fname: javascript source file name
    @type fname: C{str}

    @param ignore: names of javascript modules to exclude from dependency list
    @type ignore: sequence

    @param boostrap: names of javascript modules to always include, regardless
    of explicit dependencies (defaults to L{athena.LivePage}'s list of
    bootstrap modules)
    @type boostrap: sequence

    @param packages: all javascript packages we know about.  defaults to the
    result of L{athena.allJavascriptPackages}
    @type packages: C{dict}

    @return: modules included by javascript in file named C{fname}
    @rtype: dependency-ordered list of L{athena.JSModule} instances
    """
    if packages is None:
        packages = athena.allJavascriptPackages()

    # TODO if a module is ignored, we should ignore its dependencies
    bootstrapModules = [athena.JSModule.getOrCreate(m, packages)
                        for m in bootstrap if m not in ignore]

    packages[_DUMMY_MODULE_NAME] = fname
    module = athena.JSModule(_DUMMY_MODULE_NAME, packages)

    return (bootstrapModules +
            [dep for dep in module.allDependencies()
             if (dep.name not in bootstrap
                 and dep.name != _DUMMY_MODULE_NAME
                 and dep.name not in ignore)])



def findJavascriptInterpreter():
    """
    Return a string path to a JavaScript interpreter if one can be found in
    the executable path. If not, return None.
    """
    for script in ['smjs', 'js']:
        _jsInterps = procutils.which(script)
        if _jsInterps:
            return _jsInterps[0]
    return None



def generateTestScript(fname, after={'Divmod.Base': ('Divmod.Base.addLoadEvent = function() {};',)},
                              dependencies=None):
    """
    Turn the contents of the Athena-style javascript test module in the file
    named C{fname} into a plain javascript script.  Recursively includes any
    modules that are depended on, as well as the utility module
    nevow/test/testsupport.js.

    @param fname: javascript source file name
    @type fname: C{str}

    @param after: mapping of javascript module names to sequences of lines of
    javascript source that should be injected into the output immediately
    after the source of the named module is included
    @type after: C{dict}

    @param dependencies: the modules the script depends on.  Defaults to the
    result of L{getDependencies}
    @type dependencies: dependency-ordered list of L{athena.JSModule}
    instances

    @return: converted javascript source text
    @rtype: C{str}
    """
    if dependencies is None:
        dependencies= getDependencies(fname)

    load = lambda fname: 'load(%r);' % (fname,)
    initialized = set()
    js = [load(sibpath(nevow.__file__, 'test/testsupport.js'))]
    for m in dependencies:
        segments = m.name.split('.')
        if segments[-1] == '__init__':
            segments = segments[:-1]
        initname = '.'.join(segments)
        if initname not in initialized:
            initialized.add(initname)
            if '.' in initname:
                prefix = ''
            else:
                prefix = 'var '
            js.append('%s%s = {};' % (prefix, initname))
        js.append(load(m.mapping[m.name]))
        if m.name in after:
            js.extend(after[m.name])

    js.append(file(fname).read())

    return '\n'.join(js)



class TestProtocolLineReceiverServer(LineReceiver):
    """
    Subunit protocol which is also a Twisted LineReceiver so that it
    includes line buffering logic.
    """
    delimiter = '\n'

    def __init__(self, proto):
        self.proto = proto


    def lineReceived(self, line):
        """
        Forward the line on to the subunit protocol's lineReceived method,
        which expects it to be newline terminated.
        """
        self.proto.lineReceived(line + '\n')



class JavaScriptTestCase(TrialTestCase):
    def __init__(self, methodName='runTest'):
        TrialTestCase.__init__(self, methodName)
        self.testMethod = getattr(self, methodName)


    def checkDependencies(self):
        """
        Check that all the dependencies of the test are satisfied.

        @raise NotSupported: If any one of the dependencies is not satisfied.
        """
        js = findJavascriptInterpreter()
        if js is None:
            raise NotSupported("Could not find JavaScript interpreter")
        if subunit is None:
            raise NotSupported("Could not import 'subunit'")


    def _writeToTemp(self, contents):
        fname = self.mktemp()
        fd = file(fname, 'w')
        try:
            fd.write(contents)
        finally:
            fd.close()
        return fname


    def makeScript(self, testModule):
        js = """
// import Divmod.UnitTest
// import %(module)s

Divmod.UnitTest.runRemote(Divmod.UnitTest.loadFromModule(%(module)s));
""" % {'module': testModule}
        jsfile = self._writeToTemp(js)
        scriptFile = self._writeToTemp(generateTestScript(jsfile))
        return scriptFile


    def _runWithSigchild(self, f, *a, **kw):
        """
        Run the given function with an alternative SIGCHLD handler.
        """
        oldHandler = signal.signal(signal.SIGCHLD, signal.SIG_DFL)
        try:
            return f(*a, **kw)
        finally:
            signal.signal(signal.SIGCHLD, oldHandler)


    def run(self, result):
        try:
            self.checkDependencies()
        except NotSupported, e:
            result.startTest(self)
            result.addSkip(self, str(e))
            result.stopTest(self)
            return
        js = findJavascriptInterpreter()
        script = self.makeScript(self.testMethod())
        server = subunit.TestProtocolServer(result)
        protocol = TestProtocolLineReceiverServer(server)

        # What this *SHOULD BE*
        # spawnProcess(protocol, js, (script,))
        # return protocol.someDisconnectCallback()

        # However, *run cannot return a Deferred profanity profanity profanity
        # profanity*, so instead it is *profanity* this:
        def run():
            r, w = popen2([js, script])
            while True:
                bytes = r.read(4096)
                if bytes:
                    protocol.dataReceived(bytes)
                else:
                    break
        self._runWithSigchild(run)



def setJavascriptInterpreterOrSkip(testCase):
    """
    If we're unable to find a javascript interpreter (currently we only look
    for smjs or js) then set the C{skip} attribute on C{testCase}. Otherwise
    assign the path to the interpreter executable to
    C{testCase.javascriptInterpreter}
    """
    script = findJavascriptInterpreter()
    if script is None:
        testCase.skip = "No JavaScript interpreter available."
    else:
        testCase.javascriptInterpreter = script
