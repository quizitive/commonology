from celery import shared_task
from users.models import Player


@shared_task()
def save_last_visit_t(player_id, key, value):
    player = Player.objects.get(id=player_id)
    player.data[key] = value
    player.save()
