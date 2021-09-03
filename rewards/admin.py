from rewards.models import MailingAddress, Claim
from django.contrib import admin

admin.site.register(MailingAddress)


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    readonly_fields = ('Claim date',)
