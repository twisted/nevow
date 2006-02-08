from nevow import tags as t, static, util, loaders, athena, inevow
from nevow.livepage import js, flt


class tabbedPaneGlue:

    _css = util.resource_filename('nevow.taglibrary', "tabbedPane.css")
    _js = util.resource_filename('nevow.taglibrary', "tabbedPane.js")

    fileCSS = static.File(_css, 'text/css')
    fileJS = static.File(_js, 'text/javascript')
    fileGlue = (
        t.link(rel='stylesheet', type='text/css', href='/tabbedPane.css'),
        t.script(type='text/javascript', src='/tabbedPane.js')
        )

    inlineCSS = t.style(type_='text/css')[ t.xml(file(_css).read()) ]
    inlineJS = t.inlineJS(file(_js).read())
    inlineGlue = inlineJS, inlineCSS


class TabbedPane(object):
    """
    Data
    ----
    
    name     : name for this component (default 'theTabbedPane')
    pages    : sequence of (tab, page) (mandatory)
    selected : index of the selected tab (default 0)

    
    Live component interface
    ------------------------
    
    None currently.
    
    """

    def tabbedPane(self, ctx, data):
        name = data.get('name', 'theTabbedPane')
        pages = data.get('pages')
        selected = data.get('selected', 0)

        def _():
            for n, (tab, page) in enumerate(pages):
                tID = '%s_tab_%i'%(name, n)
                pID = '%s_page_%i'%(name, n)
                yield (t.li(id_=tID)[tab],
                       t.div(id_=pID)[page],
                       flt(js[tID,pID], quote = False))

        tabs, pages, j = zip(*_())
        if selected >= len(tabs):
            selected = 0

        return t.invisible[
            t.div(class_='tabbedPane',id_=name)[
                t.ul(class_='tabs')[tabs], pages
              ],
            t.inlineJS('setupTabbedPane([' + ','.join(j) + '], %i);'%selected)
            ]


tabbedPane = TabbedPane().tabbedPane

class TabbedPaneFragment(athena.LiveFragment):
    jsClass = u'Nevow.TagLibrary.TabbedPane'

    docFactory = loaders.xmlstr("""
<div class="tabbedPane" xmlns:nevow="http://nevow.com/ns/nevow/0.1" nevow:render="liveFragment">
    <nevow:attr name="name"><nevow:invisible nevow:render="name" /></nevow:attr>
    <ul class="tabs">
        <nevow:invisible nevow:render="tabs" />
    </ul>
    <li nevow:pattern="tab"
     onclick="Nevow.TagLibrary.TabbedPane.get(this).tabClicked(this); return false">
        <nevow:attr name="class"><nevow:slot name="class" /></nevow:attr>
        <nevow:slot name="tab-name" />
    </li>
    <div nevow:pattern="page">
        <nevow:attr name="class"><nevow:slot name="class" /></nevow:attr>
        <nevow:slot name="page-content" />
    </div>
    <nevow:invisible nevow:render="pages" />
</div>""".replace('\n', ''))

    def __init__(self, pages, selected=0, name='default'):
        self.pages = pages
        self.selected = selected
        self.name = name

        super(TabbedPaneFragment, self).__init__()

    def render_name(self, ctx, data):
        return self.name

    def render_tabs(self, ctx, data):
        tabPattern = inevow.IQ(self.docFactory).patternGenerator('tab')
        for (i, (name, content)) in enumerate(self.pages):
            if self.selected == i:
                cls = 'selected'
            else:
                cls = 'taglibrary-tabbedpane-' + self.name + '-tabname-' + str(i)
            yield tabPattern.fillSlots(
                      'tab-name', name).fillSlots(
                      'class', cls)

    def render_pages(self, ctx, data):
        pagePattern = inevow.IQ(self.docFactory).patternGenerator('page')
        for (i, (name, content)) in enumerate(self.pages):
            if self.selected == i:
                cls = 'selected'
            else:
                cls = 'taglibrary-tabbedpane-'  + self.name + '-tabdata-' + str(i)
            yield pagePattern.fillSlots(
                    'page-content', content).fillSlots(
                    'class', cls)

__all__ = [ "tabbedPane", "tabbedPaneGlue", "TabbedPaneFragment" ]


