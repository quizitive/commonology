# Generated by Django 3.2.8 on 2022-01-05 02:19

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0019_auto_20211116_1002'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='referrer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='referrals', to=settings.AUTH_USER_MODEL),
        ),
    ]
