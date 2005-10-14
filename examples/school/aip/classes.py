import forms

from aip import base, store, iaip

class Classes(base.Generic):
    template = 'classes.html'

    def locateChild(self, ctx, segments):
        if segments[0] == 'class':
            it = iaip.IStore(ctx).getItemByID(int(segments[1]))
            return Class(it), segments[2:]
        return super(Classes, self).locateChild(ctx, segments)

    child_years = lambda self, ctx: SchoolYears()
    child_proposals = lambda self, ctx: Proposals()
    child_laboratories = lambda self, ctx: Laboratories()
    child_timetable = lambda self, ctx: TimeTable()
    child_useful_material = lambda self, ctx: UsefulMaterial()
    child_teachers = lambda self, ctx: Teachers()

    def data_classes(self, ctx, data):
        return store.Class.get_all(iaip.IStore(ctx))

class Class(base.Generic):
    template = 'classes_class.html'

    def data_class(self, ctx, data):
        return self.original.label()

    def data_students(self, ctx, data):
        return self.original.students

class SchoolYear(base.Generic):
    addSlash = False
    template = 'classes_schoolyear.html'

    def data_year(self, ctx, data):
        return self.original.label()

    def data_classes(self, ctx, data):
        return self.original.classes

class SchoolYears(base.Generic):
    template = 'classes_schoolyears.html'

    def data_years(self, ctx, data):
        return store.SchoolYear.get_all(iaip.IStore(ctx))

    def childFactory(self, ctx, segment):
        if segment.isdigit():
            it = iaip.IStore(ctx).getItemByID(int(segment))
            return SchoolYear(it)

class Proposals(base.Generic):
    template = 'classes_proposals.html'

    def childFactory(self, ctx, segment):
        if segment.isdigit():
            it = iaip.IStore(ctx).getItemByID(int(segment))
            return Proposal(it)

    child_to = lambda self, ctx: ProposalsTo()

    def data_proposals(self, ctx, data):
        return store.Proposal.get_all(iaip.IStore(ctx))

    def child_insert(self, ctx):
        from aip import login
        if not iaip.IAvatar(ctx).username:
            return login.Login()
        return InsertProposals()

class Laboratories(base.Generic):
    template = 'classes_laboratories.html'

    child_related_courses = lambda self, ctx: RelatedCourses()

    def data_laboratories(self, ctx, data):
        return store.Laboratory.get_all(iaip.IStore(ctx))

class TimeTable(base.Generic):
    template = 'classes_timetable.html'

class UsefulMaterial(base.Generic):
    template = 'classes_useful_material.html'

class Teachers(base.Generic):
    template = 'classes_teachers.html'

    child_course = lambda self, ctx: TeachersCourse()

    def data_teachers(self, ctx, data):
        return store.Teacher.get_all(iaip.IStore(ctx))

    def childFactory(self, ctx, segment):
        if segment.isdigit():
            it = iaip.IStore(ctx).getItemByID(int(segment))
            return Teacher(it)

class Teacher(base.Generic):
    template = 'classes_teachers_teacher.html'

    def data_teacher(self, ctx, data):
        return self.original

class TeachersCourse(base.Generic):
    template = 'classes_teachers_course.html'

    def data_courses(self, ctx, data):
        return store.Course.get_all(iaip.IStore(ctx))

class Proposal(base.Generic):
    template = 'classes_proposals_proposal.html'

    def data_proposal(self, ctx, data):
        return self.original
    
class ProposalsTo(base.Generic):
    template = 'classes_proposals_to.html'

    def data_to(self, ctx, data):
        return store.Proposal.by_to(iaip.IStore(ctx))
            
class InsertProposals(base.Generic):
    template = 'classes_proposals_insert.html'

    def form_add(self, ctx):
        f = forms.Form(self.add)
        store.Proposal.to_form(iaip.IStore(ctx), f)
        f.addAction(self.add)
        return f

    def add(self, ctx, form, data):
        current_teacher = iaip.IAvatar(ctx)
        store = iaip.IStore(ctx)
        data['teacher'] = teacher
        store.Proposal(store = store,
                       **data)

class RelatedCourses(base.Generic):
    template = 'classes_laboratories_related_courses.html'

    def data_courses(self, ctx, data):
        return store.Course.get_all(iaip.IStore(ctx))
