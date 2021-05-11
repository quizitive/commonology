from django.urls import path, include
from community import views, htmx

urlpatterns = [
    path('home/', views.PlayerHomeView.as_view(), name='player-home'),
    path('htmx/', htmx.ThreadHTMXView.as_view(), name='htmx'),
    path('<slug:series_slug>/', include('leaderboard.urls', namespace='series-leaderboard')),
]
