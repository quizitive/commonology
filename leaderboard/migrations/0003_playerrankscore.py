# Generated by Django 3.2.8 on 2022-01-13 20:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("leaderboard", "0002_leaderboard_winners"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlayerRankScore",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rank", models.IntegerField()),
                ("score", models.IntegerField()),
                (
                    "leaderboard",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rank_scores",
                        to="leaderboard.leaderboard",
                    ),
                ),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rank_scores",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "unique_together": {("player", "leaderboard")},
            },
        ),
    ]
