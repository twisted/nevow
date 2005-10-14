import forms

from aip import base, store, iaip

class Notices(base.Generic):
    template = 'notices.html'

    def locateChild(self, ctx, segments):
        if segments[0] == 'notice':
            if segments[1].isdigit():
                it = iaip.IStore(ctx).getItemByID(int(segments[1]))
                return Notice(it), segments[2:]
        return super(Notices, self).locateChild(ctx, segments)

    child_subject = lambda self, ctx: Subject()

    def data_notices(self, ctx, data):
        return store.Notice.get_all(iaip.IStore(ctx))

    def child_insert(self, ctx):
        from aip import login
        if not iaip.IAvatar(ctx).username:
            return login.Login()
        return InsertNotice()

class Subject(base.Generic):
    template = 'notices_subject.html'

    def data_subjects(self, ctx, data):
        return store.Notice.by_subject(iaip.IStore(ctx))

class InsertNotice(base.Generic):
    template = 'notices_insert.html'

    def form_add(self, ctx):
        f = forms.Form(self.add)
        store.Notice.to_form(iaip.IStore(ctx), f)
        f.addAction(self.add)
        return f

    def add(self, ctx, form, data):
        current_teacher = iaip.IAvatar(ctx)
        store = iaip.IStore(ctx)
        data['teacher'] = current_teacher
        store.Notice(store = store,
                     **data)

class Notice(base.Generic):
    template = 'notices_notice.html'

    def data_notice(self, ctx, data):
        return self.original
