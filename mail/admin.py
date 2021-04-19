from django.contrib import admin
from .models import MassMailMessage
from django_object_actions import DjangoObjectActions


@admin.register(MassMailMessage)
class MassMailMessageAdmin(DjangoObjectActions, admin.ModelAdmin):
    def send_test(self, request, obj):
        obj.tested = True
        obj.save()
        print("Testing", obj.test_recipient)
    send_test.label = 'Test'
    send_test.short_description = "Send a test message."

    def blast(self, request, obj):
        if obj.tested:
            print("Blasting", obj.subject)
        else:
            print("Cannot send blast until message was tested.")
    blast.label = "Blast"
    blast.short_description = "This will send the message to EVERYONE!"

    change_actions = ('send_test', 'blast')

    list_display = ('created', 'subject', 'test_recipient')
    list_filter = ('created',)
    search_fields = ('subject',)
    ordering = ('-created',)
