from django.urls import path
from django.views.generic import RedirectView
from game import views

urlpatterns = [
    path('score/', views.tabulator_form_view, name='tabulator_form'),
    path('about/', views.about_view, name='about'),
    path('game/41/', RedirectView.as_view(url='https://docs.google.com/forms/d/1C207C6iPSUY5VmIubgZjdvsz8B4xJo9uLhLkuV42NnI/viewform?edit_requested=true'))
]
