from functools import lru_cache
from collections import Counter

from pychartjs import ChartType, Color, Options, BaseSmartChart, BaseChartData

from django.db.models import Min, Q

from project.utils import our_now
from game.models import Game
from game.utils import new_players_for_game
from users.models import Player


class PlayerTrendChart(BaseSmartChart):
    type = ChartType.Line

    class options:
        scales = Options.General(
            y=Options.General(
                title=Options.Title("Number of Players")
            )
        )


class PlayersAndMembersDataset:

    def __init__(self, **kwargs):
        self.Players = GamePlayerCount(
            player_filters={},
            borderColor=Color.Hex(0x0095daFF),
            backgroundColor=Color.Hex(0x0095daFF),
            **kwargs
        )
        self.Members = GamePlayerCount(
            player_filters={'player__is_member': True},
            borderColor=Color.Hex(0xf26649FF),
            backgroundColor=Color.Hex(0xf26649FF),
            **kwargs
        )
        self.NewPlayers = GamePlayerCount(
            numerator_fcn='new_players',
            borderColor=Color.Hex(0x237073FF),
            backgroundColor=Color.Hex(0x237073FF),
            **kwargs
        )

    def get_labels(self):
        return self.Members.get_labels()


class GamePlayerCount(BaseChartData):
    # self.numerator_fcn is the name of the desired numerator function that
    # takes the argument this_period, which is a list of games in a period,
    # and returns a list of numerators that ultimately get returned to the chart

    def __init__(self, slug, since_game=0, player_filters=None, agg_period=1, **kwargs):
        self.slug = slug
        self.since_game = since_game
        self.numerator_fcn = 'players_with_filters'
        self.player_filters = player_filters or {}
        self.agg_period = agg_period
        super().__init__(**kwargs)

    @lru_cache(maxsize=1)
    def queryset(self):
        return Game.objects.filter(series__slug=self.slug, game_id__gte=self.since_game, end__lte=our_now())

    @lru_cache(maxsize=1)
    def periods(self):
        gids = self.queryset().values_list('game_id', flat=True)
        periods = []
        for idx in range(0, len(gids), self.agg_period):
            g = gids[idx]
            periods.append((max(self.since_game, g - (self.agg_period - 1)), g))
        return periods

    def get_data(self):
        data = []
        games = self.queryset()
        # todo: fetch numerator data into dictionary before iterating through periods
        for p in self.periods():
            this_period = games.filter(game_id__gte=p[0], game_id__lte=p[1])
            try:
                numerator_fcn = self.__getattribute__(self.numerator_fcn)
                this_pd_avg = sum(numerator_fcn(this_period)) / this_period.count()
            except ZeroDivisionError:
                break
            data.append(this_pd_avg)
        data.reverse()
        return data

    def players_with_filters(self, this_period):
        return [g.players_dict.filter(**self.player_filters).count() for g in this_period]

    def new_players(self, this_period):
        return [new_players_for_game(g.series.slug, g.game_id).count() for g in this_period]

    def get_labels(self):
        periods = self.periods()
        periods.reverse()
        if self.agg_period == 1:
            return [f"Game {s}" for s, _ in periods]
        return [f"Games {s} - {e}" for s, e in periods]
