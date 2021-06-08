from django.views.generic.base import View
from django.shortcuts import render, redirect
from django import forms
from django.views.generic.edit import FormMixin
from django.contrib import messages
from django.core.mail import send_mail
from game.utils import next_event, find_latest_active_game

import logging

logger = logging.getLogger(__name__)


def about_view(request, *args, **kwargs):
    context = next_game_context()
    return render(request, 'about.html', context)


def index(request):
    if request.user.is_authenticated:
        return redirect('leaderboard:current-leaderboard')
    context = next_game_context()
    return render(request, 'index.html', context)


def next_game_context():
    event_text, event_time = next_event()
    game_is_on = find_latest_active_game('commonology') is not None
    return {
        'event_time': event_time,
        'event_text': event_text,
        'game_is_on': game_is_on,
    }


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


class ContactForm(forms.Form):
    choices = (("1", "Game Host"), ("2", "Investor Relations"))
    to_email = ['concierge@commonologygame.com', 'ms@quizitive.com']
    from_email = forms.EmailField(required=True)
    destination = forms.ChoiceField(choices=choices)
    message = forms.CharField(widget=forms.Textarea, max_length=750, min_length=2)


class ContactView(CardFormView):
    form_class = ContactForm
    header = "Establishing Contact"
    button_label = "Next"
    custom_message = "Enter a message and we WILL read it."

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            from_email = form.data['from_email']
            destination = int(form.data['destination'])
            email = form.to_email[destination - 1]
            msg = form.data['message']

            subject = form.choices[destination - 1][1]
            msg = f"Contact Form -- {from_email} sent this message with subject: {subject}\n{msg}"

            logger.info(msg)
            send_mail(subject=subject, message=msg,
                      from_email=None, recipient_list=[email])

            self.custom_message = 'Thank you, we hope to reply today or early tomorrow.'
            return self.render(request, form=None, button_label='OK',
                           form_method="get", form_action='/')

        return self.render(request)
