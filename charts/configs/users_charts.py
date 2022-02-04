from datetime import datetime, timedelta

from django.db.models import Count
from django.db.models.functions import Trunc
from users.models import Player

from charts.utils import BaseSmartChart, BaseChartDataset, BaseChartSeries


class SubscribersChart(BaseSmartChart):

    name = "subscribers_trend"

    def __init__(self, **kwargs):
        self.data_class = SubscribersDataset(**kwargs)
        super().__init__(**kwargs)


class SubscribersDataset(BaseChartDataset):

    def __init__(self, **kwargs):
        self.all_players = PlayersOverTime(**kwargs)
        self.subscribers = PlayersOverTime(player_filters={'subscribed': True}, **kwargs)

    def get_labels(self):
        return self.all_players.get_labels()

    def get_all_series(self):
        return [
            {"name": "All Players", "data": self.all_players.get_data()},
            {"name": "Subscribers", "data": self.subscribers.get_data()},
        ]


class PlayersOverTime(BaseChartSeries):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.player_filters = kwargs.get("player_filters", {})
        min_date_str = kwargs.get("min_date", "2020-07-22")
        self.min_date = datetime.strptime(min_date_str, "%Y-%m-%d")
        self.query = self._query()

    def _query(self):
        return Player.objects.filter(**self.player_filters).annotate(
            joined=Trunc('date_joined', 'day')).order_by('joined').values('joined').annotate(
            count=Count('id'))

    def get_data(self):
        total_players = []
        cur_total = 0
        cur_date = self.min_date.date()
        for d in self.query:
            while cur_date < d['joined'].date():
                total_players.append(cur_total)
                cur_date += timedelta(days=1)
            cur_total += d['count']
            total_players.append(cur_total)
            cur_date += timedelta(days=1)
        return total_players

    def get_labels(self):
        numdays = (datetime.today().date() - self.min_date.date()).days
        return [(self.min_date.date() + timedelta(days=days)).strftime("%Y-%m-%d") for days in range(numdays)]
