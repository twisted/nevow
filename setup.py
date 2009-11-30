#!/usr/bin/python

from nevow import __version__ as version

try:
    import setuptools
except ImportError:
    setuptools = None

import os
data_files=[]
for (dirpath, dirnames, filenames) in os.walk("doc"):
    if ".svn" in dirnames:
        del dirnames[dirnames.index(".svn")]
    thesedocs = []
    for fname in filenames:
        thesedocs.append(os.path.join(dirpath, fname))
    data_files.append((dirpath, thesedocs))

data_files.append((os.path.join('twisted', 'plugins'), [os.path.join('twisted', 'plugins', 'nevow_widget.py')]))

setupdict = {
    'name': 'Nevow', 
    'version': version,
    'maintainer': 'Divmod, Inc.', 
    'maintainer_email': 'support@divmod.org', 
    'description': 'Web Application Construction Kit', 
    'url': 'http://divmod.org/trac/wiki/DivmodNevow', 
    'license': 'MIT', 
    'platforms': ["any"], 
    'classifiers': [
        "Development Status :: 5 - Production/Stable",
        "Framework :: Twisted",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries",
        ],
    'scripts': ['bin/nevow-xmlgettext', 'bin/nit'],
    'data_files': data_files,
    'package_data': {
            'formless': [
                'freeform-default.css'
                ],
            'nevow': [
                'Canvas.swf',
                '*.css',
                '*.js',
                'css/*.css',
                'css/Nevow/*.css',
                'css/Nevow/TagLibrary/*.css',
                'js/Divmod/*.js',
                'js/Nevow/*.js',
                'js/Nevow/Test/*.js',
                'js/Nevow/Athena/Tests/*.js',
                'js/Divmod/Runtime/*.js',
                'js/Nevow/Athena/*.js',
                'js/Nevow/TagLibrary/*.js',
                'js/Divmod/Test/*.js',
                'js/PythonTestSupport/*.js',
                ],
            'nevow.athena_private': [
                '*.png'
                ],
            'nevow.taglibrary': [
                '*.css',
                '*.js'
                ],
            'nevow.livetrial': [
                '*.css',
                '*.js'
                ],
            'nevow.test': [
                '*.js'
                ],
            'nevow.test.test_package.Foo': [
                '*.js'
                ],
            'nevow.test.test_package.Foo.Baz': [
                '*.js'
                ],
            }
}

if setuptools:
    # Importing setuptools worked -- then we do the following setup script:
    from setuptools import setup, find_packages

    setupdict['packages'] = find_packages()
    setupdict['include_package_data'] = True
else:
    # No setuptools -- decide where the data files should go and explicitly list
    # the packages.

    from distutils.core import setup

    import os.path
    import glob
    import sys

    # Where should our data files go?
    # They want to go in our package directory , which is under site-packages.
    # We determine the location of site-packages here, for later use. It will be
    # interpreted as relative to sys.prefix.

    # This junk can go once we decide to drop Python 2.3 support or switch to
    # requiring setuptools. package_data is a much cleaner solution.
    if sys.platform.lower().startswith('win'):
        site_packages = 'Lib/site-packages/'
    else:
        version = '.'.join([str(i) for i in sys.version_info[:2]])
        site_packages = 'lib/python' + version + '/site-packages/'

    # Turn the package_data into a data_files for 2.3 compatability
    setupdict['data_files'] = []
    for pkg, patterns in setupdict['package_data'].items():
        pkgdir = os.path.join(*pkg.split('.'))
        for pattern in patterns:
            globdir = os.path.dirname(pattern)
            files = glob.glob(os.path.join(pkgdir, pattern))
            setupdict['data_files'].append((os.path.join(site_packages,pkgdir,globdir),files))

    # We need to list the packages explicitly.
    setupdict['packages'] = [
        'formless', 'formless.test', 'nevow', 'nevow.flat',
        'nevow.scripts', 'nevow.test', 'nevow.taglibrary',
        'nevow.plugins', 'nevow.livetrial', 'twisted.plugins']

if setuptools is not None:
    from distutils.command.sdist import sdist
    setupdict['cmdclass'] = {'sdist': sdist}


setup(**setupdict)

