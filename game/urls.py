from django.urls import path
from game import views

app_name = 'game'

urlpatterns = [
    path('score/', views.tabulator_form_view, name='tabulator_form'),
    path('play/', views.GameEntryView.as_view(), name='play'),
    path('play/<game_uuid>', views.GameEntryView.as_view(), name='uuidplay'),
    path('play/<game_uuid>/<pending_uuid>', views.GameEntryValidationView.as_view(), name='player_confirm'),
    path('game/<int:game_id>/', views.GameFormView.as_view(), name='game-form'),
    path('game/<int:game_id>/<str:player_signed_id>/', views.GameFormView.as_view(), name='game-view'),
    path('suggest-a-question/', views.QuestionSuggestionView.as_view(), name='question-suggest'),
    path('stats/', views.stats_view, name='game-stats')
]
