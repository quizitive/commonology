from django.urls import path, include
from community import views

urlpatterns = [
    path('home/', views.PlayerHomeView.as_view(), name='home'),
    path('<slug:series_slug>/', include('leaderboard.urls'))
]
