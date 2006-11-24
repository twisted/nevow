
from time import time

from twisted.python.usage import Options

from nevow.json import serialize, parse

if __name__ == '__main__':
    from json_string_tokenizer import main
    raise SystemExit(main())



class StringTokenizer(Options):
    optParameters = [
        ('iterations', 'i', '1000', 'Number of iterations for which to run the benchmark.'),
        ('scale', 's', '100', 'Factor determining the overall input size.')]


    def postOptions(self):
        self['iterations'] = int(self['iterations'])
        self['scale'] = int(self['scale'])


BASE = u'Hello, world.  "Quotes".'
def benchmark(iterations, scale):
    """
    Deserialize a string C{iterations} times.  Make the string longer based
    on C{scale}.

    Prints the mean time per parse call.
    """
    s = serialize(BASE * scale)
    before = time()
    for i in xrange(iterations):
        parse(s)
    after = time()
    print (after - before) / iterations, 'per call'



def main(args=None):
    """
    Benchmark nevow.json string parsing, maybe with some parameters.
    """
    options = StringTokenizer()
    options.parseOptions(args)
    benchmark(options['iterations'], options['scale'])
