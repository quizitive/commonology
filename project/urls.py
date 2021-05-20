import debug_toolbar

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin
from game import views
from .views import about_view

urlpatterns = [
    path('', views.index, name='home'),
    path('about/', about_view, name='about'),
    path('', include('users.urls')),
    path('', include('game.urls')),
    path('', include('mail.urls')),
    path('', include('quizitive.urls')),
    path('', include('leaderboard.urls')),
    path('c/<slug:series_slug>/', include('leaderboard.urls', namespace='series-leaderboard')),
    path('c/<slug:series_slug>/', include('game.urls', namespace='series-game')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('admin/', admin.site.urls),
    path('', include('social_django.urls', namespace='social')),
    path('__debug__/', include(debug_toolbar.urls)),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + \
    static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
