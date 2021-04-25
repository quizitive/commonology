from ckeditor_uploader.widgets import CKEditorUploadingWidget

from django import forms
from django.contrib import admin

from game.models import Game, Question, Answer, AnswerCode


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'game_id')
    ordering = ('-game_id', )
    search_fields = ('game_id', 'name')

#
# class QuestionAdminForm(forms.ModelForm):
#     image = forms.ImageField(widget=CKEditorUploadingWidget())
#
#     class Meta:
#         model = Question
#         fields = '__all__'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'game')
    list_filter = ('game__name',)
    search_fields = ('text', 'game__name')


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
