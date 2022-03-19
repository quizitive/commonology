from django.urls import path
from django.views.generic.base import RedirectView

from leaderboard import views
from leaderboard import htmx


app_name = 'leaderboard'


urlpatterns = [
    path('', views.LeaderboardView.as_view(), name='series-home'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='current-leaderboard'),
    path('leaderboard/<int:game_id>/', views.LeaderboardView.as_view(), name='game-id-leaderboard'),
    path('results/', views.ResultsView.as_view(), name='current-results'),
    path('results/<int:game_id>/', views.ResultsView.as_view(), name='game-id-results'),
    path('host-note/', views.HostNoteView.as_view(), name='current-host-note'),
    path('host-note/<int:game_id>/', views.HostNoteView.as_view(), name='game-id-host-note'),
    path('stats/', views.PlayerStatsView.as_view(), name='player-stats'),
    path('leaderboard/htmx/', htmx.LeaderboardHTMXView.as_view(), name='htmx'),
    path('share/', views.results_share_count_view, name='share'),
    # path('me/', views.PlayerHomeView.as_view(), name='player-home')

    # todo: deprecate this after week 42
    path('leaderboard/results/', RedirectView.as_view(pattern_name='leaderboard:current-results'))
]
