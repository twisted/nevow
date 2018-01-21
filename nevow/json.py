# Copyright (c) 2018, Divmod
# See LICENSE for details.

# Original nevow had a custom json module; there's probably no point
# keeping that now that built-in json in python is ok.
#
# This is just a thin wrapper to make sure athena objects are serialisable.

import json

from nevow.inevow import IAthenaTransportable
from nevow import rend, page, _flat, tags


class NevowJSONEncoder(json.JSONEncoder):
    """a json.JSONEncoder with extra logic for encoding some custom nevow
    types.
    """
    def default(self, obj):
        from nevow import athena
        if isinstance(obj, (athena.LiveFragment, athena.LiveElement)):
            return obj._structured()

        elif isinstance(obj, (rend.Fragment, page.Element)):
            res = []
            def _w(s):
                res.append(s)
            wrapper = tags.div(xmlns="http://www.w3.org/1999/xhtml")
            for _ in _flat.flatten(None, _w, wrapper[obj], False, False):
                pass
            return "".join(res)

        else:
            res = []
            def _w(s):
                res.append(s)

            transportable = IAthenaTransportable(obj, None)
            if transportable is None:
                return json.JSONEncoder.default(self, obj)
            else:
                _w('(new ' + transportable.jsClass + '(')
                arguments = transportable.getInitialArguments()
                for n, e in enumerate(arguments):
                    _w(self.default(e))
                    if n != len(arguments) - 1:
                        _w(',')
                _w('))')
                return "".join(res)
    

class NevowJSONDecoder(json.JSONDecoder):
    """a json.JSONDecoder with logic for decoding the extra types
    serialized by NevowJSONEncoder.
    """


def dumps(obj, **kwargs):
    """
    JSON-encode an object to a str.

    @param obj: None, True, False, an int, long, float, unicode string,
    list, tuple, or dictionary the JSON-encoded form of which will be
    returned.
    """
    return NevowJSONEncoder(**kwargs).encode(obj)


def loads(string, **kwargs):
    """
    Return the object represented by the JSON-encoded string C{s}.

    For backward compatibility, C{s} can also be a byte string (it will
    be interpreted as utf-8).
    """
    if isinstance(string, bytes):
        string = string.decode("utf-8")
    return NevowJSONDecoder(**kwargs).decode(string)


__all__ = ['loads', 'dumps']
