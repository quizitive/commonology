from celery import shared_task


@shared_task(queue='serial')
def save_last_visit_t(player, key, value):
    player.data[key] = value
    player.save()
