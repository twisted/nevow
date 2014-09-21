#!/usr/bin/python

import versioneer
versioneer.VCS = 'git'
versioneer.versionfile_source = 'nevow/_version.py'
versioneer.versionfile_build = 'nevow/_version.py'
versioneer.tag_prefix = 'nevow-'
versioneer.parentdir_prefix = 'Nevow-'

# For the convenience of the travis configuration, make this information
# particularly easy to find.  See .travis.yml.
_MINIMUM_TWISTED_VERSION = "13.0"

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

if __name__ == "__main__":
    setup(
        name='Nevow',
        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),
        packages=find_packages(),
        py_modules=["twisted.plugins.nevow_widget"],
        include_package_data=True,
        author='Divmod, Inc.',
        author_email='support@divmod.org',
        maintainer='Twisted Matrix Labs',
        maintainer_email='twisted-web@twistedmatrix.com',
        description='Web Application Construction Kit',
        url='https://github.com/twisted/nevow',
        license='MIT',
        platforms=["any"],
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Framework :: Twisted",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python",
            "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
            "Topic :: Software Development :: Libraries",
            ],
        scripts=['bin/nevow-xmlgettext', 'bin/nit'],
        data_files=data_files,
        package_data={
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
                },
        install_requires=[
            # Nevow builds on Twisted Web's HTTP server.  It also uses various
            # other generally useful pieces of Twisted (such as its logging system,
            # not to mention reactors and Deferreds).
            #
            # That dependency will be expressed here with a version range including
            # only those versions of Twisted against which Nevow's continuous
            # integration system is configured to actually test.  This ensures any
            # combination allowed by this declaration has been tested and found to
            # work.
            "twisted>=" + _MINIMUM_TWISTED_VERSION,
            ],
        zip_safe=False,
    )
