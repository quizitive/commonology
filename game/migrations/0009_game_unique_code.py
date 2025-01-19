# Generated by Django 3.1.4 on 2021-06-23 01:25

from django.db import migrations, models
import uuid


def gen_uuid(apps, schema_editor):
    Game = apps.get_model("game", "Game")
    for row in Game.objects.all():
        row.uuid = uuid.uuid4()
        row.save(update_fields=["uuid"])


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0008_auto_20210608_1438"),
    ]

    operations = [
        migrations.AddField(
            model_name="game",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, null=True),
        ),
        migrations.RunPython(gen_uuid, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(model_name="game", name="uuid", field=models.UUIDField(default=uuid.uuid4, unique=True)),
    ]
