import base64
from io import BytesIO
from qrcode import QRCode
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django.shortcuts import render, redirect, reverse
from django import forms
from django.core.mail import send_mail
from project.card_views import BaseCardView, CardFormView, recaptcha_check
from project.utils import ANALYTICS_REDIS
from game.utils import next_event, find_latest_public_game

import logging

logger = logging.getLogger(__name__)


def document_render(request, filename, title):
    context = next_game_context()
    context['filename'] = filename
    context['title'] = title
    return render(request, 'document.html', context)


def about_view(request, *args, **kwargs):
    context = next_game_context()
    return render(request, 'about.html', context)


def product_view(request, *args, **kwargs):
    return document_render(request, 'product.html', 'Product Description')


def our_story_view(request, *args, **kwargs):
    return document_render(request, 'our_story.html', 'Our Story')


def testimonials_view(request, *args, **kwargs):
    return document_render(request, 'testimonials.html', 'Testimonials')


def raffle_rules_view(request, *args, **kwargs):
    return document_render(request, 'raffle_rules.html', 'Raffle Rules')


def tos_view(request, *args, **kwargs):
    return document_render(request, 'tos.html', 'Terms of Service')


def privacy_view(request, *args, **kwargs):
    return document_render(request, 'privacy.html', 'Privacy Policy')


def sponsor_view(request, *args, **kwargs):
    return render(request, 'sponsor.html')


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
    choices = (("1", "Game Host"), ("2", "Investor Relations"), ("3", "Technical Question"))
    to_email = ['concierge@commonologygame.com', 'ms@commonologygame.com', 'tech@commonologygame.com']
    from_email = forms.EmailField(required=True)
    destination = forms.ChoiceField(choices=choices)
    message = forms.CharField(widget=forms.Textarea, max_length=750, min_length=2)


class ContactView(CardFormView):
    form_class = ContactForm
    header = "Establishing Contact"
    button_label = "Send"
    custom_message = mark_safe("Enter a message and we WILL read it.")

    def post(self, request, *args, **kwargs):
        recaptcha_check(request)
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


@staff_member_required
def instant_player_stats(request):
    resp = ""
    for source in ("google", "facebook"):
        starts = ANALYTICS_REDIS.get(f"{source}_instant_game_starts")
        completes = ANALYTICS_REDIS.get(f"{source}_instant_game_completes")
        resp = resp + f"{source.upper()}: There have been {starts} instant " \
                      f"game starts and {completes} completes.<br/><br/>"
    return HttpResponse(mark_safe(resp))


class QRView(BaseCardView):
    card_template = 'qr.html'

    def get_context_data(self, *args, **kwargs):
        request = self.request
        url = 'https://commonologygame.com'
        if request.user.is_authenticated:
            url = f"{url}/qr/{request.user.code}"
        else:
            url = f"{url}/play"

        # Creating an instance of qrcode
        qr = QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        image = qr.make_image(fill='black', back_color='white')

        buffered = BytesIO()
        image.save(buffered, format='PNG')
        img_str = base64.b64encode(buffered.getvalue())
        img_str = img_str.decode('utf-8')

        src = f'data:image/png;base64,{img_str}'
        return super().get_context_data(*args, qr=src)

    def get(self, request, *args, **kwargs):
        if 'rcode' in kwargs:
            r = kwargs['rcode']
            url = f"{reverse('game:play')}?r={r}"
            return redirect(url)
        return super().get(request, *args, **kwargs)
