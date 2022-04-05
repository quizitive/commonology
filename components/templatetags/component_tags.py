from django import template
from django.template.loader import render_to_string
from project.views import make_play_qr

from components.models import SponsorComponent

register = template.Library()


@register.simple_tag
def sponsor_component_cards():
    context = {"components": SponsorComponent.active_sponsor_components()}
    return render_to_string('components/card_component_stream.html', context=context)
