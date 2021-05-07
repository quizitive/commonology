from django import template
from django.shortcuts import reverse


register = template.Library()


@register.simple_tag(takes_context=True)
def question_responses(context):
    try:
        return context['answer_tally'][context['q'].text]
    except KeyError:
        return {}


@register.simple_tag(takes_context=True)
def button_highlight(context, dest_link):
    if context['view'] == dest_link:
        return 'cg-blue'
    else:
        return 'w3-light-grey'


@register.simple_tag(takes_context=True)
def series_or_default_url(context, view_name):
    if context['series_slug']:
        return reverse(f'series-leaderboard:{view_name}', kwargs={'series_slug': context['series_slug']})
    else:
        return reverse(f'leaderboard:{view_name}')
