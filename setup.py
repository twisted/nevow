#!/usr/bin/python

import versioneer
versioneer.VCS = 'git'
versioneer.versionfile_source = 'nevow/_version.py'
versioneer.versionfile_build = 'nevow/_version.py'
versioneer.tag_prefix = 'nevow-'
versioneer.parentdir_prefix = 'Nevow-'

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
        "twisted>=13.0",
        ],
    extras_require={
        'doc': [
            'Sphinx',
        ],
    },
    zip_safe=False,
)
