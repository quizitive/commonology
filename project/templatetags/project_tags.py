import os
from pathlib import Path
from django import template
from django.contrib.staticfiles import finders
from django.utils.safestring import mark_safe
from project.settings import STATIC_VERSIONS
from django.templatetags.static import StaticNode
from game.utils import players_vs_previous, new_players_v_previous, most_recently_started_game
from project.views import make_play_qr

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
        new_cur, new_prev, new_pct_chg = new_players_v_previous(current_game)
    except AttributeError:
        return "There was an issues calculating this statistic."
    output = f'{cur} players {action_terms[0]} this week, compared to {prev} {action_terms[1]} last week. ' \
             f'That represents a change of {pct_chg:.2f}%.<br/><br/>' \
             f'That includes {new_cur} new players, compared to {new_prev} {action_terms[1]} last week.'
    return mark_safe(output)


@register.simple_tag(takes_context=True)
def current_player_id(context):
    request = context.get('request')
    if not request:
        return None
    player_id = request.user.id
    if not player_id:
        player_id = context.get('player_id')
    return player_id


@register.simple_tag(takes_context=True)
def qr_url(context, code=None):
    if code is not None:
        return make_play_qr(code)

    request = context.get('request')

    if (request is not None) and (request.user.is_authenticated):
        src = make_play_qr(request.user.code)
    else:
        src = make_play_qr()

    return src
