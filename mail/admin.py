from django.contrib import admin
from .models import MailMessage
from django_object_actions import DjangoObjectActions

from .utils import make_absolute_urls
from .tasks import mass_mail

@admin.register(MailMessage)
class MailMessageAdmin(DjangoObjectActions, admin.ModelAdmin):
    def send_test(self, request, obj):
        message = make_absolute_urls(obj.message)
        from_email = (obj.from_email, obj.from_name)
        mass_mail(obj.subject, message, from_email, email_list=[(obj.test_recipient, 0)])
        obj.tested = True
        obj.save()
    send_test.label = 'Test'
    send_test.short_description = "Send a test message."

    def blast(self, request, obj):
        if obj.tested:
            print("Blasting", obj.subject)
        else:
            print("Cannot send blast until message was tested.")
        obj.sent = True
        obj.save()
    blast.label = "Blast"
    blast.short_description = "This will send the message to EVERYONE!"

    change_actions = ('send_test', 'blast')

    list_display = ('created', 'subject', 'test_recipient')
    list_filter = ('created',)
    search_fields = ('subject',)
    ordering = ('-created',)
