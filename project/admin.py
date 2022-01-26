from django.contrib import admin
from django.urls import path
from django.shortcuts import render

from charts.charts import Charts


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
                    "chart": Charts.lazy_chart(
                        Charts.weekly_players,
                        slug='commonology',
                        name="weekly_players",
                        since_game=38
                    ),
                    "header": "Player/Member Growth Weekly",
                    "custom_message": "Weekly player counts, of whom are members and new players"
                },
                {
                    "chart": Charts.lazy_chart(
                        Charts.weekly_players,
                        slug='commonology',
                        name="weekly_players_4wk",
                        since_game=38,
                        agg_period=4
                    ),
                    "header": "Player/Member Growth 4-Week-Average",
                    "custom_message": "4-week-average player counts, of whom are members and new players"
                }
            ]
        })
        return render(request, 'game/stats.html', context)
