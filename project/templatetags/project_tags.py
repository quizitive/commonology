from django import template
from project.settings import BUILD_NUMBER
from game.utils import players_vs_previous, most_recently_started_game

register = template.Library()


@register.simple_tag(takes_context=True)
def bn(context):
    return BUILD_NUMBER


@register.simple_tag
def current_game_overview():
    current_game, is_active = most_recently_started_game('commonology')
    action_terms = ('so far', 'at this point') if is_active else ('', '')
    cur, prev, pct_chg = players_vs_previous(current_game)
    return f'{cur} players {action_terms[0]} this week, compared to {prev} {action_terms[1]} last week. ' \
           f'That represents a change of {pct_chg:.2f}%.'
