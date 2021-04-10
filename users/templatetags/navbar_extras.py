from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.shortcuts import render

from users.forms import LoginForm


register = template.Library()


@register.simple_tag(takes_context=True)
def login_logout_url(context):
    request = context['request']
    if request.user.is_authenticated:
        s = 'logout'
    else:
        s = 'login'
    url = reverse(s)
    # url = f"<A HREF={url}>{s}</A>"
    return url


login_logout_url.is_safe = True


@register.simple_tag
def login_modal(request):
    if not request:
        return
    return render(request, 'users/modals/login_modal.html', {'form': LoginForm})
