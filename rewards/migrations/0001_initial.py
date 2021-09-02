# Generated by Django 3.1.4 on 2021-09-02 21:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0015_player_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='Claim',
            fields=[
                ('player', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='users.player')),
                ('reward', models.CharField(default='First edition coffee mug', help_text='ex. Coffee mug', max_length=150)),
                ('Claim date', models.DateField(auto_now=True)),
                ('Sent date', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='MailingAddress',
            fields=[
                ('player', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='users.player')),
                ('Full Name', models.CharField(max_length=128)),
                ('Address line 1', models.CharField(max_length=128)),
                ('Address line 2', models.CharField(blank=True, max_length=128)),
                ('City', models.CharField(max_length=128)),
                ('State', models.CharField(max_length=2)),
                ('ZIP / Postal code', models.CharField(max_length=12)),
            ],
        ),
    ]
