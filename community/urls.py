from django.urls import path

from community import views

urlpatterns = [
    path('home/', views.PlayerHomeView.as_view(), name='home'),
]
