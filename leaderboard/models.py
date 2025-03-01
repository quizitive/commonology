from datetime import timedelta
from random import choice

from bulk_update_or_create import BulkUpdateOrCreateQuerySet
from ckeditor_uploader.fields import RichTextUploadingField
from sortedm2m.fields import SortedManyToManyField

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from project.utils import our_now
from game.models import Game, AnswerCode
from components.models import Component
from users.models import Player


class Leaderboard(models.Model):
    game = models.OneToOneField(Game, related_name="leaderboard", unique=True, on_delete=models.CASCADE)
    sheet_name = models.CharField(
        max_length=10000, help_text="The name of the Google Sheet which contains response data."
    )
    publish_date = models.DateTimeField(
        verbose_name="When the leaderboard can be published to the website.", null=False, blank=False
    )
    top_components = SortedManyToManyField(
        Component,
        blank=True,
        related_name="leaderboards",
        help_text="These components will appear immediately below the logo on both the "
        "leaderboard and results pages.",
    )
    top_commentary = RichTextUploadingField(null=True, blank=True)
    bottom_commentary = RichTextUploadingField(null=True, blank=True)

    def __str__(self):
        return f"Game {self.game.game_id} Leaderboard"

    @property
    def publish(self):
        return our_now() > self.publish_date

    def qid_answer_dict(self, player_id):
        """Returns a dict like {"123": "ABC", ... }"""
        qid_ac_tuples = AnswerCode.objects.raw(
            f"""select ac.id, ac.question_id, ac.coded_answer
            from game_answercode ac, game_answer a, game_question q, game_game g
            where a.raw_string = ac.raw_string
            and a.question_id = ac.question_id
            and a.question_id = q.id
            and q.game_id = g.id
            and g.game_id = {self.game.game_id}
            and a.player_id = {player_id}"""
        )
        return {str(qid_ac.question_id): qid_ac.coded_answer for qid_ac in qid_ac_tuples}


@receiver(post_save, sender=Game)
def make_leaderboard_for_new_game(sender, instance, created, **kwargs):
    if created:
        Leaderboard.objects.create(
            game_id=instance.id, sheet_name=instance.name, publish_date=instance.end + timedelta(hours=60)
        )


class PlayerRankScore(models.Model):
    objects = BulkUpdateOrCreateQuerySet.as_manager()
    player = models.ForeignKey(Player, related_name="rank_scores", on_delete=models.CASCADE, db_index=True)
    leaderboard = models.ForeignKey(Leaderboard, related_name="rank_scores", on_delete=models.CASCADE, db_index=True)
    rank = models.IntegerField()
    score = models.IntegerField()

    class Meta:
        unique_together = ("player", "leaderboard")
        ordering = ("leaderboard__game__game_id",)


class LeaderboardMessage(models.Model):
    metric = models.CharField(
        choices=[("rank", "Rank"), ("percentile", "Percentile")],
        help_text="E.g. Players with rank between 1-100. Players in the 90-99th percentile.",
        max_length=35,
    )
    min_value = models.IntegerField(help_text="The minimum value of the metric for this message to be eligible")
    max_value = models.IntegerField(help_text="The maximum value of the metric for this message to be eligible")
    message = models.CharField(
        help_text=f"This is added to the player results card on the leaderboard/results. You can reference the "
        f"given player's rank and percentile in the message by using {{rank}} and {{score}}."
        f"You can even to {{rank + 1}} to reference the next player, or {{100 - percentile}} to get"
        f"the percent of players who did better than the player.",
        max_length=255,
    )

    def message_with_subs(self, rank, percentile):
        """Replace occurrences of literal {rank} and {percentile} with the actual value."""
        allowed_subs = {
            "{rank}": str(rank),
            "{rank + 1}": str(rank + 1),
            "{percentile}": str(percentile),
            "{100 - percentile}": str(100 - percentile),
        }
        sub_message = self.message
        for match, sub in allowed_subs.items():
            sub_message = sub_message.replace(match, sub)
        return sub_message

    @classmethod
    def select_random_eligible(cls, rank, percentile):
        eligible = LeaderboardMessage.objects.filter(
            models.Q(metric="rank", max_value__gte=rank, min_value__lte=rank)
            | models.Q(metric="percentile", max_value__gte=percentile, min_value__lte=percentile)
        )
        if not eligible:
            return ""
        rand_msg = choice(list(eligible))
        return rand_msg.message_with_subs(rank, percentile)
