from django.db.models.signals import post_save
from django.dispatch import receiver
from project import settings
from django.contrib.auth import get_user_model


@receiver(post_save, sender=get_user_model())
def player_postsave(sender, instance, **kwargs):
    if settings.MAILCHIMP_SIGNAL_INHIBIT:
        return
    print("Receiver finished.")
