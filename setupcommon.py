name='Nevow'
from nevow import __version__ as version
maintainer = 'Divmod, Inc.'
maintainer_email = 'support@divmod.org'
description = 'Web Application Construction Kit'
url='http://divmod.org/trac/wiki/DivmodNevow'
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
            'Canvas.swf',
            '*.css',
	    'js/Divmod/*.js', 
	    'js/Nevow/*.js',
	    'js/Nevow/Athena/Tests/*.js',
	    'js/Divmod/Runtime/*.js',
	    'js/Nevow/Athena/*.js',
	    'js/Nevow/TagLibrary/*.js',
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
