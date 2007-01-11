# Copyright (c) 2006 Divmod.
# See LICENSE for details.

"""
Out-of-browser conversion of javascript test modules that use Athena's "//
import" syntax into monolithic scripts suitable for feeding into a plain
javascript interpreter
"""

from sys import argv
from twisted.python.util import sibpath
import nevow, subprocess

_DUMMY_MODULE_NAME = 'ConsoleJSTest'

def getDependencies(fname, ignore=('Divmod.Runtime', 'MochiKit.DOM'),
                           bootstrap=nevow.athena.LivePage.BOOTSTRAP_MODULES,
                           packages=None):
    """
    Get the javascript modules that the code in the file with name C{fname}
    depends on, recursively

    @param fname: javascript source file name
    @type fname: C{str}

    @param ignore: names of javascript modules to exclude from dependency list
    @type ignore: sequence

    @param boostrap: names of javascript modules to always include, regardless
    of explicit dependencies (defaults to L{nevow.athena.LivePage}'s list of
    bootstrap modules)
    @type boostrap: sequence

    @param packages: all javascript packages we know about.  defaults to the
    result of L{nevow.athena.allJavascriptPackages}
    @type packages: C{dict}

    @return: modules included by javascript in file named C{fname}
    @rtype: dependency-ordered list of L{nevow.athena.JSModule} instances
    """
    if packages is None:
        packages = nevow.athena.allJavascriptPackages()

    packages[_DUMMY_MODULE_NAME] = fname

    # TODO if a module is ignored, we should ignore its dependencies

    return ([nevow.athena.JSModule.getOrCreate(m, packages)
               for m in bootstrap if m not in ignore] +

            [dep for dep in nevow.athena.JSModule(
                                _DUMMY_MODULE_NAME, packages).allDependencies()
                if dep.name not in bootstrap
                    and dep.name != _DUMMY_MODULE_NAME
                    and dep.name not in ignore])


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
    @type dependencies: dependency-ordered list of L{nevow.athena.JSModule}
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

def run():
    """
    Read a single filename from the command line arguments, replace any module
    imports with the body of the module in question and pipe the result to the
    spidermonkey javascript interpreter

    """
    # TODO: support more than one filename at a time
    js = generateTestScript(argv[1])
    subprocess.Popen('/usr/bin/smjs', stdin=subprocess.PIPE).communicate(js)
