# Generated by Django 3.1.4 on 2021-04-19 17:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mail', '0004_auto_20210419_1738'),
    ]

    operations = [
        migrations.AlterField(
            model_name='massmailmessage',
            name='from_email',
            field=models.EmailField(default='alex@commonologygame.com', max_length=254, verbose_name='from email address'),
        ),
    ]
