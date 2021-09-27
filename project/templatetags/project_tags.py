import os
from pathlib import Path
from django import template
from django.templatetags.static import do_static, StaticNode
from project.settings import BUILD_NUMBER
from game.utils import players_vs_previous, most_recently_started_game


BASE_DIR = Path(__file__).resolve().parent.parent.parent
register = template.Library()


@register.simple_tag(takes_context=True)
def bn(context):
    return BUILD_NUMBER


@register.tag('v_static')
def bn_do_static(parser, token):
    bits = token.split_contents()
    path = parser.compile_filter(bits[1])
    path = str(path).strip('\"')
    fn = os.path.join(BASE_DIR, 'project/static', path)
    t = os.path.getmtime(fn)
    v = int(t)
    result = do_static(parser, token)
    result.path.token += f"?v={v}"
    return result


@register.simple_tag
def current_game_overview():
    current_game, is_active = most_recently_started_game('commonology')
    action_terms = ('so far', 'at this point') if is_active else ('', '')
    cur, prev, pct_chg = players_vs_previous(current_game)
    return f'{cur} players {action_terms[0]} this week, compared to {prev} {action_terms[1]} last week. ' \
           f'That represents a change of {pct_chg:.2f}%.'
