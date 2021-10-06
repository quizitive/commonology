import sys
import os
import django


path = os.getcwd()
sys.path.append(path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()


from users.models import Player


from_player = Player.objects.get(email='bluesutf201@gnail.com')
to_player = Player.objects.get(email='bluesurf201@gmail.com')

for referee in from_player.players_referred:
    referee.referrer = to_player
    referee.save()
