# Generated by Django 3.1.4 on 2021-09-05 19:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0015_player_data"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MailingAddress",
            fields=[
                (
                    "player",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to="users.player",
                    ),
                ),
                ("name", models.CharField(max_length=128, verbose_name="Full Name")),
                ("address1", models.CharField(max_length=128, verbose_name="Address line 1")),
                ("address2", models.CharField(blank=True, max_length=128, verbose_name="Address line 2")),
                ("city", models.CharField(max_length=128, verbose_name="City")),
                ("state", models.CharField(max_length=2, verbose_name="State")),
                ("zip_code", models.CharField(max_length=12, verbose_name="ZIP / Postal code")),
            ],
        ),
        migrations.CreateModel(
            name="Claim",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "reward",
                    models.CharField(default="First edition coffee mug", help_text="ex. Coffee mug", max_length=150),
                ),
                ("claim_date", models.DateField(auto_now=True, verbose_name="Claim date")),
                ("sent_date", models.DateField(blank=True, null=True, verbose_name="Sent date")),
                ("player", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "unique_together": {("player", "reward")},
            },
        ),
    ]
