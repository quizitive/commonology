from django.urls import path, include
from community import views

urlpatterns = [
    path('home/', views.PlayerHomeView.as_view(), name='player-home'),
    path('<slug:series_slug>/', include('leaderboard.urls', namespace='series-leaderboard')),
    path('<slug:series_slug>/', include('game.urls', namespace='series-game')),
]
