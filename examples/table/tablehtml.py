import random

from twisted.python import util

from nevow import loaders
from nevow import rend


class Table(rend.Page):

    # addSlash is used to automatically ad a slash at the end of each url
    # http://localhost:8080/foo -> http://localhost:8080/foo/
    addSlash = True
    docFactory = loaders.xmlfile(util.sibpath(__file__, 'tablehtml.html'))

    def data_theList(self, context, data):
        return [(x, random.randint(0, 5000)) for x in range(random.randint(0, 10))]
        
    def render_row(self, context, data):
        context.fillSlots('first_column', data[0])
        context.fillSlots('second_column', data[1])
        return context.tag
