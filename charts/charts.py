from urllib import parse

from game.charts import PlayerTrendChart


class Charts:
    weekly_players = "weekly_players"

    @classmethod
    def lazy_chart(cls, chart_name, **kwargs):
        url_fmt = parse.urlencode(kwargs)
        return f"{chart_name}?{url_fmt}"

    @classmethod
    def get_chart_class(cls, chart_name):
        charts = {
            cls.weekly_players: PlayerTrendChart
        }
        return charts[chart_name]
