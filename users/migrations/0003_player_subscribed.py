# Generated by Django 3.1.4 on 2021-03-18 22:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_player_following"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="subscribed",
            field=models.BooleanField(default=True),
        ),
    ]
