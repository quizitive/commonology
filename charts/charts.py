from game.charts import GamePlayerTrendChart


class Charts:
    """A container class for accessing available charts"""

    # Define charts here
    game_player_trend = GamePlayerTrendChart

    @classmethod
    def get_chart(cls, chart_name):
        return getattr(cls, chart_name)
