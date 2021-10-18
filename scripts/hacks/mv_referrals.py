import sys
import os
import django


path = os.getcwd()
sys.path.append(path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()


from users.models import Player
from rewards.utils import send_reward_notice


def mv_referrals(from_email, to_email):
    from_player = Player.objects.get(email=from_email)
    to_player = Player.objects.get(email=to_email)

    for referee in from_player.players_referred:
        referee.referrer = to_player
        referee.save()


def blusurf():
    mv_referrals('bluesutf201@gnail.com', 'bluesurf201@gmail.com')


def tessa():
    to_player = Player.objects.get(email='tessa.burke@meltwater.com')
    froms = [Player.objects.get(email=e) for e in ['kellydawnmendoza@gmail.com',
                                                   'maggiestanford20@gmail.com',
                                                   'gpiccoletti@gmail.com',
                                                   'dustin.mannino@meltwater.com',
                                                   'zach.baker@meltwater.com']]
    for referee in froms:
        referee.referrer = to_player
        referee.save()

    for p in to_player.players_referred:
        print(p)

    # BEWARE - ONLY CALL THIS WHEN RUNNING IN PRODUCTION
    send_reward_notice(to_player)

    # Rose Mendoza
    # Kelly Mendoza, kellydawnmendoza@gmail.com
    # Trevor Ells - OK
    # Caroline Montgomery -- OK
    # Maggie Stanford -- maggiestanford20@gmail.com
    # Nabila Mahmud -- OK
    # Gianni Pickles -- gpiccoletti@gmail.com
    # Jordan Williams --- OK
    # Dustin Mannino -- dustin.mannino@meltwater.com
    # Fred Walker -- OK
    # Zach Baker -- zach.baker@meltwater.com
    # Gail Robertson -- OK
    # Andres Ferret -- OK


def alex():
    alex_emails = ['alex@quizitive.com', 'alexandrafruin@gmail.com']
    for e in alex_emails:
        mv_referrals(e, 'alex@commonologygame.com')


def entwisht():
    mv_referrals('entwishy@gmail.com', 'entwisht@gmail.com')
