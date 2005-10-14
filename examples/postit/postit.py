import time

from twisted.web import xmlrpc

from atop.store import transacted
from nevow import loaders, rend, inevow, static, url
from store import IPostit, Post

def pptime(tt):
    return time.strftime('%Y-%m-%d @ %H:%M %Z', tt)

def atompptime(tt):
    return time.strftime('%Y-%m-%dT%H:%M:%S%z', tt)

class Base(rend.Page):
    
    def __init__(self, store, *args, **kwargs):
        super(Base, self).__init__(*args, **kwargs)
        self.store = store
        
    def renderHTTP(self, ctx):
        self.store.transact(rend.Page.renderHTTP, self, ctx)

class Main(Base):
    docFactory = loaders.xmlfile('postit.html')
    child_styles = static.File('styles/')
    child_images = static.File('images/')

    def childFactory(self, ctx, segment):
        if segment == 'atom.xml':
            return Atom(self.store)
        elif segment == 'rpc2.py':
            return PostItRPC(self.store)

    def render_title(self, ctx, data): return ctx.tag.clear()['Post-it']
    
    def data_get_posts(self, ctx, data):
        return IPostit(self.store).getPosts(15)
        
    def render_post(self, ctx, data):
        id = data.poolToUID[IPostit(self.store).postsPool]
        ctx.tag.fillSlots('tit_tit_attr', data.title)
        ctx.tag.fillSlots('tit_url_attr', data.url)
        ctx.tag.fillSlots('title', data.title)
        ctx.tag.fillSlots('perma_tit_attr', 'PermaLink')
        ctx.tag.fillSlots('perma_url_attr', url.here.add('view', id))
        ctx.tag.fillSlots('id', id)
        ctx.tag.fillSlots('author', data.author)
        ctx.tag.fillSlots('data', pptime(data.dateCreated))
        ctx.tag.fillSlots('content', data.content)
        return ctx.tag

class Atom(Base):
    docFactory = loaders.xmlfile('atom.xml')
    
    def beforeRender(self, ctx):
        inevow.IRequest(ctx).setHeader("Content-Type", "application/application+xml; charset=UTF-8")
    
    def data_getFirstPost(self, ctx, data):
        for post in IPostit(self.store).getPosts(1):
            return post
    

    def render_modified(self, ctx, data): return ctx.tag.clear()[atompptime(data.dateCreated)]
    
    def data_get_posts(self, ctx, data):
        return IPostit(self.store).getPosts(15)
        
    def render_post(self, ctx, data):
        id = data.poolToUID[IPostit(self.store).postsPool]
        ctx.tag.fillSlots('title', data.title)
        ctx.tag.fillSlots('link', data.url)
        ctx.tag.fillSlots('id', id)
        ctx.tag.fillSlots('created', atompptime(data.dateCreated))
        ctx.tag.fillSlots('modified', atompptime(data.dateCreated))        
        ctx.tag.fillSlots('author', data.author)
        ctx.tag.fillSlots('content', data.content)
        return ctx.tag
    
class PostItRPC(xmlrpc.XMLRPC):
    """Publishes stuff"""

    def __init__(self, store):
        xmlrpc.XMLRPC.__init__(self)
        self.store = store
    
    def xmlrpc_publish(self, token, url, title, desc, user):
        newPost = Post(self.store, user, title, url, desc)
        id = IPostit(self.store).addNewPost(newPost)
        return id
    xmlrpc_publish = transacted(xmlrpc_publish)
    
    def xmlrpc_entries(self, token, count):
        return [(entry.url, entry.title, entry.content) for entry in IPostit(self.store).getPosts(count)]
    xmlrpc_entries = transacted(xmlrpc_entries)
