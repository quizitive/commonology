import sys
import os
import datetime
import django

path = os.getcwd()
sys.path.append(path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from users.models import Player
from game.utils import write_winner_certificate
from game.mail import send_prior_winner_notice
from project.utils import our_now
from users.utils import player_log_entry

data = """64,Emma Himes
64,Ryan Murphy"""
data = [i.split(",") for i in data.split("\n")]

data = """Emma Himes,emma@not_her_email.com,64
Ryan Murphy,rmurphy@not_his_email.com,64"""

data = [i.split(",") for i in data.split("\n")]
data = [(i[1], i[2]) for i in data]


def do(winner, game_number):
    filename = write_winner_certificate(winner.display_name, our_now(), game_number)
    send_prior_winner_notice(winner, game_number, filename)


# marc = Player.objects.get(email='ms@koplon.com')
# do(marc, 1)

for email, game_number in data:
    players = Player.objects.filter(email=email).all()
    for winner in players:
        if winner.subscribed:
            print(f"{winner.display_name},{game_number}")
            le = player_log_entry(winner, f"Award Certificate sent for game {game_number}.")
            le.action_time = datetime.datetime(2021, 11, 2, 16, 46, 0)
            le.save()
            # do(winner, game_number)
