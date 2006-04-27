# Copyright (c) 2004 Divmod.
# See LICENSE for details.

from twisted.python.context import get as getCtx
from nevow.util import Deferred
from nevow import flat


def deferflatten(stan, ctx, writer):
    finished = Deferred()

    iterable = flat.iterflatten(
        stan, ctx, writer, lambda D: isinstance(D, Deferred))

    def drive():
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
                drive()
                return result
            def eb(failure):
                finished.errback(failure)
                return failure
            cfac = getCtx('CursorFactory')
            if cfac:
                deferred.addCallback(cfac.store.transback, cb).addErrback(cfac.store.transback, eb)
            else:
                deferred.addCallback(cb).addErrback(eb)

    drive()
    return finished
    

def DeferredSerializer(original, context):
    d = Deferred()
    def cb(result):
        d.callback(flat.serialize(result, context))
        return result
    original.addCallback(cb)
    return d
