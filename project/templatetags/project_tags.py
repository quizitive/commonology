import os
from pathlib import Path
from django import template
from django.contrib.staticfiles import finders
# from project.settings import BUILD_NUMBER
from django.templatetags.static import StaticNode
from game.utils import players_vs_previous, most_recently_started_game


BASE_DIR = Path(__file__).resolve().parent.parent.parent
register = template.Library()


# @register.simple_tag(takes_context=True)
# def bn(context):
#     return BUILD_NUMBER


@register.simple_tag
def v_static(format_string):
    # {% v_static css/components/bottombar.css %}
    # should result in "/static/css/components/bottombar.css?v=1632137649"

    path = StaticNode.handle_simple(format_string)

    fn = finders.find(format_string)
    t = os.path.getmtime(fn)
    v = int(t)

    path = f"{path}?v={v}"
    return path


@register.simple_tag
def current_game_overview():
    current_game, is_active = most_recently_started_game('commonology')
    action_terms = ('so far', 'at this point') if is_active else ('', '')
    cur, prev, pct_chg = players_vs_previous(current_game)
    return f'{cur} players {action_terms[0]} this week, compared to {prev} {action_terms[1]} last week. ' \
           f'That represents a change of {pct_chg:.2f}%.'
