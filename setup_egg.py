#!/usr/bin/env python
# -*- test-case-name: "nevow.test -xformless.test" -*-

# Use setuptools, it's easier
from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

# Import Nevow for the version string
import nevow

setup(

    name='nevow',
    version=nevow.__version__,
    packages = find_packages(),
    scripts=['bin/nevow-xmlgettext'],
    zip_safe = True,

    author='Donovan Preston et al',
    author_email='dp@divmod.org',
    description='Web Application Construction Kit',
    url='http://www.nevow.com/',

    package_data={
        'formless': ['freeform-default.css'],
        'nevow': [
            'liveglue.js',
            'livetest.js',
            'livetest-postscripts.js',
            'livetest.css',
            'Canvas.swf',
            ],
        'nevow.taglibrary': [
            'tabbedPane.js',
            'tabbedPane.css',
            'progressBar.js',
            'progressBar.css',
            ]
        },
    )

