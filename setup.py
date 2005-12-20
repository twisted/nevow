#!/usr/bin/env python2.3
# -*- test-case-name: "nevow.test -xformless.test" -*-

import os.path
from distutils.command import install
from distutils.core import setup
import sys
import setupcommon

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

# Turn the package_data into a data_files for 2.3 compatability
data_files = []
for pkg, files in setupcommon.package_data.items():
    pkgdir = os.path.join(*pkg.split('.'))
    files = [os.path.join(pkgdir, file) for file in files]
    data_files.append([site_packages+pkgdir, files])

# We need to list the packages explicitly.
packages = [
    'formless', 'formless.test', 'nevow', 'nevow.flat',
    'nevow.scripts', 'nevow.test', 'nevow.taglibrary',
    'nevow.plugins']

setup(
    name=setupcommon.name,
    version=setupcommon.version,
    maintainer=setupcommon.maintainer,
    maintainer_email=setupcommon.maintainer_email,
    description=setupcommon.description,
    url=setupcommon.url,
    license=setupcommon.license,
    platforms=setupcommon.platforms,
    classifiers=setupcommon.classifiers,
    packages=packages,
    scripts=setupcommon.scripts,
    data_files=data_files,
    )
