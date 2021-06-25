from django.urls import path
from game import views

app_name = 'game'

urlpatterns = [
    path('score/', views.tabulator_form_view, name='tabulator_form'),
    path('play/', views.GameEntryView.as_view(), name='play'),
    path('play/<game_uuid>', views.GameEntryView.as_view(), name='play'),
    path('play/<game_uuid>/<pending_uuid>', views.GameEntryValidationView.as_view(), name='player_confirm'),
]
