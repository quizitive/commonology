from datetime import datetime, timedelta

from django.db.models import Count
from django.db.models.functions import Trunc
from game.models import Game
from project.utils import our_now
from leaderboard.models import PlayerRankScore
from leaderboard.leaderboard import player_score_rank_percentile, player_percentile_in_all_games
from users.models import Player

from charts.utils import BaseSmartChart, BaseChartDataset, BaseChartSeries


class PlayerRankTrendChart(BaseSmartChart):

    name = "player_rank_trend"

    def __init__(self, **kwargs):
        self.data_class = PlayerRankDataset(**kwargs)
        super().__init__(**kwargs)

    def get_chart(self):
        return {
            "height": 450,
            "width": f"{len(self.data_class.get_labels()) * 45}px",
            "type": 'bar',
            "offsetX": -15,
            "zoom": {"enabled": False}
        }

    def get_grid(self):
        return {"row": {"opacity": 0}, "show": False}

    def get_xaxis(self):
        # x axis labels
        return {
            "categories": self.data_class.get_labels(),
            "labels": {
                "rotate": -90,
                "rotateAlways": True,
            },
            "tickPlacement": 'on'
        }

    def get_yaxis(self):
        return {"axisTick": {"show": False}, "axisBorder": {"show": False}, "labels": {"show": False}}

    def get_plot_options(self):
        return {"bar": {"borderRadius": 4, "columnWidth": "85%"}}

    def get_stroke(self):
        return {"curve": "smooth"}

    def get_colors(self):
        return ["#f26649", "#237073"]


class PlayerRankDataset(BaseChartDataset):

    def __init__(self, **kwargs):
        self.rank_history = PlayerRankHistory(**kwargs)
        # self.subscribers = PlayersOverTime(player_filters={'subscribed': True}, **kwargs)

    def get_labels(self):
        return self.rank_history.get_labels()

    def get_all_series(self):
        return [
            {"name": "Percentile", "data": self.rank_history.get_data()},
        ]


class PlayerRankHistory(BaseChartSeries):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.player_id = kwargs.get("player_id")
        self.slug = kwargs.get("slug")
        self.from_game = int(kwargs.get("from_game"))
        self.to_game = int(kwargs.get("to_game"))
        self.player_percentiles = player_percentile_in_all_games(self.player_id, self.slug)

    def get_data(self):
        return [pp for gid, pp in self.player_percentiles.items()
                if self.from_game <= gid <= self.to_game]

    def get_labels(self):
        return [f"Game {gid}" for gid, _ in self.player_percentiles.items()
                if self.from_game <= gid <= self.to_game]
