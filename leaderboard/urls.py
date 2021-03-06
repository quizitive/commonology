from django.urls import path

from leaderboard import views

urlpatterns = [
    path('', views.loggedin_leaderboard_view, name='loggedin_leaderboard'),
    path('<int:game_id>/', views.game_leaderboard_view, name='game_leaderboard'),
    path('<str:uuid>/', views.LeaderboardView.as_view(), name='uuid_leaderboard'),
    path('results/<int:game_id>/', views.ResultsView.as_view(), name='results')
]
