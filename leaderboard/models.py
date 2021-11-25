from django.db import models

from ckeditor_uploader.fields import RichTextUploadingField
from sortedm2m.fields import SortedManyToManyField

from project.utils import our_now
from game.models import Game
from components.models import Component


class Leaderboard(models.Model):
    game = models.ForeignKey(Game, related_name='leaderboards', unique=True, on_delete=models.CASCADE)
    sheet_name = models.CharField(
        max_length=10000,
        help_text="The name of the Google Sheet which contains response data."
    )
    live_after = models.DateTimeField(
        verbose_name="When the leaderboard can be published to the website.", null=False, blank=False)
    top_components = SortedManyToManyField(
        Component,
        related_name='leaderboards',
        help_text="These components will appear immediately below the logo on both the "
                  "leaderboard and results pages."
    )
    top_commentary = RichTextUploadingField(null=True, blank=True)
    bottom_commentary = RichTextUploadingField(null=True, blank=True)

    @property
    def publish(self):
        return our_now() > self.live_after
