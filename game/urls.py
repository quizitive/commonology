from django.urls import path
from game import views


app_name = 'game'

urlpatterns = [
    path('score/', views.tabulator_form_view, name='tabulator_form'),
    path('about/', views.about_view, name='about'),
    path('play/', views.GameEntryView.as_view(), name='play'),
    path('play/<uidb64>', views.GameEntryValidationView.as_view(), name='player_confirm'),
]
