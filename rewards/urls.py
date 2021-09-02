from django.urls import path
from rewards import views


urlpatterns = [
    path("claim/", views.ClaimView.as_view(), name="claim"),
]
