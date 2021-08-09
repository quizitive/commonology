from django.views.generic.base import View
from django.shortcuts import render, redirect
from django.views.generic.edit import FormMixin, ContextMixin
from django.contrib import messages
from django.template.loader import render_to_string


class BaseCardView(ContextMixin, View):
    """
    A base class with sensible defaults for our basic card views
    See template cards/base_card.html for additional template
    variables that can be set to customize form further.
    """
    header = None
    custom_message = None
    button_label = "Ok"
    card_template = 'cards/base_card.html'
    page_template = 'single_card_view.html'

    def get(self, request, *args, **kwargs):
        return self.render(request, *args, **kwargs)

    def render(self, request, *args, **kwargs):
        return render(request, self.page_template, self.get_context_data(**kwargs))

    def render_card(self, request, *args, **kwargs):
        return render_to_string(self.card_template, self.get_context_data(**kwargs), request)

    def get_context_data(self, *args, **kwargs):
        context = {
            'header': self.header,
            'card_template': self.card_template,
            'button_label': self.button_label,
            'custom_message': self.custom_message
            }
        context.update(kwargs)
        return super().get_context_data(**context)

    def warning(self, request, message, *args, **kwargs):
        self.custom_message = ''
        messages.warning(request, message)
        return self.render(request, *args, **kwargs)

    def info(self, request, message, *args, **kwargs):
        self.custom_message = ''
        messages.info(request, message)
        return self.render(request, *args, **kwargs)

    def render_message(self, request, message, *args, **kwargs):
        self.custom_message = message
        return self.render(request, *args, **kwargs)


class CardFormView(FormMixin, BaseCardView):
    """
    A base class with sensible defaults for our basic user form-in-card
    See template cards/base_card.html for additional template
    variables that can be set to customize form further.
    Common use case would be to define a form_class and override post()
    to handle form-specific functionality
    """
    # form_class = YourFormClass

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

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


class CardChartView(BaseCardView):
    header = "A Chart"


class MultiCardPageView(BaseCardView):
    """Renders many card views to a single page"""

    page_template = 'multi_card_view.html'
    cards = []

    def dispatch(self, request, *args, **kwargs):
        self.cards = kwargs.get('cards')
