from django.urls import path
from django.views.generic import RedirectView
from game import views


app_name = 'game'

urlpatterns = [
    path('score/', views.tabulator_form_view, name='tabulator_form'),
    path('about/', views.about_view, name='about'),
    path('play/', views.GameEntryView.as_view(), name='play'),
]
