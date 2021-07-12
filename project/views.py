from django.views.generic.base import View
from django.shortcuts import render, redirect
from django import forms
from django.views.generic.edit import FormMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
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


class CardChartView(CardFormView):

    header = "A Chart"



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


from pychartjs import BaseChart, ChartType, Color


class ChartJS(BaseChart):

    def __init__(self, data_class, name, **kwargs):
        self.data_class = data_class
        self.name = name
        self.kwargs = kwargs

    @property
    def data_name(self):
        return self.name + "-data"

    @property
    def data(self):
        return self.data_class(**self.kwargs)


class BaseChartDataClass:

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)
        self.data = self._data()

    def _data(self):
        raise NotImplementedError


class ExampleDataClass(BaseChartDataClass):

    def _data(self):
        if self.game_id == 1:
            return [12, 19, 3, 17, 10]
        return [1, 4, 13, 12, 9]


class ExampleDataClass2(BaseChartDataClass):

    def _data(self):
        if self.game_id == 1:
            return [12, 19, 3, 17, 10]
        return [1, 4, 13, 12, 9]


class ExampleTwoDatasetDataClass(BaseChartDataClass):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dataset1_1 = self._dataset_1()

    class Dataset1(BaseChartDataClass):
        def _data(self):
            if self.game_id == 1:
                return [12, 19, 3, 17, 10]
            return [1, 4, 13, 12, 9]

    class Dataset2(BaseChartDataClass):
        def _data(self):
            if self.game_id == 1:
                return [12, 19, 3, 17, 10]
            return [1, 4, 13, 12, 9]


class GamePlayers(BaseChartDataClass):

    def _data(self):
        pass


class WeeklyPlayers(BaseChartDataClass):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.backgroundColor = Color.Green

    def _data(self):
        if self.game_id == 1:
            return [12, 19, 3, 17, 10]
        return [1, 4, 13, 12, 9]



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
