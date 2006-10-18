// import Nevow.TagLibrary

Nevow.TagLibrary.TabbedPane = Nevow.Athena.Widget.subclass("Nevow.TabbedPane");

Nevow.TagLibrary.TabbedPane.methods(
    function __init__(self, node, selectedTabName) {
        self._loaded = false;
        self._pendingTabSwitch = null;
        Divmod.Base.addLoadEvent(function() {
            self.node.style.opacity = "";
            self._loaded = true;
            if(self._pendingTabSwitch) {
                /* switch to the tab that was most recently clicked
                   while we were busy loading */
                self.tabClicked(self._pendingTabSwitch);
            }
        });

        var name = node.getAttribute("name");
        var getElementsByTagNameShallow = function(root, tagName) {
            return Divmod.Runtime.theRuntime.getElementsByTagNameShallow(root, tagName);
        }
        var tabContainer = getElementsByTagNameShallow(node, "ul")[0];
        var tabs = getElementsByTagNameShallow(tabContainer, "li");
        var panes = getElementsByTagNameShallow(node, "div");
        var elems = {};
        for(var i = 0; i < tabs.length; i++) {
            elems[tabs[i].firstChild.nodeValue] = [tabs[i], panes[i]];
        }
        /* this is a mapping of tab offsets to [tab-element, pane-element] */
        self._elements = elems;
        self._lastSelectedTabName = selectedTabName;

        Nevow.TagLibrary.TabbedPane.upcall(self, "__init__", node);
    },

    function tabClicked(self, tab) {
        if(!self._loaded) {
            self._pendingTabSwitch = tab;
            return;
        }

        var lastSelected = self._elements[self._lastSelectedTabName],
            lastSelectedTab = lastSelected[0],
            lastSelectedPane = lastSelected[1];

        lastSelectedTab.className = "nevow-tabbedpane-tab";
        lastSelectedPane.className = "nevow-tabbedpane-pane";

        tab.className = "nevow-tabbedpane-selected-tab";
        var tabName = tab.firstChild.nodeValue, pane = self._elements[tabName][1];
        pane.className = "nevow-tabbedpane-selected-pane";

        self._lastSelectedTabName = tabName;
    });

// backward compatability

function setupTabbedPane(data, selectedTab) {
    for(i=0; i<data.length; i++) {

        tab = document.getElementById(data[i][0]);
        page = document.getElementById(data[i][1]);

        if(i == selectedTab) {
            tab.className = 'nevow-tabbedpane-selected-tab'
            page.className = 'nevow-tabbedpane-selected-pane';
        }

        tab.onclick = function() {

            for(i=0; i<data.length; i++) {
                tab = document.getElementById(data[i][0]);
                page = document.getElementById(data[i][1]);

                if(tab.id == this.id) {
                    tab.className = 'nevow-tabbedpane-selected-tab';
                    page.className = 'nevow-tabbedpane-selected-pane';
                }
                else {
                    tab.className = 'nevow-tabbedpane-tab';
                    page.className = 'nevow-tabbedpane-pane';
                }
            }
        }
    }
}

