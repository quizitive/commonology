from datetime import datetime

from django.db.models import Count
from django.db.models.functions import Trunc
from users.models import Player

from charts.utils import BaseSmartChart, BaseChartDataset, BaseChartSeries


class SubscribersChart(BaseSmartChart):

    name = "subscribers_trend"

    def __init__(self, **kwargs):
        self.data_class = SubscribersDataset(**kwargs)
        super().__init__(**kwargs)

    def get_xaxis(self):
        return {"type": "datetime"}


class SubscribersDataset(BaseChartDataset):

    def __init__(self, **kwargs):
        self.subscribers = SubscribersOverTime(**kwargs)

    def get_labels(self):
        pass

    def get_all_series(self):
        return {"data": self.subscribers.get_data()}


class SubscribersOverTime(BaseChartSeries):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.query = self._query()

    def _query(self):
        return Player.objects.filter(subscribed=True).annotate(
            joined=Trunc('date_joined', 'day')).order_by('joined').values('joined').annotate(
            count=Count('id'))

    def get_data(self):
        return [{'x': d['joined'].strftime('%Y-%m-%d'), 'y': d['count']} for d in self.query]

    def get_labels(self):
        return [d['date_joined'] for d in self.query]
