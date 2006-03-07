
import StringIO
from itertools import izip

from twisted.trial import unittest

from nevow import athena

class Utilities(unittest.TestCase):

    testModuleImpl = '''\
lalal this is javascript honest
// uh oh!  a comment!  gee I wish javascript had an import system
// import Example.Module
here is some more javascript code
// import Another
// import Module
the end
'''


    def testJavaScriptModule(self):
        testModuleFilename = self.mktemp()
        testModule = file(testModuleFilename, 'w')
        testModule.write(self.testModuleImpl)
        testModule.close()

        modules = {'test.module': testModuleFilename}
        m1 = athena.JSModule.getOrCreate('test.module', modules)
        m2 = athena.JSModule.getOrCreate('test.module', modules)
        self.assertEquals(m1.name, 'test.module')

        self.assertIdentical(m1, m2)

        deps = [d.name for d in m1.dependencies()]
        deps.sort()
        self.assertEquals(deps, ['Another', 'Example.Module', 'Module'])

        modules['Another'] = self.mktemp()
        anotherModule = file(modules['Another'], 'w')
        anotherModule.write('// import Secondary.Dependency\n')
        anotherModule.close()

        modules['Example.Module'] = self.mktemp()
        exampleModule = file(modules['Example.Module'], 'w')
        exampleModule.write('// import Example.Dependency\n')
        exampleModule.close()

        modules['Module'] = self.mktemp()
        moduleModule = file(modules['Module'], 'w')
        moduleModule.close()

        # Stub these out with an empty file
        modules['Secondary.Dependency'] = modules['Module']
        modules['Example.Dependency'] = modules['Module']

        depgraph = {
            'Another': ['Secondary.Dependency'],
            'Example.Module': ['Example.Dependency'],
            'Module': [],
            'test.module': ['Another', 'Example.Module', 'Module'],
            'Secondary.Dependency': [],
            'Example.Dependency': []}

        allDeps = [d.name for d in m1.allDependencies()]
        for m in allDeps:
            modDeps = depgraph[m]
            for d in modDeps:
                # All dependencies should be loaded before the module
                # that depends upon them.
                self.failUnless(allDeps.index(d) < allDeps.index(m))

class TestFragment(athena.LiveFragment):
    pass

class Nesting(unittest.TestCase):

    def testFragmentNesting(self):
        lp = athena.LivePage()
        tf1 = TestFragment()
        tf2 = TestFragment()

        tf1.setFragmentParent(lp)
        tf2.setFragmentParent(tf1)

        self.assertEquals(lp.liveFragmentChildren, [tf1])
        self.assertEquals(tf1.liveFragmentChildren, [tf2])
        self.assertEquals(tf2.liveFragmentChildren, [])
        self.assertEquals(tf2.fragmentParent, tf1)
        self.assertEquals(tf1.fragmentParent, lp)

        self.assertEquals(tf2.page, lp)
        self.assertEquals(tf1.page, lp)


class Tracebacks(unittest.TestCase):
    frames = (('Error()', '', 0),
              ('someFunction()', 'http://somesite.com:8080/someFile', 42),
              ('anotherFunction([object Object])', 'http://user:pass@somesite.com:8080/someOtherFile', 69))

    stack = '\n'.join(['%s@%s:%d' % frame for frame in frames])

    exc = {u'name': 'SomeError',
           u'message': 'An error occurred.',
           u'stack': stack}

    def testStackParsing(self):
        p = athena.parseStack(self.stack)
        for iframe, oframe in izip(self.frames[::-1], p):
            self.assertEquals(oframe, iframe)

    def testStackLengthAndOrder(self):
        f = athena.getJSFailure(self.exc, {})
        self.assertEqual(len(f.frames), len(self.frames))
        self.assertEqual(f.frames[0][0], self.frames[-1][0])
