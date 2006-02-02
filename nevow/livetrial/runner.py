from twisted.python import filepath

from nevow import athena, loaders, tags, rend, url, static
from nevow.livetrial import testcase

here = filepath.FilePath(__file__).parent()
staticData = here.child('static')

class TestSuiteFragment(athena.LiveFragment):
    jsClass = u'Nevow.Athena.Test.TestSuite'
    docFactory = loaders.xmlfile(staticData.child('suite.xhtml').path)

    def __init__(self, suite):
        super(TestSuiteFragment, self).__init__()
        self.suite = suite

    def render_name(self, ctx, data):
        return ctx.tag[self.suite.name]

    def render_tests(self, ctx, data):
        for test in self.suite.tests:
            if isinstance(test, testcase.TestSuite):
                suite = test
                while len(suite.tests) == 1 and isinstance(suite.tests[0], testcase.TestSuite):
                    suite = suite.tests[0]
                if len(suite.tests) > 0:
                    f = TestSuiteFragment(suite)
                else:
                    continue
            else:
                f = test()

            f.setFragmentParent(self)
            yield f

DOCTYPE_XHTML = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'

class TestRunner(TestSuiteFragment):
    jsClass = u'Nevow.Athena.Test.TestRunner'
    docFactory = loaders.xmlfile(staticData.child('runner.xhtml').path)

    def __init__(self, suite):
        super(TestRunner, self).__init__(suite)

class TestFramework(athena.LivePage):
    addSlash = True
    docFactory = loaders.stan([
        tags.xml(DOCTYPE_XHTML),
        tags.html[
            tags.head(render=tags.directive('liveglue'))[
                tags.link(rel='stylesheet', href='static/livetest.css'),
            ],
            tags.body[
                tags.invisible(render=tags.directive('runner')),
                tags.invisible(render=tags.directive('debug')),
            ],
        ],
    ])

    def __init__(self, testSuite):
        super(TestFramework, self).__init__(None, None, jsModuleRoot=url.here.child('jsmodule'))
        self.testSuite = testSuite

    def render_runner(self, ctx, data):
        f = TestRunner(self.testSuite)
        f.setFragmentParent(self)
        return f

    def render_debug(self, ctx, data):
        f = athena.IntrospectionFragment()
        f.setFragmentParent(self)
        return f

    def child_static(self, ctx):
        return static.File(staticData.path)

class TestFrameworkRoot(rend.Page):
    def child_app(self, ctx):
        return TestFramework(self.original)
    child_ = url.URL.fromString('/app')
