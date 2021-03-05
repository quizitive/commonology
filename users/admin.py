from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser, PendingEmail


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ('email', 'is_staff', 'is_active', 'is_superuser')
    list_filter = ('email', 'is_staff', 'is_active', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal', {'fields': ('first_name', 'last_name', 'birth_date')}),
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


class PendingEmailAdmin(admin.ModelAdmin):
    list_display = ('email', 'referrer', 'created', 'uuid')
    list_filter = ('created',)
    search_fields = ('email', 'referrer', 'uuid')


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(PendingEmail, PendingEmailAdmin)
