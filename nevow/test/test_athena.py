
import StringIO

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
