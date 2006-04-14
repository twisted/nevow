
from zope.interface import implements

from nevow import inevow
from nevow import loaders
from nevow import rend
from nevow import tags
from nevow.url import here

from formless import annotate
from formless import webform


whole = [(1, 'one'), (2, 'two'), (3, 'buckle'), (4, 'my'), (5, 'shoe')]


def doQuery(q, *args):
    """Pretend like we have a database and we are accessing it through this hypothetical interface.
    Ignore this. Use dbapi or adbapi instead, and build a real sql table. I hope that's obvious.
    """
    matchid = 'select * from foo where id ='
    setsql = 'update foo set subject = '
    insertsql = 'insert into foo values'
    if q == 'select * from foo':
        return whole
    elif q.startswith(matchid):
        theId = args[0]
        for dbid, subj in whole:
            if dbid == theId:
                return [(dbid, subj)]
        raise KeyError, theId
    elif q.startswith(setsql):
        newsubj, theId = args
        for index, (dbid, subj) in enumerate(whole):
            if dbid == theId:
                whole[index] = (dbid, newsubj)
    elif q.startswith(insertsql):
        max = whole[-1][0]
        subject, = args
        whole.append((max + 1, subject))


class IAddItem(annotate.TypedInterface):
    def addItem(newSubject=annotate.String()):
        pass
    addItem = annotate.autocallable(addItem)


class DBBrowser(rend.Page):
    implements(IAddItem)
    addSlash = True

    def addItem(self, newSubject):
        doQuery('insert into foo values subject = "%s"', newSubject)

    def data_queryDatabase(self, context, data):
        return doQuery('select * from foo')

    def render_row(self, context, data):
        theId, theSubj = data
        return context.tag[ # put our anchor in the li provided by the template
            tags.a(href=theId)[ theSubj ]
        ]

    docFactory = loaders.stan(
        tags.html[
            tags.body[
                tags.h1["Welcome, user"],
                tags.ul(data=tags.directive("queryDatabase"), render=tags.directive("sequence"))[
                    tags.li(pattern="item", render=render_row)
                    ],
                webform.renderForms()
                ]
            ]
        )

    def childFactory(self, ctx, name):
        """Since we created anchor tags linking to children of this resource
        directly by id, when the anchor is clicked, childFactory will be called
        with the appropriate id as the name argument."""
        try:
            ## Pass the id of the database item we want to be rendered on this page
            ## to the DBItem constructor. This integer will be used as the default data
            ## for this page.
            return DBItem(int(name))
        except ValueError:
            pass
            ## returning None results in a 404


class IItemWithSubject(annotate.TypedInterface):
    def setSubject(newSubject=annotate.String(label="Change Subject")):
        pass
    setSubject = annotate.autocallable(setSubject)


class DBItem(rend.Page):
    implements(IItemWithSubject)
    addSlash=True

    def setSubject(self, newSubject):
        ## Self.original is the data that was passed to the DBItem constructor above; the id of this record
        doQuery('update foo set subject = "%s" where id = %s', newSubject, self.original)

    def render_viewSelector(self, context, data):
        args = inevow.IRequest(context).args
        view = args.get('view', ['view'])[0]
        if view == 'view':
            selector = "View | ", tags.a(href=here.add('view','edit'))[ "Edit" ]
            editor = ''
        else:
            selector = tags.a(href=here.add('view','view'))["View"], " | Edit"
            editor = context.onePattern('edit')() # get one copy of the edit pattern
        viewer = context.onePattern('view')() # get one copy of the view pattern
        return selector, viewer, editor

    def render_itemDetail(self, context, data):
        theId, theSubject = doQuery('select * from foo where id = %s', self.original)[0]
        return tags.h2["Object ", theId], tags.span["Subject: ", theSubject]

    docFactory = loaders.stan(
        tags.html[
            tags.body[
                tags.p[tags.a(href=here.parent())["Up"]],
                tags.div(render=render_viewSelector)[
                    tags.p(pattern="edit")[webform.renderForms()],
                    tags.p(pattern="view")[render_itemDetail]
                    ]
                ]
            ]
        )

