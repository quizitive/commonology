import datetime

from django.db.models import Min

from project.utils import our_now, quick_cache
from game.models import Game, Answer


@quick_cache(60 * 60)
def new_players_for_game(slug, game_id):
    new_players = Answer.objects.values('player_id').annotate(
        Min('question__game__game_id')
    ).order_by('player_id').filter(
        question__game__game_id__min=game_id, question__game__series__slug=slug
    ).values_list('player_id', flat=True)
    return new_players


def find_latest_active_game(slug):
    t = our_now()
    g = Game.objects.filter(series__slug=slug, end__gte=t, start__lte=t).order_by('start').reverse().first()
    return g


def find_latest_public_game(slug):
    t = our_now()
    g = Game.objects.filter(series__slug=slug, series__public=True,
                            end__gte=t, start__lte=t).order_by('start').reverse().first()
    return g


# Get next game start or game end
def next_event():
    now = our_now()
    if now.weekday() in (3, 4) or (now.weekday() == 2 and now.hour >= 12):
        return 'The game ends in...', next_friday_1159(now).strftime("%Y-%m-%dT%H:%M:%S")
    return 'The next game begins in...', next_wed_noon(now).strftime("%Y-%m-%dT%H:%M:%S")


def next_wed_noon(now):
    next_wed = now
    while next_wed.weekday() != 2:
        next_wed = next_wed + datetime.timedelta(1)
    return next_wed.replace(hour=12, minute=00, second=00)


def next_friday_1159(now):
    next_fri = now
    while next_fri.weekday() != 4:
        next_fri = next_fri + datetime.timedelta(1)
    return next_fri.replace(hour=23, minute=59, second=59)
