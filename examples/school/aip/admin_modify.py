from aip import base, iaip

import forms

def modify(item_to_modify):
    def _(ctx, form, data):
        return item_to_modify.modify(ctx, form, data)
    _.__name__ = modify.__name__
    return _

class Modify(base.Generic):
    template = 'admin_modify.html'
    def form_modify(self, ctx):
        mod = modify(self.original)
        f = forms.Form(mod)
        self.original.to_form_modify(iaip.IStore(ctx), f)
        f.addAction(mod)
        return f

