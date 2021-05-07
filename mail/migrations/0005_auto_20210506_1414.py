# Generated by Django 3.1.4 on 2021-05-06 14:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mail', '0004_auto_20210421_1755'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mailmessage',
            name='from_email',
            field=models.EmailField(choices=[('alex@commonologygame.com', 'alex@commonologygame.com'), ('ms@commonologygame.com', 'ms@commonologygame.com'), ('ted@commonologygame.com', 'ted@commonologygame.com'), ('concierge@commonologygame.com', 'concierge@commonologygame.com')], default='alex@commonologygame.com', max_length=254, verbose_name='from email address'),
        ),
    ]
