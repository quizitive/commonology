from rewards.models import Claim
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.safestring import mark_safe
from project.utils import our_now
from rewards.models import MailingAddress


@admin.register(MailingAddress)
class MailingAddressAdmin(admin.ModelAdmin):
    list_display = ("player",)


class SentFilter(SimpleListFilter):
    title = "Not Sent"
    parameter_name = "claim"

    def lookups(self, request, model_admin):
        return [("sent", "Sent"), ("not_sent", "Not Sent")]

    def queryset(self, request, queryset):
        if self.value() == "sent":
            return queryset.filter(sent_date__isnull=False)
        if self.value() == "not_sent":
            return queryset.filter(sent_date__isnull=True)


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    readonly_fields = ("claim_date",)
    list_filter = (SentFilter,)
    search_fields = ("player__email", "player__display_name", "player__first_name", "player__last_name")
    list_display = ("player", "claim_date", "sent_date")
    readonly_fields = ["address"]
    actions = ("mark_selected_as_shipped",)

    def address(self, obj):
        try:
            a = MailingAddress.objects.get(player=obj.player)
            return mark_safe(f"<a href='/admin/rewards/mailingaddress/{a.pk}/change/'>address</a><br>" f"{a}")
        except MailingAddress.DoesNotExist:
            return "missing"

    # the following is necessary if 'link' method is also used in list_display
    address.allow_tags = True

    def mark_selected_as_shipped(self, request, queryset):
        for q in queryset:
            q.sent_date = our_now()
            q.save()
        self.message_user(request, f"{queryset.count()} claims were just marked as shipped!")
