# Generated by Django 3.2.8 on 2021-11-25 15:01

import ckeditor_uploader.fields
from django.db import migrations, models
import django.db.models.deletion
import sortedm2m.fields
from datetime import timedelta


def create_leaderboards_from_games(apps, schema_editor):
    Location = apps.get_model("components", "Location")
    Location.objects.create(app_name="leaderboard")
    Game = apps.get_model("game", "Game")
    Leaderboard = apps.get_model("leaderboard", "Leaderboard")
    for game in Game.objects.all():
        Leaderboard.objects.create(
            game=game,
            sheet_name=game.sheet_name,
            publish_date=game.end + timedelta(days=2, hours=12),
            top_commentary=game.top_commentary,
            bottom_commentary=game.bottom_commentary,
        )


def undo_leaderboards(apps, schema_editor):
    Leaderboard = apps.get_model("leaderboard", "Leaderboard")
    for lb in Leaderboard.objects.all():
        game = lb.game
        game.sheet_name = (game.sheet_name,)
        game.top_commentary = (game.top_commentary,)
        game.bottom_commentary = game.bottom_commentary
        game.publish = lb.publish
        game.save()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("components", "0001_initial"),
        ("game", "0013_answer_removed"),
    ]

    operations = [
        migrations.CreateModel(
            name="Leaderboard",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "sheet_name",
                    models.CharField(
                        help_text="The name of the Google Sheet which contains response data.", max_length=10000
                    ),
                ),
                (
                    "publish_date",
                    models.DateTimeField(verbose_name="When the leaderboard can be published to the website."),
                ),
                ("top_commentary", ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True)),
                ("bottom_commentary", ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True)),
                (
                    "game",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, related_name="leaderboard", to="game.game"
                    ),
                ),
                (
                    "top_components",
                    sortedm2m.fields.SortedManyToManyField(
                        blank=True,
                        help_text="These components will appear immediately below the logo on both the leaderboard and results pages.",
                        related_name="leaderboards",
                        to="components.Component",
                    ),
                ),
            ],
        ),
        migrations.RunPython(create_leaderboards_from_games, undo_leaderboards),
    ]
