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
    change_form_template = 'admin/mail_change_form.html'

    def keep_form_open(self, request):
        request.POST._mutable = True
        request.POST['_continue'] = 'Save and continue editing'
        request.POST._mutable = False

    def response_change(self, request, obj):
        if '_button_test' in request.POST:
            self.keep_form_open(request)
            self.send_test(request, obj)
        elif '_button_blast' in request.POST:
            if obj.enable_blast:
                self.blast(request, obj)
                obj.enable_blast = False
                obj.save()
            else:
                self.keep_form_open(request)
                if not obj.enable_blast:
                    messages.add_message(request, messages.WARNING, "You must enable blast with the checkbox below.")

        x = super().response_change(request, obj)
        return x

    def send_test(self, request, obj):
        # super().save_model(request, obj, self.form)
        super().response_change(request, obj)
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
        messages.add_message(request, messages.INFO, 'Test message sent.')

    def blast(self, request, obj):
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

    change_actions = ('send_test', 'blast')

    list_display = ('subject', 'sent_date', 'test_recipient')
    list_filter = ('created',)
    search_fields = ('subject',)
    ordering = ('-sent_date',)
    filter_horizontal = ('top_components', 'bottom_components')
    save_on_top = True

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
        messages.add_message(request, messages.INFO, 'Attempted to cancel message, may not work if less than 20 min away.')
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
