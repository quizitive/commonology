from inspect import getmembers, ismethod
import json

from django.utils.functional import cached_property


class BaseChartSubclass:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)
        for method in self.__dir__():
            if method[:4] == 'get_':
                self.__setattr__(method[4:], self.__getattribute__(method)())


class BaseSmartChart(BaseChartSubclass):

    def __init__(self, data_class, name, **kwargs):
        self.data_class = data_class
        self.name = name
        self.kwargs = kwargs
        self.options = self._get_options()
        super().__init__(**kwargs)

    @cached_property
    def data(self):
        return self.data_class(**self.kwargs)

    @cached_property
    def data_name(self):
        return self.name + "-data"

    def get_series(self):
        return self.data_class(**self.kwargs).get_all_series()

    def get_xaxis(self):
        # x axis labels
        return {
            "categories": self.data_class(**self.kwargs).get_labels()
        }

    def _options_dict(self):
        return {}

    def _get_options(self):
        op_dict = self._options_dict()
        for name, get_method in self._get_methods():
            if name in op_dict:
                op_dict[name].update(get_method())
            else:
                op_dict[name] = get_method()
        return json.dumps(op_dict)

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


class BaseChartData(BaseChartSubclass):

    def get_data(self):
        raise NotImplementedError

    def get_labels(self):
        raise NotImplementedError
