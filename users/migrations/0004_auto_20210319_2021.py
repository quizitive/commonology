# Generated by Django 3.1.4 on 2021-03-19 20:21

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_player_subscribed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pendingemail',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
