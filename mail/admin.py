from django.contrib import admin
from .models import MassMailMessage

@admin.register(MassMailMessage)
class MassMailMessageAdmin(admin.ModelAdmin):
    pass
