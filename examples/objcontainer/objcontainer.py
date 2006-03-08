"""Example of using nevow.accessors.ObjectContainer to allow data directives to
look inside application types.
"""

from nevow import accessors, inevow, loaders, rend, tags as T
from twisted.python.components import registerAdapter

class Image:
    """An image consisting of a filename and some comments.
    """
    def __init__(self, filename, comments):
        self.filename = filename
        self.comments = comments
        
        
# Register the adapter so Nevow can access Image instance attributes.
registerAdapter(accessors.ObjectContainer, Image, inevow.IContainer)


# Just a list of images to render in the page.
images = [
    Image('python.gif', ['Hisssssssss']),
    Image('cat.gif', ['Meeow', 'Purrrrrrrr']),
    ]
    
    
class ImagePage(rend.Page):
    """A simple page that renders a list of images. We registered an adapter
    earlier so that the data= directives inside the pattern can look inside
    Image instances.
    """
    
    addSlash = True
    
    def render_images(self, ctx, data):
        """Render a list of images.
        """
        tag = T.div(data=images, render=rend.sequence)[
            T.div(pattern='item')[
                T.p(data=T.directive('filename'), render=T.directive('data')),
                T.ul(data=T.directive('comments'), render=rend.sequence)[
                    T.li(pattern='item', render=T.directive('data')),
                    ],
                ],
            ]
        return tag
        
    docFactory = loaders.stan( T.html[T.body[T.directive('images')]] )
        
        
def createResource():
    """Create the root resource of the example.
    """
    return ImagePage()
    
