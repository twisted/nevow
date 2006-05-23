# Copyright (c) 2004 Divmod.
# See LICENSE for details.

from twisted.python.context import get as getCtx
from twisted.internet import defer
from nevow import flat


def _isDeferred(d):
    """
    Flattener predicate for trampolining out when handling a Deferred.
    """
    return isinstance(d, defer.Deferred)


def _drive(iterable, finished):
    """
    Spin an iterable returned by L{nevow.flat.iterflatten}, setting up
    callbacks and errbacks on Deferreds it spits out so as to continue spinning
    it after those Deferreds fire.
    """
    try:
        next = iterable.next()
    except StopIteration:
        finished.callback('')
    except:
        finished.errback()
    else:
        deferred, returner = next
        def cb(result):
            returner(result)
            _drive(iterable, finished)
            return result
        def eb(failure):
            finished.errback(failure)
            return failure
        cfac = getCtx('CursorFactory')
        if cfac:
            deferred.addCallback(cfac.store.transback, cb).addErrback(cfac.store.transback, eb)
        else:
            deferred.addCallback(cb).addErrback(eb)


def deferflatten(stan, ctx, writer):
    finished = defer.Deferred()
    iterable = flat.iterflatten(stan, ctx, writer, _isDeferred)
    _drive(iterable, finished)
    return finished


def DeferredSerializer(original, context):
    d = defer.Deferred()
    def cb(result):
        d.callback(flat.serialize(result, context))
        return result
    original.addCallback(cb)
    return d
