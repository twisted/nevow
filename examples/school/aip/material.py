import itertools, os

import forms

from nevow import tags as t, static

from aip import base, iaip

class Material(base.Generic):
    template = 'material.html'

    child_works = lambda self, ctx: Works()
    child_games = lambda self, ctx: Games()
    child_other = lambda self, ctx: Other()

    def child_insert(self, ctx):
        from aip import login
        if not iaip.IAvatar(ctx).username:
            return login.Login()
        return InsertGames()

class Works(base.Generic):
    template = 'material_works.html'

    def data_works(self, ctx, data):
        l = os.listdir('documents/works')
        def _(item):
            name = item.split('.html')[0]
            return name, ' '.join([el.capitalize() for el in name.split('_')])
        return [_(link) for link in l]

    def childFactory(self, ctx, segment):
        name = '_'.join(segment.split(' ')).lower()+'.html'
        fd = file('documents/works/'+name)
        content = fd.read()
        fd.close()
        return Work(t.xml(content))

class Games(base.Generic):
    template = 'material_games.html'

    def data_games(self, ctx, data):
        l = os.listdir('documents/games')
        def _(item):
            name = item.split('.html')[0]
            return name, ' '.join([el.capitalize() for el in name.split('_')])
        return [_(link) for link in l]

    def childFactory(self, ctx, segment):
        name = '_'.join(segment.split(' ')).lower()+'.html'
        fd = file('documents/games/'+name)
        content = fd.read()
        fd.close()
        return Game(t.xml(content))

class Game(base.Generic):
    template = 'material_games_game.html'
    child_images = static.File('documents/images/')

    def render_content(self, ctx, data):
        return self.original

class Work(base.Generic):
    template = 'material_works_work.html'
    child_images = static.File('documents/images/')

    def render_content(self, ctx, data):
        return self.original

class Other(base.Generic):
    template = 'material_other.html'

class InsertGames(base.Generic):
    template = 'material_insert.html'

    def form_add(self, ctx):
        f = forms.Form(self.add)
        f.addField('title', forms.String(required=True))
        f.addField('content', forms.File(required=True), forms.FileUploadRaw)
        f.addAction(self.add)
        return f

    def add(self, ctx, form, data):
        _, fd = data['content']
        filename = data['title']
        name = '_'.join(filename.split(' ')).lower()+'.html'       
        f = file('documents/games/'+name, 'w')
        f.write(fd.read())
        f.close()
        fd.close()
