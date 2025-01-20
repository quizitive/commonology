import sys
import os
import datetime
from dateutil.relativedelta import relativedelta
import pytz
import django


path = os.getcwd()
sys.path.append(path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from game.models import Game


wrong_dt = datetime.datetime(2020, 1, 1, 0, 0, 0, tzinfo=pytz.timezone("UTC"))
seven_days = relativedelta(days=7)

for g in Game.objects.filter(series__name="Commonology").all().order_by("-game_id"):
    if g.game_id == 44:
        t_start = g.start
        t_end = g.end
        print("Game 44", t_start, t_end)
    if g.start == wrong_dt:
        t_start -= seven_days
        t_end -= seven_days
        g.start = t_start
        g.end = t_end
        g.save()
        print(g, g.start, g.end)
