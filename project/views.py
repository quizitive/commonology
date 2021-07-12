from django.shortcuts import render, redirect
from django import forms
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from project.card_views import CardFormView
from game.utils import next_event, find_latest_public_game

import logging

logger = logging.getLogger(__name__)


def document_render(request, filename):
    context = next_game_context()
    context['filename'] = filename
    return render(request, 'document.html', context)


def about_view(request, *args, **kwargs):
    return document_render(request, 'about.html')


def product_view(request, *args, **kwargs):
    return document_render(request, 'product.html')


def tos_view(request, *args, **kwargs):
    return document_render(request, 'tos.html')


def privacy_view(request, *args, **kwargs):
    return document_render(request, 'privacy.html')


def index(request):
    if request.user.is_authenticated:
        return redirect('leaderboard:current-leaderboard')
    context = next_game_context()
    return render(request, 'index.html', context)


def next_game_context():
    event_text, event_time = next_event()
    game_is_on = find_latest_public_game('commonology') is not None
    return {
        'event_time': event_time,
        'event_text': event_text,
        'game_is_on': game_is_on,
    }


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


@login_required
def stats_view(request):
    chart_1 = ChartJS(ExampleDataClass, name="myChart", game_id=1, backgroundColor=Color.Green)
    chart_2 = ChartJS(ExampleDataClass, name="chart_2", game_id=2)
    context = {
        "custom_message": "Trend of the percent of game players that are members",
        "chart_1": chart_1,
        "chart_2": chart_2,
    }
    return render(request, 'stats.html', context)
