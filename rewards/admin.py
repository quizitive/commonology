from rewards.models import MailingAddress, Claim
from django.contrib import admin
from django.contrib.admin import SimpleListFilter

admin.site.register(MailingAddress)


class SentFilter(SimpleListFilter):
    title = "Not Sent"
    parameter_name = 'claim'

    def lookups(self, request, model_admin):
        return [("sent", "Sent"), ('not_sent', 'Not Sent')]

    def queryset(self, request, queryset):
        if self.value() == 'sent':
            return queryset.filter(sent_date__isnull=False)
        if self.value() == 'not_sent':
            return queryset.filter(sent_date__isnull=True)


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    readonly_fields = ('claim_date',)
    list_filter = (SentFilter,)
