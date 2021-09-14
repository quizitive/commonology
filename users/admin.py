from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import SimpleListFilter
from django.db.models import Count

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
    list_display = ('email', 'date_joined', 'display_name', 'first_name', 'last_name', 'subscribed', 'get_series')
    list_filter = ('date_joined', 'subscribed', 'is_member', 'is_staff', 'is_active', 'is_superuser',
                   'series')
    fieldsets = (
        (None, {'fields': ('email', 'password', 'code')}),
        ('Personal', {'fields': ('first_name', 'last_name', 'display_name', 'birth_date', 'is_member', 'subscribed')}),
        ('Other', {'fields': ('date_joined', 'location')}),
        ('Referrals', {'fields': ('referrer', 'referrals',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser',
                                    'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name',
                       'is_staff', 'is_active', 'is_superuser', 'groups')}
        ),
    )
    readonly_fields = ('code', 'referrals')
    search_fields = ('email', 'first_name', 'last_name', 'display_name')
    ordering = ('email',)
    actions = [subscribe_action, unsubscribe_action]
    inlines = [SeriesInLine]

    def get_series(self, obj):
        return "\n".join([s.slug for s in obj.series.all()])
    get_series.short_description = 'Series'


@admin.register(PendingEmail)
class PendingEmailAdmin(admin.ModelAdmin):
    list_display = ('email', 'created', 'referrer', 'uuid')
    list_filter = ('created',)
    search_fields = ('email', 'uuid')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
    search_field = ('name', 'id', 'players__email', 'players__display_name')


class Referrer(Player):
    class Meta:
        proxy = True

    @property
    def referral_count(self):
        return len(self.referrers.all())


class ReferrerFilter(SimpleListFilter):
    title = "Referrals"
    parameter_name = 'n_referrals'

    def lookups(self, request, model_admin):
        return [("less", "Less"), ('more', 'More')]

    def queryset(self, request, queryset):
        if self.value() == 'less':
            ids = [i['referrer'] for i in
                   Player.objects.values('referrer').
                   annotate(n=Count('referrer')).
                   filter(n__lt=10).
                   all()]
            return queryset.filter(id__in=ids)

        if self.value() == 'more':
            ids = [i['referrer'] for i in
                   Player.objects.values('referrer').
                   annotate(n=Count('referrer')).
                   filter(n__gte=10).
                   all()]
            return queryset.filter(id__in=ids)

        return queryset


@admin.register(Referrer)
class ReferrersAdmin(PlayerUserAdmin):
    list_filter = (ReferrerFilter, 'date_joined', 'subscribed')
    list_display = ('email', 'date_joined', 'referral_count')

    def get_queryset(self, request):
        ids = [i['referrer'] for i in
               Player.objects.values('referrer').
               annotate(n=Count('referrer')).
               filter(n__gte=0).
               all()]
        qs = super(PlayerUserAdmin, self).get_queryset(request).filter(id__in=ids)
        return qs
