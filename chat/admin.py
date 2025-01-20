from django.contrib import admin

from chat.models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("commenter", "comment", "status")

    # todo: this will break when we have threads on anything not associated with a game
    # when that happens, a more robust solution would be implementing a custom ListFilter
    # see https://docs.djangoproject.com/en/3.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_filter
    list_filter = (
        "removed",
        "thread__object__game",
    )

    search_fields = ("player__email__exact", "player__display_name", "comment", "removed", "thread__object__game__name")

    def status(self, obj):
        return not obj.removed

    status.boolean = True
