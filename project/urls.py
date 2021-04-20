import debug_toolbar

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin
from game import views

urlpatterns = [

    path('', include('users.urls')),
    path('', include('game.urls')),
    path('', include('mail.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('leaderboard/', include('leaderboard.urls')),
    path('c/', include('community.urls')),
    path('admin/', admin.site.urls),
    path('', include('social_django.urls', namespace='social')),
    path('__debug__/', include(debug_toolbar.urls)),
    path('', views.index, name='home'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + \
              static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
