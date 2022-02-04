from game.charts import GamePlayerTrendChart
from charts.configs.users_charts import SubscribersChart


class Charts:
    """A container class for accessing available charts"""

    # Define charts here
    game_player_trend = GamePlayerTrendChart
    subscribers_trend = SubscribersChart

    @classmethod
    def get_chart(cls, chart_name):
        return getattr(cls, chart_name)
