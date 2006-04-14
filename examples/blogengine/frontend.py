from time import time as now
from zope.interface import implements, Interface

from twisted.web import xmlrpc
from twisted.python.components import registerAdapter

from nevow import rend, loaders, url, static
from nevow import tags as t, inevow
from formless import annotate, iformless, webform

from axiomstore import Post
from iblogengine import IStore, IBlog

def pptime(tt):
    return tt.asHumanly()+" UTC"
def atompptime(tt):
    return tt.asISO8601TimeAndDate()
class ITimer(Interface):
    pass

#####################################
categories = ['Programming', 'Test', 'Sport', 'People', 'Python', 
              'Databases', 'bench', 'woo', 'Friends']

class IInsert(annotate.TypedInterface):
    def insert(
        ctx = annotate.Context(),
        title = annotate.String(strip=True, required=True, \
                                requiredFailMessage="Title must be provided", tabindex='1'),
        author = annotate.String(strip=True, default="Anonymous", tabindex='2'),
        id = annotate.String(hidden=True),
        category = annotate.Choice(categories, tabindex='3'),
        content = annotate.Text(required=True, \
                                requiredFailMessage="Posts with no content are not allowed", tabindex='4'),
        ):
        pass
    insert = annotate.autocallable(insert)

#####################################
class BaseUI(rend.Page):
    addSlash = True
    def renderHTTP(self, ctx):
        return IStore(ctx).transact(rend.Page.renderHTTP, self, ctx)
        
    def locateChild(self, ctx, segments):
        return IStore(ctx).transact(rend.Page.locateChild, self, ctx, segments)

#############################
class UI(BaseUI):
    
    docFactory = loaders.xmlfile ('ui.html')
    child_styles = static.File('styles')
    child_images = static.File('images')
    child_webform_css = webform.defaultCSS

    def render_starttimer(self, ctx, data):
        ctx.remember(now(), ITimer)
        return ctx.tag
        
    def render_stoptimer(self, ctx, data):
        start = ITimer(ctx)
        return ctx.tag['%s' % (now()-start)]

    def render_needForms(self, ctx, data):
        action = ctx.arg('action', 'view')
        if action == 'edit':
            form = inevow.IQ(ctx).onePattern('frm')
            return ctx.tag[form]
        return ctx.tag.clear()

    def data_getEntries(self, ctx, data):
        num = ctx.arg('num', '60')
        return IBlog(IStore(ctx)).getPosts(int(num))

    def render_entries(self, ctx, data):
        ctx.tag.fillSlots('modification', pptime(data.modified))
        ctx.tag.fillSlots('category', data.category)
        ctx.tag.fillSlots('author', data.author)
        ctx.tag.fillSlots('title', data.title)
        ctx.tag.fillSlots('content', data.content)
        ctx.tag.fillSlots('permaLink', url.root.child('%s' % (data.id)))
        return ctx.tag

    def render_insert(self, ctx, data):
        return ctx.tag

    def render_editer(self, ctx, data):
        ctx.tag.fillSlots('editPost', url.root.child('%s' % (data.id)
                                                         ).add('action','edit'))
        return ctx.tag

    def render_insert(self, ctx, data):
        ctx.tag.fillSlots('insert', url.root.child('insertEntry'))
        return ctx.tag

    def child_insertEntry(self, ctx):
        return NewEntry()

    def childFactory(self, ctx, segment):
        id = segment.isdigit() and segment or '-1'
        if int(id) >= 0:
            return IBlog(IStore(ctx)).getOne(int(id))
        elif segment == 'rpc2':
            return BlogRPC(IStore(ctx))
        elif segment == 'atom.xml':
            return Atom()

    def child_thx(self, ctx):
        return Thx()

##################################
class NewEntry(BaseUI):
    implements(IInsert)
                
    docFactory = loaders.stan(
        t.html[
            t.head[
                t.title['Insertion form'],
                t.link(rel='stylesheet', type='text/css', href=url.root.child('webform_css')),
            ],
            t.body[
                t.h1['Insertion'],
                t.invisible(render=t.directive("forms"))
            ]
        ])    
    def render_forms(self, ctx, data):
        d = iformless.IFormDefaults(ctx).getAllDefaults('insert')
        d['author'] = 'Anonymous'
        d['id'] = IBlog(IStore(ctx)).getNextId()
        return webform.renderForms()

    def insert(self, ctx, id, title, author, category, content):
        newPost = Post(store=IStore(ctx),
                       id=int(id),
                       author=unicode(author),
                       title=unicode(title),
                       category=unicode(category),
                       content=unicode(content))
        IBlog(IStore(ctx)).addNewPost(newPost)
        inevow.IRequest(ctx).setComponent(iformless.IRedirectAfterPost, '/thx')

#####################################
class Thx(rend.Page):
    docFactory = loaders.stan(
            t.html[
                t.body[
                    t.h1['Succeeded'],                    
                    t.a(href=url.root)["Back to main"]
                ]
            ])

####################################
class Entry(UI):
    implements(IInsert)
    def data_getEntries(self, ctx, data):
        return [data]

    def render_forms(self, ctx, data):
        d = iformless.IFormDefaults(ctx).getAllDefaults('insert')
        d['author'] = self.original.author
        d['category'] = self.original.category
        d['title'] = self.original.title
        d['content'] = self.original.content
        d['id'] = self.original.id
        return webform.renderForms()

    def insert(self, ctx, id, title, author, category, content):
        self.original.author = unicode(author)
        self.original.title = unicode(title)
        self.original.category = unicode(category)
        self.original.content = unicode(content)
        inevow.IRequest(ctx).setComponent(iformless.IRedirectAfterPost, '/thx')

#####################################
class Atom(BaseUI):
    docFactory = loaders.xmlfile('atom.xml')
    
    def beforeRender(self, ctx):
        inevow.IRequest(ctx).setHeader("Content-Type", "application/application+xml; charset=UTF-8")
    
    def data_getFirstPost(self, ctx, data):
        for post in IBlog(IStore(ctx)).getPosts(1):
            return post

    def render_modified(self, ctx, data): 
        return ctx.tag.clear()[atompptime(data.modified)]
    
    def data_get_posts(self, ctx, data):
        return IBlog(IStore(ctx)).getPosts(15)
        
    def render_post(self, ctx, data):
        #id = data.poolToUID[IBlog(IStore(ctx)).postsPool]
        # mkp: ...I don't know what that means or what it's for.
        ctx.tag.fillSlots('title', data.title)
        ctx.tag.fillSlots('link', url.root.child(data.id))
        ctx.tag.fillSlots('id', data.id)
        ctx.tag.fillSlots('created', atompptime(data.created))
        ctx.tag.fillSlots('modified', atompptime(data.modified))        
        ctx.tag.fillSlots('author', data.author)
        ctx.tag.fillSlots('content', data.content)
        return ctx.tag

#####################################
from axiom.item import transacted
class BlogRPC(xmlrpc.XMLRPC):
    """Publishes stuff"""

    def __init__(self, store):
        xmlrpc.XMLRPC.__init__(self)
        self.store = store
    
    def xmlrpc_publish(self, author, title, category, content):
        newid = IBlog(self.store).getNextId()
        newPost = Post(store=self.store,
                       id=newid,
                       author=unicode(author),
                       title=unicode(title),
                       category=unicode(category),
                       content=unicode(content))
        IBlog(self.store).addNewPost(newPost)
        return 'Successfully added post number %s' % newid
    xmlrpc_publish = transacted(xmlrpc_publish)

    def xmlrpc_edit(self, id, author, title, category, content):
        post = IBlog(self.store).getOne(id)
        post.author = author
        post.title = title
        post.category = category
        post.content = content
        post.setModified()
        return 'Successfully modified post number %s' % id
    xmlrpc_edit = transacted(xmlrpc_edit)
        
    def xmlrpc_entries(self, count):
        return [(entry.id, entry.author, entry.category, entry.title, entry.content) \
                for entry in IBlog(self.store).getPosts(count)]
    
    xmlrpc_entries = transacted(xmlrpc_entries)

registerAdapter(Entry, Post, inevow.IResource)

