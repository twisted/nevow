from nevow import static

from aip import base

class Religion(base.Generic):
    template = 'religion.html'

    child_remove = lambda self, ctx: Remove()

class Remove(base.Generic):
    template = 'religion_remove.html'

    children = {
        'modulo_esonero.doc': static.File('documents/modulo_esonero.doc')
    }
