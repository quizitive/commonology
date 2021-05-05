from django import template


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
