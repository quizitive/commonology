
import sys
import os
import django
from django.db import transaction
from dateutil.relativedelta import relativedelta
import openpyxl


path = os.getcwd()
sys.path.append(path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()


from users.models import Player
from game.models import Game, Series
from leaderboard.models import PlayerRankScore


fn = os.path.join(os.path.join('/Users/ms/Downloads/', 'Commonology Backfill Weeks.xlsx'))
ws = openpyxl.load_workbook(fn)

commonology = Series.objects.get(slug="commonology")

game_44 = Game.objects.get(game_id=44)


def calc_dates(game_id):
    start_date = game_44.start
    end_date = game_44.end
    n = (44 - game_id) * 7
    delta = relativedelta(days=n)
    start_date -= delta
    end_date -= delta
    return start_date, end_date


def list_game_dates():
    for i in range(1, 44):
        b, e = calc_dates(i)
        delta = relativedelta(days=2)
        e += delta
        print(f"{i} {e.strftime('%A')} {e.date()}")


def set_game_dates(g):
    start_date, end_date = calc_dates(g.game_id)
    g.start = start_date
    g.end = end_date
    return start_date, end_date


def get_player(email, display_name):
    try:
        p = Player.objects.get(email=email)
    except Player.DoesNotExist:
        p = Player(email=email)
        p.display_name = display_name
        p.subscribed = False
        p.save()

    return p


@transaction.atomic
def process_game(game_id, data):
    g = Game()
    g.game_id = game_id
    g.name = f'Commonology Game {game_id}'
    g.series = commonology
    set_game_dates(g)
    g.save()

    lb = g.leaderboard
    lb.publish_date = g.end + relativedelta(days=3)
    lb.save()

    for email, name, score, rank in data:
        p = get_player(email=email, display_name=name)
        prs = PlayerRankScore()
        prs.player = p
        prs.leaderboard = l
        prs.rank = rank
        prs.score = score
        prs.save()


def print_player_scores(game_id):
    g = Game.objects.get(game_id=game_id, series=commonology)
    lb = g.leaderboard
    for i in PlayerRankScore.objects.filter(leaderboard=lb).all():
        print(i.player, i.score, i.rank)


def read_sheet(w):
    data = []
    r = 1

    email = w.active.cell(row=r, column=1).value
    if '@' not in email:
        r += 1
        email = w.active.cell(row=r, column=1).value
    while email:
        name = w.active.cell(row=r, column=2).value
        score = w.active.cell(row=r, column=3).value
        data.append([email, name, score, 0])

        r += 1
        email = w.active.cell(row=r, column=1).value

    rank = 0
    last_score = '0'
    data.sort(key=lambda x: -x[2])
    for rec in data:
        email, name, score, x = rec
        if score == last_score:
            rank = rank
        else:
            rank += 1
            last_score = score
        rec[2] = float(score)
        rec[3] = rank

    return data


def process(game_id):
    sheet_name = f'Week {game_id}'
    ws.active = ws.sheetnames.index(sheet_name)
    data = read_sheet(ws)

    process_game(game_id, data)


def do_it():
    for game_id in range(1, 2):
        print(f'Processing game {game_id}')
        process(game_id)

        print()
        print()
        print_player_scores(game_id)


# do_it()
list_game_dates()

#  pg_restore -d postgresql://postgres:postgres@localhost/commonology --verbose --clean --no-acl --no-owner ./pg_dumps/commonology_Sun.tar
# missing email for week 6, 14,
# Missing data for 21 - 27 - we have raw data for them.
