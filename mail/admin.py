from django.contrib import admin, messages
from .models import MailMessage
from django_object_actions import DjangoObjectActions

from .utils import make_absolute_urls
from .sendgrid_utils import mass_mail


@admin.register(MailMessage)
class MailMessageAdmin(DjangoObjectActions, admin.ModelAdmin):
    def send_test(self, request, obj):
        email = obj.test_recipient
        message = make_absolute_urls(obj.message)
        from_email = (obj.from_email, obj.from_name)
        mass_mail(obj.subject, message, from_email, email_list=[(email, id)])
        obj.tested = True
        obj.save()
        messages.add_message(request, messages.INFO, 'Test message sent.')
    send_test.label = 'Test'
    send_test.short_description = "Send a test message."

    def blast(self, request, obj):
        if obj.sent:
            messages.add_message(request, messages.WARNING,
                                 "This blast was already sent.")
        elif obj.tested:
            message = make_absolute_urls(obj.message)
            from_email = (obj.from_email, obj.from_name)
            mass_mail(obj.subject, message, from_email, categories=obj.categories)
            obj.sent = True
            obj.save()
            messages.add_message(request, messages.INFO, 'Blast message sent.')
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
    save_on_top = True

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if 'message' in form.changed_data:
            obj.tested = False
            obj.sent = False
            obj.save()
