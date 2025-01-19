from django.urls import path
from mail import views


app_name = "mail"

urlpatterns = [
    path("mailtest/", views.mailtest, name="mailtest"),
    path("onemail/", views.OneMailView.as_view(), name="one_mail"),
]
