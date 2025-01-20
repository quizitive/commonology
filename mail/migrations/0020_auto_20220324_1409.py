# Generated by Django 3.2.8 on 2022-03-24 18:09

import ckeditor_uploader.fields
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import sortedm2m.fields


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0014_auto_20211125_1001"),
        ("components", "0003_sponsorcomponent"),
        ("mail", "0019_mailmessage_scheduled"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="mailmessage",
            name="sent",
        ),
        migrations.RemoveField(
            model_name="mailmessage",
            name="tested",
        ),
        migrations.CreateModel(
            name="MailLog",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("from_name", models.CharField(default="Alex Fruin", max_length=150)),
                (
                    "from_email",
                    models.EmailField(
                        choices=[
                            ("concierge@commonologygame.com", "concierge@commonologygame.com"),
                            ("alex@commonologygame.com", "alex@commonologygame.com"),
                            ("ms@commonologygame.com", "ms@commonologygame.com"),
                            ("ted@commonologygame.com", "ted@commonologygame.com"),
                        ],
                        default="alex@commonologygame.com",
                        max_length=254,
                        verbose_name="from email address",
                    ),
                ),
                ("test_recipient", models.EmailField(max_length=254, verbose_name="test recipient email address")),
                (
                    "categories",
                    models.CharField(
                        blank=True,
                        help_text="A comma separated list of categories. i.e GameOn|Reminder|Results + Week#",
                        max_length=50,
                    ),
                ),
                (
                    "reminder",
                    models.BooleanField(
                        default=False,
                        help_text="This is a game reminder messsage.  Only players opting for reminders will get it",
                    ),
                ),
                ("subject", models.CharField(max_length=150)),
                (
                    "message",
                    ckeditor_uploader.fields.RichTextUploadingField(
                        blank=True, help_text="Play link example: https://commonologygame.com/play-game_url_args-"
                    ),
                ),
                ("created", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "scheduled",
                    models.DateTimeField(
                        blank=True, help_text="If set then mail will go out at the scheduled time.", null=True
                    ),
                ),
                ("sent_date", models.DateTimeField(blank=True, null=True)),
                ("batch_id", models.CharField(max_length=256)),
                ("canceled", models.DateTimeField(blank=True, default=None, null=True)),
                (
                    "bottom_components",
                    sortedm2m.fields.SortedManyToManyField(
                        blank=True,
                        help_text="These appear below the the main message",
                        related_name="maillog_messages_bottom",
                        to="components.Component",
                    ),
                ),
                (
                    "series",
                    models.ForeignKey(
                        default=1,
                        help_text="Only subscribed players will receive the email.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="game.series",
                    ),
                ),
                (
                    "top_components",
                    sortedm2m.fields.SortedManyToManyField(
                        blank=True,
                        help_text="These appear just below the header image, above the main message",
                        related_name="maillog_messages_top",
                        to="components.Component",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
