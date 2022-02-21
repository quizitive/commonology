from django import template
from django.template.loader import render_to_string

from components.models import SponsorComponent

register = template.Library()


@register.simple_tag
def sponsor_component_cards():
    context = {"components": SponsorComponent.active_sponsor_components()}
    return render_to_string('components/card_component_stream.html', context=context)


@register.simple_tag
def sponsor_components_simple():
    context = {"components": SponsorComponent.active_sponsor_components()}
    return render_to_string('components/simple_component_stream.html', context=context)
