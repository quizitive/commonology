# Generated by Django 3.1.4 on 2021-04-22 16:38

from django.db import migrations
import users.models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0007_citext_extension"),
    ]

    operations = [
        migrations.AlterField(
            model_name="player",
            name="email",
            field=users.models.CustomCIEmailField(max_length=254, unique=True, verbose_name="email address"),
        ),
        migrations.AlterField(
            model_name="player",
            name="referrer",
            field=users.models.CustomCIEmailField(
                blank=True, max_length=254, null=True, verbose_name="Referrer email address"
            ),
        ),
    ]
