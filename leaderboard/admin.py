import logging

from django.contrib import admin
from django.contrib.messages import constants as messages
from django.shortcuts import redirect

from django_object_actions import DjangoObjectActions
from sortedm2m_filter_horizontal_widget.forms import SortedFilteredSelectMultiple

from components.models import Component
from leaderboard.models import Leaderboard
from leaderboard.leaderboard import tabulate_results, winners_of_game, clear_leaderboard_cache


@admin.register(Leaderboard)
class LeaderboardAdmin(DjangoObjectActions, admin.ModelAdmin):
    save_on_top = True
    list_display = ('game_name', 'game_id', 'series', 'publish_date')
    ordering = ('-game__game_id', )
    search_fields = ('game__game_id', 'game__name', 'game__series__slug')
    list_filter = ('game__series',)
    filter_horizontal = ('top_components',)
    actions = ('clear_cache', 'score_selected_games',
               'score_selected_games_update_existing', 'email_winner_certificates', 'find_raffle_winner')
    change_actions = ('go_to_game'),
    view_on_site = True

    @admin.display(ordering='-game__game_id')
    def game_id(self, obj):
        return obj.game.game_id

    @admin.display()
    def game_name(self, obj):
        return obj.game.name

    @admin.display()
    def series(self, obj):
        return obj.game.series

    def clear_cache(self, request, queryset):
        lbs_deleted, ats_deleted = clear_leaderboard_cache(queryset)
        self.message_user(request, f"{lbs_deleted} cached leaderboards were deleted")
        self.message_user(request, f"{ats_deleted} cached answer tallies were deleted")

    def score_selected_games(self, request, queryset):
        for leaderboard in queryset:
            self._score_game(request, leaderboard.game)
    score_selected_games.short_description = "Score Selected Games"

    def score_selected_games_update_existing(self, request, queryset):
        for leaderboard in queryset:
            self._score_game(request, leaderboard.game, update=True)
    score_selected_games_update_existing.short_description = 'Score Selected Games (update existing - slower!)'

    def _score_game(self, request, game, update=False):
        try:
            tabulate_results(game, update)
            self.message_user(request, f"{game.name} has successfully been scored!")
        except Exception as e:
            self.message_user(request, "An unexpected error occurred. Ping Ted.",
                              level=messages.ERROR)
            logging.error("Exception occurred", exc_info=True)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name in ('top_components',):
            kwargs['queryset'] = Component.objects.filter(locations__app_name='leaderboard')
            kwargs['widget'] = SortedFilteredSelectMultiple()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def go_to_game(self, request, obj):
        return redirect('admin:game_game_change', obj.game.id)
