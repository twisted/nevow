#!/usr/bin/env python2.3
# -*- test-case-name: "nevow.test -xformless.test" -*-

from distutils.command import install
from distutils.core import setup
import nevow
import sys

# Where should our data files go?
# They want to go in our package directory , which is under site-packages.
# We determine the location of site-packages here, for later use. It will be
# interpreted as relative to sys.prefix.
# This junk can go once we decide to drop Python 2.3 support or switch to
# setuptools. package_data is a much cleaner solution.
if sys.platform.lower().startswith('win'):
    site_packages = 'Lib/site-packages/'
else:
    version = '.'.join([str(i) for i in sys.version_info[:2]])
    site_packages = 'lib/python' + version + '/site-packages/'

setup(
    name='Nevow',
    version=nevow.__version__,
    maintainer='Divmod, Inc.',
    maintainer_email='support@divmod.org',
    description='Web Application Construction Kit',
    url='http://divmod.org/projects/nevow',
    license='MIT',
    platforms=["any"],
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content"],

    packages=['formless', 'formless.test', 'nevow', 'nevow.flat',
              'nevow.scripts', 'nevow.test', 'nevow.taglibrary'],

    scripts=['bin/nevow-xmlgettext'],

    data_files=[
        [site_packages+'formless', [
            'formless/freeform-default.css']],
        [site_packages+'nevow', [
            'nevow/liveglue.js',
            'nevow/livetest.js',
            'nevow/livetest-postscripts.js',
            'nevow/livetest.css',
            'nevow/Canvas.swf']],
        [site_packages+'nevow/taglibrary', [
            'nevow/taglibrary/tabbedPane.js',
            'nevow/taglibrary/tabbedPane.css',
            'nevow/taglibrary/progressBar.js',
            'nevow/taglibrary/progressBar.css']]])
