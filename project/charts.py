from pychartjs import BaseChart, ChartType, Color


class ChartJS(BaseChart):

    def __init__(self, data_class, name, **kwargs):
        self.data_class = data_class
        self.name = name
        self.kwargs = kwargs

    @property
    def data_name(self):
        return self.name + "-data"

    @property
    def data(self):
        return self.data_class(**self.kwargs)


class BaseChartDataClass:

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)
        self.data = self._data()

    def _data(self):
        raise NotImplementedError


class ExampleDataClass(BaseChartDataClass):

    def _data(self):
        if self.game_id == 1:
            return [12, 19, 3, 17, 10]
        return [1, 4, 13, 12, 9]


class ExampleDataClass2(BaseChartDataClass):

    def _data(self):
        if self.game_id == 1:
            return [12, 19, 3, 17, 10]
        return [1, 4, 13, 12, 9]


class ExampleTwoDatasetDataClass(BaseChartDataClass):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dataset1_1 = self._dataset_1()

    class Dataset1(BaseChartDataClass):
        def _data(self):
            if self.game_id == 1:
                return [12, 19, 3, 17, 10]
            return [1, 4, 13, 12, 9]

    class Dataset2(BaseChartDataClass):
        def _data(self):
            if self.game_id == 1:
                return [12, 19, 3, 17, 10]
            return [1, 4, 13, 12, 9]


class GamePlayers(BaseChartDataClass):

    def _data(self):
        pass


class WeeklyPlayers(BaseChartDataClass):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.backgroundColor = Color.Green

    def _data(self):
        if self.game_id == 1:
            return [12, 19, 3, 17, 10]
        return [1, 4, 13, 12, 9]

