name='Nevow'
version='0.7.0'
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
scripts=['bin/nevow-xmlgettext', 'bin/nit']
package_data={
        'formless': [
            'freeform-default.css'
            ],
        'nevow': [
            'athena.js',
            'defer.js',
            'divmod.js',
            'Canvas.swf',
            'liveglue.js',
            'livetest.css',
            'livetest.js',
            'livetest-postscripts.js',
            'MochiKit.js',
            'MochiKitLogConsole.js',
            'nevow.js',
            'runtime.js',
            'widget.js',
            'xml.js',
            ],
        'nevow.taglibrary': [
            'tabbedPane.js',
            'tabbedPane.css',
            'progressBar.js',
            'progressBar.css',
            'taglibrary.js',
            ],
        'nevow.livetrial': [
            'livetest.css',
            'livetest.js',
            ],
        }
