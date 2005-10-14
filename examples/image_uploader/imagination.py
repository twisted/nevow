from zope.interface import implements

from nevow import loaders, rend, tags as t, compy, inevow, static, url
from formless import webform, annotate
from atop.store import Store

from images import Image, IImages

class IInsert(annotate.TypedInterface):
    def insert(self, 
               ctx = annotate.Context(),
               title = annotate.String(),
               author = annotate.String(),
               image = annotate.FileUpload(required=True,
                                           requiredFailMessage="Must upload something")
               ):
        """ Insert a new image """
    insert = annotate.autocallable(insert, action="New Image")

class TransactionalPage(rend.Page):
    adaptsToStore = False
    def __init__(self, store, *args, **kwargs):
        super(TransactionalPage, self).__init__(*args, **kwargs)
        if self.adaptsToStore:
            self.original = store
            self.store = store
        else:
            self.original = store
            self.store = store.store
    
    def locateChild(self, ctx, segments):
        return self.store.transact(super(TransactionalPage, self).locateChild, ctx, segments)
    
    def renderHTTP(self, ctx):
        return self.store.transact(super(TransactionalPage, self).renderHTTP, ctx)
    

class Root(TransactionalPage):
    adaptsToStore = True
    child_webform_css = webform.defaultCSS
    implements(IInsert)
    
    def data_images(self, ctx, data):
        return IImages(self.store).getImages(15)
    
    def render_image(self, ctx, data):
        return t.a(href=url.here.child(data.filename))[data.title]

    def insert(self, ctx, title, author, image):
        img = Image(self.store, image.value, title, author)
        IImages(self.store).addImage(img)

    def locateChild(self, ctx, segments):
        if segments[0] == 'fs':
            data = IImages(self.store).getOne('/'.join(segments))
            return static.Data(data.getImage(), 'image/jpeg'), ()
        return super(Root, self).locateChild(ctx, segments)
            
    docFactory = loaders.stan(
        t.html[
            t.head[
                t.title['Imagination'],
                t.link(rel='stylesheet', type='text/css', href=url.root.child('webform_css'))
            ],
            t.body[
                webform.renderForms(),
                t.ul(render=t.directive("sequence"), 
                     data=t.directive("images"))[
                         t.li(pattern="item")[render_image],
                         t.li(pattern="empty")["No images yet"]
                ]
            ]
        ]
    )
        

compy.registerAdapter(Root, Store, inevow.IResource)
