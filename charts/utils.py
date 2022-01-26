from inspect import getmembers, ismethod
import json


class BaseChartSubclass:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)


class BaseSmartChart(BaseChartSubclass):

    data_class = None
    name = None
    options_dict = {}

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        super().__init__(**kwargs)

    def options(self):
        op_dict = self.options_dict
        for name, get_method in self._get_methods():
            if name in op_dict:
                op_dict[name].update(get_method())
            else:
                op_dict[name] = get_method()
        return json.dumps(op_dict)

    def get_series(self):
        return self.data_class(**self.kwargs).get_all_series()

    def get_xaxis(self):
        # x axis labels
        return {
            "categories": self.data_class(**self.kwargs).get_labels()
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

