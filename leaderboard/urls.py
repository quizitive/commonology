from django.urls import path

from leaderboard import views
from leaderboard import htmx

urlpatterns = [
    path('', views.LeaderboardView.as_view(), name='leaderboard'),
    path('<int:game_id>/', views.LeaderboardView.as_view(), name='leaderboard-game'),
    path('results/', views.ResultsView.as_view(), name='results'),
    path('htmx/', htmx.LeaderboardHTMXView.as_view(), name='leaderboard-htmx')
]
