import logging

from django.contrib import admin
from django.contrib.messages import constants as messages
from django.forms.fields import CharField
from django.contrib.postgres.forms import SimpleArrayField
from django.forms import Textarea, ModelForm
from django.db import models
from django.utils.html import format_html

from game.models import Series, Game, Question, Answer, AnswerCode
from game.mail import send_winner_notice
from leaderboard.leaderboard import tabulate_results, winners_of_game
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
    readonly_fields = ["uuid"]
    list_display = ('name', 'game_id', 'series', 'start', 'end', 'play')
    ordering = ('-game_id', )
    search_fields = ('game_id', 'name', 'series__slug')
    filter_horizontal = ('hosts',)
    list_filter = ('series',)
    inlines = (QuestionAdmin,)
    actions = ('clear_cache', 'score_selected_games',
               'score_selected_games_update_existing', 'email_winner_certificates')
    view_on_site = True

    def clear_cache(self, request, queryset):
        lb_prefixes = [f'leaderboard_{q[0]}_{q[1]}' for q in queryset.values_list('series__slug', 'game_id')]
        lbs_deleted = redis_delete_patterns(*lb_prefixes)
        at_prefixes = [f'build_answer_tally:{repr(q)}' for q in queryset]
        ats_deleted = redis_delete_patterns(*at_prefixes)
        self.message_user(request, f"{lbs_deleted} cached leaderboards were deleted")
        self.message_user(request, f"{ats_deleted} cached answer tallies were deleted")

    def score_selected_games(self, request, queryset):
        for game in queryset:
            self._score_game(request, game)
    score_selected_games.short_description = "Score Selected Games"

    def score_selected_games_update_existing(self, request, queryset):
        for game in queryset:
            self._score_game(request, game, update=True)
    score_selected_games_update_existing.short_description = 'Score Selected Games (update existing - slower!)'

    def _score_game(self, request, game, update=False):
        try:
            tabulate_results(game, update)
            self.message_user(request, f"{game.name} has successfully been scored!")
        except Exception as e:
            self.message_user(request, "An unexpected error occurred. Ping Ted.",
                              level=messages.ERROR)
            logging.error("Exception occurred", exc_info=True)

    def email_winner_certificates(self, request, queryset):
        for game in queryset:
            game_number = game.game_id
            n = 0
            winners = winners_of_game(self.game)
            for winner in winners:
                send_winner_notice(winner, game_number)
                n += 1
            self.message_user(request, f"{n} winner certifictes sent.")

    def get_readonly_fields(self, request, obj=None):
        # This will list model fields with editable=False in the admin.
        if obj:
            return [f.name for f in obj._meta.fields if not f.editable]
        else:
            return self.readonly_fields

    def play(self, obj):
        series = Series.objects.filter(id=obj.series_id).first()
        if series:
            return format_html(f"<a href=/c/{series.slug}/play/{obj.uuid}>play</a>")
        else:
            return f"{obj.uuid}"
    play.allow_tags = True


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('raw_string', 'question', 'player', 'game')
    search_fields = ('raw_string', 'question__text', 'question__game__name', 'player__email')

    list_filter = ('question__game__name', )

    def game(self, obj):
        return obj.game


@admin.register(AnswerCode)
class AnswerCodeAdmin(admin.ModelAdmin):
    list_display = ('coded_answer', 'question')
    search_fields = ('coded_answer', 'question__text', 'question__game__name')

    def game(self, obj):
        return obj.game
