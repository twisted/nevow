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
package_data=[
    ['formless', [
        'formless/freeform-default.css']],
    ['nevow', [
        'nevow/liveglue.js',
        'nevow/livetest.js',
        'nevow/livetest-postscripts.js',
        'nevow/livetest.css',
        'nevow/Canvas.swf']],
    ['nevow/taglibrary', [
        'nevow/taglibrary/tabbedPane.js',
        'nevow/taglibrary/tabbedPane.css',
        'nevow/taglibrary/progressBar.js',
        'nevow/taglibrary/progressBar.css']]]
package_data={
        'formless': [
            'freeform-default.css'
            ],
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
        }
