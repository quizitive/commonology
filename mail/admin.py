from django.contrib import admin, messages
from django_object_actions import DjangoObjectActions

from sortedm2m_filter_horizontal_widget.forms import SortedFilteredSelectMultiple

from .models import MailMessage, Component
from users.models import Player
from .utils import make_absolute_urls
from .sendgrid_utils import mass_mail, sendgrid_send


@admin.register(MailMessage)
class MailMessageAdmin(DjangoObjectActions, admin.ModelAdmin):
    def send_test(self, request, obj):
        email = obj.test_recipient
        try:
            test_user = Player.objects.get(email=obj.test_recipient)
            user_code = test_user.code
        except Player.DoesNotExist:
            user_code = -1
        msg = make_absolute_urls(obj.message)
        from_email = (obj.from_email, obj.from_name)
        sendgrid_send(obj.subject, msg=msg, email_list=[(email, user_code)],
                      from_email=from_email, unsub_link=True, components=obj.components.all())
        obj.tested = True
        obj.save()
        messages.add_message(request, messages.INFO, 'Test message sent.')
    send_test.label = 'Test'
    send_test.short_description = "Send a test message."

    def blast(self, request, obj):
        if not obj.enable_blast:
            messages.add_message(request, messages.WARNING,
                                 "You must enable blast with the checkbox below.")
        elif obj.sent:
            messages.add_message(request, messages.WARNING,
                                 "This blast was already sent.  You can send again by unchecking the sent box below.")
        elif obj.tested:
            message = make_absolute_urls(obj.message)
            from_email = (obj.from_email, obj.from_name)
            if obj.series is None:
                messages.add_message(request, messages.WARNING, 'You must choose a series.')
                return

            if obj.series.slug == 'everyone':
                players = Player.objects
            else:
                players = obj.series.players

            n = mass_mail(obj.subject, message, from_email, players=players,
                          categories=obj.categories, components=obj.components.all())
            obj.sent = True
            obj.save()
            if n:
                messages.add_message(request, messages.INFO, f'Blast message sent to {n} players.')
            else:
                messages.add_message(request, messages.WARNING, 'No players found in that series.')
        else:
            messages.add_message(request, messages.WARNING,
                                 "Cannot send blast until message is tested.")

    blast.label = "Blast"
    blast.short_description = "This will send the message to EVERYONE!"

    change_actions = ('send_test', 'blast')

    list_display = ('created', 'subject', 'test_recipient')
    list_filter = ('created',)
    search_fields = ('subject',)
    ordering = ('-created',)
    filter_horizontal = ('components',)
    save_on_top = True

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if 'message' in form.changed_data:
            obj.tested = False
            obj.sent = False
            obj.save()

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'components':
            kwargs['widget'] = SortedFilteredSelectMultiple()
        return super(MailMessageAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(Component)
class MailComponentAdmin(admin.ModelAdmin):
    list_display = ('name', 'template')
    fields = ('name', 'location', 'message', 'template', 'context')
