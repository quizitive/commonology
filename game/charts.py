from collections import Counter

from pychartjs import ChartType, Color, Options, BaseSmartChart, BaseChartData

from django.db.models import Count, F, Min
from django.utils.functional import cached_property

from game.models import Game
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
            player_filters={'is_member': True},
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
        print("Foo")

    def get_labels(self):
        return self.Members.get_labels()


class GamePlayerCount(BaseChartData):
    # self.numerator_fcn is the name of the desired numerator function that
    # defines the count of players for each game based on custom filters. It returns
    # a dict of such as {game_id: player_count}

    def __init__(self, slug, since_game=0, player_filters=None, agg_period=1, **kwargs):
        self.slug = slug
        self.since_game = since_game
        self.numerator_fcn = 'players_with_filters'
        self.player_filters = player_filters or {}
        self.agg_period = agg_period
        super().__init__(**kwargs)

    def players_with_filters(self):
        players_with_filter_count = Player.objects.filter(
            answers__question__game__game_id__gte=self.since_game,
            answers__question__game__series__slug='commonology',
            **self.player_filters
        ).values(
            game_id=F('answers__question__game__game_id')
        ).annotate(num_players=Count('id', distinct=True))
        return {game['game_id']: game['num_players'] for game in players_with_filter_count}

    @staticmethod
    def new_players():
        first_games = Player.objects.filter(
            answers__question__game__series__slug='commonology').annotate(
            first_game=Min('answers__question__game__game_id')
        ).values_list('id', 'first_game')
        return Counter([fg[1] for fg in first_games])

    @cached_property
    def periods(self):
        gids = Game.objects.filter(game_id__gte=self.since_game).values_list('game_id', flat=True)
        periods = []
        for idx in range(0, len(gids), self.agg_period):
            g = gids[idx]
            periods.append((max(self.since_game, g - (self.agg_period - 1)), g))
        return periods

    def get_data(self):
        numerator_fcn = self.__getattribute__(self.numerator_fcn)
        numerator_dict = numerator_fcn()
        data = []
        for p in self.periods:
            game_ids = [gid for gid in range(p[0], p[1] + 1)]
            try:
                this_pd_avg = sum([numerator_dict[gid] for gid in game_ids]) / len(game_ids)
            except ZeroDivisionError:
                break
            data.append(this_pd_avg)
        data.reverse()
        return data

    def get_labels(self):
        if self.agg_period == 1:
            return [f"Game {s}" for s, _ in reversed(self.periods)]
        return [f"Games {s} - {e}" for s, e in reversed(self.periods)]
