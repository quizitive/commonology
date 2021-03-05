# Generated by Django 3.1.4 on 2021-03-04 21:28

from django.db import migrations, models
import game.utils


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
                ('raw_string', models.CharField(max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='AnswerCode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raw_string', models.CharField(max_length=1000)),
                ('coded_answer', models.CharField(db_index=True, max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('game_id', models.IntegerField(unique=True)),
                ('name', models.CharField(max_length=100)),
                ('sheet_name', models.CharField(help_text='The name of the Google Sheet which contains response data', max_length=10000)),
                ('publish', models.BooleanField(default=False, help_text='This game can be published to the dashboard')),
            ],
            options={
                'ordering': ['-game_id'],
            },
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('display_name', models.CharField(max_length=100)),
                ('email', models.CharField(max_length=256, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=10000)),
                ('type', models.CharField(choices=[('MC', 'Multiple Choice'), ('FR', 'Free Response'), ('OP', 'Optional')], max_length=2)),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.CharField(default=game.utils.create_key, max_length=7, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
    ]
