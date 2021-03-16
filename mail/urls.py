from django.urls import path
from mail import views

urlpatterns = [
    path('mailtest/', views.mailtest, name='mailtest'),
]
