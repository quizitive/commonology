from rewards.models import Claim
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.safestring import mark_safe
from rewards.models import MailingAddress


@admin.register(MailingAddress)
class MailingAddressAdmin(admin.ModelAdmin):
    list_display = ('player', )


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
    list_display = ('player', 'claim_date', 'sent_date')  # , 'address')
    readonly_fields = ['address']

    def address(self, obj):
        try:
            a = MailingAddress.objects.get(player=obj.player)
            return mark_safe(f"<a href='/admin/rewards/mailingaddress/{a.pk}/change/'>address</a><br>"
                             f"{a}")
        except MailingAddress.DoesNotExist:
            return "missing"

    # the following is necessary if 'link' method is also used in list_display
    address.allow_tags = True
