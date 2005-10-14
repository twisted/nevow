from nevow import tags as t, static, util
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

__all__ = [ "tabbedPane", "tabbedPaneGlue" ]


