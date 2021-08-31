# Generated by Django 3.1.4 on 2021-08-26 15:56

import ckeditor_uploader.fields
from django.db import migrations, models
import sortedm2m.fields
from sortedm2m.operations import AlterSortedManyToManyField


class Migration(migrations.Migration):

    dependencies = [
        ('mail', '0012_auto_20210825_1420'),
    ]

    operations = [
        migrations.AddField(
            model_name='component',
            name='location',
            field=models.CharField(choices=[('top', 'Top'), ('btm', 'Bottom')], default='btm', max_length=3),
        ),
        migrations.AddField(
            model_name='component',
            name='message',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='component',
            name='template',
            field=models.CharField(default='mail/simple_component.html', max_length=150),
        ),
        AlterSortedManyToManyField(
            model_name='mailmessage',
            name='components',
            field=sortedm2m.fields.SortedManyToManyField(blank=True, help_text=None, related_name='messages', to='mail.Component'),
        ),
    ]