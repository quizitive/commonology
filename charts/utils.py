from inspect import getmembers, ismethod
import json
from urllib import parse
from uuid import uuid4

from project.utils import REDIS


class BaseChartSubclass:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)


class BaseSmartChart(BaseChartSubclass):

    data_class = None
    name = None
    options_dict = {
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
            "width": 4,
            "curve": "straight"
        },
        "markers": {
            "size": 3,
            "strokeWidth": 0
        },
        "colors": ["#0095da", "#f26649", "#237073"],
        "xaxis": {
            "tickPlacement": "on"
        },
        "yaxis": {
            "labels": {
                "align": "right"
            },
            "decimalsInFloat": 0
        }
    }

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.uuid = uuid4().hex
        super().__init__(**kwargs)

    def html_id(self):
        return f"{self.name}_{self.uuid}"

    @classmethod
    def htmx_path(cls, **kwargs):
        url_fmt = parse.urlencode(kwargs)
        REDIS.set(url_fmt, 1, timeout=30)
        return f"/charts/htmx/{cls.name}?{url_fmt}"

    def options(self):
        # called from template: .../charts/simple_chart.html
        op_dict = self.options_dict
        for name, get_method in self._get_methods():
            if name in op_dict and isinstance(op_dict[name], dict) and isinstance(get_method(), dict):
                op_dict[name].update(get_method())
            else:
                op_dict[name] = get_method()
        return json.dumps(op_dict)

    def get_series(self):
        return self.data_class.get_all_series()

    def get_xaxis(self):
        # x axis labels
        return {
            'tickAmount': min(12.0, len(self.data_class.get_labels()) / 4),
            "categories": self.data_class.get_labels()
        }

    def _get_methods(self):
        get_methods = []
        for name, method in getmembers(self, ismethod):
            parsed_name = name.split("_")
            if parsed_name[0] != "get":
                continue
            get_methods.append((self._to_camel_case(parsed_name[1:]), method))
        return get_methods

    @staticmethod
    def _to_camel_case(components):
        return components[0] + ''.join(x.title() for x in components[1:])


class BaseChartDataset:

    def get_all_series(self):
        raise NotImplementedError

    def get_labels(self):
        raise NotImplementedError


class BaseChartSeries(BaseChartSubclass):

    def get_data(self):
        raise NotImplementedError
