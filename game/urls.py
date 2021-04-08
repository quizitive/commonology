from django.urls import path

from game import views

urlpatterns = [
    path('score/', views.tabulator_form_view, name='tabulator_form'),
    path('ted/', views.ted, name='ted'),
]
