import json

from django.contrib import admin
from django.urls import path
from django.shortcuts import render

from project.utils import quick_cache

from game.charts import PlayerTrendChart, PlayersAndMembersDataset


class CommonologyAdmin(admin.AdminSite):
    index_template = 'admin/index.html'
    enable_nav_sidebar = True

    def get_urls(self):
        urls = super().get_urls()
        other_urls = [path('stats/', self.admin_view(self.stats_view), name='game-stats'), ]
        return other_urls + urls

    def stats_view(self, request):
        # chart_1 = PlayerTrendChart(
        #     PlayersAndMembersDataset, slug='commonology', name="chart_3", since_game=38)
        # chart_2 = PlayerTrendChart(
        #     PlayersAndMembersDataset, slug='commonology', name="chart_2", since_game=38, agg_period=4)
        context = dict(
            # Include common variables for rendering the admin template.
            self.each_context(request),
            title='Stats'
        )
        context.update({
            "charts": [
                {
                    "name": "weekly_players",
                    "header": "Player/Member Growth Weekly",
                    "custom_message": "Weekly player counts, of whom are members and new players"
                },
                {
                    "name": "weekly_players_4wma",
                    "header": "Player/Member Growth 4-Week-Average",
                    "custom_message": "4-week-average player counts, of whom are members and new players"
                }
            ]
        })
        return render(request, 'game/stats.html', context)
