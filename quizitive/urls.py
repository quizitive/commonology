from django.urls import path
from quizitive import views


urlpatterns = [
    path("quizitive/", views.HomeView.as_view(), name="quizitive_home"),
]
