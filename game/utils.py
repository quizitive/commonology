import os
from os import environ as env
import subprocess
import datetime

from django.db.models import Min
from project.settings import WINNER_ROOT, WINNER_TEMPLATE_PDF
from project.utils import our_now, quick_cache, to_ascii
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


def most_recently_started_game(slug):
    t = our_now()
    g = Game.objects.filter(series__slug=slug, start__lte=t).order_by('start').reverse().first()
    is_active = True if g.end > t else False
    return g, is_active


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


def players_vs_previous(game):
    prev = Game.objects.get(game_id=game.game_id - 1, series__slug='commonology')
    now = our_now()
    players_so_far = game.game_questions.first().raw_answers.filter(timestamp__lte=now).count()
    this_time_last_week = now - datetime.timedelta(7)
    players_so_far_last_week = prev.game_questions.first().raw_answers.filter(
        timestamp__lte=this_time_last_week).count()
    return players_so_far, players_so_far_last_week, 100 * (players_so_far / players_so_far_last_week - 1)


def write_winner_certificate(name, date, game_number):
    # On Mac: brew install pdfk-java
    path = WINNER_ROOT
    os.makedirs(path, exist_ok=True)

    base = f"{name}{date}{game_number}".replace(',', '').replace(' ', '').strip()
    fn_fdf = os.path.join(path, f"{base}.fdf")
    filename = f"{base}.pdf"
    fn = os.path.join(path, filename)

    name = to_ascii(name)


    fdf = f'''
        %FDF-1.2
        1 0 obj << /FDF << /Fields [
        << /T(Name) /V({name}) >>
        << /T(Date) /V({date}) >>
        << /T(Game \#) /V({game_number}) >>
        ] >> >>
        endobj
        trailer
        << /Root 1 0 R >>
        %%EOF
    '''

    if not env.get('GITHUB_COMMONOLOGY_CI_TEST'):
        with open(fn_fdf, 'w') as fh:
            fh.write(fdf)

        subprocess.run(['pdftk', WINNER_TEMPLATE_PDF, 'fill_form', fn_fdf,
                        'output', fn, 'need_appearances', 'flatten'])

    return filename
