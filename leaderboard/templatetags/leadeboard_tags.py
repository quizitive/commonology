from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def question_responses(context):
    try:
        return context['answer_tally'][context['q'].text]
    except KeyError:
        return {}
