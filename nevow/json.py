# -*- test-case-name: nevow.test.test_json -*-
# Copyright (c) 2004 Divmod.
# See LICENSE for details.

r"""JavaScript Object Notation

Currently only serialization is supported.  Also, serialization isn't
completely supported.  Many strings will be incorrectly serialized.
Floating points are not yet supported.  None serializes to null, True and
False to true and false, tuples and lists serialize to arrays and
dictionaries serialize to objects.

unserialization is supported via parse(str).

The parser does not understand utf-8 characters at all. All unicode
characters passed to 'dump' be encoded using the \u1000 syntax. High-ascii
characters will be literal high unicode characters. i.e. json "\xf0" will
become python u'\xf0' which is '\xc3\xb0' when encoded in utf-8.

Brain damage: the parser understands json objects of the form
{ "foo":"bar" }
but the serializer gives json objects of the form
{ foo:"bar" }
"""

import re, types

class ParseError(ValueError):
    pass

whitespace = re.compile(
            r'('
            r'[\r\n\t\ ]+'
            r'|/\*.*?\*/'
            r'|//[^\n]*[\n]'
            r')'
            , re.VERBOSE + re.DOTALL)
openBrace = re.compile(r'{')
closeBrace = re.compile(r'}')
openSquare = re.compile(r'\[')
closeSquare = re.compile(r'\]')

class StringTokenizer(object):
    """
    because r'(?<!\\)"([^"]+|\\")*(?<!\\)"'
    """

    def match(self, s):
        if not s.startswith('"'):
            return None

        bits = []

        SLASH = "\\"

        bit, s = s[:1], s[1:]
        bits = [bit]
        while s:
            if s.startswith(SLASH):
                bit, s = s[:2], s[2:]
            else:
                bit, s = s[:1], s[1:]
            bits.append(bit)
            if bit == '"':
                self.matched = ''.join(bits)
                return self

        return None

    def group(self, num):
        return self.matched
        
string = StringTokenizer()
identifier = re.compile(r'[A-Za-z_][A-Za-z_0-9]*')
colon = re.compile(r':')
comma = re.compile(r',')
true = re.compile(r'true')
false = re.compile(r'false')
null = re.compile(r'null')
floatNumber = re.compile(r'-?([1-9][0-9]*|0)(\.[0-9]+)([eE][-+]?[0-9]+)?')
longNumber = re.compile(r'-?([1-9][0-9]*|0)([eE][-+]?[0-9]+)?')

class StringToken(str):
    pass

class IdentifierToken(str):
    pass

class WhitespaceToken(object):
    pass

def jsonlong(s):
    if 'e' in s:
        m, e = map(long, s.split('e', 1))
    else:
        m, e = long(s), 0
    return m * 10 ** e

# list of tuples, the first element is a compiled regular expression the second
# element returns a token and the original string.
actions = [
    (whitespace, lambda s: (WhitespaceToken, s)),
    (openBrace, lambda s: ('{',s)),
    (closeBrace, lambda s: ('}',s)),
    (openSquare, lambda s: ('[',s)),
    (closeSquare, lambda s: (']',s)),
    (string, lambda s: (StringToken(s), s)),
    (colon, lambda s: (':', s)),
    (comma, lambda s: (',', s)),
    (true, lambda s: (True, s)),
    (false, lambda s: (False, s)),
    (null, lambda s: (None, s)),
    (identifier, lambda s: (IdentifierToken(s), s)),
    (floatNumber, lambda s: (float(s), s)),
    (longNumber, lambda s: (jsonlong(s), s)),
]
def tokenise(s):
    tokens = []
    while s:
        for regexp, action in actions:
            m = regexp.match(s)
            if m:
                tok, tokstr = action(m.group(0))
                break
        else:
            raise ValueError, "Invalid Input, %r" % (s[:10],)

        if tok is not WhitespaceToken:
            tokens.append(tok)
        s = s[len(tokstr):]

    return tokens

def accept(want, tokens):
    t = tokens.pop(0)
    if want != t:
        raise ParseError, "Unexpected %r, %s expected" % (t , want)

def parseValue(tokens):
    if tokens[0] == '{':
        return parseObject(tokens)

    if tokens[0] == '[':
        return parseList(tokens)

    if tokens[0] in (True, False, None):
        return tokens.pop(0), tokens

    if type(tokens[0]) == StringToken:
        return parseString(tokens)

    if type(tokens[0]) in (int, float, long):
        return tokens.pop(0), tokens

    raise ParseError, "Unexpected %r" % tokens[0]


def parseString(tokens):
    if type(tokens[0]) is not StringToken:
        raise ParseError, "Unexpected %r" % tokens[0]
    return tokens.pop(0)[1:-1].decode('unicode-escape'), tokens


def parseIdentifier(tokens):
    if type(tokens[0]) is not IdentifierToken:
        raise ParseError("Unexpected %r" % (tokens[0],))
    return tokens.pop(0), tokens


def parseList(tokens):
    l = []
    tokens.pop(0)
    first = True
    while tokens[0] != ']':
        if not first:
            accept(',', tokens)
        first = False

        value, tokens = parseValue(tokens)
        l.append(value)

    accept(']', tokens)
    return l, tokens


def parseObject(tokens):
    o = {}
    tokens.pop(0)
    first = True
    while tokens[0] != '}':
        if not first:
            accept(',', tokens)
        first = False

        name, tokens = parseString(tokens)
        accept(':', tokens)
        value, tokens = parseValue(tokens)
        o[name] = value

    accept('}', tokens)
    return o, tokens


def parse(s):
    tokens = tokenise(s)
    value, tokens = parseValue(tokens)
    if tokens:
        raise ParseError, "Unexpected %r" % tokens[0]
    return value

class CycleError(Exception):
    pass

def unicodeEscapePlusBackslashFix(obj):
    # Required for Python 2.4 and earlier.
    return obj.replace('\\', '\\\\').replace('"', '\\"').encode('unicode-escape')

def unicodeEscapeWithoutBackslashFix(obj):
    # Required for Python 2.4.2+ on dapper (screw you guys) and Python 2.5.
    return obj.encode('unicode-escape').replace('"', '\\"')

if u'\\'.encode('unicode-escape') == '\\\\':
    unicodeEscape = unicodeEscapeWithoutBackslashFix
else:
    unicodeEscape = unicodeEscapePlusBackslashFix


def _serialize(obj, w, seen):
    if isinstance(obj, types.BooleanType):
        if obj:
            w('true')
        else:
            w('false')
    elif isinstance(obj, (int, long, float)):
        w(str(obj))
    elif isinstance(obj, unicode):
        w('"')
        w(unicodeEscape(obj))
        w('"')
    elif isinstance(obj, types.NoneType):
        w('null')
    elif id(obj) in seen:
        raise CycleError(type(obj))
    elif isinstance(obj, (tuple, list)):
        w('[')
        for n, e in enumerate(obj):
            _serialize(e, w, seen)
            if n != len(obj) - 1:
                w(',')
        w(']')
    elif isinstance(obj, dict):
        w('{')
        for n, (k, v) in enumerate(obj.iteritems()):
            _serialize(k, w, seen)
            w(':')
            _serialize(v, w, seen)
            if n != len(obj) - 1:
                w(',')
        w('}')
    else:
        raise TypeError("Unsupported type %r: %r" % (type(obj), obj))

_undefined = object()
def serialize(obj=_undefined, **kw):
    if obj is _undefined:
        obj = kw
    L = []
    _serialize(obj, L.append, {})
    return ''.join(L)
