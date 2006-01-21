from twisted.web import xmlrpc

from nevow import loaders, rend, inevow, static, url
from store import IPostit, Post

def pptime(tt):
    return tt.asHumanly()

def atompptime(tt):
    return tt.asISO8601TimeAndDate()

class Base(rend.Page):
    
    def __init__(self, store, *args, **kwargs):
        super(Base, self).__init__(*args, **kwargs)
        self.store = store
        
    def renderHTTP(self, ctx):
        return self.store.transact(rend.Page.renderHTTP, self, ctx)
    
    def locateChild(self, ctx, segments):
        return self.store.transact(rend.Page.locateChild, self, ctx, segments)

class Main(Base):
    docFactory = loaders.xmlfile('postit.html')
    child_styles = static.File('styles/')
    child_images = static.File('images/')

    def childFactory(self, ctx, segment):
        if segment == 'atom.xml':
            return Atom(self.store)
        elif segment == 'rpc2.py':
            return PostItRPC(self.store)

    def render_title(self, ctx, data): 
        return ctx.tag.clear()[IPostit(self.store).name]
    
    def data_get_posts(self, ctx, data):
        return IPostit(self.store).getPosts(15)
        
    def render_post(self, ctx, data):
        ctx.tag.fillSlots('tit_tit_attr', data.title)
        ctx.tag.fillSlots('tit_url_attr', data.url)
        ctx.tag.fillSlots('title', data.title)
        ctx.tag.fillSlots('perma_tit_attr', 'PermaLink')
        ctx.tag.fillSlots('perma_url_attr', url.here.add('view', data.storeID))
        ctx.tag.fillSlots('id', data.storeID)
        ctx.tag.fillSlots('author', data.author)
        ctx.tag.fillSlots('data', pptime(data.created))
        ctx.tag.fillSlots('content', data.content)
        return ctx.tag

class Atom(Base):
    docFactory = loaders.xmlfile('atom.xml')
    
    def beforeRender(self, ctx):
        inevow.IRequest(ctx).setHeader("Content-Type", "application/application+xml; charset=UTF-8")
    
    def data_getFirstPost(self, ctx, data):
        for post in IPostit(self.store).getPosts(1):
            return post

    def render_modified(self, ctx, data): 
        return ctx.tag.clear()[atompptime(data.created)]
    
    def data_get_posts(self, ctx, data):
        return IPostit(self.store).getPosts(15)
        
    def render_post(self, ctx, data):
        ctx.tag.fillSlots('title', data.title)
        ctx.tag.fillSlots('link', data.url)
        ctx.tag.fillSlots('id', data.storeID)
        ctx.tag.fillSlots('created', atompptime(data.created))
        ctx.tag.fillSlots('modified', atompptime(data.created))
        ctx.tag.fillSlots('author', data.author)
        ctx.tag.fillSlots('content', data.content)
        return ctx.tag
    
class PostItRPC(xmlrpc.XMLRPC):
    """Publishes stuff"""

    def __init__(self, store):
        xmlrpc.XMLRPC.__init__(self)
        self.store = store
    
    def xmlrpc_publish(self, token, url, title, desc, user):
        def _():
            newPost = Post(store=self.store,
                           author=user.decode('utf-8'), 
                           title=title.decode('utf-8'), 
                           url=url.decode('utf-8'), 
                           content=desc.decode('utf-8'))
            return newPost
        newPost = self.store.transact(_)
        return newPost.storeID

    def xmlrpc_entries(self, token, count):
        def _():
            return [(entry.url, entry.title, entry.content) for entry in IPostit(self.store).getPosts(count)]
        return self.store.transact(_)
