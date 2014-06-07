#!/usr/bin/python

from nevow import __version__ as version

from setuptools import setup, find_packages

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

setupdict['packages'] = find_packages()
setupdict['include_package_data'] = True

from distutils.command.sdist import sdist
setupdict['cmdclass'] = {'sdist': sdist}

setup(**setupdict)

