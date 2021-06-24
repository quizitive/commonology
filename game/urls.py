from django.urls import path
from game import views

app_name = 'game'

urlpatterns = [
    path('score/', views.tabulator_form_view, name='tabulator_form'),
    path('play/', views.GameEntryView.as_view(), name='play'),
    path('play/<uidb64>/', views.GameEntryValidationView.as_view(), name='player_confirm'),
    # path('my-answers/', views.GameFormView.as_view(), name='game-form'),
    path('game/<int:game_id>/', views.GameFormView.as_view(), name='game-form'),
    path('game/<int:game_id>/<str:player_answers_code>/', views.GameFormView.as_view(), name='game-view')
]
