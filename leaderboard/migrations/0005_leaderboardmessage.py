# Generated by Django 3.2.8 on 2022-02-26 14:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leaderboard", "0004_remove_leaderboard_winners"),
    ]

    operations = [
        migrations.CreateModel(
            name="LeaderboardMessage",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "metric",
                    models.CharField(
                        choices=[("rank", "Rank"), ("percentile", "Percentile")],
                        help_text="E.g. Players with rank between 1-100. Players in the 90-99th percentile.",
                        max_length=35,
                    ),
                ),
                (
                    "min_value",
                    models.IntegerField(help_text="The minimum value of the metric for this message to be eligible"),
                ),
                (
                    "max_value",
                    models.IntegerField(help_text="The maximum value of the metric for this message to be eligible"),
                ),
                (
                    "message",
                    models.CharField(
                        help_text=f"This is added to the player results card on the leaderboard/results. You can reference the "
                        f"given player's rank and percentile in the message by using {{rank}} and {{score}}."
                        f"You can even to {{rank + 1}} to reference the next player, or {{100 - percentile}} to get"
                        f"the percent of players who did better than the player.",
                        max_length=255,
                    ),
                ),
            ],
        ),
    ]
