from django.contrib import admin
from .models import MassMailMessage


@admin.register(MassMailMessage)
class MassMailMessageAdmin(admin.ModelAdmin):
    list_display = ('created', 'subject', 'test_recipient')
    list_filter = ('created',)
    search_fields = ('subject',)
    ordering = ('-created',)
