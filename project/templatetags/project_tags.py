from django import template
from project.settings import BUILD_NUMBER

register = template.Library()


@register.simple_tag(takes_context=True)
def bn(context):
    return BUILD_NUMBER
