from pychartjs import BaseChart, ChartType, Color, BaseChartDataClass
from game.models import Game

class ChartJS(BaseChart):

    def __init__(self, data_class, name, **kwargs):
        self.data_class = data_class
        self.name = name
        self.kwargs = kwargs
        self.type = ChartType.Line

    @property
    def data_name(self):
        return self.name + "-data"

    @property
    def data(self):
        return self.data_class(**self.kwargs)


class SimpleDataChart(BaseChart):

    def __init__(self, name, **kwargs):
        self.name = name
        self.kwargs = kwargs
        self.type = ChartType.Line

    @property
    def data_name(self):
        return self.name + "-data"

    class data:
        # data = [12, 19, 3, 17, 10]

        class Series1:
            data = [12, 19, 3, 17, 10]

        class Series2:
            data = [1, 4, 13, 12, 9]



class ExampleDataClass(BaseChartDataClass):

    labels = [f'foo{n}' for n in range(5)]

    def get_data(self):
        if hasattr(self, 'members'):
            return [12, 19, 3, 17, 10]
        return [1, 4, 13, 12, 9]


class ExampleMultiSeriesDatset:

    def __init__(self, **kwargs):
        self.dataset1 = ExampleDataClass(**kwargs)
        self.dataset2 = GamePlayerCount(40)
        # super().__init__(**kwargs)


class GamePlayerCount(BaseChartDataClass):

    def __init__(self, since_game, **kwargs):
        self.since_game = since_game
        super().__init__(**kwargs)

    def get_data(self):
        return [g.players.count() for g in Game.objects.filter(game_id__gte=self.since_game)]


class WeeklyPlayers(BaseChartDataClass):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.backgroundColor = Color.Green

    def get_data(self):
        if self.game_id == 1:
            return [12, 19, 3, 17, 10]
        return [1, 4, 13, 12, 9]

