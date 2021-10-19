from django.urls import path
from rewards import views


urlpatterns = [
    path("claim/", views.ClaimView.as_view(), name="claim"),
    path("award_certificate/<int:n>/", views.AwardCertificate.as_view(), name='award_certificate'),
]
