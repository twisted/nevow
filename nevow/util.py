# Copyright (c) 2004 Divmod.
# See LICENSE for details.


import os.path
import sys


def escapeToXML(text, isattrib = False):
    """Borrowed from twisted.xish.domish

    Escape text to proper XML form, per section 2.3 in the XML specification.

     @type text: L{str}
     @param text: Text to escape

     @type isattrib: L{bool}
     @param isattrib: Triggers escaping of characters necessary for use as attribute values
    """
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    if isattrib:
        text = text.replace("'", "&apos;")
        text = text.replace("\"", "&quot;")
    return text


def getPOSTCharset(ctx):
    """Locate the unicode encoding of the POST'ed form data.

    To work reliably you must do the following:

      - set the form's enctype attribute to 'multipart/form-data'
      - set the form's accept-charset attribute, probably to 'utf-8'
      - add a hidden form field called '_charset_'

    For instance::

      <form action="foo" method="post" enctype="multipart/form-data" accept-charset="utf-8">
        <input type="hidden" name="_charset_" />
        ...
      </form>
    """

    from nevow import inevow

    request = inevow.IRequest(ctx)
    
    # Try the magic '_charset_' field, Mozilla and IE set this.
    charset = request.args.get('_charset_',[None])[0]
    if charset:
        return charset

    # Look in the 'content-type' request header
    contentType = request.received_headers.get('content-type')
    if contentType:
        charset = dict([ s.strip().split('=') for s in contentType.split(';')[1:] ]).get('charset')
        if charset:
            return charset

    return 'utf-8'


from twisted.python.reflect import qual, namedAny, allYourBase, accumulateBases
from twisted.python.util import uniquify

from twisted.internet.defer import Deferred, succeed, maybeDeferred, DeferredList
from twisted.python import failure
from twisted.python.failure import Failure
from twisted.python import log


## The tests rely on these, but they should be removed ASAP
def remainingSegmentsFactory(ctx):
    return tuple(ctx.tag.postpath)


def currentSegmentsFactory(ctx):
    return tuple(ctx.tag.prepath)

class _RandomClazz(object):
    pass
class _NamedAnyError(Exception):
    'Internal error for when importing fails.'
    
def _namedAnyWithBuiltinTranslation(name):
    if name == '__builtin__.function':
        name='types.FunctionType'
    elif name == '__builtin__.method':
        return _RandomClazz # Hack
    elif name == '__builtin__.instancemethod':
        name='types.MethodType'
    elif name == '__builtin__.NoneType':
        name='types.NoneType'
    elif name == '__builtin__.generator':
        name='types.GeneratorType'
    return namedAny(name)

# Import resource_filename from setuptools's pkg_resources module if possible
# because it handles resources in .zip files. If it's not provide a version
# that assumes the resource is directly available on the filesystem. 
try:
    from pkg_resources import resource_filename
except ImportError:
    def resource_filename(modulename, resource_name):
        modulepath = namedAny(modulename).__file__
        return os.path.join(os.path.dirname(os.path.abspath(modulepath)), resource_name)

