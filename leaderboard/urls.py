from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin

from leaderboard import views

urlpatterns = [
    path('', views.loggedin_leaderboard_view, name='loggedin_leaderboard'),
    path('<int:game_id>/', views.game_leaderboard_view, name='game_leaderboard'),
    path('<str:uuid>/', views.uuid_leaderboard_view, name='uuid_leaderboard'),
    path('results/<int:game_id>/', views.ResultsView.as_view(), name='results')
]