from django.contrib import admin
from django.forms import Textarea
from django.db import models

from game.models import Series, Game, Question, Answer, AnswerCode


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    filter_horizontal = ('hosts', )
    exclude = ('players',)


class QuestionAdmin(admin.StackedInline):
    model = Question
    list_display = ('text', 'game')
    list_filter = ('game__name',)
    search_fields = ('text', 'game__name')
    ordering = ('number', )
    fieldsets = (
        (None, {
            'fields': ()
        }),
        ('Question', {
            'classes': ('collapse',),
            'fields': ('number', 'text', 'type', 'image', 'hide_default_results', 'caption'),
        }),
    )
    formfield_overrides = {models.CharField: {'widget': Textarea(attrs={'size': '200'})}}

    def get_extra(self, request, obj=None, **kwargs):
        return 0


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ('name', 'game_id', 'series', 'start', 'end')
    ordering = ('-game_id', )
    search_fields = ('game_id', 'name', 'series')
    filter_horizontal = ('hosts',)
    list_filter = ('series',)
    inlines = (QuestionAdmin,)


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
