from twisted.application import service, strports
from nevow import appserver

from environment import env as e
import store
import dispatcher
import itodo

application = service.Application('todo')
db = store.Todos(e.dbname, e.user, e.password, e.host)
disp = dispatcher.Dispatch()

site = appserver.NevowSite(resource=disp)
site.remember(db, itodo.ITodos)
site.remember(e, itodo.IEnv)

webserver = strports.service("tcp:8080", site)
webserver.setServiceParent(application)
