# Copyright (c) 2004 Divmod.
# See LICENSE for details.

"""Builtin template loaders that supply a Page or renderer with a
document to render.

Nevow provides the following DocFactory loaders by default:

  - B{stan} - turn a stan tag tree into a DocFactory
  - B{xmlfile} - load a well formed XML document from file
  - B{htmlfile} - legacy alias for xmlfile
  - B{xmlstr} - load a well formed XML document from a string
  - B{htmlstr} - legacy alias for xmlstr

Until nevow 0.14, the html loaders would accept malformed XHTML.
Since twisted.web.microdom is no longer supported, maintaining
that feature became difficult.  Just write well-formed XHTML.  It's not
so hard.
"""

import warnings

import os.path
from zope.interface import implementer

from twisted.python.reflect import getClass

from nevow import inevow
from nevow import flat
from nevow.flat import flatsax
from nevow.util import CachedFile


@implementer(inevow.IDocFactory)
class stan(object):
    """A stan tags document factory"""


    stan = None
    pattern = None
    _cache = None

    def __init__(self, stan=None, pattern=None):
        if stan is not None:
            self.stan = stan
        if pattern is not None:
            self.pattern = pattern


    def load(self, ctx=None, preprocessors=()):
        if self._cache is None:
            stan = [self.stan]
            for proc in preprocessors:
                stan = proc(stan)
            stan = flat.precompile(stan, ctx)
            if self.pattern is not None:
                stan = inevow.IQ(stan).onePattern(self.pattern)
            self._cache = stan
        return self._cache



@implementer(inevow.IDocFactory)
class xmlstr(object):


    template = None
    pattern = None
    ignoreDocType = None
    ignoreComment = None
    _cache = None

    def __init__(self, template=None, pattern=None, ignoreDocType=False, ignoreComment=False):
        if template is not None:
            self.template = template
        if pattern is not None:
            self.pattern = pattern
        if ignoreDocType is not None:
            self.ignoreDocType = ignoreDocType
        if ignoreComment is not None:
            self.ignoreComment = ignoreComment

    def load(self, ctx=None, preprocessors=()):
        """
        Get an instance, possibly cached from a previous call, of this document
        """
        if self._cache is None:
            doc = flatsax.parseString(self.template, self.ignoreDocType, self.ignoreComment)
            for proc in preprocessors:
                doc = proc(doc)
            doc = flat.precompile(doc, ctx)
            if self.pattern is not None:
                doc = inevow.IQ(doc).onePattern(self.pattern)
            self._cache = doc
        return self._cache


@implementer(inevow.IDocFactory)
class xmlfile(object):


    template = None
    templateDir = None
    pattern = None
    ignoreDocType = False
    ignoreComment = False

    def __init__(self, template=None, pattern=None, templateDir=None, ignoreDocType=None, ignoreComment=None):
        self._cache = {}
        if template is not None:
            self.template = template
        if pattern is not None:
            self.pattern = pattern
        if templateDir is not None:
            self.templateDir = templateDir
        if ignoreDocType is not None:
            self.ignoreDocType = ignoreDocType
        if ignoreComment is not None:
            self.ignoreComment = ignoreComment
        if self.templateDir is not None:
            self._filename = os.path.join(self.templateDir, self.template)
        else:
            self._filename = self.template

        self._cache = {}

    def load(self, ctx=None, preprocessors=()):
        rendererFactoryClass = None
        if ctx is not None:
            r = inevow.IRendererFactory(ctx, None)
            if r is not None:
                rendererFactoryClass = getClass(r)

        cacheKey = (self._filename, self.pattern, rendererFactoryClass)
        cachedFile = self._cache.get(cacheKey)
        if cachedFile is None:
            cachedFile = self._cache[cacheKey] = CachedFile(self._filename, self._reallyLoad)

        return cachedFile.load(ctx, preprocessors)

    def _reallyLoad(self, path, ctx, preprocessors):
        doc = flatsax.parse(open(self._filename), self.ignoreDocType, self.ignoreComment)
        for proc in preprocessors:
            doc = proc(doc)
        doc = flat.precompile(doc, ctx)

        if self.pattern is not None:
            doc = inevow.IQ(doc).onePattern(self.pattern)

        return doc


htmlfile = xmlfile
htmlstr = xmlstr
