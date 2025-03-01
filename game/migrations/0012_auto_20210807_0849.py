# Generated by Django 3.1.4 on 2021-08-07 12:49

from django.db import migrations, models


def number_questions(apps, schema_editor):
    Game = apps.get_model("game", "Game")
    gs = Game.objects.all()
    for g in gs:
        for q in g.questions.order_by("number"):
            if g.questions.filter(number=q.number).count() > 1:
                q_nums = g.questions.values_list("number", flat=True)
                while q.number in q_nums:
                    q.number += 1
            q.save()


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0011_auto_20210702_2101"),
    ]

    operations = [
        migrations.RunPython(number_questions, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="question",
            name="number",
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AlterUniqueTogether(
            name="question",
            unique_together={("game", "number")},
        ),
    ]
