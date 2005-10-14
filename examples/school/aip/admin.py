from aip import base, store, iaip, thanks
from aip.base import AdminBase
import forms

# Se rimuovo una materia, devo rimuovere la linea da insegna
# Prima di rimuovere devo chiedere conferma

class Admin(base.Generic):
    template = 'admin.html'

    child_classes = lambda self, ctx: AdminClasses()
    child_teachers = lambda self, ctx: AdminTeachers()
    child_students = lambda self, ctx: AdminStudents()
    child_courses = lambda self, ctx: AdminCourses()
    child_schoolyears = lambda self, ctx: AdminSchoolYears()
    child_notices = lambda self, ctx: AdminNotices()
    child_laboratories = lambda self, ctx: AdminLaboratories()
    child_proposals = lambda self, ctx: AdminProposals()
    child_thanks = lambda self, ctx: thanks.Thanks()

class AdminSchoolYears(AdminBase):
    template = 'admin_schoolyears.html'

    def data_years(self, ctx, data):
        return store.SchoolYear.get_all(iaip.IStore(ctx))

    def add_form_fields(self, ctx, form):
        store.SchoolYear.to_form(iaip.IStore(ctx), form)

    def add(self, ctx, form, data):
        store.SchoolYear(store=iaip.IStore(ctx),
                         anno=data['year'])

class AdminClasses(AdminBase):
    template = 'admin_classes.html'

    def data_classes(self, ctx, data):
        return store.Class.get_all(iaip.IStore(ctx))

    def add_form_fields(self, ctx, form):
        store.Class.to_form(iaip.IStore(ctx), form)
    
    def add(self, ctx, form, data):
        year = iaip.IStore(ctx).getItemByID(data['schoolyear'])
        store.Class(store=iaip.IStore(ctx),
                    number_letter = data['number_letter'],
                    schoolyear = year)
                         
class AdminCourses(AdminBase):
    template = 'admin_courses.html'

    def data_courses(self, ctx, data):
        return store.Course.get_all(iaip.IStore(ctx))

    def add_form_fields(self, ctx, form):
        store.Course.to_form(iaip.IStore(ctx), form)

    def add(self, ctx, form, data):
        store.Course(store=iaip.IStore(ctx),
                     **data)

class AdminTeachers(AdminBase):
    template = 'admin_teachers.html'

    def data_teachers(self, ctx, data):
        return store.Teacher.get_all(iaip.IStore(ctx))

    def add_form_fields(self, ctx, form):
        store.Teacher.to_form(iaip.IStore(ctx), form)
        form.addField('password', forms.String(required=True), forms.CheckedPassword)        

    def add(self, ctx, form, data):
        courses = data.pop('courses')
        data['password'] = unicode(data['password'])
        d = store.Teacher(store=iaip.IStore(ctx),
                          **data)
        d.courses = courses
    
class AdminStudents(AdminBase):
    template = 'admin_students.html'

    def data_students(self, ctx, data):
        return store.Student.get_all(iaip.IStore(ctx))

    def add_form_fields(self, ctx, form):
        store.Student.to_form(iaip.IStore(ctx), form)        

    def add(self, ctx, form, data):
        class_ = data.pop('classe')
        class_ = iaip.IStore(ctx).getItemByID(class_)
        data['class_'] = class_
        store.Student(store=iaip.IStore(ctx),
                      **data)
        
class AdminNotices(AdminBase):
    template = 'admin_notices.html'

    def data_notices(self, ctx, data):
        return store.Notice.get_all(iaip.IStore(ctx))

    def add_form_fields(self, ctx, form):
        store.Notice.to_form(iaip.IStore(ctx), form)

    def add(self, ctx, form, data):
        current_teacher = iaip.IAvatar(ctx)
        store = iaip.IStore(ctx)
        data['teacher'] = current_teacher
        store.Notice(store = store,
                     **data)
    
class AdminLaboratories(AdminBase):
    template = 'admin_laboratories.html'

    def data_laboratories(self, ctx, data):
        return store.Laboratory.get_all(iaip.IStore(ctx))

    def add_form_fields(self, ctx, form):
        store.Laboratory.to_form(iaip.IStore(ctx), form)

    def add(self, ctx, form, data):
        course = iaip.IStore(ctx).getItemByID(data['course'])
        data['course'] = course
        store.Laboratory(store = iaip.IStore(ctx),
                         **data)
    
class AdminProposals(AdminBase):
    template = 'admin_proposals.html'    

    def data_proposals(self, ctx, data):
        return store.Proposal.get_all(iaip.IStore(ctx))
    
    def add_form_fields(self, ctx, form):
        store.Proposal.to_form(iaip.IStore(ctx), form)

    def add(self, ctx, form, data):
        current_teacher = iaip.IAvatar(ctx)
        store = iaip.IStore(ctx)
        data['teacher'] = current_teacher
        store.Proposal(store = store,
                       **data)

