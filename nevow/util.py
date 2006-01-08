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


def qual(clazz):
    return clazz.__module__ + '.' + clazz.__name__


def namedAny(name):
    """Get a fully named package, module, module-global object, or attribute.
    """
    names = name.split('.')
    topLevelPackage = None
    moduleNames = names[:]
    while not topLevelPackage:
        try:
            trialname = '.'.join(moduleNames)
            topLevelPackage = __import__(trialname)
        except ImportError:
            # if the ImportError happened in the module being imported,
            # this is a failure that should be handed to our caller.
            # count stack frames to tell the difference.

            # string-matching is another technique, but I think it could be
            # fooled in some funny cases
            #if sys.exc_info()[1] != "cannot import name %s" % trialname:
            #    raise
            import traceback
            if len(traceback.extract_tb(sys.exc_info()[2])) > 1:
                raise
            moduleNames.pop()
    
    obj = topLevelPackage
    for n in names[1:]:
        obj = getattr(obj, n)
        
    return obj


def uniquify(lst):
    """Make the elements of a list unique by inserting them into a dictionary.
    This must not change the order of the input lst.
    """
    dct = {}
    result = []
    for k in lst:
        if not dct.has_key(k): result.append(k)
        dct[k] = 1
    return result


def allYourBase(classObj, baseClass=None):
    """allYourBase(classObj, baseClass=None) -> list of all base
    classes that are subclasses of baseClass, unless it is None,
    in which case all bases will be added.
    """
    l = []
    accumulateBases(classObj, l, baseClass)
    return l


def accumulateBases(classObj, l, baseClass=None):
    for base in classObj.__bases__:
        if baseClass is None or issubclass(base, baseClass):
            l.append(base)
        accumulateBases(base, l, baseClass)


try:

    from twisted.internet.defer import Deferred, succeed, maybeDeferred, DeferredList
    from twisted.python import failure
    from twisted.python.failure import Failure
    from twisted.python import log

except ImportError:
    class Deferred(object): pass
    class Failure(object):
        def __init__(self, e):
            self.exc = e
    class DeferredList(object):
        def __init__(self, l):
            self.l = l

        def addCallback(self, cb, *args, **kw):
            cb(self.l, *args, **kw)

        def addErrback(self, eb, *args, **kw):
            pass

        def addBoth(self, cbeb, *args, **kw):
            cbeb(self.l, *args, **kw)

    class Logger(object):
        def msg(self, *args, **kw):
            for arg in args:
                print >> sys.stderr, arg
            for k, v in kw.items():
                print >> sys.stderr, "%s: %s" % (k, v)

    log = Logger()

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

