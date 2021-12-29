from emoji import is_emoji

from django import template
from django.shortcuts import reverse
from django.utils.safestring import mark_safe

from game.utils import find_latest_active_game

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
def series_or_default_url(context, app_name, view_name, **kwargs):
    if context.get('series_slug'):
        kwargs.update({'series_slug': context['series_slug']})
        return reverse(f'series-{app_name}:{view_name}', kwargs=kwargs)
    else:
        return reverse(f'{app_name}:{view_name}', kwargs=kwargs)


@register.simple_tag(takes_context=True)
def formatted_answer_cell(context, counter):
    qid = str(context['q'].id)
    addl_classes = ''
    addl_style = ''
    addl_div = ''
    res = context['res']
    val = context['val']
    if counter > 10:
        addl_classes = f'question-{qid} hideable'
        addl_style = 'style="display:none;"'

    # empty list for unauthenticated players
    if context['player_answers']:
        # if a player didn't answer a question this will be empty
        if this_q_answer := context['player_answers'].filter(question_id=qid).first():
            # check if the player answer matches the current answer
            if this_q_answer[3] == res:
                addl_classes += ' player-answer'
                addl_div = f'<span class="w3-cell-row {addl_classes}" {addl_style}>my answer</span>'

    result = f'<div class="w3-cell-row response-item w3-card-0 ' \
             f'w3-round w3-padding {addl_classes}" {addl_style}>' \
             f'<div class="w3-cell w3-rest">{res}</div>' \
             f'<div class="answer-score w3-cell w3-cell-middle w3-cell-right">{val}</div>' \
             f'</div>{addl_div}'

    return mark_safe(result)


@register.simple_tag
def profile_char(display_name):
    first_char = display_name[:1]
    style = " style=\"padding-left:2px;\"" if is_emoji(first_char) else ""
    final_html = f"<span{style}>{first_char}</span>"
    return mark_safe(final_html)


@register.simple_tag(takes_context=True)
def active_game(context):
    return find_latest_active_game(context.get('series_slug') or 'commonology')
