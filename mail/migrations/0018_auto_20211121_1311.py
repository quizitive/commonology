# Generated by Django 3.2.8 on 2021-11-21 18:11

from django.db import migrations
import sortedm2m.fields
from django.forms.models import model_to_dict


def attach_components(apps, schema_editor):
    Component = apps.get_model('components', 'Component')
    MailMessage = apps.get_model('mail', 'MailMessage')

    for mm in MailMessage.objects.all():
        components = mm.components.all()
        for old_comp in components:
            new_comp = Component.objects.get(id=old_comp.id)
            if old_comp.location == 'top':
                mm.top_components.add(new_comp)
            else:
                mm.bottom_components.add(new_comp)


def backward_passthrough(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('components', '0001_initial'),
        ('mail', '0017_alter_mailmessage_from_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='mailmessage',
            name='bottom_components',
            field=sortedm2m.fields.SortedManyToManyField(blank=True, help_text='These appear below the the main message', related_name='messages_bottom', to='components.Component'),
        ),
        migrations.AddField(
            model_name='mailmessage',
            name='top_components',
            field=sortedm2m.fields.SortedManyToManyField(blank=True, help_text='These appear just below the header image, above the main message', related_name='messages_top', to='components.Component'),
        ),
        migrations.RunPython(attach_components, backward_passthrough),
        migrations.RemoveField(
            model_name='mailmessage',
            name='components',
        ),
        migrations.DeleteModel(
            name='Component',
        ),
    ]
