
from nevow import rend, loaders, url, tags as t
import forms
from aip import iaip, store

MAINMENU = [ {'title':'Informations',
               'url':'/index'},
              {'title':'School Calendar',
               'url':'/cal'},
              {'title':'Canteen',
               'url':'/canteen'},
              {'title':'Religion',
               'url':'/religion'},
              {'title':'Courses',
               'url':'/courses'},
              {'title':'Logistics Information',
               'url':'/logistics'},
              {'title':'Credits',
               'url':'/credits'},
              {'title':'Contacs',
               'url':'/contacts'}
            ]

SUBMENU = [ {'title':'Classes',
             'url':'/classes'},
            {'title':'Notices',
             'url':'/notices'},
            {'title':'Teaching Material',
             'url':'/material'}
          ]

class Base(rend.Page, forms.ResourceMixin):
    docFactory = loaders.xmlfile('main.html',
                                 templateDir='templates')

    def __init__(self, *a, **kw):
        rend.Page.__init__(self, *a, **kw)
        forms.ResourceMixin.__init__(self)

    def data_mainmenu(self, ctx, data):
        return MAINMENU

    def data_submenu(self, ctx, data):
        return SUBMENU

    def render_url(self, ctx, data):
        seg = url.URL.fromContext(ctx).pathList()[0]
        if seg == data['url'][1:]:
            return ctx.tag(href=data['url'], id="current")[data['title']]
        return ctx.tag(href=data['url'])[data['title']]

type_to_url = {
    store.Teacher: url.root.child('classes').child('teachers'),
    store.Proposal: url.root.child('classes').child('proposals'),
    store.Notice: url.root.child('notices').child('notice'),
    store.Class: url.root.child('classes').child('class'),
    store.SchoolYear: url.root.child('classes').child('year'),
}
    
class Generic(Base):
    addSlash = True
    template = None
    def macro_content(self, ctx):
        return loaders.xmlfile(self.template,
                               templateDir='templates',
                               ignoreDocType=True)

    def render_reference_to_string(self, ctx, data):
        base_url = type_to_url.get(type(data), None)
        if not base_url:
            return ctx.tag[data.label()]
        u = base_url.child(str(data.storeID))
        return ctx.tag.clear()[t.a(href=u)[data.label()]]

    def render_string_and_link(self, ctx, data):
        return ctx.tag[t.a(href=data[0])[data[1]]]

type_to_tables = {
    store.Course: (store.Teaches, store.Teaches.course),
    store.Teacher: (store.Teaches, store.Teaches.teacher)
}

class AdminBase(Generic):
    def form_add(self, ctx):
        form = forms.Form(self.add)
        self.add_form_fields(ctx, form)
        form.addAction(self.add)
        return form

    def add(self, ctx, form, data):
        pass

    def render_link_to_remove(self, ctx, data):
        u = url.here.child('remove').child(str(data))
        return ctx.tag[t.a(href=u)['Remove']]

    def render_link_to_modify(self, ctx, data):
        u = url.here.child('modify').child(str(data))
        return ctx.tag[t.a(href=u)['Modify']]

    def render_string_tagliato(self, ctx, data):
        return ctx.tag[data[:30]]
    
    def locateChild(self, ctx, segments):
        from aip import thanks, admin_modify
        if segments[0] == 'remove':
            it = iaip.IStore(ctx).getItemByID(int(segments[1]))
            tp = type_to_tables.get(type(it), None)
            if tp:
                table, field = tp
                for element in iaip.IStore(ctx).query(table, field == it):
                    element.deleteFromStore()
            it.deleteFromStore()
            return url.root.child('admin').child('thanks'), ()
        elif segments[0] == 'modify':
            it = iaip.IStore(ctx).getItemByID(int(segments[1]))
            return admin_modify.Modify(it), segments[2:]
        return super(AdminBase, self).locateChild(ctx, segments)
