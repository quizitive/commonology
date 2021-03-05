from django.contrib import admin

from game.models import Game, Question, Player, Team, Answer, AnswerCode


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'game_id')
    ordering = ('-game_id', )
    search_fields = ('game_id', 'name')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'game')
    search_fields = ('text', 'game__name')


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('email', 'display_name')
    search_fields = ('email', 'display_name')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
    search_field = ('name', 'id', 'players__email', 'players__display_name')


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
