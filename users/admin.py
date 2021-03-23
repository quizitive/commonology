from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import PlayerCreationForm, PlayerChangeForm
from .models import Player, PendingEmail, Team


@admin.register(Player)
class PlayerUserAdmin(UserAdmin):
    add_form = PlayerCreationForm
    form = PlayerChangeForm
    model = Player
    list_display = ('email', 'is_staff', 'is_active', 'is_superuser')
    list_filter = ('email', 'is_staff', 'is_active', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal', {'fields': ('first_name', 'last_name', 'display_name', 'birth_date', 'is_member')}),
        ('Other', {'fields': ('location', 'referrer')}),
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
    search_fields = ('email',)
    ordering = ('email',)


@admin.register(PendingEmail)
class PendingEmailAdmin(admin.ModelAdmin):
    list_display = ('email', 'referrer', 'created', 'uuid')
    list_filter = ('created',)
    search_fields = ('email', 'referrer', 'uuid')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
    search_field = ('name', 'id', 'players__email', 'players__display_name')
