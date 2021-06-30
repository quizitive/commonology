from django import template
from django.urls import reverse
from django.template.loader import render_to_string

from users.forms import LoginForm
from game.utils import find_latest_active_game


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
    return render_to_string('users/modals/login_modal.html', {'form': LoginForm}, request=request)


@register.simple_tag
def login_next_url(request):
    if val := request.GET.get("next"):
        return f'?next={val}'
    p = request.path
    if p == '/login/' or p == '/join/':
        return ''
    return f'?next={p}'


@register.simple_tag
def game_is_on():
    return find_latest_active_game('commonology') is not None
