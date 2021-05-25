from django import template
from django.shortcuts import reverse
from django.utils.safestring import mark_safe

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


@register.simple_tag(takes_context=True)
def formatted_answer_cell(context, counter):
    qid = str(context['q'].id)
    addl_classes = ''
    addl_style = ''
    addl_div = ''
    res = context['res']
    val = context['val']
    if counter > 10:
        addl_classes = f'q-{qid} hideable'
        addl_style = 'style="display:none;"'

    if context['player_answers'] and context['player_answers'].get(question_id=qid)[3] == res:
        addl_classes += ' player-answer'
        addl_div = f'<span class="w3-cell-row player-answer">my answer</span>'

    result = f'<div class="w3-cell-row response-item w3-card-0 ' \
             f'w3-round w3-padding {addl_classes}" {addl_style}>' \
             f'<div class="w3-cell w3-rest">{res}</div>' \
             f'<div class="answer-score w3-cell w3-cell-middle w3-cell-right">{val}</div>' \
             f'</div>{addl_div}'

    return mark_safe(result)
