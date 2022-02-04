from django.contrib import admin
from django.db.models import Min
from django.urls import path
from django.shortcuts import render

from project.htmx import htmx_call
from charts.charts import Charts
from game.models import Game


class CommonologyAdmin(admin.AdminSite):
    index_template = 'admin/index.html'
    enable_nav_sidebar = True

    def get_urls(self):
        urls = super().get_urls()
        other_urls = [path('stats/', self.admin_view(self.stats_view), name='game-stats'), ]
        return other_urls + urls

    def stats_view(self, request):
        context = dict(
            # Include common variables for rendering the admin template.
            self.each_context(request),
            title='Stats'
        )
        context.update({
            "cards": [
                {
                    "chart": htmx_call(request, Charts.game_player_trend.htmx_path(slug='commonology')),
                    "header": "Player/Member Growth Weekly",
                    "custom_message": "Weekly player counts, of whom are members and new players"
                },
                {
                    "chart": htmx_call(request, Charts.game_player_trend.htmx_path(slug='commonology', agg_period=4)),
                    "header": "Player/Member Growth 4-Week-Average",
                    "custom_message": "4-week-average player counts, of whom are members and new players"
                },
                {
                    "chart": htmx_call(request, Charts.subscribers_trend.htmx_path()),
                    "header": "Players and subscribers by date joined",
                    "custom_message": f"Cumulative count of total players and current "
                                      f"subscribers by the date they joined"
                },
            ]
        })
        return render(request, 'game/stats.html', context)
