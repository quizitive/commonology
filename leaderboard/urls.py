from django.urls import path

from leaderboard import views
from leaderboard import htmx


app_name = 'leaderboard'


urlpatterns = [
    path('', views.LeaderboardView.as_view(), name='default'),
    path('<int:game_id>/', views.LeaderboardView.as_view(), name='game'),
    path('results/', views.ResultsView.as_view(), name='results'),
    path('htmx/', htmx.LeaderboardHTMXView.as_view(), name='htmx')
]
