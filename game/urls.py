from django.urls import path
from game import views

app_name = 'game'

urlpatterns = [
    # path('score/', views.tabulator_form_view, name='tabulator_form'),
    path('play/', views.GameEntryView.as_view(), name='play'),
    path('play/<game_uuid>/', views.GameEntryView.as_view(), name='uuidplay'),
    path('play/<game_uuid>/<pending_uuid>/', views.GameEntryValidationView.as_view(), name='player_confirm'),
    path('game/<int:game_id>/', views.GameFormView.as_view(), name='game-form'),
    path('game/<int:game_id>/<str:player_signed_id>/', views.GameFormView.as_view(), name='game-view'),
    path('instant/', views.InstantGameView.as_view(), name='instant-game'),
    path('suggest-a-question/', views.QuestionSuggestionView.as_view(), name='question-suggest'),
    path("award_certificate/<int:game_id>/", views.AwardCertificateView.as_view(), name='award_certificate'),
    path('award_certificate/', views.AwardCertificateFormView.as_view(), name='award_certificate_form'),
]
