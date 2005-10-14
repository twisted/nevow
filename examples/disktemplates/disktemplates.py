import random

from nevow import inevow, loaders, rend
from twisted.python import util


class Mine(rend.Page):

    addSlash = True
    docFactory = loaders.xmlfile(util.sibpath(__file__, 'disktemplates.html'))

    def render_foo(self, context, data):
        return inevow.IQ(context).onePattern(random.choice(['one', 'two', 'three']))

    def data_theList(self, context, data):
        return [random.randint(0, 5000) for x in range(random.randint(0, 10))]

    def data_empty(self, context, data):
        return []
