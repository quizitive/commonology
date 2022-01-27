from django.contrib import admin
from django.db.models import Min
from django.urls import path
from django.shortcuts import render

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
                    "chart": Charts.lazy_chart(Charts.game_player_trend, slug='commonology'),
                    "header": "Player/Member Growth Weekly",
                    "custom_message": "Weekly player counts, of whom are members and new players"
                },
                {
                    "chart": Charts.lazy_chart(Charts.game_player_trend, slug='commonology', agg_period=4),
                    "header": "Player/Member Growth 4-Week-Average",
                    "custom_message": "4-week-average player counts, of whom are members and new players"
                }
            ]
        })
        return render(request, 'game/stats.html', context)
