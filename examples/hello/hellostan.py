from twisted.application import internet, service

from nevow import appserver
from nevow import loaders
from nevow import rend
from nevow import tags as T


class Page(rend.Page):
    """Example of using stan to render a page.
    """
    addSlash = True
    docFactory = loaders.stan(
        T.html[
            T.head[
                T.title['Hello'],
                ],
            T.body[
                T.p(id="body")['Welcome to the wonderful world of Nevow!'],
                ],
            ]
        )

application = service.Application('hellostan')
webServer = internet.TCPServer(8080, appserver.NevowSite(Page()))
webServer.setServiceParent(application)
