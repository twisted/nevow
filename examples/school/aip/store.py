
import operator, itertools

from twisted.cred.portal import IRealm
from twisted.cred.credentials import IUsernamePassword, IUsernameHashedPassword
from twisted.cred.checkers import ICredentialsChecker, ANONYMOUS
from twisted.cred.error import UnauthorizedLogin

from zope.interface import implements, Interface, Attribute, classImplements

from nevow.accessors import ObjectContainer
from nevow.inevow import IContainer
from nevow.compy import registerAdapter

from forms import iforms
import forms

from axiom import store, item
from axiom.attributes import reference, text, AND, OR, integer

from aip import iaip

class BadCredentials(UnauthorizedLogin):
    pass

class NoSuchUser(UnauthorizedLogin):
    pass

class DuplicateUser(Exception):
    pass

class SchoolYear(item.Item):
    schemaVersion = 1
    typeName = 'schoolyear'

    year = text()
    
    @staticmethod
    def get_all(store):
        return store.query(SchoolYear,
                           sort=SchoolYear.year.descending)

    @staticmethod
    def to_form(store, form):
        form.addField('year', forms.String(required=True))

    def get_classes(self):
        return self.store.query(Class,
                                Class.schoolyear == self,
                                sort=Class.number_letter.ascending)
    classes = property(get_classes)

    def to_form_modify(self, store, form):
        self.to_form(store, form)
        form.data = {'year': self.anno }

    def modify(self, ctx, form, data):
        self.year = data['year']
        self.touch()

    def key(self):
        return self.storeID
    
    def label(self):
        return 'A.S. ' + self.year
classImplements(SchoolYear, iforms.IKey)
classImplements(SchoolYear, iforms.ILabel)

    
class Class(item.Item):
    schemaVersion = 1
    typeName = 'class'
    
    number_letter = text()
    
    schoolyear = reference(reftype=SchoolYear)

    @staticmethod
    def get_all(store):
        return store.query(Class,
                           sort=Class.number_letter.descending)

    @staticmethod
    def to_form(store, form):
        years = SchoolYear.get_all(store)
        form.addField('number_letter', forms.String(required=True))
        form.addField('schoolyear',
                      forms.Integer(required=True),
                      forms.widgetFactory(forms.SelectChoice, years))

    def get_students(self):
        return self.store.query(Student,
                                Student.class_ == self)
    students = property(get_students)

    def to_form_modify(self, store, form):
        self.to_form(store, form)
        form.data = { 'number_letter': self.number_letter,
                      'schoolyear': self.schoolyear.storeID }

    def modify(self, ctx, form, data):
        self.number_letter = data['number_letter']
        self.schoolyear = self.store.getItemByID(data['schoolyear'])
        self.touch()

    def key(self):
        return self.storeID
    
    def label(self):
        return self.number_letter
classImplements(Class, iforms.IKey)
classImplements(Class, iforms.ILabel)


class Course(item.Item):
    schemaVersion = 1
    typeName = 'course'

    name = text()

    @staticmethod
    def get_all(store):
        return store.query(Course,
                           sort=Course.name.ascending)

    @staticmethod
    def to_form(store, form):
        form.addField('nome', forms.String(required=True))

    def get_laboratories(self):
        return self.store.query(Laboratory,
                                Laboratory.course == self)
    laboratories = property(get_laboratories)
    
    def get_teachers(self):
        return itertools.imap(operator.attrgetter('teacher'),
                              self.store.query(Teaches, Teaches.course == self))
    teachers = property(get_teachers)

    def to_form_modify(self, store, form):
        self.to_form(store, form)
        form.data = { 'name': self.name }

    def modify(self, ctx, form, data):
        self.name = data['name']
        self.touch()

    def key(self):
        return self.storeID
    
    def label(self):
        return self.nome
classImplements(Course, iforms.IKey)
classImplements(Course, iforms.ILabel)


class Teacher(item.Item):
    schemaVersion = 1
    typeName = 'teacher'

    name = text()
    surname = text()
    address = text()
    phone = text()
    fiscal_code = text()
    username = text()
    password = text()

    @staticmethod
    def get_all(store):
        return store.query(Teacher,
                           sort=Teacher.surname.ascending)

    @staticmethod
    def to_form(store, form):
        courses = store.query(Course)
        form.addField('name', forms.String(required=True))
        form.addField('surname', forms.String(required=True))
        form.addField('address' , forms.String(required=True))
        form.addField('phone' , forms.String(required=True))
        form.addField('fiscal_code' , forms.String(required=True))
        form.addField('username', forms.String(required=True))
        form.addField('courses',
                      forms.Sequence(forms.Integer(required=True), required=True),
                      forms.widgetFactory(forms.CheckboxMultiChoice, courses))

    def get_courses(self):
        courses_id = self.store.query(Teaches, Teaches.teacher == self)
        return (crs.course for crs in courses_id)
        
    def set_courses(self, courses):
        for course in courses:
            c = self.store.getItemByID(course)
            for res in self.store.query(Teaches,
                                        AND(Teaches.teacher == self,
                                            Teaches.course == c)):
                # Check it is not already there
                return
            Teaches(store = self.store,
                    teacher = self,
                    course = c)

    courses = property(get_courses, set_courses)

    def to_form_modify(self, store, form):
        courses_id = store.query(Teaches, Teaches.teacher == self)
        materie = (crs.course.storeID for crs in courses_id)
        self.to_form(store, form)
        form.addField('password', forms.String(), forms.CheckedPassword)
        form.data = {'name': self.name,
                     'surname': self.surname,
                     'address': self.address,
                     'phone': self.phone,
                     'fiscal_code': self.fiscal_code,
                     'username': self.username,
                     'courses': courses}

    def modify(self, ctx, form, data):
        self.name = data.get('name')
        self.surname = data.get('surname')
        self.address = data.get('address')
        self.phone = data.get('phone')
        self.fiscal_code = data.get('fiscal_code')
        self.username = data.get('username')
        self.courses = data.get('courses')
        pwd = data.get('password', None)
        if pwd:
            self.password = unicode(data.get('password'))
        self.touch()

    def get_notices(self):
        return self.store.query(Notice,
                                Notice.teacher == self)

    def get_proposals(self):
        return self.store.query(Proposal,
                                Proposal.teacher == self)

    def key(self):
        return self.storeID
    
    def label(self):
        return self.name + ' ' + self.surname
classImplements(Teacher, iforms.IKey)
classImplements(Teacher, iforms.ILabel)

    

class Student(item.Item):
    schemaVersion = 1
    typeName = 'student'
    
    name = text()
    surname = text()
    address = text()
    phone = text()
    fiscal_code = text()

    class_ = reference(reftype=Class)

    @staticmethod
    def get_all(store):
        return store.query(Student,
                           sort=Student.surname.ascending)

    @staticmethod
    def to_form(store, form):
        classes = store.query(Class)
        form.addField('name', forms.String(required=True))
        form.addField('surname', forms.String(required=True))
        form.addField('address' , forms.String(required=True))
        form.addField('phone' , forms.String(required=True))
        form.addField('fiscal_code' , forms.String(required=True))
        form.addField('classes',
                      forms.Integer(required=True),
                      forms.widgetFactory(forms.SelectChoice, classes))

    def to_form_modify(self, store, form):
        self.to_form(store, form)
        form.data = { 'name': self.name,
                      'surname': self.surname,
                      'address': self.address,
                      'phone': self.phone,
                      'fiscal_code': self.fiscal_code,
                      'class': self.class_.storeID }

    def modify(self, ctx, form, data):
        self.name = data['name']
        self.surname = data['surname']
        self.address = data['address']
        self.phone = data['phone']
        self.fiscal_code = data['fiscal_code']
        self.class_ = self.store.getItemByID(data['class'])
        self.touch()

class Notice(item.Item):
    schemaVersion = 1
    typeName = 'notice'    

    subject = text()
    title = text()
    content = text()

    teacher = reference(reftype=Teacher)

    @staticmethod
    def get_all(store):
        return store.query(Notice)

    @staticmethod
    def to_form(store, form):
        form.addField('subject', forms.String(required=True))
        form.addField('title', forms.String(required=True))
        form.addField('content', forms.String(required=True), forms.TextArea)

    @staticmethod
    def by_subject(store):
        args = list(itertools.groupby(list(store.query(Notice)), operator.attrgetter('subject')))
        for subject, _ in args:
            yield subject, store.query(Notice, Notice.subject == subject)

    def to_form_modify(self, store, form):
        form.addField('teacher', forms.String(immutable=True))
        self.to_form(store, form)
        form.data = { 'subject': self.subject,
                      'title': self.title,
                      'content': self.content,
                      'teacher': self.teacher.name }

    def modify(self, ctx, form, data):
        self.subject = data['subject']
        self.title = data['title']
        self.content = data['content']
    
    def key(self):
        return self.storeID
    
    def label(self):
        return self.titolo
classImplements(Notice, iforms.IKey)
classImplements(Notice, iforms.ILabel)

class Laboratory(item.Item):
    schemaVersion = 1
    typeName = 'laboratory'

    name = text()

    course = reference(reftype=Course)

    @staticmethod
    def get_all(store):
        return store.query(Laboratory)

    @staticmethod
    def to_form(store, form):
        courses = store.query(Course)
        form.addField('name', forms.String(required=True))
        form.addField('course',
                      forms.Integer(required=True),
                      forms.widgetFactory(forms.SelectChoice, courses))

    def to_form_modify(self, store, form):
        self.to_form(store, form)
        form.data = {'name': self.name,
                     'course': self.course.storeID }

    def modify(self, ctx, form, data):
        self.name = data['name']
        self.course = self.store.getItemByID(data['course'])
        self.touch()


class Proposal(item.Item):
    schemaVersion = 1
    typeName = 'proposal'

    to = text()
    title = text()
    content = text()

    teacher = reference(reftype=Teacher)

    @staticmethod
    def get_all(store):
        return store.query(Proposal)

    @staticmethod
    def to_form(store, form):
        form.addField('to', forms.String(required=True))
        form.addField('title', forms.String(required=True))
        form.addField('content', forms.String(required=True), forms.TextArea)

    @staticmethod
    def by_to(store):
        tos = list(itertools.groupby(store.query(Proposal), operator.attrgetter('to')))
        for to, _ in tos:
            yield to, store.query(Proposal, Proposal.to == to)

    def to_form_modify(self, store, form):
        self.to_form(store, form)
        form.addField('teacher', forms.String(immutable=True))        
        form.data = { 'to': self.to,
                      'title': self.title,
                      'content': self.content,
                      'teacher': self.teacher.name }

    def modify(self, ctx, form, data):
        self.to = data['to']
        self.title = data['title']
        self.content = data['content']
        self.touch()

    def key(self):
        return self.storeID
    
    def label(self):
        return self.title
classImplements(Proposal, iforms.IKey)
classImplements(Proposal, iforms.ILabel)


class Teaches(item.Item):
    schemaVersion = 1
    typeName = 'teaches'

    course = reference(reftype=Course)
    teacher = reference(reftype=Teacher)

class TeachesIn(item.Item):
    schemaVersion = 1
    typeName = 'teaches_in'

    class_ = reference(reftype=Class)
    teacher = reference(reftype=Teacher)
        
class WasPartOf(item.Item):
    schemaVersion = 1
    typeName = 'was_part_of'

    student = reference(reftype=Student)
    class_ = reference(reftype=Class)

class Anon(object):
    name = None
    surname = None
    address = None
    phone = None
    fiscal_code = None
    username = None
    password = None

class LoginSystem(item.Item):
    implements(IRealm, ICredentialsChecker)

    credentialInterfaces = (IUsernameHashedPassword, IUsernamePassword)

    schemaVersion = 1
    typeName = 'login_system'

    loginCount = integer(default=0)

    def install(self):
        self.store.powerUp(self, IRealm)
        self.store.powerUp(self, ICredentialsChecker)

    def get_teacher(self, username):
        for account in self.store.query(Teacher,
                                        Teacher.username == username):
            return account

    def create_teacher(self, name, surname, address, phone,
                       fiscal_code, username, password):
        username = unicode(username)
        if self.get_teacher(username) is not None:
            raise DuplicateUser(username)
        return Teacher(store = self.store,
                       name = unicode(name),
                       surname = unicode(surname),
                       address = unicode(address),
                       phone = unicode(phone),
                       fiscal_code = unicode(fiscal_code),
                       password = unicode(password),
                       username = username)

    def requestAvatar(self, avatarId, mind, *interfaces):
        from aip import main
        if avatarId is ANONYMOUS:
            av = Anon()
        else:
            av = self.store.getItemByID(avatarId)
        for interface in interfaces:
            page = main.RootPage()
            page.remember(av, iaip.IAvatar)
            return interface, page, lambda: None
        raise NotImplementedError()

    def requestAvatarId(self, credentials):
        username = unicode(credentials.username)
        acct = self.get_teacher(username)
        if acct is not None:
            password = acct.password
            if credentials.checkPassword(password):
                return acct.storeID
            else:
                raise BadCredentials()
        raise NoSuchUser(credentials.username)


registerAdapter(ObjectContainer, SchoolYear, IContainer)
registerAdapter(ObjectContainer, Class, IContainer)
registerAdapter(ObjectContainer, Student, IContainer)
registerAdapter(ObjectContainer, Teacher, IContainer)
registerAdapter(ObjectContainer, Notice, IContainer)
registerAdapter(ObjectContainer, Course, IContainer)
registerAdapter(ObjectContainer, Laboratory, IContainer)
registerAdapter(ObjectContainer, Proposal, IContainer)
