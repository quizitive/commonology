from collections import Counter

from django.db.models import Count, F, Min
from django.utils.functional import cached_property

from charts.utils import BaseSmartChart, BaseChartData
from project.utils import our_now
from game.models import Game
from users.models import Player


class PlayerTrendChart(BaseSmartChart):

    def _options_dict(self):
        od = {
            "grid": {
                "row": {
                    "colors": ['#f3f3f3', 'transparent'],
                    "opacity": 0.5
                }
            },
            "chart": {
                "height": 450,
                "type": 'line'
            },
            "stroke": {
                "width": 4
            },
            "markers": {
                "size": 3,
                "strokeWidth": 0
            },
            "colors": ["#0095da", "#f26649", "#237073"],
            "xaxis": {
                "tickAmount": 12,
                "tickPlacement": "on"
            },
            "yaxis": {
                "labels": {
                    "align": "right"
                },
                "decimalsInFloat": 0
            }
        }
        return od


class PlayersAndMembersDataset:

    def __init__(self, **kwargs):
        self.Players = GamePlayerCount(**kwargs)
        self.Members = GamePlayerCount(player_filters={'is_member': True}, **kwargs)
        self.NewPlayers = GamePlayerCount(numerator_fcn='new_players', **kwargs)

    def get_labels(self):
        return self.Members.get_labels()

    def get_all_series(self):
        return [
            {"name": "Players", "data": self.Players.get_data()},
            {"name": "Members", "data": self.Members.get_data()},
            {"name": "New Players", "data": self.NewPlayers.get_data()},
        ]


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
            answers__question__game__series__slug=self.slug,
            **self.player_filters
        ).values(
            game_id=F('answers__question__game__game_id')
        ).annotate(num_players=Count('id', distinct=True))
        return {game['game_id']: game['num_players'] for game in players_with_filter_count}

    def new_players(self):
        first_games = Player.objects.filter(
            answers__question__game__series__slug=self.slug).annotate(
            first_game=Min('answers__question__game__game_id')
        ).values_list('id', 'first_game')
        return Counter([fg[1] for fg in first_games])

    @cached_property
    def periods(self):
        gids = Game.objects.filter(series__slug=self.slug, game_id__gte=self.since_game,
                                   end__lte=our_now()).values_list('game_id', flat=True)
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


