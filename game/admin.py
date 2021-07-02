from django.contrib import admin
from django.forms.fields import CharField
from django.contrib.postgres.forms import SimpleArrayField
from django.forms import Textarea, ModelForm
from django.db import models

from game.models import Series, Game, Question, Answer, AnswerCode
from project.utils import redis_delete_patterns


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    filter_horizontal = ('hosts', )
    exclude = ('players',)


class QuestionAdminForm(ModelForm):
    choices = SimpleArrayField(CharField(), delimiter='\r\n', widget=Textarea(attrs={'cols': '30', 'rows': '5'}),
        required=False, help_text="Enter each choice on a new line")

    class Meta:
        fields = '__all__'


class QuestionAdmin(admin.StackedInline):
    model = Question
    list_display = ('text', 'game')
    list_filter = ('game__name',)
    search_fields = ('text', 'game__name')
    ordering = ('number', )
    form = QuestionAdminForm
    fieldsets = (
        (None, {
            'fields': ()
        }),
        ('Question', {
            'classes': ('collapse',),
            'fields': ('number', 'text', 'image', 'choices', 'type', 'caption'),
        }),
    )
    formfield_overrides = {models.CharField: {'widget': Textarea(attrs={'cols': '100', 'rows': '2'})}}

    def get_extra(self, request, obj=None, **kwargs):
        return 0


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('name', 'game_id', 'series', 'start', 'end')
    ordering = ('-game_id', )
    search_fields = ('game_id', 'name', 'series__slug')
    filter_horizontal = ('hosts',)
    list_filter = ('series',)
    inlines = (QuestionAdmin,)
    actions = ('clear_cache', )
    view_on_site = True

    def clear_cache(self, request, queryset):
        lb_prefixes = [f'leaderboard_{q[0]}_{q[1]}' for q in queryset.values_list('series__slug', 'game_id')]
        lbs_deleted = redis_delete_patterns(*lb_prefixes)
        at_prefixes = [f'answertally_{q[0]}_{q[1]}' for q in queryset.values_list('series__slug', 'game_id')]
        ats_deleted = redis_delete_patterns(*at_prefixes)
        self.message_user(request, f"{lbs_deleted} cached leaderboards were deleted")
        self.message_user(request, f"{ats_deleted} cached answer tallies were deleted")


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('raw_string', 'question', 'game')
    search_fields = ('raw_string', 'question__text', 'question__game__name')

    def game(self, obj):
        return obj.game


@admin.register(AnswerCode)
class AnswerCodeAdmin(admin.ModelAdmin):
    list_display = ('coded_answer', 'question')
    search_fields = ('coded_answer', 'question__text', 'question__game__name')

    def game(self, obj):
        return obj.game
