import os

from twisted.python import util

from nevow import inevow, loaders, rend, tags as T, url
from nevow.i18n import _, I18NConfig


LOCALE_DIR = util.sibpath(__file__, 'locale')


langs = [d for d in os.listdir(LOCALE_DIR) if d != '.svn']
langs.sort()

class Common(rend.Page):
    
    addSlash = True
    
    def renderHTTP(self, ctx):
        
        # We're only overriding renderHTTP to look for a 'lang' query parameter
        # without cluttering up the messages renderer, below.
        
        # If 'lang' is present then we "force" the translation language. This
        # simulates how user preferences from the session might be used to
        # override the browser's language settings.
        lang = ctx.arg('lang')
        if lang is not None:
            ctx.remember([lang], inevow.ILanguages)
            
        # Let the base class handle it, really.
        return rend.Page.renderHTTP(self, ctx)

    def render_langs(self, ctx, data):
        """Render a list of links to select from the available translations.
        """
        out = [T.a(href=url.here.remove('lang'))['default'], ' | ']
        for lang in langs:
            out.append(T.a(href=url.here.replace('lang', lang))[lang])
            out.append(' | ')
        return out[:-1]

class Page(Common):
    def render_message(self, ctx, data):
        """Render a localised message. The _(..) construct looks the
        translation up at render time.
        """
        return ctx.tag.clear()[_('Hello')]

    def render_formatstrings(self, ctx, data):
        return ctx.tag.clear()[
            "Demonstration of i18n'ed string formatting: ",
            _("%(first)d plus %(second)c equals %(result)c, or %(roman)s in roman numbers")
            % { 'first': 1,
                'second': '1',
                'result': 50,
                'roman': 'II',
                },
            ]

    docFactory = loaders.stan(
        T.html[
            T.body[
                T.p['Select your preferred language: ', T.directive('langs')],
                T.p[render_message],
                T.p[render_formatstrings],
                ],
            ],
        )

def preparePage(pageFactory):
    root = pageFactory()
    # Configure the I18N stuff
    root.remember(I18NConfig(domain='test', localeDir=LOCALE_DIR), inevow.II18NConfig)
    return root

def createResource():
    return preparePage(Page)
