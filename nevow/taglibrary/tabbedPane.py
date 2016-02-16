from nevow import tags as t, static, util, loaders, athena, inevow


class tabbedPaneGlue:
    """
    Record which holds information about the Javascript & CSS requirements
    of L{TabbedPane} and L{TabbedPaneFragment}.

    @type stylesheetPath: C{str}
    @ivar stylesheetPath: Filesystem path of the tabbed pane stylesheet.

    @type fileCSS: L{static.File}
    @ivar fileCSS: Resource which serves L{stylesheetPath}.

    @type inlineCSS: L{t.style}
    @ivar inlineCSS: <style> tag containing the tabbedpane CSS inline.
    """
    stylesheetPath = util.resource_filename('nevow', 'css/Nevow/TagLibrary/TabbedPane.css')

    fileCSS = static.File(stylesheetPath, 'text/css')

    inlineCSS = t.style(type_='text/css')[ t.xml(file(stylesheetPath).read()) ]



class TabbedPaneFragment(athena.LiveFragment):
    jsClass = u'Nevow.TagLibrary.TabbedPane.TabbedPane'
    cssModule = u'Nevow.TagLibrary.TabbedPane'

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

__all__ = [ "tabbedPaneGlue", "TabbedPaneFragment" ]


