from nevow import tags as t, static, util, loaders, athena, inevow
from nevow.livepage import js, flt


class tabbedPaneGlue:

    _css = util.resource_filename('nevow.taglibrary', "tabbedPane.css")
    _js = util.resource_filename('nevow', "js/Nevow/TagLibrary/TabbedPane.js")

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
                yield (t.li(class_='nevow-tabbedpane-tab', id_=tID)[tab],
                       t.div(class_='nevow-tabbedpane-pane', id_=pID)[page],
                       flt(js[tID,pID], quote = False))

        tabs, pages, j = zip(*_())
        if selected >= len(tabs):
            selected = 0

        return t.invisible[
            t.div(class_='nevow-tabbedpane',id_=name)[
                t.ul(class_='nevow-tabbedpane-tabs')[tabs], pages
              ],
            t.inlineJS('setupTabbedPane([' + ','.join(j) + '], %i);'%selected)
            ]


tabbedPane = TabbedPane().tabbedPane

class TabbedPaneFragment(athena.LiveFragment):
    jsClass = u'Nevow.TagLibrary.TabbedPane.TabbedPane'

    docFactory = loaders.xmlstr("""
<div class="nevow-tabbedpane"
  xmlns:nevow="http://nevow.com/ns/nevow/0.1"
  xmlns:athena="http://divmod.org/ns/athena/0.7"
  nevow:render="liveFragment"
  style="opacity: .3">
    <ul class="nevow-tabbedpane-tabs" id="tab-container">
        <nevow:invisible nevow:render="tabs" />
    </ul>
    <li nevow:pattern="tab"
      ><athena:handler event="onclick"
      handler="dom_tabClicked" /><nevow:attr name="class"><nevow:slot
     name="class" /></nevow:attr><nevow:slot name="tab-name" /></li>
    <div nevow:pattern="page">
        <nevow:attr name="class"><nevow:slot name="class" /></nevow:attr>
        <nevow:slot name="page-content" />
    </div>
    <div id="pane-container"><nevow:invisible nevow:render="pages" /></div>
</div>""".replace('\n', ''))

    def __init__(self, pages, selected=0, name='default'):
        self.pages = pages
        self.selected = selected
        self.name = name

        super(TabbedPaneFragment, self).__init__()

    def getInitialArguments(self):
        return (unicode(self.pages[self.selected][0], 'utf-8'),)

    def render_tabs(self, ctx, data):
        tabPattern = inevow.IQ(self.docFactory).patternGenerator('tab')
        for (i, (name, content)) in enumerate(self.pages):
            if self.selected == i:
                cls = 'nevow-tabbedpane-selected-tab'
            else:
                cls = 'nevow-tabbedpane-tab'
            yield tabPattern.fillSlots(
                      'tab-name', name).fillSlots(
                      'class', cls)

    def render_pages(self, ctx, data):
        pagePattern = inevow.IQ(self.docFactory).patternGenerator('page')
        for (i, (name, content)) in enumerate(self.pages):
            if self.selected == i:
                cls = 'nevow-tabbedpane-selected-pane'
            else:
                cls = 'nevow-tabbedpane-pane'
            yield pagePattern.fillSlots(
                    'page-content', content).fillSlots(
                    'class', cls)

__all__ = [ "tabbedPane", "tabbedPaneGlue", "TabbedPaneFragment" ]


