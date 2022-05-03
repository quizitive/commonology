import sys
import os
import django


path = os.getcwd()
sys.path.append(path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()


from users.models import Player

def mv_referrals(from_email, to_email):
    from_player = Player.objects.get(email=from_email)
    to_player = Player.objects.get(email=to_email)

    for referee in from_player.players_referred:
        referee.referrer = to_player
        referee.save()


def alex():
    alex_emails = ['alex@quizitive.com', 'alexandrafruin@gmail.com']
    for e in alex_emails:
        mv_referrals(e, 'alex@commonologygame.com')
