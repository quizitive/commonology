from users.models import Player

qs = Player.objects.exclude(email='ms@quizitive.com').all()
for u in qs:
    u.subscribed = False
    u.save()
