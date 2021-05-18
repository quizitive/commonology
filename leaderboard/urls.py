from django.urls import path

from leaderboard import views
from leaderboard import htmx


app_name = 'leaderboard'


urlpatterns = [
    path('', views.LeaderboardView.as_view(), name='series-home'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='current-leaderboard'),
    path('leaderboard/<int:game_id>/', views.LeaderboardView.as_view(), name='game-id-leaderboard'),
    path('results/', views.ResultsView.as_view(), name='current-results'),
    path('results/<int:game_id>/', views.ResultsView.as_view(), name='game-id-results'),
    path('leaderboard/htmx/', htmx.LeaderboardHTMXView.as_view(), name='htmx'),
    # path('me/', views.PlayerHomeView.as_view(), name='player-home')
]
