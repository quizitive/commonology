from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe


register = template.Library()


@register.simple_tag(takes_context=True)
def login_logout_url(context):
    request = context['request']
    if request.user.is_authenticated:
        s = 'logout'
    else:
        s = 'login'
    url = reverse(s)
    url = f"<A HREF={url}>{s}</A>"
    return mark_safe(url)


login_logout_url.is_safe = True
