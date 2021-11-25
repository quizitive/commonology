# Generated by Django 3.2.8 on 2021-11-25 15:01

from django.db import migrations
import sortedm2m.fields


class Migration(migrations.Migration):

    dependencies = [
        ('components', '0001_initial'),
        ('game', '0013_answer_removed'),
        ('leaderboard', '0001_initial')
    ]

    operations = [
        migrations.RemoveField(
            model_name='game',
            name='bottom_commentary',
        ),
        migrations.RemoveField(
            model_name='game',
            name='publish',
        ),
        migrations.RemoveField(
            model_name='game',
            name='sheet_name',
        ),
        migrations.RemoveField(
            model_name='game',
            name='top_commentary',
        ),
        migrations.AddField(
            model_name='game',
            name='top_components',
            field=sortedm2m.fields.SortedManyToManyField(help_text='Components that will appear at the top of the game form.', related_name='games_top', to='components.Component'),
        ),
    ]
