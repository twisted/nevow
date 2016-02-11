# vi:ft=python
from nevow import tags as T, rend, loaders, athena, url
from formless import annotate, webform
from twisted.python import util

animals = {'elf' : 'Pointy ears.  Bad attitude regarding trees.',
           'chipmunk': 'Cute.  Fuzzy.  Sings horribly.',
           'chupacabra': 'It sucks goats.',
           'ninja': 'Stealthy and invisible, and technically an animal.',
           }


class TypeAheadPage(athena.LivePage):
    _tmpl = util.sibpath(__file__, "typeahead.html")
    docFactory = loaders.xmlfile(_tmpl)
    def render_typehereField(self, ctx, data):
        frag = TypeAheadFieldFragment()
        frag.page = self
        return frag

class TypeAheadFieldFragment(athena.LiveFragment):
    docFactory = loaders.stan(
            T.span(render=T.directive('liveFragment'))[ '\n',
                T.input(type="text", _class="typehere"), '\n',
                T.h3(_class="description"),
                ])

    def loadDescription(self, typed):
        if typed == '':
            return None, '--'
        matches = []
        for key in animals:
            if key.startswith(typed):
                 matches.append(key)
        if len(matches) == 1:
            return matches[0], animals[matches[0]]
        elif len(matches) > 1:
            return None, "(Multiple found)"
        else:
            return None, '--'
    athena.expose(loadDescription)

class DataEntry(rend.Page):
    """Add Animal"""
    addSlash = 1

    docFactory = loaders.stan(
            T.html[T.body[T.h1[
                "First, a Setup Form."],
                T.h2["Enter some animals as data.  Click 'Done' to test looking up these animals."],
                T.h3["The neat stuff happens when you hit 'Done'."],
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
        return list(animals.keys())

    def child_typeahead(self, ctx):
        return TypeAheadPage(None, None)

