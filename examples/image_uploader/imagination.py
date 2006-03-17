from zope.interface import implements

from nevow import loaders, rend, tags as t, static, url
from formless import webform, annotate

from images import Image, IImages

import random
from string import ascii_letters as alpha # ohhh...

alphaDigit = alpha + '0123456789'

def label(length=None):
   """
   Return one of 183,123,959,522,816 possible labels.
   """

   first = random.choice(alpha)
   rest = [random.choice(alphaDigit) for i in xrange(length or 7)]
   newLabel = first + ''.join(rest)
   return newLabel

class IInsert(annotate.TypedInterface):
    def insert(ctx = annotate.Context(),
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
        self.store = store

    def locateChild(self, ctx, segments):
        return self.store.transact(super(TransactionalPage, self).locateChild, ctx, segments)

    def renderHTTP(self, ctx):
        return self.store.transact(super(TransactionalPage, self).renderHTTP, ctx)


class Root(TransactionalPage):
    child_webform_css = webform.defaultCSS
    implements(IInsert)

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
                         t.li(pattern="item", render=t.directive("image")),
                         t.li(pattern="empty")["No images yet"]
                ]
            ]
        ]
    )

    def data_images(self, ctx, data):
        return IImages(self.store).getImages(15)

    def render_image(self, ctx, data):
        return t.a(href=url.root.child('fs').child(data.hash))[data.title]

    def insert(self, ctx, title, author, image):
        img = Image(store=self.store,
                    image=image.value,
                    title=title.decode('utf-8'),
                    author=author.decode('utf-8'),
                    hash=label().decode('utf-8'))

    def locateChild(self, ctx, segments):
        if segments[0] == 'fs':
            data = IImages(self.store).getOne(segments[1].decode('utf-8'))
            return static.Data(data.image, 'image/jpeg'), ()
        return super(Root, self).locateChild(ctx, segments)

