import nevow

name='Nevow'
version=nevow.__version__
maintainer = 'Divmod, Inc.'
maintainer_email = 'support@divmod.org'
description = 'Web Application Construction Kit'
url='http://divmod.org/projects/nevow'
license='MIT'
platforms=["any"]
classifiers=[
    "Intended Audience :: Developers",
    "Programming Language :: Python",
    "Development Status :: 4 - Beta",
    "Topic :: Internet :: WWW/HTTP :: Dynamic Content"]
scripts=['bin/nevow-xmlgettext']
package_data={
        'formless': [
            'freeform-default.css'
            ],
        'nevow': [
            'athena.js',
            'MochiKit.js',
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
        }
