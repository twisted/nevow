from zope.interface import implements

from twisted.python.components import registerAdapter

from nevow import loaders, rend, inevow, tags as T
from formless import annotate, webform
 
class Tree(dict):
    def __init__(self, name, description, *children):
        self.name = name
        self.description = description
        for child in children:
            self.add(child)
    def add(self, child):
        self[child.name] = child
    def __nonzero__(self):
        return True
 
class ITreeEdit(annotate.TypedInterface):
    def setDescription(description=annotate.String()):
        pass
    setDescription = annotate.autocallable(setDescription)
    def deleteChild(name=annotate.String(required=True)):
        pass
    deleteChild = annotate.autocallable(deleteChild, invisible=True)
    def addChild(name=annotate.String(required=True),
                       description=annotate.String()):
        pass
    addChild = annotate.autocallable(addChild)
 
class TreeRenderer(rend.Page):
    implements(ITreeEdit)
    addSlash = True
    docFactory = loaders.htmlstr("""
<html>
<head><title>Tree Editor</title></head>
<body><h1><span nevow:data="description"
                nevow:render="string">Tree Description</span></h1>
<span nevow:render="descriptionForm"/>
<ol nevow:data="children" nevow:render="sequence">
<li nevow:pattern="item"><span nevow:render="childLink"/>
<span nevow:render="childDel"/>
</li>
</ol>
<a href="..">Up</a>
</body>
</html>
    """)
    def setDescription(self, description):
        self.original.description = description
    def addChild(self, name, description):
        self.original.add(Tree(name, description))
    def deleteChild(self, name):
        del self.original[name]
    def data_description(self, context, data):
        return self.original.description
    def data_children(self, context, data):
        return self.original.items()
    def render_childLink(self, context, data):
        return T.a(href='subtree_%s/'%data[0])[data[1].description]
    def childFactory(self, ctx, name):
        if name.startswith('subtree_'):
            return self.original[name[len('subtree_'):]]
    def render_descriptionForm(self, context, data):
        return webform.renderForms()
    def render_childDel(self, context, (name, _)):
        ret = T.form(action="./freeform_post!!deleteChild",
                     enctype="multipart/form-data", method="POST")[
               T.input(type="hidden", name="name", value=name),
               T.input(type="submit", value="Delete")]
        return ret
 
registerAdapter(TreeRenderer, Tree, inevow.IResource)
