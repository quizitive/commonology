from django.views.generic.base import View
from django.shortcuts import render
from django.views.generic.edit import FormMixin
from django.contrib import messages
from django.forms import Form


class CardFormView(FormMixin, View):
    """
    A base class with sensible defaults for our basic user form-in-card
    See template cards/base_card.html for additional template
    variables that can be set to customize form further.
    Common use case would be to define a form_class and override post()
    to handle form-specific functionality
    """
    # form_class = YourFormClass
    header = "Welcome To Commonology"
    custom_message = None
    button_label = "Ok"
    card_template = 'cards/base_card.html'
    page_template = 'users/base.html'

    def get(self, request, *args, **kwargs):
        return self.render(request, *args, **kwargs)

    def render(self, request, *args, **kwargs):
        return render(request, self.page_template, self.get_context_data(**kwargs))

    def get_context_data(self, *args, **kwargs):
        context = {
            'header': self.header,
            'form': self.get_form(),
            'card_template': self.card_template,
            'button_label': self.button_label,
            'custom_message': self.custom_message
            }
        context.update(kwargs)
        return super().get_context_data(**context)

    def get_form(self, form_class=None):
        if not self.form_class:
            return
        form = super().get_form()
        return self.format_form(form)

    @staticmethod
    def format_form(form):
        for key, field in form.fields.items():
            if field.widget.__class__.__name__ == 'CheckboxInput':
                field.widget.attrs['class'] = 'w3-check'
            else:
                field.widget.attrs['class'] = 'w3-input'
        return form

    def warning(self, request, message, keep_form=True):
        self.custom_message = ''
        messages.warning(request, message)
        if not keep_form:
            self.form_class = None
        return self.render(request)
