from nevow import rend, loaders, tags as t
from nevow.taglibrary import tabbedPane

class TabbedPage(rend.Page):
    addSlash = True
    docFactory = loaders.stan(
        t.html[
            t.head[
                t.title["Tabbed Page Example"],
                tabbedPane.tabbedPaneGlue.inlineGlue
            ],
            t.body[
                t.invisible(data=t.directive("pages"),
                            render=tabbedPane.tabbedPane)
            ]
        ]
    )
    
    def data_pages(self, ctx, data):
        return {"name": "outer",
                "selected": 1,
                "pages": (("One", t.p["First One"]),
                          ("Two", t.p["Second One"]),
                          ("Three", t.p[t.invisible(
                            render = tabbedPane.tabbedPane,
                            data = {"name":  "inner",
                                    "pages": (("Four", t.p["Fourth One"]),
                                              ("Five", t.p["Fifth One"])) })]
                           ))}
