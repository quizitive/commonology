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

    @quick_cache()
    def stats_view(self, request):
        chart_1 = PlayerTrendChart(
            PlayersAndMembersDataset, slug='commonology', name="chart_3", since_game=38)
        chart_2 = PlayerTrendChart(
            PlayersAndMembersDataset, slug='commonology', name="chart_2", since_game=38, agg_period=4)
        context = dict(
            # Include common variables for rendering the admin template.
            self.each_context(request),
            title='Stats'
        )
        context.update({
            "chart_1": chart_1,
            "chart_2": chart_2,
        })
        return render(request, 'game/stats.html', context)
