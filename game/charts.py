from functools import lru_cache

from pychartjs import ChartType, Color, Options, BaseSmartChart, BaseChartData
from game.models import Game


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
        self.Members = GamePlayerCount(
            player_filters={'player__is_member': True},
            borderColor=Color.Hex(0xf26649FF),
            backgroundColor=Color.Hex(0xf26649FF),
            **kwargs
        )
        self.Players = GamePlayerCount(
            player_filters={},
            borderColor=Color.Hex(0x0095daFF),
            backgroundColor=Color.Hex(0x0095daFF),
            **kwargs
        )

    def get_labels(self):
        return self.Members.get_labels()


class GamePlayerCount(BaseChartData):

    def __init__(self, slug, since_game=0, player_filters=None, agg_period=1, **kwargs):
        self.slug = slug
        self.since_game = since_game
        self.player_filters = player_filters or {}
        self.agg_period = agg_period
        super().__init__(**kwargs)

    @lru_cache(maxsize=1)
    def queryset(self):
        return Game.objects.filter(series__slug=self.slug, game_id__gte=self.since_game, publish=True)

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
        for p in self.periods():
            this_period = games.filter(game_id__gte=p[0], game_id__lte=p[1])
            try:
                this_pd_avg = sum([g.players.filter(**self.player_filters).count() for g in this_period]) / this_period.count()
            except ZeroDivisionError:
                break
            data.append(this_pd_avg)
        data.reverse()
        return data

    def get_labels(self):
        periods = self.periods()
        periods.reverse()
        if self.agg_period == 1:
            return [f"Game {s}" for s, _ in periods]
        return [f"Games {s} - {e}" for s, e in periods]
