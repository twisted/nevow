from twisted.application import strports, service

from nevow import rend, loaders, appserver, tags as t

import powerups as pups

class LibraryPage(rend.Page):
    docFactory = loaders.stan(
        t.html[
            t.head[
                t.title["My Library"]
            ],
            t.body[
                t.p(render=t.directive("book"))[
                    t.slot(name="title"),
                    t.hr,
                    t.slot(name="description")
                ]
            ]
        ]
    )
    def render_book(self, ctx, data):
        # This is dumb because it's hardcoded, if you add other books
        # to the store you may try to use ctx.args.get() to pass some
        # arguments through the url
        key = u"Title: 1"
        # self.original here, is actually our store.Store instance.
        # using pups.ILibrary(self.original) brings us the Powerup subclass
        # that we defined as a Store component in module powerups.py
        book = pups.ILibrary(self.original).getBookByTitle(u'Title: 1')
        ctx.tag.fillSlots('title', book.title)
        ctx.tag.fillSlots('description', book.description)
        return ctx.tag

# starting the database
s = pups.initialize("store")
site = appserver.NevowSite(resource = LibraryPage(s))
application = service.Application("Nevow_and_Axiom")
webserver = strports.service("8080", site)
webserver.setServiceParent(application)
