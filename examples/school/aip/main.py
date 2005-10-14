from forms import defaultCSS

from nevow import rend, loaders, tags as t, static, url, inevow

from aip import iaip, base

from aip import index, cal, canteen, religion
from aip import courses, logistics, credits
from aip import contacts, classes, notices, material

class RootPage(base.Generic):
    addSlash = True
    template = 'i.html'

    child_theme = static.File('theme')
    children = {'forms.css': static.File('/Volumes/dati/Sviluppo/forms/forms/forms.css')}

    child_index = lambda self, ctx: index.Index()
    child_cal = lambda self, ctx: cal.Calendar()
    child_canteen = lambda self, ctx: canteen.Canteen()
    child_religion = lambda self, ctx: religion.Religion()
    child_courses = lambda self, ctx: courses.Courses()
    child_logistics = lambda self, ctx: logistics.Logistics()
    child_credits = lambda self, ctx: credits.Credits()
    child_contacts = lambda self, ctx: contacts.Contacts()
    child_classes = lambda self, ctx: classes.Classes()
    child_notices = lambda self, ctx: notices.Notices()
    child_material = lambda self, ctx: material.Material()
    child_login = lambda self, ctx: Login()

    def child_admin(self, ctx):
        from aip import admin, login
        if not iaip.IAvatar(ctx).username:
            return login.Login()
        return admin.Admin()
