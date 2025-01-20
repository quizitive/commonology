from django.urls import path, re_path

from . import views, consumers

urlpatterns = [
    path("<str:room_name>/", views.room, name="room"),
]

# using re_path due to limitations with URLPatterns
websocket_urlpatterns = [
    # re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r"ws/chat/(?P<game_id>\w+)/$", consumers.CommentConsumer.as_asgi()),
]
