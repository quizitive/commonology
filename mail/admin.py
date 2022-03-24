from django.contrib import admin, messages
from django_object_actions import DjangoObjectActions

from sortedm2m_filter_horizontal_widget.forms import SortedFilteredSelectMultiple

from project.utils import our_now, log_entry
from .models import MailMessage, MailLog, add_mail_log
from .utils import mass_mail, sendgrid_send, sendgrid_cancel
from users.models import Player
from components.models import Component, SponsorComponent


@admin.register(MailMessage)
class MailMessageAdmin(DjangoObjectActions, admin.ModelAdmin):
    def send_test(self, request, obj):
        email = obj.test_recipient
        try:
            test_user = Player.objects.get(email=obj.test_recipient)
            user_code = test_user.code
        except Player.DoesNotExist:
            user_code = -1

        from_email = (obj.from_email, obj.from_name)
        top_components = list(SponsorComponent.active_sponsor_components()) + list(obj.top_components.all())
        n, msg, batch_id = sendgrid_send(obj.subject, msg=obj.message, email_list=[(email, user_code)],
                                         from_email=from_email, unsub_link=True,
                                         top_components=top_components, bottom_components=obj.bottom_components.all())
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
            if obj.series is None:
                messages.add_message(request, messages.WARNING, 'You must choose a series.')
                return

            n, log_msg, batch_id = mass_mail(obj)

            log_entry(obj, log_msg, request.user)

            obj.sent = True
            obj.sent_date = our_now()
            obj.save()

            add_mail_log(obj, batch_id=batch_id)

            if n:
                messages.add_message(request, messages.INFO, f'Blast message sent to {n} players.')
            else:
                messages.add_message(request, messages.WARNING, 'No valid recipients found, message not sent.')
        else:
            messages.add_message(request, messages.WARNING,
                                 "Cannot send blast until message is tested.")

    blast.label = "Blast"
    blast.short_description = "This will send the message to EVERYONE!"

    change_actions = ('send_test', 'blast')

    list_display = ('subject', 'sent_date', 'test_recipient')
    list_filter = ('created',)
    search_fields = ('subject',)
    ordering = ('-sent_date',)
    filter_horizontal = ('top_components', 'bottom_components')
    save_on_top = True

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if 'message' in form.changed_data:
            obj.tested = False
            obj.sent = False
            obj.save()

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name in ('top_components', 'bottom_components'):
            kwargs['queryset'] = Component.objects.filter(locations__app_name='mail')
            kwargs['widget'] = SortedFilteredSelectMultiple()
        return super(MailMessageAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(MailLog)
class MailLogAdmin(DjangoObjectActions, admin.ModelAdmin):

    def cancel_send(self, request, obj):
        result = sendgrid_cancel(batch_id=obj.batch_id)
        obj.canceled = our_now()
        obj.save()
        messages.add_message(request, messages.INFO, 'Attempted to cancel message.')
    cancel_send.label = 'Cancel Message'
    cancel_send.short_description = "Tries to stop message at SendGrid."

    list_display = ('subject', 'sent_date')
    list_filter = ('created',)
    search_fields = ('subject',)
    ordering = ('-sent_date',)
    filter_horizontal = ('top_components', 'bottom_components')
    save_on_top = True

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    change_actions = ('cancel_send', )
