# vi:ft=python
from nevow import tags as T, rend, loaders, athena, url
from formless import annotate, webform
from twisted.python import util

animals = {u'elf' : u'Pointy ears.  Bad attitude regarding trees.',
           u'chipmunk': u'Cute.  Fuzzy.  Sings horribly.',
           u'chupacabra': u'It sucks goats.',
           }


class TypeAheadPage(athena.LivePage):
    _tmpl = util.sibpath(__file__, "typeahead.html")
    docFactory = loaders.xmlfile(_tmpl)
    def remote_loadDescription(self, ctx, typed):
        if typed == '':
            return None, u'--'
        matches = []
        for key in animals:
            if key.startswith(typed):
                 matches.append(key)
        if len(matches) == 1:
            return matches[0], animals[matches[0]]
        elif len(matches) > 1:
            return None, u"(Multiple found)"
        else:
            return None, u'--'

class DataEntry(rend.Page):
    """Add Animal"""
    addSlash = 1

    docFactory = loaders.stan(
            T.html[T.body[T.p[
                """Enter some animals as data.  Click 'Done' to test 
                looking up these animals.""",],
                webform.renderForms(),
                T.ol(data=T.directive("animals"), render=rend.sequence)[
                        T.li(pattern="item", render=T.directive("string")),
                                                                        ],
                T.h1[T.a(href=url.here.child('typeahead'))["Done"]],
                          ]
                    ]
                              )
    def bind_animals(self, ctx, ):
        """Add Animal"""
        return annotate.MethodBinding(
                'animals',
                annotate.Method(arguments=
                    [annotate.Argument('animal', annotate.String()),
                     annotate.Argument('description', annotate.Text())]),
                action="Add Animal",
                                      )

    def animals(self, animal, description):
        """Add Animal"""
        if not (animal and description):
            return
        animals[animal.decode('utf-8')] = description.decode('utf-8')
        return url.here

    def data_animals(self, ctx, data):
        return animals.keys()

    child_typeahead = athena.liveLoader(TypeAheadPage)

