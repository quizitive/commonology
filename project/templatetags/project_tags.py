import os
from pathlib import Path
from django import template
from django.contrib.staticfiles import finders
from project.settings import STATIC_VERSIONS
from django.templatetags.static import StaticNode
from game.utils import players_vs_previous, most_recently_started_game


BASE_DIR = Path(__file__).resolve().parent.parent.parent
register = template.Library()


@register.simple_tag
def v_static(format_string):
    # {% v_static css/components/bottombar.css %}
    # should result in "/static/css/components/bottombar.css?v=1632137649"

    path = StaticNode.handle_simple(format_string)

    if path in STATIC_VERSIONS:
        v = STATIC_VERSIONS[path]
    else:
        try:
            fn = finders.find(format_string)
            t = os.path.getmtime(fn)
        except Exception as e:
            print('v_static cannot find this file: ', format_string)
            raise e

        v = int(t)
        STATIC_VERSIONS[path] = v

    path = f"{path}?v={v}"
    return path


@register.simple_tag
def current_game_overview():
    current_game, is_active = most_recently_started_game('commonology')
    action_terms = ('so far', 'at this point') if is_active else ('', '')
    try:
        cur, prev, pct_chg = players_vs_previous(current_game)
    except AttributeError:
        return "There was an issues calculating this statistic."
    return f'{cur} players {action_terms[0]} this week, compared to {prev} {action_terms[1]} last week. ' \
           f'That represents a change of {pct_chg:.2f}%.'


@register.simple_tag(takes_context=True)
def current_player_id(context):
    request = context.get('request')
    if not request:
        return None
    player_id = request.user.id
    if not player_id:
        player_id = context.get('player_id')
    return player_id
