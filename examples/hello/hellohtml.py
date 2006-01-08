from twisted.python import util

from nevow import loaders
from nevow import rend


class Page(rend.Page):
    """Example of using an HTML template to render a page.
    """
    addSlash = True
    docFactory = loaders.xmlfile(util.sibpath(__file__, 'hellohtml.html'))

