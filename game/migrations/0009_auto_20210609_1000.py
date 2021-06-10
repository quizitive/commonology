# Generated by Django 3.1.4 on 2021-06-09 10:00

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0008_auto_20210608_1438'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='choices',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100, null=True), blank=True, null=True, size=None),
        ),
        migrations.AlterField(
            model_name='question',
            name='type',
            field=models.CharField(choices=[('GA', 'Game'), ('OP', 'Optional'), ('OV', 'Optional (visible)')], max_length=2),
        ),
    ]
