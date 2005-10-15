#!/usr/bin/env python
# -*- test-case-name: "nevow.test -xformless.test" -*-

# Use setuptools, it's easier
from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages
import setupcommon

# Import Nevow for the version string
import nevow

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
    packages=find_packages(),
    scripts=setupcommon.scripts,
    package_data=setupcommon.package_data,
    zip_safe = True,
    )

