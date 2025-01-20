from django.contrib import admin
from components.models import Component, Location, SponsorComponent


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ("name", "template")
    fields = ("name", "message", "template", "context", "locations")
    search_fields = ("name", "message")
    filter_horizontal = ("locations",)


@admin.register(Location)
class ComponentLocationAdmin(admin.ModelAdmin):
    list_display = ("app_name", "location")


@admin.register(SponsorComponent)
class SponsorComponentAdmin(admin.ModelAdmin):
    list_display = ("name", "template")
    fields = ("name", "message", "template", "context", "locations", "start_date", "end_date")
    search_fields = ("name", "message")
    filter_horizontal = ("locations",)
