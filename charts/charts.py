from urllib import parse

from game.charts import GamePlayerTrendChart


class Charts:
    """A container class for accessing available charts"""

    # Define charts here, be sure to add to get_chart_class() below
    game_player_trend = "game_player_trend"

    @classmethod
    def get_chart_class(cls, chart_name):
        """Lookup charts by their name"""
        charts = {
            cls.game_player_trend: GamePlayerTrendChart
        }
        return charts[chart_name]

    @classmethod
    def lazy_chart(cls, chart_name, **kwargs):
        url_fmt = parse.urlencode(kwargs)
        return f"{chart_name}?{url_fmt}"
