from django.urls import path
from django.views.generic import RedirectView
from game import views

urlpatterns = [
    path('score/', views.tabulator_form_view, name='tabulator_form'),
    path('about/', views.about_view, name='about'),
    path('play/', RedirectView.as_view(url='https://docs.google.com/forms/d/1ZOnEcI5I8zay9tOk5KoUT69yss0wk3eHKb0K2MfInSY/viewform?edit_requested=true'))
]
