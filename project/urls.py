import debug_toolbar

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin
from game import views


urlpatterns = [
    path('', include('users.urls')),
    path('', include('game.urls')),
    path('leaderboard/', include('leaderboard.urls')),
    path('admin/', admin.site.urls),
    path('__debug__/', include(debug_toolbar.urls)),
    path('', views.index, name='home'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
