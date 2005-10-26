/*

Originally adapted from http://svn.colorstudy.com/home/ianb/form.js

*/

/***********************************************************************
 *
 * Copyright (c) 2005 Imaginary Landscape LLC and Contributors.
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 **********************************************************************/

/*
This follows the WHAT-WG spec roughly, with the intention of following
it more closely in the future.

Its primary feature at the moment is the repeating field model from:
http://www.whatwg.org/specs/web-forms/current-work/#repeatingFormControls

You do this like:

  <form validate="1">

  <fieldset repeat="template" id="address">
  Address: <textarea name="addr-[address]"></textarea><br>
  <button type="remove">Remove this address</button>
  </fieldset>

  <button type="add" template="address">Add an address</button>

  </form>

The validate="1" attribute enables this library on that form.
repeat="template" marks something as a template, the id names the
template.  Fields inside the template have [id] substituted with an
integer.  Two kinds of buttons -- add and remove -- add a new
instance of the template, or remove the containing instance.

There's other stuff in here -- like validation and filling in the
templates -- but it's rough and probably will change to better
fit what WHAT-WG defines.

This library will move in the future, this is just a temporary
location for it.

*/


/* Utility functions */

DOM = MochiKit.DOM;
logError = MochiKit.Logging.logError;
logDebug = MochiKit.Logging.logDebug;



function all_inputs(node) {
    return MochiKit.Base.filter(
        function (el) {
            return (el.tagName == 'INPUT' || el.tagName == 'TEXTAREA'
                    || el.tagName == 'SELECT');
    }, all_child_tags(node));
}

function all_child_tags(node) {
    return DOM.getElementsByTagAndClassName('*', null, node);
}

function forms_assert(v, msg, allowWindow) {
    if (! v || (! allowWindow && v === this)) {
        throw ('Assertion failed (' 
               + (v === this ? 'got window object' : v) + ')'
               + (msg ? ': '+msg : ''));
    }
}

/*****************************************
 * Forms
 *****************************************/

function getForm(formId) {
    var form = getForm.allForms[formId];
    if (! form) {
        throw ('Form ' + formId + ' not found');
    }
    return form;
}

getForm.allForms = {};

getForm.register = function (formId, form) {
    getForm.allForms[formId] = form;
};

function Form(root) {
    forms_assert(this, 'Form');
    root = this.root = DOM.getElement(root);
    if (! this.root.getAttribute('validate')) {
        return;
    }
    this.id = this.root.getAttribute('id');
    getForm.register(this.id, this);
    this.templates = {}
    this.scanTemplates();
    this.scanAddButtons();
    this.scanFormData();
    MochiKit.DOM.addToCallStack(this.root, "onsubmit", validateForm);
}

Form.prototype.validate = function () {
    inputs = all_inputs(this.root);
    good = true;
    for (var i = 0; i<inputs.length; i++) {
        if (inputs[i].getAttribute('form-required')
            && inputs[i].name) {
            good = process_required(inputs[i]) && good;
        }
    }
    return good;
}

function validateForm() {
    var formEl = this;
    var form = getForm(formEl.getAttribute('id'));
    if (form) {
        return form.validate();
    }
}


Form.prototype.scanTemplates = function () {
    var self = this;
    forms_assert(self, 'scanTemplates(this)');
    MochiKit.Iter.forEach(
        DOM.getElementsByTagAndClassName('*', null, this.root),
        function (el) {
            if (el.getAttribute('repeat') == 'template') {
                new Template(self, el);
            }
        });
};

Form.prototype.scanAddButtons = function () {
    /* Find all add buttons */
    var self = this;
    MochiKit.Iter.forEach(
        this.root.getElementsByTagName('button'),
        function (el) {
            if (el.getAttribute('type') == 'add') {
                tmpl = self.templates[el.getAttribute('template')];
                tmpl.prepareAddButton(el);
            }
        });
};

Form.prototype.scanFormData = function () {
    /* Find all form data */
    var self = this;
    MochiKit.Iter.forEach(
        DOM.getElementsByTagAndClassName('*', 'form-data', this.root),
        function (data) {
            tmpl = self.templates[data.getAttribute('template')];
            tmpl.addFormData(data);
        });
}


/*****************************************
 * Templates (repeating forms)
 *****************************************/

function Template(form, root) {
    forms_assert(this, 'Template');
    forms_assert(form, 'Template(form)'); 
    forms_assert(root, 'Template(root)');
    root = this.root = DOM.getElement(root);
    this.id = root.getAttribute('id');
    logDebug('Enabling template ' + this.id
             + ' on form: ' + form.id);
    form.templates[this.id] = this;
    this.form = form;
    this.templateInstances = [];
    this.nextId = 0;
    DOM.hideElement(root);
    var self = this;
    MochiKit.Iter.forEach(
        DOM.getElementsByTagAndClassName('button', null, this.root),
        function (el) {
            if (el.getAttribute('type') == 'add') {
                self.prepareAddButton(el);
            }
        });
}

Template.prototype.prepareAddButton = function (button) {
    button.onclick = addButtonOnClick;
    logDebug('Prepared add button: ' + button + ' for template: '
             + this.id);
};

Template.prototype.prepareRemoveButton = function (button, inst) {
    button.repeatId = inst.getAttribute('id');
    button.onclick = removeButtonOnClick;
    logDebug('Prepared remove button: ' + button + ' for template: '
             + button.templateId);
}

Template.prototype.createInstance = function () {
    var form = this.form;
    var inst = this.root.cloneNode(true);
    forms_assert(inst, 'createInstance: inst');
    DOM.showElement(inst);
    var elements = DOM.getElementsByTagAndClassName('*', null, inst);
    var index = this.nextId;
    inst.setAttribute('id', this.id + index);
    inst.setAttribute('templateIndex', index);
    var templateVar = new RegExp("\\[" + this.id + "\\]", "g");
    var innerTemplates = [];
    this.nextId++;
    for (var i=0; i < elements.length; i++) {
        var el = elements[i];
        for (var j=0; j < el.attributes.length; j++) {
            var attr = el.attributes[j];
            var current = attr.nodeValue;
            var newValue = current.replace(templateVar, index);
            if (current != newValue) {
                // We're trying to avoid DOM manipulation if possible...
                attr.nodeValue = newValue;
            }
        }
        if (el.getAttribute('repeat') == 'template') {
            // We can't initialize these until this template is fully
            // set up
            innerTemplates.push(el);
        }
        if (el.tagName == 'BUTTON' && el.getAttribute('type') == 'add') {
            // @@: Should we call this later?
            this.prepareAddButton(el);
        }
    }
    for (var i=0; i < innerTemplates.length; i++) {
        t = new Template(form, innerTemplates[i]);
    }
    var buttons = inst.getElementsByTagName('button');
    for (var i=0; i < buttons.length; i++) {
        if (buttons[i].getAttribute('type') == 'remove') {
            this.prepareRemoveButton(buttons[i], inst);
        }
    }
    var last = this.lastInsertedTemplate();
    if (last.nextSibling) {
        last.parentNode.insertBefore(inst, last.nextSibling);
    } else {
        last.parentNode.appendChild(inst);
    }
    this.templateInstances.push(inst);
    return inst;
}

Template.prototype.lastInsertedTemplate = function () {
    var insts = this.templateInstances
    for (var i=insts.length-1; i >= 0; i--) {
        if (insts[i] && insts[i].parentNode) {
            return insts[i];
        }
    }
    // When no templates instances have been created yet, the template
    // itself is the place to insert things
    return this.root;
}

Template.prototype.addFormData = function (data) {
    var self = this;
    var inst = this.createInstance();
    forms_assert(inst, 'addFormData: inst');
    var allFields = all_inputs(inst);
    MochiKit.Iter.forEach(
        all_child_tags(data),
        function (field) {
            if (! field.getAttribute) {
                return;
            }
            var fieldName = field.getAttribute('form-name');
            if (! fieldName) {
                return;
            }
            fieldName = fieldName.replace(
                new RegExp('\\[' + self.id + '\\]', "g"),
                inst.getAttribute('templateIndex'));
            var fieldValue = field.getAttribute('form-value');
            var set = false;
            logDebug('Setting field "' + fieldName + '" to value: "'
                     + fieldValue + '" in template: ' + this.id);
            MochiKit.Iter.forEach(
                allFields,
                function (instField) {
                    if (instField.getAttribute('name') == fieldName) {
                        set_input_value(instField, fieldValue);
                        set = true;
                    }
                });
            if (! set) {
                throw ('No template field by the name ' + fieldName + ' found');
            }
        } 
    );
    DOM.swapDOM(data);
}


function removeButtonOnClick() {
    try {
        DOM.swapDOM(this.repeatId);
    } catch (e) {
        logError(e);
        alert('Error removing section: ' + e);
    }
    return false;
}

function addButtonOnClick() {
    try {
        var button = this;
        var form = getForm(button.form.getAttribute('id'));
        var templateId = button.getAttribute('template');
        var template = form.templates[templateId];
        if (! template) {
            throw ('No template named ' + templateId);
        }
        logDebug('Adding template ' + templateId + ' to form '
                 + form + ': ' + template);
        template.createInstance();
    } catch (e) {
        logError(e);
        alert('Error adding section: ' + e);
    }
    return false;
}








/*****************************************
 * Validation
 *****************************************/

/* This stuff is rough, doesn't follow WHAT-WG, and maybe is broken
   at the moment.  */


function process_required(input) {
    var types = input.getAttribute('form-required').split(',');
    var value;
    if (input.errorNode) {
        input.parentNode.removeChild(input.errorNode);
        input.errorNode = null;
    }
    MochiKit.DOM.removeElementClass(input, 'error');
    for (var i=0; i<types.length; i++) {
        var validator = validators[types[i]];
        if (! validator) {
            throw ('Unknown validation type: ' + types[i]);
        }
        result = validator(get_input_value(input), input, types[i]);
        if (result) {
            var err = MochiKit.DOM.DIV({'class': 'error'}, result);
            input.parentNode.insertBefore(err, input);
            MochiKit.DOM.addElementClass(input, 'error');
            input.errorNode = err;
            return false;
        }
    }
    return true;
}

function get_input_value(input) {
    if (input.tagName == 'INPUT' || input.tagName == 'TEXTAREA') {
        return input.value;
    } else if (input.tagName == 'SELECT') {
        return input.options[input.selectedIndex].value;
    } else {
        throw ('Unknown input tag: ' + input.tagName);
    }
}    

function set_input_value(input, value) {
    if (input.tagName == 'INPUT' || input.tagName == 'TEXTAREA') {
        input.value = value;
    } else if (input.tagName == 'SELECT') {
        for (var i=0; i < input.options.length; i++) {
            if (input.options[i].value == value) {
                input.selectedIndex = i;
                return;
            }
        }
        throw ('Value not found in select list ' 
               + input.getAttribute('name') + ': "'
               + value + '"');
    } else {
        throw ('Unknown input tag: ' + input.tagName);
    }
}

var validators = {
    present: function (value) {
        if (! value) {
            return 'Please enter something';
        }
    },
    url: function (value, input) {
        value = MochiKit.Format.strip(value);
        if (value && value.search(/^https?:\/\//) == -1) {
            value = 'http://' + value;
        }
        input.value = value;
    },
    'path-dir': function (value, input) {
        value = MochiKit.Format.strip(value);
        if (value && value.search(/\/$/) == -1) {
            value = value + '/';
        }
    }
};

MochiKit.DOM.addLoadEvent(
    function () {
        MochiKit.Iter.forEach(
            document.getElementsByTagName('form'),
            function (el) {new Form(el)});
    });
