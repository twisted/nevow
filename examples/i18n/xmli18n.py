import os
from nevow import loaders
from nevow.i18n import render as i18nrender
from i18n import Common, preparePage

class Page(Common):
    docFactory = loaders.xmlfile(
        'hello.html',
        templateDir=os.path.split(os.path.abspath(__file__))[0])

    render_i18n = i18nrender()
        
def createResource():
    return preparePage(Page)
