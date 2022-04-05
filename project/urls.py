import debug_toolbar
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin
from .views import index, about_view, product_view, our_story_view, testimonials_view, \
    tos_view, privacy_view, ContactView, raffle_rules_view, sponsor_view, instant_player_stats, \
    QRView, qr_poster_view

admin.site.site_header = "Commonology Administration"
admin.site.site_title = "Commonology Administration"

urlpatterns = [
    path('', index, name='home'),
    path('about/', about_view, name='about'),
    path('product/', product_view, name='product'),
    path('our_story/', our_story_view, name='our_story'),
    path('testimonials/', testimonials_view, name='testimonials'),
    path('raffle_rules/', raffle_rules_view, name='raffle_rules'),
    path('tos/', tos_view, name='tos'),
    path('privacy/', privacy_view, name='privacy'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('sponsor/', sponsor_view, name='sponsor'),
    path('qr/<rcode>', QRView.as_view(), name='qr_r'),
    path('qrposter', qr_poster_view, name='qr_poster'),
    path('', include('users.urls')),
    path('', include('game.urls')),
    path('', include('mail.urls')),
    path('', include('quizitive.urls')),
    path('', include('leaderboard.urls')),
    path('', include('rewards.urls')),
    path('c/<slug:series_slug>/', include('leaderboard.urls', namespace='series-leaderboard')),
    path('c/<slug:series_slug>/', include('game.urls', namespace='series-game')),
    path('chat/', include('chat.urls')),
    path('charts/', include('charts.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('admin/', admin.site.urls),
    path('', include('social_django.urls', namespace='social')),
    path('analytics/', instant_player_stats),
    path('__debug__/', include(debug_toolbar.urls)),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + \
    static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
