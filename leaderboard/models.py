from datetime import timedelta

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from ckeditor_uploader.fields import RichTextUploadingField
from sortedm2m.fields import SortedManyToManyField

from project.utils import our_now
from game.models import Game
from components.models import Component
from users.models import Player


class Leaderboard(models.Model):
    game = models.OneToOneField(Game, related_name='leaderboard', unique=True, on_delete=models.CASCADE)
    sheet_name = models.CharField(
        max_length=10000,
        help_text="The name of the Google Sheet which contains response data."
    )
    publish_date = models.DateTimeField(
        verbose_name="When the leaderboard can be published to the website.", null=False, blank=False)
    top_components = SortedManyToManyField(
        Component,
        blank=True,
        related_name='leaderboards',
        help_text="These components will appear immediately below the logo on both the "
                  "leaderboard and results pages."
    )
    top_commentary = RichTextUploadingField(null=True, blank=True)
    bottom_commentary = RichTextUploadingField(null=True, blank=True)
    winners = models.ManyToManyField(Player, blank=True, related_name='games_won', db_index=True)

    def __str__(self):
        return f"Game {self.game.game_id} Leaderboard"

    @property
    def publish(self):
        return our_now() > self.publish_date


@receiver(post_save, sender=Game)
def make_leaderboard_for_new_game(sender, instance, created, **kwargs):
    if created:
        Leaderboard.objects.create(
            game_id=instance.id, sheet_name=instance.name, publish_date=instance.end + timedelta(hours=60))
