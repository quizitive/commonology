import debug_toolbar

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin
from game import views


urlpatterns = [
    path('', include('users.urls')),
    path('admin/', admin.site.urls),
    path('__debug__/', include(debug_toolbar.urls)),
    path('', views.index, name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('leaderboard/', views.loggedin_leaderboard_view, name='loggedin_leaderboard'),
    path('leaderboard/<int:game_id>/', views.game_leaderboard_view, name='game_leaderboard'),
    path('leaderboard/<str:uuid>/', views.uuid_leaderboard_view, name='uuid_leaderboard'),
    path('results/<int:game_id>/', views.ResultsView.as_view(), name='results'),
    path('score/', views.tabulator_form_view, name='tabulator_form'),
    path('marc/', views.marc, name='marc'),
    path('ted/', views.ted, name='ted'),
    path('mailtest/', views.mailtest, name='mailtest'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
