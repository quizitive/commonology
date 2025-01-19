from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import SimpleListFilter
from django.db.models import Count, Q

from .forms import PlayerCreationForm, PlayerChangeForm
from .models import Player, PendingEmail, Team
from .actions import subscribe_action, unsubscribe_action

from game.models import Series


class SeriesInLine(admin.TabularInline):
    model = Series.players.through


@admin.register(Player)
class PlayerUserAdmin(UserAdmin):
    add_form = PlayerCreationForm
    form = PlayerChangeForm
    model = Player
    list_display = ("email", "date_joined", "display_name", "first_name", "last_name", "subscribed", "get_series")
    list_filter = ("date_joined", "subscribed", "is_member", "is_staff", "is_active", "is_superuser", "series")
    fieldsets = (
        (None, {"fields": ("email", "password", "code")}),
        (
            "Personal",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "display_name",
                    "birth_date",
                    "is_member",
                    "subscribed",
                    "reminder",
                )
            },
        ),
        ("Other", {"fields": ("date_joined", "location")}),
        ("Games Played", {"fields": ("games_played",)}),
        (
            "Referrals",
            {
                "fields": (
                    "referrer",
                    "referrals_roster",
                )
            },
        ),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "is_staff",
                    "is_active",
                    "is_superuser",
                    "groups",
                ),
            },
        ),
    )
    readonly_fields = ("code", "referrals_roster", "games_played")
    search_fields = ("email", "first_name", "last_name", "display_name")
    ordering = ("email",)
    actions = [subscribe_action, unsubscribe_action]
    inlines = [SeriesInLine]

    def get_series(self, obj):
        return "\n".join([s.slug for s in obj.series.all()])

    get_series.short_description = "Series"


class ValidatedEmailFilter(SimpleListFilter):
    title = "Validated"
    parameter_name = "validated"

    def lookups(self, request, model_admin):
        return [("yes", "Validated"), ("no", "Not validated")]

    def queryset(self, request, qs):
        v = self.value()
        if "no" == v:
            qs = qs.exclude(email__in=Player.objects.values_list("email", flat=True))
        elif "yes" == v:
            qs = qs.filter(email__in=Player.objects.values_list("email", flat=True))

        return qs


@admin.register(PendingEmail)
class PendingEmailAdmin(admin.ModelAdmin):
    list_display = ("email", "created", "referrer", "uuid")
    list_filter = ("created", ValidatedEmailFilter)
    search_fields = ("email", "uuid")


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "id")
    search_field = ("name", "id", "players__email", "players__display_name")


class Referrer(Player):
    class Meta:
        proxy = True


def referral_filter_ids(low=None, high=None):
    # Really want to do this:
    # select B.*, count(A.*) as n from users_player A, users_player B where A.referrer_id=B.id
    #   group by B.id, B.* order by B.id
    # BUT ... Django ORM does NOT support self joins

    active_players = Player.objects.filter(referrer__isnull=False).filter(answers__isnull=False).distinct()
    f = Q(id__in=[i.id for i in active_players])
    qs = Player.objects.values("referrer").annotate(n=Count("referrer", filter=f))

    if low:
        qs = qs.filter(n__gte=low)
    if high:
        qs = qs.filter(n__lte=high)

    ids = [i["referrer"] for i in qs.all()]
    return ids


class ReferrerFilter(SimpleListFilter):
    title = "Referrals"
    parameter_name = "n_referrals"

    def lookups(self, request, model_admin):
        return [
            ("less5", "Less than 5"),
            ("five", "Five"),
            ("less10", "6 to 9"),
            ("ten", "Ten"),
            ("less15", "11 to 15"),
            ("more", "More than 15"),
        ]

    def queryset(self, request, qs):
        v = self.value()
        if "less5" == v:
            qs = qs.filter(id__in=referral_filter_ids(high=4))
        if "five" == v:
            qs = qs.filter(id__in=referral_filter_ids(low=5, high=5))
        elif "less10" == v:
            qs = qs.filter(id__in=referral_filter_ids(low=6, high=9))
        if "ten" == v:
            qs = qs.filter(id__in=referral_filter_ids(low=10, high=10))
        elif "less15" == v:
            qs = qs.filter(id__in=referral_filter_ids(low=11, high=15))
        elif "more" == v:
            qs = qs.filter(id__in=referral_filter_ids(low=16))

        return qs


class ReferrerClaimFilter(SimpleListFilter):
    title = "Referral prize claims"
    parameter_name = "claims"

    def lookups(self, request, model_admin):
        return [("not_claimed", "Not claimed"), ("claimed", "Claimed"), ("sent", "Sent")]

    def queryset(self, request, qs):
        v = self.value()
        if "not_claimed" == v:
            qs = qs.filter(claim__isnull=True)
        elif "claimed" == v:
            qs = qs.filter(claim__isnull=False)
        elif "sent" == v:
            qs = qs.filter(claim__sent_date__isnull=False)
        return qs


@admin.register(Referrer)
class ReferrersAdmin(PlayerUserAdmin):
    list_filter = (ReferrerFilter, ReferrerClaimFilter, "date_joined", "subscribed")
    list_display = ("email", "date_joined", "referral_count")
    ordering = None

    def get_queryset(self, request):
        ids = referral_filter_ids()
        qs = super(PlayerUserAdmin, self).get_queryset(request).filter(id__in=ids)
        return qs
