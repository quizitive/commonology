# Generated by Django 3.1.4 on 2021-07-20 14:20

import ckeditor_uploader.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("mail", "0009_auto_20210716_1348"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mailmessage",
            name="message",
            field=ckeditor_uploader.fields.RichTextUploadingField(
                blank=True, help_text="Play link example: https://commonologygame.com/play-game_url_args-"
            ),
        ),
    ]
