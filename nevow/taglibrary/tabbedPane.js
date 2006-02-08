// import Nevow.TagLibrary

Nevow.TagLibrary.TabbedPane = Nevow.Athena.Widget.subclass("Nevow.TabbedPane");

Nevow.TagLibrary.TabbedPane.methods(
    function __init__(self, node) {
        var name = node.getAttribute("name");
        self._tabPrefix = "taglibrary-tabbedpane-" + name + "-tabname-";
        self._pagePrefix = "taglibrary-tabbedpane-" + name + "-tabdata-";
        self._selectedClassName = "selected";
        self._elements = {};

        Nevow.TagLibrary.TabbedPane.upcall(self, "__init__", node);
    },

    function _getHandyNode(self, classValue) {
        if(!(classValue in self._elements)) {
            self._elements[classValue] = self.nodeByAttribute('class', classValue);
        }
        return self._elements[classValue];
    },

    function tabClicked(self, tab) {

        if(!self.lastSelectedTab) {
            var selected = self.nodesByAttribute("class", "selected");
            if(selected[0].parentNode.className == "tabs") {
                self.lastSelectedTab = selected[0];
                self.lastSelectedPage = selected[1];
            } else {
                self.lastSelectedTab = selected[1];
                self.lastSelectedPage = selected[0];
            }
            var tabs = self.lastSelectedTab.parentNode.getElementsByTagName("li");
            for(var i = 0; i < tabs.length; i++) {
                if(tabs[i] == self.lastSelectedTab) {
                    self.lastSelectedOffset = i;
                    break;
                }
            }
        }

        self.lastSelectedTab.className = self._tabPrefix + self.lastSelectedOffset;
        self.lastSelectedPage.className = self._pagePrefix + self.lastSelectedOffset;
            
        var tabOffset = tab.className.substr(self._tabPrefix.length, tab.className.length);
        var page = self._getHandyNode(self._pagePrefix + tabOffset);
        tab.className = page.className = self._selectedClassName;

        self.lastSelectedTab = tab;
        self.lastSelectedPage = page;
        self.lastSelectedOffset = tabOffset;
    });

// backward compatability

function setupTabbedPane(data, selectedTab) {
    for(i=0; i<data.length; i++) {

        tab = document.getElementById(data[i][0]);
        page = document.getElementById(data[i][1]);

        if(i == selectedTab) {
            tab.className = 'selected'
            page.className = 'selected';
        }

        tab.onclick = function() {

            for(i=0; i<data.length; i++) {
                tab = document.getElementById(data[i][0]);
                page = document.getElementById(data[i][1]);

                if(tab.id == this.id) {
                    tab.className = 'selected';
                    page.className = 'selected';
                }
                else {
                    tab.className = '';
                    page.className = '';
                }
            }
        }
    }
}

